"""Mistral Codestral provider — SMS verification required."""

from src.providers.base import BaseProvider


class MistralCodestralProvider(BaseProvider):
    name = "Mistral Codestral"
    env_var = "CODESTRAL_API_KEY"
    tier = "sms"
    signup_url = "https://codestral.mistral.ai"
    api_key_url = "https://codestral.mistral.ai"
    free_models = ["Codestral (code-focused model)"]
    credits = "Permanent free tier"
    rate_limits = "30 RPM, 2,000 RPD"
    gotchas = "Code-focused model only. Separate from main Mistral platform."

    async def run(self, page, config):
        print(f"\n  {self.name} ({self.tier})")
        print(f"  📱 Requires phone/SMS verification during signup")
        if self.gotchas:
            print(f"  ⚠️  {self.gotchas}")
        await page.goto(self.signup_url)
        try:
            await page.fill('input[type="email"]', config["email"])
        except Exception:
            pass
        print(f"  ► Complete signup + phone verification, then go to: {self.api_key_url}")
        print(f"  ► Create a new API key and paste it below (or ENTER to skip):")
        key = input("  Key > ").strip()
        return key if key else None
