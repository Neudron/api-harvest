# AI API Providers: Free Access Guide (2025-05)

> Source: OpenCode/models.dev registry + community free-llm-api-resources
> Total providers checked: 39
> Date verified: 2026-05-26

---

## TIER 1 — Permanent Free Tiers (No Expiration, No Credit Card)

These providers offer genuinely free API access that never expires and does not require a credit card.

### 1. Google Gemini (AI Studio)

- **Free tier type:** Permanent, unlimited (rate-limited)
- **Rate limits:** Flash models: 5-15 RPM, 250K tok/min, 20-500 RPD | Gemma models: 30 RPM, 15K tok/min, 14,400 RPD
- **Free models:** Gemini 3 Flash, Gemini 3.1 Flash-Lite, Gemini 2.5 Flash, Gemini 2.5 Flash-Lite, Gemini 3.1 Flash TTS, Gemini Robotics-ER, Gemma 3 (1B/4B/12B/27B)
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** Yes (outside UK/CH/EEA/EU)
- **Signup URL:** https://aistudio.google.com
- **API Key URL:** https://aistudio.google.com/apikey
- **Gotchas:** The permanent-free tier covers Flash / Flash-Lite (and Gemma) models; Pro models are billing-gated. Rate limits get slashed periodically. Not available in EU countries. Data may be used for model training depending on region.

### 2. Groq

- **Free tier type:** Permanent free tier
- **Rate limits:** 30 RPM, 6K-70K tok/min, 1,000-14,400 RPD (varies by model)
- **Free models:** Llama 3.1 8B (14,400 RPD), Llama 3.3 70B (1,000 RPD), Llama 4 Scout (1,000 RPD), GPT-OSS 120B (1,000 RPD), GPT-OSS 20B (1,000 RPD), Qwen3 32B (1,000 RPD), Whisper Large v3/v3 Turbo (2,000 RPD), Compound/Compound-Mini (250 RPD), Gemma, Allam 2 7B
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://console.groq.com
- **API Key URL:** https://console.groq.com/keys
- **Gotchas:** Rate limits vary per model. Developer tier (free, requires CC) gives 10x higher limits. Partially acquired by NVIDIA (Dec 2025). No batch API on free tier.

### 3. Cerebras

- **Free tier type:** Permanent free tier
- **Rate limits:** 30 RPM, 60K tok/min, 14,400 RPD, 1M tok/day (GPT-OSS 120B: 1M tok/day)
- **Free models:** GPT-OSS 120B, Llama 3.1 8B, DeepSeek R1, Qwen3, GLM 4.7
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://cloud.cerebras.ai
- **API Key URL:** https://cloud.cerebras.ai
- **Gotchas:** Context length capped at 8,192 tokens on free tier (128K+ on paid). Ultra-fast inference — 20x faster than OpenAI/Anthropic. Some models being deprecated (Llama 3.1 8B, Qwen 3 235B — May 27, 2026). Developer tier ($10 min deposit) gives 10x limits + priority.

### 4. Mistral (La Plateforme)

- **Free tier type:** Permanent free tier (Experiment plan)
- **Rate limits:** 1 RPS per model, 500K tok/min, 1B tok/month
- **Free models:** ALL Mistral models — Mistral Large, Mistral Medium, Mistral Small, Codestral, Ministral, Nemo, Pixtral
- **Requires credit card:** No
- **Requires phone verification:** Yes
- **Data used for training:** Yes (required to opt-in for Experiment plan)
- **Signup URL:** https://console.mistral.ai
- **API Key URL:** https://console.mistral.ai/api-keys
- **Gotchas:** 1 RPS is very restrictive — fine for testing only, not for production. Must opt-in to data training. Phone verification required. Experiment plan may change.

### 5. Mistral Codestral (Separate Endpoint)

- **Free tier type:** Permanent free tier
- **Rate limits:** 30 RPM, 2,000 RPD
- **Free models:** Codestral (code-focused model)
- **Requires credit card:** No
- **Requires phone verification:** Yes
- **Data used for training:** No
- **Signup URL:** https://codestral.mistral.ai
- **API Key URL:** https://codestral.mistral.ai
- **Gotchas:** Code-focused model only. The free beta is over — Codestral is now a standard priced model on La Plateforme (legacy accounts may retain free access via the dedicated codestral.mistral.ai endpoint). Separate from the main Mistral platform.

