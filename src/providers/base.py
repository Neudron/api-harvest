"""Base provider class for AI API key harvesting."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderResult:
    """Result of running a provider's signup flow."""
    provider: "BaseProvider"
    key: Optional[str] = None       # None if skipped or failed
    skipped: bool = False            # True if tier not selected
    error: Optional[str] = None


class BaseProvider(ABC):
    """Abstract base class for all AI API key provider modules.

    Subclasses must define class-level attributes and can override the run() method
    to provide custom signup flow logic.
    """

    # Class-level attributes — subclasses override these
    name: str                   # "Groq", "Anthropic", etc.
    env_var: str                # "GROQ_API_KEY", "ANTHROPIC_API_KEY", etc.
    tier: str                   # "email" | "sms" | "cc"
    signup_url: str             # URL to open for signup
    api_key_url: str            # URL where the key is created/found
    free_models: list           # ["Llama 3.1 8B (14,400 RPD)", ...]
    credits: str                # "Permanent free tier" or "$25/month recurring"
    rate_limits: str            # "30 RPM, 14,400 RPD"
    gotchas: str                # Warning text shown to user before signup

    async def run(self, page, config: dict) -> Optional[str]:
        """Default signup flow.

        Args:
            page: Playwright Page object for browser automation
            config: Dict with keys "email" (str) and "name" (str)

        Returns:
            API key string, or None if skipped/empty
        """
        # 1. Open the signup page
        await page.goto(self.signup_url)

        # 2. Try to pre-fill the email field
        try:
            await page.fill('input[type="email"]', config["email"])
        except Exception:
            # Field not found or other error — continue anyway
            pass

        # 3. Print instructions to terminal
        print(f"\n  {self.name} ({self.tier})")
        if self.gotchas:
            print(f"  ⚠️  {self.gotchas}")
        print(f"  ► Now navigate to: {self.api_key_url}")
        print(f"  ► Create a new API key, then paste it below (or press ENTER to skip):")

        # 4. Read key from user input
        key = input("  Key > ").strip()

        # 5. Return the key or None if empty
        return key if key else None
