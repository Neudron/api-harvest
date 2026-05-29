"""Google Vertex AI provider — credit card required."""

from src.providers.base import BaseProvider


class VertexProvider(BaseProvider):
    name = "Google Vertex AI"
    env_var = "VERTEX_API_KEY"
    tier = "cc"
    signup_url = "https://cloud.google.com/free/"
    api_key_url = "https://console.cloud.google.com/apis/credentials"
    free_models = [
        "Gemini",
        "Claude (via Vertex)",
        "Llama",
        "Mistral",
        "and more",
    ]
    credits = "$300 GCP credits / 90 days"
    rate_limits = "Standard GCP limits"
    gotchas = "CRITICAL: Must upgrade to paid billing account to access Vertex AI. Free trial alone is blocked from Vertex. CC WILL be charged if you exceed $300."

    async def run(self, page, config):
        print(f"\n  {self.name} ({self.tier})")
        print(f"  💳 Requires credit card + billing upgrade")
        if self.gotchas:
            print(f"  ⚠️  {self.gotchas}")
        print(f"""
  Steps:
  1. Sign up at: {self.signup_url}
  2. Upgrade to paid billing account (required for Vertex)
  3. Enable Vertex AI API at: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
  4. Create API key at: {self.api_key_url}
  5. Alternatively, use Application Default Credentials (gcloud auth)
  """)
        key = input("  VERTEX_API_KEY > ").strip()
        return key if key else None
