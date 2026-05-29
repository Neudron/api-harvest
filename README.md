# api-harvest

A CLI that walks your browser through signing up at AI API providers and harvests their free API keys. Playwright drives the pages, your existing Google login handles SSO, and Google Gemini auto-rescues broken selectors when provider UIs drift.

## What it does

For each of the 32 free providers listed in `providers.md` (13 permanent-free Tier 1 plus 19 trial-credit Tier 2; the 7 paid-only providers are excluded), the CLI:

1. Opens the signup URL in a real Chrome window.
2. Clicks "Continue with Google" and reuses your existing Google session.
3. Pauses for SMS verification when required, but only after the SMS input is actually on screen.
4. Pauses for credit-card entry on AWS and GCP, with a one-keystroke skip option. Azure OpenAI auto-skips, since manual approval takes 1+ business days.
5. Pauses for email confirmation when the provider gates the dashboard behind a verification link (Cohere, Cloudflare, HuggingFace, NLP Cloud).
6. Creates an API key, captures it via a `MutationObserver` armed *after* the create click (so stale readonly inputs don't poison the result), and validates it against a per-provider regex.
7. Writes the key to `outputs/.env`, `outputs/keys.json`, and `outputs/keys.md` immediately, so partial runs are durable.

Google AI Studio is always harvested first. Its key bootstraps an in-process Gemini "AI assistant" that watches every subsequent provider. When a Playwright selector fails, Gemini sees a screenshot plus the surrounding DOM and proposes a replacement. Strict per-step (at most 1 rescue) and per-run (default 30) budgets prevent runaway spend.

## Install

```bash
pip install -e .[dev]
playwright install chromium
```

The CLI needs a real TTY for the hotkey listener and the SMS / CC / email prompts. Don't run it under `nohup` or inside non-interactive CI.

## Quick start

```bash
harvest run --profile-dir ./harvest-chrome
```

On the first run a fresh Chromium window opens. Sign in to Google manually once. The profile is reused on every subsequent run.

## Browser modes

Pick exactly one. The CLI rejects both-or-neither with a clear error.

### CDP: attach to your already-running Chrome

This is the safest option against bot detection because it's literally your real Chrome with all its cookies and extensions.

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.config/google-chrome &
harvest run --cdp-port 9222
```

api-harvest only closes pages *it* opened. Your Chrome window and any pre-existing tabs are left alone when the run ends.

### Persistent profile: let api-harvest launch its own Chromium

```bash
harvest run --profile-dir ./harvest-chrome
```

A dedicated Chromium profile lives at `./harvest-chrome`. First-run Google sign-in is manual; the profile is reused after.

## Commands

```bash
harvest list                                    # show all 32 parsed providers
harvest status                                  # show current state.json + AI budget used

harvest run --profile-dir ./harvest-chrome      # main flow
harvest run --cdp-port 9222                     # attach to existing Chrome
harvest run --only groq,cerebras                # subset
harvest run --skip aws-bedrock,gcp-vertex       # exclude
harvest run --no-dashboard                      # plain-log mode (CI, recordings)
harvest run --gemini-key sk-…                   # pre-seed; skips bootstrap from AI Studio
harvest run --ai-model gemini-2.5-flash         # default; --ai-budget 30 default

harvest reset cohere                            # forget one provider so re-run retries it
harvest reset                                   # forget everything

harvest export --format md                      # re-render keys.md from keys.json
harvest export --format env                     # re-render .env only
harvest export                                  # all three formats
```

`--gemini-key` also reads from `$GEMINI_API_KEY` / `$GOOGLE_GENERATIVE_AI_API_KEY` if the flag isn't passed.

## What a run looks like

A Rich `Live` dashboard takes over the terminal:

```
┌─────────────────────────────────────────────────────────────┐
│ api-harvest  done 7/32   failed 1   skipped 2   pending 22  │
├──────────────────────────────┬──────────────────────────────┤
│ Tier 1                       │ Now: Mistral                 │
│  Google Gemini   OK   AIza…  │ Step: waiting for SMS input  │
│  Groq            OK   gsk_…  │ ████████░░ 60%               │
│  Cerebras        OK   csk_…  │                              │
│  Mistral         RUN  …      │ Recent:                      │
│ Tier 2                       │   [groq] key captured        │
│  xAI             OK   xai-…  │   [ai] rescued #create-key   │
│  Anthropic       SKIP CC     │                              │
├──────────────────────────────┴──────────────────────────────┤
│ Hotkeys: [s] skip current   [q] quit gracefully   [p] pause │
└─────────────────────────────────────────────────────────────┘
```

Hotkeys (TTY only):

- `s` skips the current provider, marks it `user_skipped`, and moves on.
- `q` exits gracefully after the current provider finishes. State is flushed.
- `p` pauses or resumes the Live region, which is useful when reading manual instructions.

`Ctrl+C` is equivalent to `q` plus an immediate exit. Whatever was in flight is marked `user_skipped="interrupted (Ctrl+C)"` so it isn't retried on the next run.

## Manual interventions

The CLI handles these by pausing the dashboard and prompting on stdin:

| Trigger | Behavior |
|---|---|
| SMS verification | Waits up to 60 s for an SMS input field to appear, *then* prompts you to type the code. If no input ever appears (e.g., your phone is already verified on the account) the step is silently skipped. |
| Credit card | One-time prompt before the handler starts. `r` resumes, `s` skips the provider entirely. AWS Bedrock and GCP Vertex use this; Azure OpenAI auto-skips. |
| Email verification | If post-SSO the page says "verify your email" (or similar), pause for you to click the link, then `r` to continue. |
| CAPTCHA | Detected by iframe URL; same pause-for-takeover flow. |
| Stale Google login | If the SSO flow lands on `accounts.google.com/signin`, pause for you to sign in. |

## Outputs

Written incrementally after every successful key. `outputs/` is gitignored.

- `outputs/.env` holds `KEY=VALUE` lines using the env-var names from `providers.md`. De-duped on rewrite.
- `outputs/keys.json` holds structured records: provider slug, name, tier, status, key, env var, created_at, dashboard URL, rate limits, notes.
- `outputs/keys.md` is a human-readable markdown table grouped by tier; the key column shows only the last 4 chars for safety.

`harvest export` re-renders any subset of these from `keys.json` without re-running automation.

## State, resume, and debugging

State lives under `.harvest/` (gitignored):

- `.harvest/state.json` records what's done, failed, or skipped, plus `ai_budget_used`. Re-running skips `done` and `user_skipped` entries; `failed` ones are retried.
- `.harvest/screenshots/<slug>-<step>-<ts>.png` is captured on selector failure.
- `.harvest/html/<slug>-<ts>.html` is the full DOM at the moment of failure.
- `.harvest/errors/<slug>-<ts>.log` is the full Python traceback when an unexpected exception bubbles up from a handler. The path is included in `HarvestResult.error` so you can find it from `harvest status`.
- `.harvest/ai_calls.jsonl` is an audit log of every Gemini selector-rescue call: prompt, suggestion, latency, run-budget-used.

## How the Gemini AI rescue works

1. Google AI Studio runs first with `ai=None`. The captured `AIzaSy…` key bootstraps a long-lived `AIAssistant`.
2. For every subsequent provider, `Handler.safe_click` / `safe_click_candidates` wraps each Playwright click. On `TimeoutError`:
3. The handler captures a viewport screenshot plus the DOM trimmed to roughly 8 KB around the failed selector and asks Gemini what the right selector is, using structured JSON output validated against `SelectorSuggestion`.
4. The handler retries the suggested selector exactly once. If Gemini suggests the same selector that just failed (sometimes it does), the retry is skipped.
5. Budget is enforced strictly: per-step at most 1 rescue, per-run default 30. Track usage with `harvest status` (the `ai_budget_used` field).

To skip the Google-AI-Studio bootstrap and use your own key:

```bash
export GEMINI_API_KEY=AIza…
harvest run --profile-dir ./harvest-chrome --skip google-gemini-ai-studio
```

## Project layout

```
api-harvest/
├── providers.md                # the catalog the CLI parses
├── pyproject.toml              # entry point: harvest = harvest.cli:app
├── harvest/
│   ├── cli.py                  # typer commands
│   ├── parser.py               # providers.md to list[ProviderSpec]
│   ├── orchestrator.py         # sequential pipeline, hotkey handling, AI bootstrap
│   ├── browser.py              # CDP attach OR persistent profile
│   ├── dashboard.py            # Rich Live UI
│   ├── interactive.py          # async stdin prompts that play nice with Live
│   ├── hotkeys.py              # s/q/p listener
│   ├── events.py               # EventBus
│   ├── state.py                # atomic JSON state, resume
│   ├── output.py               # .env / keys.json / keys.md writers
│   ├── selectors.py            # SSO-button candidates + per-provider key regexes
│   ├── ai_assistant.py         # google-genai client; budget; audit log
│   └── handlers/
│       ├── base.py             # Handler ABC, safe_click, MutationObserver capture
│       ├── recipes.py          # GoogleSsoCreateKeyRecipe, EmailSignupRecipe, CloudConsoleRecipe
│       ├── google_aistudio.py  # bespoke, runs first, no AI rescue
│       ├── github_models.py    # bespoke, PAT with `models` scope
│       ├── cloudflare.py       # bespoke, token with Workers AI scope
│       ├── aws_bedrock.py      # CC pause + IAM Access Key
│       ├── gcp_vertex.py       # CC pause + Service Account JSON
│       ├── azure_openai.py     # auto-skip stub
│       └── <24 others>.py      # ~20 lines each, subclass a recipe
└── tests/
    ├── test_parser.py          # 32 providers, tier split, CC/phone flags
    ├── test_state.py           # roundtrip, reset, resume filter
    ├── test_output.py          # .env dedup, keys.json upsert, keys.md re-render
    ├── test_selectors.py       # KEY_PATTERNS match real samples, reject garbage
    ├── test_cli.py             # CliRunner: list/status/run-validation/export
    └── test_dashboard.py       # _apply event handling
```

The 27 thin per-provider handlers exist so per-provider drift (a renamed "Create Key" button) is one tiny patch instead of 27 patches. Three shared recipes (`GoogleSsoCreateKeyRecipe`, `EmailSignupRecipe`, `CloudConsoleRecipe`) absorb most of the variation.

## Tests + CI

```bash
pytest -q              # 104 tests, all offline (no browser, no network)
ruff check harvest/ tests/
```

GitHub Actions (`.github/workflows/ci.yml`) runs both on every push and pull request against Python 3.11.

## Scope and limitations

- Free providers only. The 7 "NOT FREE" providers in `providers.md` are excluded by the parser.
- AWS and GCP require a credit card, so the CLI pauses and you handle it in the browser. Azure OpenAI auto-skips because access approval is manual and takes 1+ business days.
- CAPTCHAs and email links always escalate to a manual takeover prompt. The CLI never tries to solve them or read your mail.
- Sequential by design. Google SSO state is shared across providers, manual prompts require attention, and parallelism invites CAPTCHA. There's no `--concurrency` flag.
- No credential storage. The CLI reuses whatever's in your Chrome session (CDP) or the persistent profile dir. It doesn't store Google passwords or 2FA secrets.
- First-run setup is manual. If you've never logged into Google in this profile, you sign in once via the browser.

## License

MIT. See [`LICENSE`](./LICENSE).