### 6. OpenRouter

- **Free tier type:** Permanent free tier (free models only)
- **Rate limits:** 20 RPM, 50 RPD unfunded | 1,000 RPD with $10 lifetime topup
- **Free models (29+ models with ':free' suffix):** DeepSeek V4 Flash, GPT-OSS 120B, GPT-OSS 20B, NVIDIA Nemotron 3 Nano/Super, Llama 3.3 70B Instruct, Llama 3.2 3B Instruct, Qwen3 Coder, Qwen3 Next 80B, Gemma 4 26B/31B, GLM 4.5 Air, MiniMax M2.5, Dolphin Mistral 24B, Hermes 3 Llama 3.1 405B, Arcee Trinity Large Thinking, Liquid LFM 2.5, Baidu Cobuddy, Poolside Laguna
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** Varies by upstream model provider
- **Signup URL:** https://openrouter.ai
- **API Key URL:** https://openrouter.ai/settings/keys
- **Gotchas:** Only ':free' suffix models are free. 50 RPD unfunded is very restrictive. $10 topup bumps to 1,000 RPD for free models. Free model availability rotates as providers change offerings. Some free models may have quality or availability issues.

### 7. Cohere

- **Free tier type:** Permanent free tier (Trial keys)
- **Rate limits:** 20 RPM, 1,000 requests/month (shared across ALL models)
- **Free models:** Command A, Command A Reasoning, Command A Vision, Command A Translate, Command R+, Command R, Command R7B, Aya Expanse 32B, Aya Vision 32B, Rerank, Embed
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://dashboard.cohere.com/welcome/register
- **API Key URL:** https://dashboard.cohere.com/api-keys
- **Gotchas:** Only 1,000 API calls/month TOTAL across all models — very limited. Trial keys cannot be used for production or commercial purposes. Some users report responses getting cut off mid-sentence on trial keys.

### 8. Vercel AI Gateway

- **Free tier type:** Permanent free tier ($5/month recurring credits)
- **Rate limits:** $5/month in credits (resets monthly)
- **Free models:** Multi-provider access — OpenAI, Anthropic, Google, Meta, and more with zero markup on token prices. One API key for hundreds of models.
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://vercel.com/signup
- **API Key URL:** https://vercel.com/dashboard/~/ai-gateway
- **Gotchas:** $5/month covers light testing only. Unlocking the credit may require card / identity verification, and once you add a payment method you become a paid customer and stop receiving the free credit. Zero Data Retention (ZDR) costs extra. If you exceed $5, you need to enable paid tier.

### 9. NVIDIA NIM

- **Free tier type:** Permanent free tier
- **Rate limits:** 40 RPM
- **Free models:** Various open models (Llama, Mistral, etc.) listed at https://build.nvidia.com/models
- **Requires credit card:** No
- **Requires phone verification:** Yes
- **Data used for training:** No
- **Signup URL:** https://build.nvidia.com/explore/discover
- **API Key URL:** https://build.nvidia.com/settings/api-keys
- **Gotchas:** Models tend to have limited context windows. Phone verification required. Good for quick prototyping.

### 10. GitHub Models

- **Free tier type:** Permanent free tier (separate per-account daily quotas)
- **Rate limits:** Depends on Copilot tier — Free plan: very restrictive token limits | Pro: 300 premium requests/month
- **Free models:** GPT-4o, GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, GPT-5, GPT-5-mini, GPT-5-nano, o1, o1-mini, o3, o3-mini, o4-mini, Llama 3.3 70B, Llama 4 Maverick/Scout, DeepSeek-R1/V3, Mistral Medium 3, Mistral Small 3.1, Cohere Command A/R/R+, Phi-4, Codestral, Grok 3/3 Mini, AI21 Jamba 1.5, and more
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://github.com/marketplace/models
- **API Key URL:** https://github.com/settings/personal-access-tokens
- **Gotchas:** Extremely restrictive input/output token limits. Uses GitHub PAT, not traditional API key. Good for prototyping only. As of June 1 2026 GitHub Copilot moved to usage-based AI Credits billing; the Models API now has its own per-account daily quotas, managed separately from any Copilot plan.

### 11. Cloudflare Workers AI

