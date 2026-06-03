# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
- CI now runs a Python 3.11 / 3.12 / 3.13 matrix.

### Changed
- Secret files (`.env`, `keys.json`, `state.json`, `ai_calls.jsonl`) are written
  with owner-only `0o600` permissions via a shared `output.secure_chmod()` helper.

### Security
- Harvested API keys are no longer left world-readable on disk.
