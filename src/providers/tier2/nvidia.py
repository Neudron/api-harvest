"""NVIDIA NIM provider — SMS verification required."""

from src.providers.base import BaseProvider


class NvidiaProvider(BaseProvider):
    name = "NVIDIA NIM"
    env_var = "NVIDIA_API_KEY"
    tier = "sms"
    signup_url = "https://build.nvidia.com/explore/discover"
    api_key_url = "https://build.nvidia.com"
    free_models = [
        "Llama variants",
        "Mistral variants — see build.nvidia.com/models",
    ]
    credits = "Permanent free tier"
    rate_limits = "40 RPM"
    gotchas = "Limited context windows. Good for quick prototyping."

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