- **Free tier type:** Permanent free tier
- **Rate limits:** 10,000 neurons/day
- **Free models:** Llama 3.3 70B (FP8), Llama 4 Scout, Gemma 3 12B, Qwen QwQ 32B, Qwen 2.5 Coder 32B, GPT-OSS 120B, GPT-OSS 20B, Kimi K2.5, Kimi K2.6, Mistral Small 3.1 24B, DeepSeek R1 Distill Qwen 32B, Phi-2, Gemma 2B/7B, Llama 3/3.1/3.2 variants, IBM Granite 4.0, GLM 4.7 Flash, Qwen3 30B, Nemotron 3 120B, and more
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://dash.cloudflare.com/sign-up
- **API Key URL:** https://dash.cloudflare.com/profile/api-tokens
- **Gotchas:** Neuron-based pricing is unusual — different models consume different neuron amounts. 10,000 neurons/day may not go far with larger models. Good for lightweight inference tasks.

### 12. HuggingFace Inference Providers

- **Free tier type:** Permanent free tier
- **Rate limits:** $0.10/month in credits
- **Free models:** Various open models under 10GB. Some popular models supported even if they exceed 10GB.
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://huggingface.co/join
- **API Key URL:** https://huggingface.co/settings/tokens
- **Gotchas:** $0.10/month is very modest — covers only a few requests. Models must be under 10GB for serverless inference. Good for quick testing only.

### 13. OpenCode Zen

- **Free tier type:** Permanent free tier
- **Rate limits:** Not documented
- **Free models:** Big Pickle Stealth, MiniMax M2.5 Free, Arcee Large Preview Free
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** Yes (free models may use data for improvement)
- **Signup URL:** https://opencode.ai/docs/zen/
- **API Key URL:** https://opencode.ai/zen
- **Gotchas:** AI gateway with curated free models. Very limited model selection. Data may be used for model improvement. Part of the OpenCode project.

---

## TIER 2 — Trial Credits (Time-Limited or One-Time)

These providers offer free credits that expire or are one-time only.

### 1. xAI / Grok

- **Trial credits:** $25 one-time free credits on signup
- **Duration:** One-time (until used up)
- **Free models:** Grok 3, Grok 3 Mini, Grok 2
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://console.x.ai/
- **API Key URL:** https://console.x.ai/
- **Gotchas:** The recurring credits came from a data-sharing program that has since ended; what remains is a one-time $25 signup credit. No credit card needed — just email signup.

### 2. Alibaba/Qwen (DashScope)

- **Trial credits:** ~1 million tokens per model (input + output separately)
- **Duration:** 90 days after Model Studio activation
- **Free models:** qwen-max, qwen-plus, qwen-turbo, qwen-vl, qwen3-coder, qwen3-next, and more
- **Requires credit card:** No
- **Requires phone verification:** No (Alibaba Cloud account needed)
- **Data used for training:** No
- **Signup URL:** https://www.alibabacloud.com/en/product/model-studio
- **API Key URL:** https://dashscope.console.aliyun.com/apiKey
- **Gotchas:** Free tokens expire 90 days after activation — then pay-per-use kicks in. Alibaba Cloud account required but no CC for international accounts. Rate limits on free tier. Some models like qwen-flash have permanent tiered pricing with a free bracket.

### 3. Anthropic

- **Trial credits:** ~$5 one-time credits
- **Duration:** No expiration (until used up)
- **Free models:** Claude 4 Sonnet, Claude 4 Opus, Claude Haiku 4.5, Claude 3.5 Sonnet, Claude 3.5 Haiku
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://console.anthropic.com/
- **API Key URL:** https://console.anthropic.com/settings/keys
- **Gotchas:** Some users don't receive the credits automatically — may need to contact support. $5 is modest but enough for light testing. No credit card needed. Best way to try Claude models for free.

### 4. SambaNova Cloud

- **Trial credits:** $5 in free API credits
- **Duration:** 3 months
- **Free models:** Llama 3.3 70B, Llama 4 Maverick 17B, DeepSeek V3.1, DeepSeek V3.2, Gemma 3 12B, GPT-OSS 120B, MiniMax M2.7
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://cloud.sambanova.ai/
- **API Key URL:** https://cloud.sambanova.ai/apis
- **Gotchas:** Free tier transitioned to developer tier. Additional $5 if signed up for newsletter. Ultra-fast wafer-scale chip inference. Can create up to 25 API keys.

### 5. Amazon Bedrock

