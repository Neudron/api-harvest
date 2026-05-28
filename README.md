# api-harvest

Feature-rich CLI that auto-signs up at AI API providers and harvests free API keys, using **Playwright** to drive your browser and **Google Gemini** to rescue broken selectors when provider UIs change.

Pulls 32 providers out of `providers.md` (13 permanent-free Tier 1 + 19 trial-credit Tier 2; the 7 paid-only providers are skipped). For each one it:

1. Opens the signup URL
2. Clicks **Continue with Google** (reuses your existing Google login)
3. Pauses for SMS verification when required, prompting you in the terminal
4. Pauses for credit-card entry when required (AWS, GCP, Azure), with the option to skip
5. Creates an API key, captures it via a `MutationObserver` to dodge modal-dismiss races
6. Writes the key to `outputs/.env`, `outputs/keys.json`, and `outputs/keys.md`

**Google AI Studio is always harvested first** — the captured Gemini key then powers an in-process "AI assistant" that rescues failed Playwright selectors on every subsequent provider (one try per failed step, strict per-run budget).

## Install

```bash
pip install -e .[dev]
playwright install chromium
```

## Browser modes

Choose one at runtime:

**CDP — attach to your already-running Chrome (safest against bot detection):**
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/harvest-chrome &
harvest run --cdp-port 9222
```

**Persistent profile — let api-harvest launch its own Chromium:**
```bash
harvest run --profile-dir ./harvest-chrome
```
On first run you'll sign in to Google manually; the profile is reused after.

## Commands

```bash
harvest list                          # show parsed providers
harvest status                        # show current state.json
harvest run --profile-dir ./chrome   # main flow
harvest run --only groq,cerebras     # subset
harvest run --skip aws-bedrock       # exclude
harvest reset cohere                 # clear one provider from state
harvest reset                        # clear all
harvest export                       # re-render outputs from keys.json
```

## Live dashboard

Sequential by design — Google SSO state is shared, and concurrency invites CAPTCHA. The Rich `Live` dashboard shows:

- counts: done / failed / skipped / pending
- a colored provider table
- the current provider + step
- a progress bar
- a recent-log tail
- hotkeys: `s` skip current, `q` quit gracefully, `p` pause

## Outputs

Written incrementally after every successful key, so partial runs are durable:

- `outputs/.env` — sourceable env vars (uses names from `providers.md`)
- `outputs/keys.json` — full structured record per provider
- `outputs/keys.md` — human-readable markdown table grouped by tier

## State and resume

State lives in `.harvest/state.json`. Re-running skips `done` and `user_skipped` providers automatically; `failed` providers are retried. Screenshots and DOM dumps for failures land in `.harvest/screenshots/` and `.harvest/html/`. Every Gemini selector-rescue call is logged to `.harvest/ai_calls.jsonl`.

## Scope / limitations

- **Free providers only.** The 7 "NOT FREE" providers in `providers.md` are excluded.
- **AWS / GCP / Azure** require manual credit-card entry; the CLI pauses for you. Azure OpenAI auto-skips because it requires manual access approval (1+ business days).
- **CAPTCHAs / email verification** always escalate to a manual takeover prompt.
- **Sequential only** in v1. `--concurrency N` is reserved for future use.

## Tests

Offline unit tests (parser, state, output) only:
```bash
pytest tests/test_parser.py tests/test_state.py tests/test_output.py
```
