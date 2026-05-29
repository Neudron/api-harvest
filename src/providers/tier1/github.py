"""GitHub Models provider — email-only free tier (uses PAT, not API key)."""

from typing import Optional

from src.providers.base import BaseProvider


class GitHubModelsProvider(BaseProvider):
    name = "GitHub Models"
    env_var = "GITHUB_TOKEN"
    tier = "email"
    signup_url = "https://github.com/marketplace/models"
    api_key_url = "https://github.com/settings/tokens"
    free_models = [
        "GPT-4o",
        "GPT-4.1",
        "GPT-5-mini",
        "o4-mini",
        "Llama 3.3 70B",
        "Llama 4 Maverick/Scout",
        "DeepSeek-R1/V3",
        "Grok 3",
        "Phi-4",
        "Codestral",
        "and more",
    ]
    credits = "Permanent free tier via Copilot Free plan"
    rate_limits = "Very restrictive input/output token limits on free plan"
    gotchas = "Uses GitHub PAT with 'models' scope — not a traditional API key. Good for prototyping only."

    async def run(self, page, config: dict) -> Optional[str]:
        await page.goto(self.api_key_url)
        print(f"\n  {self.name} ({self.tier})")
        print(f"  ⚠  Uses a Personal Access Token (PAT), not a standard API key")
        print(f"  ► Go to: {self.api_key_url}")
        print(f"  ► Click 'Generate new token (classic)' → select 'models' scope → generate")
        print(f"  ► Paste the token below (or press ENTER to skip):")
        key = input("  Token > ").strip()
        return key if key else None