- **Trial credits:** $200 AWS credits (new accounts created after July 15, 2025)
- **Duration:** 6 months
- **Free models:** Claude, Llama, Mistral, Titan, Stable Diffusion, and more (must enable per model)
- **Requires credit card:** Yes
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://aws.amazon.com/free/
- **API Key URL:** https://us-east-1.console.aws.amazon.com/iam/home#/security_credentials
- **Gotchas:** Requires credit card. Credits apply across ALL AWS services, not just Bedrock — easy to burn through on other services. Must enable models separately in the console. Free trial auto-upgrades to paid after credits expire. Only for new AWS accounts.

### 6. Google Vertex AI

- **Trial credits:** $300 GCP credits
- **Duration:** 90 days
- **Free models:** Gemini, Claude (via Vertex), Llama, Mistral, and more
- **Requires credit card:** Yes
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://cloud.google.com/free/
- **API Key URL:** https://console.cloud.google.com/apis/credentials
- **Gotchas:** CRITICAL: Must upgrade to paid billing account to access Vertex AI — free trial billing account alone is blocked from Vertex. Credit card WILL be charged if you exceed $300. Credits expire after 90 days. Complex setup (enable APIs, create endpoints, configure quotas). Use Google AI Studio instead for simpler free access.

### 7. Azure OpenAI

- **Trial credits:** $200 Azure credits
- **Duration:** 30 days
- **Free models:** GPT-4o, GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, o3, o4-mini, and more OpenAI models
- **Requires credit card:** Yes
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://azure.microsoft.com/en-us/free/
- **API Key URL:** https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/AppliedAIHub/~/OpenAI
- **Gotchas:** Microsoft removed the Limited Access registration form for standard Azure OpenAI — all Azure customers are now eligible by default (no manual approval). Still needs an Azure subscription with a credit card; 30-day credit expiry. Some advanced / abuse-monitoring features remain gated.

### 8. Perplexity

- **Trial credits:** $25-50 (inconsistent across accounts)
- **Duration:** Until used
- **Free models:** Sonar, Sonar Pro, Sonar Deep Research
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://www.perplexity.ai/settings/api
- **API Key URL:** https://www.perplexity.ai/settings/api
- **Gotchas:** Credits are inconsistent — some users get $0, some $25, some $50. The Pro ($20/mo) $5/month API credit has reportedly been withdrawn for newer subscribers — treat it as unreliable. Free Perplexity accounts cannot access the API at all. Credits do not roll over.

### 9. Fireworks AI

- **Trial credits:** $1
- **Duration:** Until used
- **Free models:** Various open models (Llama, Qwen, Mixtral, etc.)
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://fireworks.ai/
- **API Key URL:** https://fireworks.ai/api-keys
- **Gotchas:** Only $1 in credits — very limited for testing. Competitive pricing after trial. No CC needed for trial.

### 10. Baseten

- **Trial credits:** $30
- **Duration:** Until used
- **Free models:** Any supported model — pay by compute time
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://app.baseten.co/
- **API Key URL:** https://app.baseten.co/settings/api_keys
- **Gotchas:** $30 is generous. Pay by compute time, not tokens. Good for custom model deployments. Model library at https://www.baseten.co/library/

### 11. Nebius

- **Trial credits:** $1
- **Duration:** Until used
- **Free models:** Various open models
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://tokenfactory.nebius.com/
- **API Key URL:** https://tokenfactory.nebius.com/project/api-keys
- **Gotchas:** Only $1. Competitive inference pricing. Good for EU-based users.

### 12. NLP Cloud

- **Trial credits:** $15
- **Duration:** Until used
- **Requires phone verification:** Yes
- **Free models:** Various open models
- **Requires credit card:** No
- **Data used for training:** No
- **Signup URL:** https://nlpcloud.com/home
- **API Key URL:** https://nlpcloud.com/home
- **Gotchas:** Phone verification required. $15 is decent for testing. Good selection of open-source models.

### 13. AI21

- **Trial credits:** $10
- **Duration:** 3 months
- **Free models:** Jamba 1.5 Large, Jamba 1.5 Mini, Jamba Instruct
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://studio.ai21.com/
- **API Key URL:** https://studio.ai21.com/
- **Gotchas:** Only Jamba family models. $10 over 3 months is limited. Niche provider.

### 14. Upstage

