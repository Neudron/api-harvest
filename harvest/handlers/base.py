from __future__ import annotations

import re
from datetime import datetime
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
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        path = SCREENSHOTS_DIR / f"{self.spec.slug}-{label}-{ts}.png"
        try:
            await page.screenshot(path=str(path), full_page=False)
        except Exception:
            pass
        return path

    async def capture_dom(self, page, around: str | None = None) -> tuple[str, Path]:
        HTML_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
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
        click_action,  # async callable
        timeout_ms: int = 10_000,
    ) -> str:
        """Install a MutationObserver, run click_action, await key text."""
        await page.evaluate(
            """
            () => {
              window.__harvestKeyCapture = new Promise((resolve) => {
                const matches = (el) => {
                  if (!el || el.nodeType !== 1) return false;
                  const tag = el.tagName.toLowerCase();
                  if (tag === 'input' && el.readOnly) return true;
                  if (tag === 'code' || tag === 'pre') return true;
                  const t = (el.getAttribute('data-testid') || '').toLowerCase();
                  if (t.includes('api-key') || t.includes('key')) return true;
                  const c = (el.className && el.className.toString().toLowerCase()) || '';
                  if (c.includes('api-key') || c.includes('apikey')) return true;
                  return false;
                };
                const extract = (el) => {
                  if (!el) return '';
                  if (el.value) return el.value;
                  return (el.textContent || '').trim();
                };
                // Check existing DOM first
                const existing = Array.from(document.querySelectorAll('input[readonly], code, pre, [data-testid*="key" i]'));
                for (const el of existing) {
                  if (matches(el)) {
                    const v = extract(el);
                    if (v && v.length >= 10) { resolve(v); return; }
                  }
                }
                const obs = new MutationObserver((muts) => {
                  for (const m of muts) {
                    for (const node of m.addedNodes) {
                      if (matches(node)) {
                        const v = extract(node);
                        if (v && v.length >= 10) { obs.disconnect(); resolve(v); return; }
                      }
                      if (node.querySelectorAll) {
                        for (const child of node.querySelectorAll('*')) {
                          if (matches(child)) {
                            const v = extract(child);
                            if (v && v.length >= 10) { obs.disconnect(); resolve(v); return; }
                          }
                        }
                      }
                    }
                  }
                });
                obs.observe(document.body, { childList: true, subtree: true });
                setTimeout(() => { obs.disconnect(); resolve(''); }, %d);
              });
            }
            """ % timeout_ms  # noqa: UP031 — JS body has braces, %-format keeps it readable
        )
        await click_action()
        text = await page.evaluate("() => window.__harvestKeyCapture")
        if not text:
            return ""
        if self.key_pattern:
            m = self.key_pattern.search(text)
            if m:
                return m.group(0)
        return text.strip()

    # ---- recipe entrypoints to override ----

    async def run(self, page) -> HarvestResult:  # pragma: no cover - subclass impl
        raise NotImplementedError
