"""Mistral La Plateforme provider — SMS verification required."""

from src.providers.base import BaseProvider


class MistralProvider(BaseProvider):
    name = "Mistral La Plateforme"
    env_var = "MISTRAL_API_KEY"
    tier = "sms"
    signup_url = "https://console.mistral.ai"
    api_key_url = "https://console.mistral.ai"
    free_models = [
        "Mistral Large",
        "Mistral Medium",
        "Mistral Small",
        "Codestral",
        "Ministral",
        "Nemo",
        "Pixtral",
    ]
    credits = "Permanent free tier (Experiment plan)"
    rate_limits = "1 RPS per model, 500K tok/min, 1B tok/month"
    gotchas = "1 RPS is very restrictive — fine for testing only. Must opt-in to data training."

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