- **Trial credits:** $10
- **Duration:** 3 months
- **Free models:** Solar Pro, Solar Mini
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://console.upstage.ai/
- **API Key URL:** https://console.upstage.ai/api-keys
- **Gotchas:** Only Solar models. Korean-focused provider. $10 over 3 months.

### 15. Modal

- **Trial credits:** $30/month recurring credits (Starter plan, all accounts)
- **Duration:** Monthly (RECURRING!)
- **Free models:** Any supported model — pay by compute time
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://modal.com/
- **API Key URL:** https://modal.com/settings/tokens
- **Gotchas:** The Starter (free) plan now grants $30/month in compute credits to all accounts by default. Serverless compute platform — you deploy and run models, pay by compute time. Good for custom inference.

### 16. Hyperbolic

- **Trial credits:** $1
- **Duration:** Until used
- **Free models:** DeepSeek V3 0324, DeepSeek R1 0528, Llama 3.3 70B Instruct, Qwen3 Coder 480B
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://app.hyperbolic.ai/
- **API Key URL:** https://app.hyperbolic.ai/settings/api-keys
- **Gotchas:** Only $1. Claims to be the cheapest GPU marketplace. Very limited trial.

### 17. Inference.net

- **Trial credits:** $1 ($25 extra if you respond to email survey)
- **Duration:** Until used
- **Free models:** Various open models
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://inference.net
- **API Key URL:** https://inference.net
- **Gotchas:** The email survey bonus ($25) makes this worthwhile. Without survey, only $1.

### 18. Scaleway Generative APIs

- **Trial credits:** 1,000,000 free tokens
- **Duration:** Until used
- **Free models:** Llama 3.3 70B, Gemma 3 27B, Qwen3 variants (235B, Coder, Embed, 3.5 397B, 3.6 35B), Mistral Small 3.2, GPT-OSS 120B, DeepSeek R1, Kimi K2.5/K2.6, Whisper Large v3, Devstral, Pixtral 12B, Holo2 30B, Voxtral Small, BGE-Multilingual-Gemma2
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://console.scaleway.com/generative-api/models
- **API Key URL:** https://console.scaleway.com/iam/api-keys
- **Gotchas:** 1M tokens is generous. EU-based provider (Paris). Good model selection including latest Qwen variants.

### 19. Novita

- **Trial credits:** $0.50
- **Duration:** 1 year
- **Free models:** Various open models
- **Requires credit card:** No
- **Requires phone verification:** No
- **Data used for training:** No
- **Signup URL:** https://novita.ai/
- **API Key URL:** https://novita.ai/settings/key-management
- **Gotchas:** Only $0.50 but lasts a year. Very limited. Image/video generation focus.

---

## NOT FREE — Skip If You Need Free Access

### OpenAI

- **Minimum cost:** $5 minimum purchase required
- **Requires credit card:** Yes
- **Why not free:** Discontinued free credits in early 2025. Must add payment method and buy $5 minimum to start. The old $18 free credits program is completely dead.
- **Signup URL:** https://platform.openai.com/signup

### Together AI

- **Minimum cost:** $5 minimum credit purchase
- **Requires credit card:** Yes
- **Why not free:** Official docs state: "Together AI does not currently offer free trials." Must buy $5 minimum. Prepaid cards and virtual cards often declined.
- **Signup URL:** https://api.together.ai

### DeepInfra

- **Minimum cost:** Pay-as-you-go only
- **Requires credit card:** Yes
- **Why not free:** No free tier or trial. Must add payment to use API. DeepStart startup program (1B free tokens) requires application approval.
- **Signup URL:** https://deepinfra.com/login

### Venice AI

- **Minimum cost:** $18/month subscription
- **Requires credit card:** No (but subscription required)
- **Why not free:** Restructured (April 2026) into four tiers (Free, Pro, Pro Plus, Max). The $18/mo Pro tier now includes API access plus a one-time $10 API credit; the Free tier is web-chat-oriented with very limited / no standalone API. Still effectively paid for sustained API use. The "free" Venice Uncensored model on OpenRouter is via OpenRouter's free tier, not Venice's own API.
- **Signup URL:** https://venice.ai

### GitLab AI (Duo)

- **Minimum cost:** $29/user/month (Premium tier) for full API access
- **Requires credit card:** No
- **Why not free:** Not a standalone API provider. Free tier has very limited AI access (primarily Duo Chat in IDE). The gitlab-ai-provider npm is a community package, not an official standalone API. Limited to GitLab-internal workflows.
- **Signup URL:** https://gitlab.com/users/sign_up

