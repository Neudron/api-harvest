# api-harvest

A command-line tool that signs you up at AI API providers and collects their free API keys. It uses Playwright to drive a browser, reuses your Google login for single sign-on, and asks Google Gemini for help when a page selector stops matching.

## What it does

It reads the catalog in `providers.md` and works through the 32 free providers listed there: 13 in the permanent-free Tier 1 and 19 in the trial-credit Tier 2. The 7 paid-only providers are left out.

For each provider it:

1. Opens the signup URL in a Chrome window.
2. Clicks "Continue with Google" and reuses your existing Google session.
3. Waits for the SMS field to actually appear before asking you for a code, when the provider needs one.
4. Pauses for credit-card entry on AWS and GCP, with a key to skip. Azure OpenAI is skipped automatically because its access approval takes a business day or more.
5. Pauses for an email confirmation link when the provider hides its dashboard behind one. That covers Cohere, Cloudflare, HuggingFace, and NLP Cloud.
6. Creates an API key, reads it as soon as it appears, and checks it against a regex for that provider.
7. Writes the key to `outputs/.env`, `outputs/keys.json`, and `outputs/keys.md` straight away, so a half-finished run keeps what it already got.

Google AI Studio runs first. The Gemini key it returns sets up an in-process assistant that watches the providers that come after it. When a Playwright selector fails, the assistant gets a screenshot plus the nearby HTML and proposes a replacement selector, which the handler tries once. A per-step cap of one rescue and a per-run cap (30 by default) keep the cost bounded.

## Install

```bash
pip install -e .[dev]
playwright install chromium
```

It needs a real terminal for the hotkeys and for the SMS, card, and email prompts. Don't run it under `nohup` or inside non-interactive CI.

## Quick start

```bash
harvest run --profile-dir ./harvest-chrome
```

The first run opens a fresh Chromium window. Sign in to Google once, by hand. The profile is reused on every run after that.

## Browser modes

Pick one. If you pass both or neither, the CLI tells you which.

Attaching to a Chrome you already started keeps you in your real browser, with its cookies and extensions, which tends to draw less bot suspicion:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.config/google-chrome &
harvest run --cdp-port 9222
```

When the run finishes it closes only the pages it opened. Your window and any tabs you already had stay open. If your Chrome has more than one profile context, point at the right one with `--cdp-context-index N`.

The other option is a dedicated Chromium profile that the tool launches itself:

```bash
harvest run --profile-dir ./harvest-chrome
```

The profile lives at `./harvest-chrome`. You sign in to Google on the first run, and it's reused after.

## Commands

```bash
harvest list                                    # show all 32 parsed providers
harvest status                                  # show current state.json and AI budget used

harvest run --profile-dir ./harvest-chrome      # main flow
harvest run --cdp-port 9222                     # attach to an existing Chrome
harvest run --only groq,cerebras                # subset
harvest run --skip aws-bedrock,gcp-vertex       # exclude
harvest run --no-dashboard                      # plain-log mode for CI or recordings
harvest run --validate                          # test-call each key right after capture
harvest run --gemini-key sk-...                 # pre-seed Gemini, skip the AI Studio bootstrap
harvest run --ai-model gemini-2.5-flash         # default model; --ai-budget defaults to 30

harvest reset cohere                            # forget one provider so a re-run retries it
harvest reset                                   # forget everything

harvest export --format md                      # re-render keys.md from keys.json
harvest export --format env                     # re-render .env only
harvest export                                  # all three formats

