"""Azure OpenAI provider — credit card required."""

from src.providers.base import BaseProvider


class AzureProvider(BaseProvider):
    name = "Azure OpenAI"
    env_var = "AZURE_OPENAI_API_KEY"
    tier = "cc"
    signup_url = "https://azure.microsoft.com/en-us/free/"
    api_key_url = "https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/AppliedAIHub/~/OpenAI"
    free_models = [
        "GPT-4o",
        "GPT-4.1",
        "GPT-4.1-mini",
        "o3",
        "o4-mini",
        "and more OpenAI models",
    ]
    credits = "$200 Azure credits / 30 days"
    rate_limits = "Standard Azure OpenAI limits"
    gotchas = "MAJOR BLOCKER: Requires separate manual access approval for Azure OpenAI. Free trial subscriptions often rejected. Approval takes 1+ business days."

    async def run(self, page, config):
        print(f"\n  {self.name} ({self.tier})")
        print(f"  💳 Requires credit card")
        if self.gotchas:
            print(f"  ⚠️  {self.gotchas}")
        print(f"""
  Steps:
  1. Sign up at: {self.signup_url}
  2. Apply for Azure OpenAI access (may take 1+ business days)
  3. Create Azure OpenAI resource at: {self.api_key_url}
  4. Go to 'Keys and Endpoint' → copy Key 1
  """)
        key = input("  AZURE_OPENAI_API_KEY > ").strip()
        return key if key else None
