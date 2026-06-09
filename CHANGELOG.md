# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Live key validation** (`harvest/validate.py`): a new `harvest validate`
  command and a `harvest run --validate` flag that make one cheap authenticated
  probe per provider (almost always `GET {base}/v1/models`) to confirm a captured
  key actually authenticates, instead of only matching its format regex. Outcomes
  (`valid` / `invalid` / `unsupported` / `error`) are recorded on each
  `HarvestResult` and surfaced in `keys.json`, a new `Valid` column in `keys.md`,
  the dashboard (`EventKind.VALIDATE`), and the command's exit code (non-zero on
  any invalid key). Stdlib-only (`urllib.request`) so it adds no dependency, with
  an injectable opener that keeps the tests fully offline. Providers without an
  account-agnostic probe resolve to `unsupported` rather than a false failure.
- **Retries with backoff** (`harvest/retry.py`): opt-in per-provider retries with
  exponential backoff. `is_retryable()` classifies transient failures
  (`HandlerError`, timeouts) vs. terminal ones (CAPTCHA, manual login, user skip,
  AI budget). Off by default (`max_attempts=1`); CC/phone providers never auto-retry.
- **Interactive-aware provider timeout**: a wall-clock watchdog that pauses while
  the user is in a manual takeover (credit card / SMS / CAPTCHA), so interactive
  entry is never cut off. Off by default (`provider_timeout_s=0`).
- **Multi-sink EventBus**: `subscribe()` fan-out so multiple consumers (dashboard,
  audit sink, future reporting) each receive every event. `JsonlEventSink` records
  all events to `.harvest/events.jsonl`.
- `EventKind.RETRY` event for surfacing retry attempts in the dashboard.
- **Settings system** (`harvest/settings.py`): config resolution with precedence
  CLI flags > `HARVEST_*` env > config file (`~/.config/api-harvest/config.toml`
  or `./.harvest.toml`) > defaults. `config.py` is now a backward-compatible shim.
- **AI backend abstraction** (`harvest/ai/`): pluggable `LLMBackend` protocol with
  `GeminiBackend`, `NullBackend`, and `FakeBackend` (enables offline testing of
  budget enforcement and audit logging without google-genai or a network).
- `version` command + `--version` flag; `doctor` preflight command; shell
  completion for provider slugs; `run --dry-run` to preview the run plan.
- `ai-log` command summarizing the AI selector-rescue audit log
  (`harvest/ai/audit.py`): calls per provider, error rate, rescue confidence.
- `report` command writing `outputs/report.md` (`harvest/report.py`): overall
  success rate, per-tier breakdown, and failure reasons.
- **Handler plugin system**: third-party handlers can register via the
  `harvest.handlers` entry-point group. Core handlers win slug collisions;
  broken plugins are skipped. (Trust boundary: plugins run arbitrary automation.)
- CI now runs a Python 3.11 / 3.12 / 3.13 matrix.

### Tested
- Handler recipes (`GoogleSsoCreateKeyRecipe`) now have offline smoke tests via
  a `FakePage`/`FakeLocator` harness, covering captured-key/done, missing-key and
  unclickable-button failures, and CAPTCHA / Google sign-in takeover routing.

### Changed
- **Rich dashboard redesign** (`harvest/dashboard.py`). A cohesive design system
  (semantic success/danger/warning/info palette, cyan brand accent), status
  badges with icons (`✓ DONE`, `◐ RUN`, `✗ FAIL`, `↷ SKIP`, `· WAIT`), a
  tier-grouped provider table with an active-row marker and per-provider CC/SMS
  flags, and a colour-coded activity log. The header now shows live status pills
  plus elapsed time, AI-rescue count, and retry count. The dashboard is now the
  Live renderable itself (`__rich__`), repainted by a single-threaded asyncio
  ticker (Rich's background refresh thread is disabled), so the clock, spinner,
  and progress bar animate continuously between events without the render ever
  racing the event loop's state updates.
  - **`[p]` pause hotkey is now actually wired**: it previously emitted
    `DASHBOARD_PAUSE`/`RESUME` events that `_apply` dropped, so the view never
    froze. `_apply` now soft-freezes/unfreezes the view (without tearing down
    Live), and the footer shows a `PAUSED` indicator.
  - **`RETRY` events are now handled** (were silently ignored): they increment a
    retry counter shown in the header and update the current step.
  - The footer lists every key: `[p]` pause/resume, `[s]` skip, `[q]` quit,
    `^C` abort.
- **Provider API-key URLs refreshed to canonical paths** (`providers.md`). Entries
  that previously stored a bare domain plus a parenthetical note (e.g.
  `https://console.mistral.ai (API Keys section after login)`) now hold a single
  clean, navigable URL — the parser uses the whole field value as the navigation
  target, so the parenthetical text was being passed to `page.goto()`. Deep
  "create key" paths were verified and adopted where stable/account-agnostic:
  Mistral (`/api-keys`), Cohere (`/api-keys`), NVIDIA NIM (`/settings/api-keys`),
  Cloudflare (`/profile/api-tokens`), Anthropic (`/settings/keys`), Baseten
  (`/settings/api_keys`), Nebius (`/project/api-keys`), Upstage (`/api-keys`),
  Modal (`/settings/tokens`), Hyperbolic (`/settings/api-keys`), Scaleway
  (`/iam/api-keys`), Novita (`/settings/key-management`), OpenCode Zen (`/zen`).
  Team/session-scoped consoles (Cerebras, xAI, AI21, Inference.net, NLP Cloud)
  keep their stable bare domain.
- **Provider free-tier / trial claims refreshed for accuracy** (`providers.md`),
  free-text only — no behavioural fields (`requires_cc` / `requires_phone`)
  changed. Notably: GitHub Models is no longer "via Copilot Free plan" (Copilot
  moved to usage-based AI Credits on 2026-06-01; the Models API has separate
  per-account quotas); Modal's Starter plan now grants $30/month to all accounts;
  xAI's $25 is a one-time signup credit, not recurring; Azure OpenAI no longer
  requires the manual Limited Access approval; Venice AI restructured into four
  tiers (Pro $18/mo includes API access); plus Gemini (free = Flash-class),
  Codestral (free beta ended), Vercel (card verification), and Perplexity
  (Pro API credit withdrawn) clarifications.
- GitHub Models handler now opens the current fine-grained PAT page
  (`/settings/personal-access-tokens/new`) instead of the legacy
  `/settings/tokens?type=beta` URL.
- Secret files (`.env`, `keys.json`, `state.json`, `ai_calls.jsonl`) are written
  with owner-only `0o600` permissions via a shared `output.secure_chmod()` helper.

### Security
- Harvested API keys are no longer left world-readable on disk.
