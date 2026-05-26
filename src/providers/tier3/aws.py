"""Amazon Bedrock (AWS) provider — credit card required."""

from src.providers.base import BaseProvider


class AWSProvider(BaseProvider):
    name = "Amazon Bedrock (AWS)"
    env_var = "AWS_ACCESS_KEY_ID"
    tier = "cc"
    signup_url = "https://aws.amazon.com/free/"
    api_key_url = "https://us-east-1.console.aws.amazon.com/iam/home#/security_credentials"
    free_models = [
        "Claude",
        "Llama",
        "Mistral",
        "Titan",
        "Stable Diffusion",
        "and more (must enable each)",
    ]
    credits = "$200 AWS credits / 6 months (new accounts after July 15, 2025)"
    rate_limits = "Standard AWS limits per model"
    gotchas = "Credits apply across ALL AWS services — easy to burn on other things. Must enable each model separately. CC required."

    async def run(self, page, config):
        print(f"\n  {self.name} ({self.tier})")
        print(f"  💳 Requires credit card for AWS signup")
        if self.gotchas:
            print(f"  ⚠️  {self.gotchas}")
        print(f"""
  Steps:
  1. Sign up at: {self.signup_url}
  2. Go to IAM: {self.api_key_url}
  3. Click 'Create access key' → select 'CLI' use case
  4. Enable Bedrock models at: https://us-east-1.console.aws.amazon.com/bedrock/home#/modelaccess
  5. Copy BOTH the Access Key ID and Secret Access Key
  """)
        access_key = input("  AWS_ACCESS_KEY_ID > ").strip()
        secret_key = input("  AWS_SECRET_ACCESS_KEY > ").strip()
        if access_key:
            if secret_key:
                print(f"  ⚠️  Save your secret key separately: {secret_key}")
            return access_key
        return None
