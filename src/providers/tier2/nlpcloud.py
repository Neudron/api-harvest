"""NLP Cloud provider — SMS verification required."""

from src.providers.base import BaseProvider


class NlpcloudProvider(BaseProvider):
    name = "NLP Cloud"
    env_var = "NLPCLOUD_API_KEY"
    tier = "sms"
    signup_url = "https://nlpcloud.com/home"
    api_key_url = "https://nlpcloud.com/"
    free_models = ["Various open-source models"]
    credits = "$15 trial credits"
    rate_limits = "Standard limits"
    gotchas = "$15 is decent for testing. Good selection of open-source models."

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
