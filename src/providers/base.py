"""Base provider class for AI API key harvesting."""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class ProviderResult:
    """Result of running a provider's signup flow."""
    provider: "BaseProvider"
    key: Optional[str] = None
    skipped: bool = False
    error: Optional[str] = None


class BaseProvider:
    """Base class for all AI API key provider modules.

    Subclasses override class-level attributes and may override run() for
    custom signup flows.
    """

    name: str
    env_var: str
    tier: str           # "email" | "sms" | "cc"
    signup_url: str
    api_key_url: str
    free_models: list
    credits: str
    rate_limits: str
    gotchas: str
    google_oauth: bool = False  # True if provider has a "Sign in with Google" button

    async def handle_google_oauth(self, page, config: dict) -> bool:
        """Attempt Google OAuth login by finding and clicking the Google button.

        Returns True on success, False on any failure (caller should fall back
        to manual login).
        """
        google_selectors = [
            'button:has-text("Sign in with Google")',
            'button:has-text("Continue with Google")',
            'a:has-text("Sign in with Google")',
            'text=Sign in with Google',
            'text=Continue with Google',
        ]

        clicked = False
        for sel in google_selectors:
            try:
                btn = await page.wait_for_selector(sel, timeout=3000)
                if btn:
                    await btn.click()
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            return False

        # If already logged into Google the popup may close immediately — that's fine
        try:
            await page.wait_for_url("*accounts.google.com*", timeout=10000)
        except Exception:
            # Either already logged in (redirect skipped) or something else — check domain
            domain = urlparse(self.signup_url).netloc
            try:
                await page.wait_for_url(f"*{domain}*", timeout=5000)
                return True  # Already authenticated
            except Exception:
                return False

        try:
            await page.fill('input[type="email"]', config.get("google_email", config["email"]))
            await page.click('#identifierNext')
            await page.wait_for_selector('input[type="password"]', timeout=6000)
            await page.fill('input[type="password"]', config["google_password"])
            await page.click('#passwordNext')
        except Exception:
            return False

        # Handle confirmation dialogs ("Continue", "Allow", "Agree")
        for btn_text in ["Continue", "Allow", "Agree"]:
            try:
                await page.wait_for_selector(f'button:has-text("{btn_text}")', timeout=4000)
                await page.click(f'button:has-text("{btn_text}")')
            except Exception:
                pass

        # Wait for redirect back to provider
        domain = urlparse(self.signup_url).netloc
        try:
            await page.wait_for_url(f"*{domain}*", timeout=15000)
            return True
        except Exception:
            return False

    async def run(self, page, config: dict) -> Optional[str]:
        """Default signup flow: navigate, attempt Google OAuth if enabled, prompt for key.

        Args:
            page: Playwright Page object (shared across all providers)
            config: Dict with email, name, and optionally google_email,
                    google_password, vision_api_key

        Returns:
            API key string, or None if skipped
        """
        await page.goto(self.signup_url)

        oauth_done = False
        if self.google_oauth and config.get("google_password"):
            print(f"  🔐 Attempting Google OAuth for {self.name}...")
            oauth_done = await self.handle_google_oauth(page, config)
            if oauth_done:
                print("  ✓ Google login successful")
                await page.goto(self.api_key_url)
            else:
                print("  ⚠  Google OAuth failed — complete login manually in the browser")
                if config.get("vision_api_key"):
                    from src.vision import vision_assist
                    advice = await vision_assist(page, f"Google login for {self.name}", config)
                    if advice:
                        print(f"\n  🤖 Vision:\n  {advice}\n")

        if not oauth_done:
            try:
                await page.fill('input[type="email"]', config["email"])
            except Exception:
                pass

        print(f"\n  {self.name} ({self.tier})")
        if self.gotchas:
            print(f"  ⚠️  {self.gotchas}")
        print(f"  ► Navigate to: {self.api_key_url}")

        has_vision = bool(config.get("vision_api_key"))
        prompt = "  ► Paste key below, or 'v' for vision help, ENTER to skip:" if has_vision \
            else "  ► Create a new API key and paste it below (or ENTER to skip):"
        print(prompt)

        while True:
            raw = input("  Key > ").strip()
            if raw.lower() == "v":
                from src.vision import vision_assist
                advice = await vision_assist(page, self.name, config)
                if advice:
                    print(f"\n  🤖 Vision Assistant:\n  {advice}\n")
                else:
                    print("  ⚠  No vision key configured (answer 'y' at startup or provide Gemini key)")
            elif raw:
                return raw
            else:
                return None