harvest validate                                # test-call every stored key
harvest validate --only groq,mistral-la-plateforme   # validate a subset
```

If you don't pass `--gemini-key`, it reads `$GEMINI_API_KEY` or `$GOOGLE_GENERATIVE_AI_API_KEY` instead.

## What a run looks like

A Rich live view takes over the terminal:

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

The hotkeys work only in a real terminal. Press `s` to skip the current provider, which marks it as user-skipped and moves on. Press `q` to stop after the current provider finishes, with state written first. Press `p` to pause or resume the live view, which helps when you're reading a prompt. Ctrl+C behaves like `q` but exits at once. Whatever was running gets marked "interrupted (Ctrl+C)" so it isn't retried next time.

## Manual steps the tool hands back to you

Some steps need a human. The tool pauses the live view and prompts on stdin.

| Trigger | What happens |
|---|---|
| SMS verification | It waits up to 60 seconds for an SMS field to appear, then asks you to type the code. If no field ever shows up (say your phone is already verified on the account), it skips the step. |
| Credit card | One prompt before the handler starts. Press `r` to resume after you enter the card, or `s` to skip the provider. AWS Bedrock and GCP Vertex use this. Azure OpenAI skips itself. |
| Email verification | If the page after sign-in says to verify your email, it pauses for you to click the link, then `r` to continue. |
| CAPTCHA | Detected by the iframe URL, then the same pause-for-takeover prompt. |
| Stale Google login | If the sign-in flow lands on `accounts.google.com/signin`, it pauses for you to log in. |

## Outputs

Files are written after every successful key, so a partial run still leaves usable output. The `outputs/` directory is gitignored.

`outputs/.env` holds `KEY=VALUE` lines using the env-var names from `providers.md`, de-duplicated on rewrite. `outputs/keys.json` holds the structured record for each provider: slug, name, tier, status, key, env var, timestamp, dashboard URL, rate limits, and notes. `outputs/keys.md` is a readable table grouped by tier, with only the last four characters of each key shown.

`harvest export` re-renders any of these from `keys.json` without running the browser again.

## Validating keys

A captured key matches a per-provider format regex, but that only proves it
looks right, not that it works. `harvest validate` makes one cheap authenticated
request per provider (almost always `GET {base}/v1/models`) and records the
outcome as `valid`, `invalid`, `unsupported`, or `error` back into `keys.json`
and the `Valid` column of `keys.md`. It exits non-zero if any stored key fails to
authenticate, so it fits in CI.

```bash
harvest validate                 # check every stored key
harvest validate --only groq     # check a subset
```

Pass `harvest run --validate` to probe each key inline, right after it's
captured, so the dashboard shows whether the key actually works before the run
moves on. Providers without an account-agnostic probe (the cloud consoles, and a
few with bespoke auth) report `unsupported` rather than a false failure.

## State, resume, and debugging

Runtime files live under `.harvest/`, which is gitignored.

`state.json` records what's done, failed, or skipped, along with the AI budget used so far. A re-run skips anything marked done or user-skipped and retries anything marked failed. On a selector failure the tool saves a screenshot under `screenshots/` and the full DOM under `html/`. When an unexpected exception comes out of a handler, the full Python traceback goes to `errors/<slug>-<ts>.log`, and that path is included in the failure record so you can find it from `harvest status`. Every Gemini rescue call is appended to `ai_calls.jsonl`: the prompt, the suggestion, the latency, and the run budget used.

## How the Gemini rescue works

1. Google AI Studio runs first with no assistant attached. The `AIzaSy…` key it returns sets up a long-lived assistant.
2. For every provider after that, `Handler.safe_click` and `safe_click_candidates` wrap each click. On a timeout the handler captures a screenshot and the DOM trimmed to about 8 KB around the failed selector.
3. It asks Gemini for the right selector, with structured JSON output validated against `SelectorSuggestion`.
4. It retries the suggested selector once. If Gemini hands back the same selector that just failed, it skips the retry.
5. The budget is enforced: at most one rescue per step, and 30 per run by default. `harvest status` shows the `ai_budget_used` count.

To skip the AI Studio bootstrap and use your own key:

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
│   ├── orchestrator.py         # sequential pipeline, hotkeys, AI bootstrap
│   ├── browser.py              # CDP attach or persistent profile
│   ├── dashboard.py            # Rich live view
│   ├── interactive.py          # async stdin prompts that cooperate with the live view
│   ├── hotkeys.py              # s/q/p listener
│   ├── events.py               # EventBus
│   ├── state.py                # atomic JSON state, resume
│   ├── output.py               # .env / keys.json / keys.md writers
│   ├── selectors.py            # SSO button candidates and per-provider key regexes
│   ├── ai_assistant.py         # google-genai client, budget, audit log
│   └── handlers/
│       ├── base.py             # Handler base class, safe_click, key capture
│       ├── recipes.py          # GoogleSsoCreateKeyRecipe, EmailSignupRecipe, CloudConsoleRecipe
│       ├── google_aistudio.py  # runs first, no AI rescue
│       ├── github_models.py    # PAT with the models scope
│       ├── cloudflare.py       # token with the Workers AI scope
│       ├── aws_bedrock.py      # card pause plus IAM access key
│       ├── gcp_vertex.py       # card pause plus service-account JSON
│       ├── azure_openai.py     # skip stub
│       └── <24 others>.py      # about 20 lines each, subclassing a recipe
└── tests/
    ├── test_parser.py          # 32 providers, tier split, cc/phone flags
    ├── test_state.py           # roundtrip, reset, resume filter
    ├── test_output.py          # .env dedup, keys.json upsert, keys.md re-render
    ├── test_selectors.py       # key regexes match real samples, reject junk
    ├── test_cli.py             # CliRunner: list, status, run validation, export
    └── test_dashboard.py       # event handling
```

The per-provider handler files are short on purpose. When a provider renames its "Create Key" button, the fix is one small file instead of a change spread across the recipe. The three shared recipes (`GoogleSsoCreateKeyRecipe`, `EmailSignupRecipe`, `CloudConsoleRecipe`) hold the logic the providers have in common.

## Tests and CI

```bash
pytest -q              # 104 tests, all offline, no browser and no network
ruff check harvest/ tests/
```

GitHub Actions runs both on every push and pull request against Python 3.11. See `.github/workflows/ci.yml`.

## Scope and limitations

It handles free providers only. The 7 paid-only providers in `providers.md` are dropped by the parser. AWS and GCP need a credit card, so the tool pauses and you enter it in the browser. Azure OpenAI skips itself because its access approval is manual and takes a business day or more. CAPTCHAs and email links always hand control back to you; the tool never tries to solve a CAPTCHA or read your mail.

The pipeline is sequential by design. Google SSO state is shared across providers, the manual prompts need your attention, and running in parallel invites more CAPTCHAs, so there's no concurrency flag.

It stores no credentials. It reuses whatever is in your Chrome session over CDP, or in the persistent profile directory. It doesn't keep your Google password or two-factor secrets. If you've never logged into Google in that profile, you sign in once in the browser.

## License

MIT. See [`LICENSE`](./LICENSE).