### GitHub Copilot

- **Minimum cost:** Free plan exists but NO REST API access
- **Requires credit card:** No
- **Why not free:** Free plan includes IDE access only. GitHub explicitly states Copilot does not provide programmatic API access. The @ai-sdk/github-copilot provider works by extracting the Copilot token from the IDE session, which is fragile and may violate ToS. Not viable for server-side applications.
- **Signup URL:** https://github.com/features/copilot

### Google Vertex AI (Anthropic Claude)

- **Minimum cost:** $300 GCP credits (90 days) but requires CC + upgrade
- **Requires credit card:** Yes
- **Why not free:** Must upgrade to paid billing account to access Vertex AI — the free trial billing account alone is blocked from Vertex AI. Credit card WILL be charged if you exceed the $300 credit. Complex setup. Use Google AI Studio or Anthropic directly instead.
- **Signup URL:** https://cloud.google.com/free/

---

## Quick Start: Get 5 Free API Keys in Under 10 Minutes

1. **Google Gemini** → https://aistudio.google.com/apikey → Sign in with Google → "Create API Key" → Done
2. **Groq** → https://console.groq.com → Sign up → https://console.groq.com/keys → "Create API Key" → Done
3. **Cerebras** → https://cloud.cerebras.ai → Sign up → Dashboard → "Create API Key" → Done
4. **xAI/Grok** → https://console.x.ai/ → Sign up → "Create API Key" → Done ($25 one-time signup credit)
5. **OpenRouter** → https://openrouter.ai → Sign up → https://openrouter.ai/settings/keys → "Create Key" → Done

---

## Free Model Availability Matrix

| Model Family | Google | Groq | Cerebras | Mistral | OpenRouter | Cohere | Vercel GW | NVIDIA | GitHub | Cloudflare |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| GPT-OSS 120B | - | YES | YES | - | YES | - | via | - | - | YES |
| Llama 3.3 70B | - | YES | - | - | YES | - | via | YES | YES | YES |
| Llama 4 Scout | - | YES | - | - | - | - | via | - | YES | YES |
| DeepSeek R1/V3 | - | - | YES | - | V4 Flash | - | via | YES | YES | R1 Distill |
| Qwen3 Coder | - | 32B | YES | Codestral | YES | - | via | - | - | QwQ 32B |
| Gemma 3/4 | YES | - | - | - | Gemma 4 | - | via | - | - | 12B |
| Mistral Small | - | - | - | YES | - | - | via | YES | YES | 3.1 24B |
| GPT-4o/4.1 | - | - | - | - | - | - | via | - | YES | - |
| Claude | - | - | - | - | - | - | via | - | - | - |
| Gemini 3 Flash | YES | - | - | - | - | - | via | - | - | - |
| Grok 3 | - | - | - | - | - | - | - | - | YES | - |
| Command A | - | - | - | - | - | YES | via | - | - | - |
| Phi-4 | - | - | - | - | - | - | via | - | YES | - |
| Kimi K2.5/K2.6 | - | - | - | - | - | - | - | - | - | YES |
| Whisper | - | YES | - | - | - | - | - | - | - | YES |

---

## Environment Variable Quick Reference

```
GOOGLE_GENERATIVE_AI_API_KEY=           # Google AI Studio
GROQ_API_KEY=                           # Groq
CEREBRAS_API_KEY=                       # Cerebras
MISTRAL_API_KEY=                        # Mistral La Plateforme
OPENROUTER_API_KEY=                     # OpenRouter
COHERE_API_KEY=                         # Cohere (Trial)
VERCEL_AI_GATEWAY_KEY=                  # Vercel AI Gateway
NVIDIA_API_KEY=                         # NVIDIA NIM
GITHUB_TOKEN=                           # GitHub Models (PAT)
CLOUDFLARE_API_TOKEN=                   # Cloudflare Workers AI
HF_TOKEN=                               # HuggingFace
XAI_API_KEY=                            # xAI / Grok
DASHSCOPE_API_KEY=                      # Alibaba/Qwen
ANTHROPIC_API_KEY=                      # Anthropic
SAMBANOVA_API_KEY=                      # SambaNova
CODESTRAL_API_KEY=                      # Mistral Codestral
OPENCODE_API_KEY=                       # OpenCode Zen
```
