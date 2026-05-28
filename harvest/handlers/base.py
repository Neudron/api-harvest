from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from harvest.config import (
    HTML_DIR,
    PLAYWRIGHT_TIMEOUT_MS,
    SCREENSHOTS_DIR,
)
from harvest.events import emit_log, emit_step
from harvest.models import EventKind, HarvestResult, ProviderSpec, StepEvent
from harvest.selectors import CAPTCHA_IFRAME_SELECTORS

if TYPE_CHECKING:
    from harvest.ai_assistant import AIAssistant
    from harvest.events import EventBus
    from harvest.interactive import InteractiveManager


class HandlerError(Exception):
    def __init__(
        self,
        goal: str,
        last_selector: str | None = None,
        screenshot_path: str | None = None,
        html_path: str | None = None,
    ):
        super().__init__(goal)
        self.goal = goal
        self.last_selector = last_selector
        self.screenshot_path = screenshot_path
        self.html_path = html_path


class RequiresManualLogin(Exception):
    pass


class CaptchaDetected(Exception):
    pass


class UserSkipped(Exception):
    pass


class Handler:
    """Base class for all provider automation handlers."""

    # Subclasses override these
    create_button_candidates: list[str] = []
    key_extract_strategy: str = "modal_input"  # modal_input|modal_code_block|toast
    key_pattern: re.Pattern | None = None

    def __init__(
        self,
        spec: ProviderSpec,
        ai: AIAssistant | None,
        interactive: InteractiveManager,
        bus: EventBus,
    ):
        self.spec = spec
        self.ai = ai
        self.interactive = interactive
        self.bus = bus
        self._step_counter = 0

    # ---- utilities ----

    async def step(self, message: str) -> None:
        self._step_counter += 1
        await emit_step(self.bus, self.spec.slug, message)

    async def log(self, message: str) -> None:
        await emit_log(self.bus, self.spec.slug, message)

    async def screenshot(self, page, label: str) -> Path:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        path = SCREENSHOTS_DIR / f"{self.spec.slug}-{label}-{ts}.png"
        try:
            await page.screenshot(path=str(path), full_page=False)
        except Exception:
            pass
        return path

    async def capture_dom(self, page, around: str | None = None) -> tuple[str, Path]:
        HTML_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        path = HTML_DIR / f"{self.spec.slug}-{ts}.html"
        try:
            content = await page.content()
        except Exception:
            content = ""
        path.write_text(content[:200_000], encoding="utf-8")
        # Trim to 8KB for AI prompts
        if around:
            idx = content.find(around)
            if idx >= 0:
                start = max(0, idx - 4000)
                end = min(len(content), idx + 4000)
                trimmed = content[start:end]
            else:
                trimmed = content[:8000]
        else:
            trimmed = content[:8000]
        return trimmed, path

    async def check_captcha(self, page) -> None:
        for sel in CAPTCHA_IFRAME_SELECTORS:
            try:
                count = await page.locator(sel).count()
            except Exception:
                count = 0
            if count > 0:
                raise CaptchaDetected(f"detected: {sel}")

    async def check_google_signin_redirect(self, page) -> None:
        try:
            url = page.url
        except Exception:
            return
        if "accounts.google.com" in url and any(
            p in url for p in ("/signin/", "/challenge/", "/v3/signin")
        ):
            raise RequiresManualLogin(f"Google sign-in required: {url}")

    # ---- safe interactions with one-shot AI rescue ----

    async def safe_click(self, page, selector: str, *, goal: str, timeout: int = PLAYWRIGHT_TIMEOUT_MS) -> str:
        await self.step(f"click: {goal}")
        try:
            await page.locator(selector).first.click(timeout=timeout)
            return selector
        except Exception:
            await self.check_captcha(page)
            await self.check_google_signin_redirect(page)
            new_sel = await self._try_ai_rescue(
                page, goal=goal, failed_selector=selector, step_id=f"click:{goal}"
            )
            if new_sel:
                try:
                    await page.locator(new_sel).first.click(timeout=timeout)
                    return new_sel
                except Exception:
                    pass
            shot = await self.screenshot(page, f"fail-click-{self._step_counter}")
            html_trimmed, html_path = await self.capture_dom(page)
            raise HandlerError(
                goal=goal,
                last_selector=selector,
                screenshot_path=str(shot),
                html_path=str(html_path),
            ) from None

    async def safe_click_candidates(self, page, candidates: list[str], *, goal: str, timeout: int = PLAYWRIGHT_TIMEOUT_MS) -> str:
        await self.step(f"locate: {goal}")
        last_err: Exception | None = None
        for label in candidates:
            for selector in (
                f"role=button[name=/{re.escape(label)}/i]",
                f"role=link[name=/{re.escape(label)}/i]",
                f"text=/{re.escape(label)}/i",
                f"button:has-text({label!r})",
                f"a:has-text({label!r})",
            ):
                try:
                    loc = page.locator(selector).first
                    await loc.wait_for(state="visible", timeout=2_000)
                    await loc.click(timeout=timeout)
                    return selector
                except Exception as e:
                    last_err = e
                    continue
        # Fall through to AI rescue using the first candidate as "intended"
        try:
            await self.check_captcha(page)
            await self.check_google_signin_redirect(page)
        except Exception:
            raise
        ai_selector = await self._try_ai_rescue(
            page,
            goal=goal,
            failed_selector=" | ".join(candidates),
            step_id=f"candidates:{goal}",
        )
        if ai_selector:
            try:
                await page.locator(ai_selector).first.click(timeout=timeout)
                return ai_selector
            except Exception as e:
                last_err = e
        shot = await self.screenshot(page, f"fail-candidates-{self._step_counter}")
        html_trimmed, html_path = await self.capture_dom(page)
        raise HandlerError(
            goal=goal,
            last_selector=str(last_err) if last_err else None,
            screenshot_path=str(shot),
            html_path=str(html_path),
        ) from last_err

    async def _try_ai_rescue(
        self,
        page,
        *,
        goal: str,
        failed_selector: str,
        step_id: str,
    ) -> str | None:
        # Short-circuit BEFORE doing screenshot/DOM work — saves disk and bandwidth
        # for the first provider (Google AI Studio runs with ai=None).
        if self.ai is None:
            return None
        try:
            screenshot_bytes = await page.screenshot()
        except Exception:
            screenshot_bytes = None
        html_trimmed, _ = await self.capture_dom(page, around=failed_selector)
        try:
            suggestion = await self.ai.rescue_selector(
                step_id=step_id,
                provider_name=self.spec.name,
                goal=goal,
                failed_selector=failed_selector,
                url=page.url,
                html_snippet=html_trimmed,
                screenshot_png=screenshot_bytes,
            )
        except Exception as e:
            await self.log(f"ai rescue failed: {e}")
            return None
        # Don't waste a click on the same selector that just failed.
        if suggestion.playwright_selector.strip() == failed_selector.strip():
            await self.log("ai suggested the same selector that failed; skipping retry")
            return None
        await self.bus.emit(
            StepEvent(
                provider_slug=self.spec.slug,
                kind=EventKind.AI_CALL,
                message=f"rescued '{goal}' → {suggestion.playwright_selector[:50]}",
                payload=suggestion.model_dump(),
            )
        )
        return suggestion.playwright_selector or None

    # ---- key capture ----

    async def capture_key_after_click(
        self,
        page,
        *,
        click_action,  # async callable that triggers the modal
        timeout_ms: int = 15_000,
    ) -> str:
        """Run `click_action`, then watch for an element whose text matches
        `self.key_pattern`. The observer attaches AFTER the click so pre-existing
        DOM nodes (search inputs, request IDs) can't resolve us with stale data.

        If `self.key_pattern` is None we fall back to a permissive 20-char
        heuristic but still skip elements that look like search inputs.
        """
        pattern_source = self.key_pattern.pattern if self.key_pattern else None
        params = {
            "pattern": pattern_source,
            "timeout": timeout_ms,
        }

        await click_action()

        # Observer installed AFTER the click. The click is what opens the modal
        # in every flow we know about, so the matching node is necessarily a
        # post-click addition.
        text = await page.evaluate(
            """
            (params) => new Promise((resolve) => {
              const re = params.pattern ? new RegExp(params.pattern) : null;
              const minLen = re ? 0 : 20;
              const candidateSelector =
                'input[readonly], code, pre, '
                + '[data-testid*="api-key" i], [data-testid*="apikey" i], '
                + '[data-testid*="token" i], [class*="api-key" i]';

              const valueOf = (el) => {
                if (!el) return '';
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') return el.value || '';
                return (el.textContent || '').trim();
              };
              const looksLikeSearch = (el) => {
                if (!el || !el.attributes) return false;
                const t = (el.getAttribute('type') || '').toLowerCase();
                const ph = (el.getAttribute('placeholder') || '').toLowerCase();
                const nm = (el.getAttribute('name') || '').toLowerCase();
                return t === 'search' || ph.includes('search') || nm.includes('search');
              };
              const accept = (el) => {
                if (!el || el.nodeType !== 1) return null;
                if (looksLikeSearch(el)) return null;
                const v = valueOf(el);
                if (!v || v.length < minLen) return null;
                if (re && !re.test(v)) return null;
                return re ? (v.match(re) || [v])[0] : v;
              };
              const scan = (root) => {
                if (!root || !root.querySelectorAll) return null;
                if (root.matches && root.matches(candidateSelector)) {
                  const hit = accept(root);
                  if (hit) return hit;
                }
                for (const el of root.querySelectorAll(candidateSelector)) {
                  const hit = accept(el);
                  if (hit) return hit;
                }
                return null;
              };

              // First pass: scan the current DOM (post-click).
              const initial = scan(document.body);
              if (initial) { resolve(initial); return; }

              // Then watch for the modal to appear.
              const obs = new MutationObserver((muts) => {
                for (const m of muts) {
                  for (const node of m.addedNodes) {
                    const hit = scan(node);
                    if (hit) { obs.disconnect(); resolve(hit); return; }
                  }
                  // Also catch in-place value mutations (input.value updates)
                  if (m.type === 'attributes' && m.target) {
                    const hit = accept(m.target);
                    if (hit) { obs.disconnect(); resolve(hit); return; }
                  }
                }
              });
              obs.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['value'],
              });
              setTimeout(() => { obs.disconnect(); resolve(''); }, params.timeout);
            })
            """,
            params,
        )

        if not text:
            return ""
        text = str(text).strip()
        if self.key_pattern:
            m = self.key_pattern.search(text)
            return m.group(0) if m else ""
        return text

    def _safe_json(self, value) -> str:
        try:
            return json.dumps(value)
        except Exception:
            return "null"

    # ---- recipe entrypoints to override ----

    async def run(self, page) -> HarvestResult:  # pragma: no cover - subclass impl
        raise NotImplementedError
