"""Google Gemini provider — Google primary auth, auto key extraction, vision bootstrap."""

from src.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    name = "Google Gemini"
    env_var = "GOOGLE_GENERATIVE_AI_API_KEY"
    tier = "email"
    signup_url = "https://aistudio.google.com"
    api_key_url = "https://aistudio.google.com/apikey"
    free_models = [
        "Gemini 2.5 Flash",
        "Gemini 2.5 Flash-Lite",
        "Gemini 3 Flash",
        "Gemma 3 (1B/4B/12B/27B)",
    ]
    credits = "Permanent free tier (rate-limited)"
    rate_limits = "5-15 RPM, 250K tok/min, 20-500 RPD (Flash); 30 RPM, 14,400 RPD (Gemma)"
    gotchas = "Rate limits periodically reduced. Not available in EU. Data used for training outside UK/CH/EEA/EU."

    async def run(self, page, config: dict):
        await page.goto(self.signup_url)

        print(f"\n  {self.name} ({self.tier})")
        if self.gotchas:
            print(f"  ⚠️  {self.gotchas}")

        # aistudio.google.com redirects directly to accounts.google.com — handle it
        if config.get("google_password"):
            print("  🔐 Attempting Google login for AI Studio...")
            try:
                await page.wait_for_url("*accounts.google.com*", timeout=8000)
                await page.fill('input[type="email"]', config.get("google_email", config["email"]))
                await page.click('#identifierNext')
                await page.wait_for_selector('input[type="password"]', timeout=6000)
                await page.fill('input[type="password"]', config["google_password"])
                await page.click('#passwordNext')
                for btn in ["Continue", "Allow", "Agree"]:
                    try:
                        await page.wait_for_selector(f'button:has-text("{btn}")', timeout=3000)
                        await page.click(f'button:has-text("{btn}")')
                    except Exception:
                        pass
                await page.wait_for_url("*aistudio.google.com*", timeout=15000)
                print("  ✓ Google login successful")
            except Exception as e:
                print(f"  ⚠  Auto-login failed ({e}) — complete in browser, then press ENTER")
                input("  (Press ENTER when logged in) > ")

        # Navigate to API key page
        await page.goto(self.api_key_url)

        # Try to auto-click "Create API key" and extract the result
        try:
            await page.wait_for_selector('button:has-text("Create API key")', timeout=5000)
            await page.click('button:has-text("Create API key")')
            # Key may appear in a dialog or inline — try common selectors
            await page.wait_for_selector(
                '[data-testid="api-key-value"], code, .api-key-display, [aria-label="API key"]',
                timeout=5000,
            )
            key_el = await page.query_selector(
                '[data-testid="api-key-value"], code, .api-key-display, [aria-label="API key"]'
            )
            if key_el:
                key = (await key_el.inner_text()).strip()
                if key.startswith("AIza"):
                    print(f"  ✓ API key auto-extracted: {key[:12]}...")
                    self._bootstrap_vision(config, key)
                    return key
        except Exception:
            pass

        # Fallback: ask user to copy the key manually
        has_vision = bool(config.get("vision_api_key"))
        prompt = "  ► Paste key below, or 'v' for vision help, ENTER to skip:" if has_vision \
            else "  ► Copy the API key from the page and paste it below (or ENTER to skip):"
        print(prompt)

        while True:
            raw = input("  Key > ").strip()
            if raw.lower() == "v":
                from src.vision import vision_assist
                advice = await vision_assist(page, "Google AI Studio API key creation", config)
                print(f"\n  🤖 Vision:\n  {advice}\n" if advice else "  ⚠  No vision key yet")
            elif raw:
                self._bootstrap_vision(config, raw)
                return raw
            else:
                return None

    def _bootstrap_vision(self, config: dict, key: str) -> None:
        """Store Gemini key as vision API key if none set yet."""
        if not config.get("vision_api_key"):
            config["vision_api_key"] = key
            print("  💡 Gemini key auto-set as vision assistant for remaining providers")
