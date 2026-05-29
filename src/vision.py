"""Vision model assistance via Gemini Flash — screenshot analysis for stuck flows."""

import base64

import httpx


async def vision_assist(page, context: str, config: dict) -> str | None:
    """Take a screenshot and ask Gemini Flash what the user should do next.

    Args:
        page: Playwright Page object
        context: Provider name or description of what's being attempted
        config: Config dict — must contain "vision_api_key" to be active

    Returns:
        Advice string from Gemini, or None if no vision key is configured
    """
    key = config.get("vision_api_key")
    if not key:
        return None

    screenshot = await page.screenshot()
    b64 = base64.b64encode(screenshot).decode()

    prompt = (
        f"You are helping a user navigate a browser to sign up for '{context}'.\n"
        "Look at the screenshot and explain:\n"
        "1. What page is currently shown?\n"
        "2. What should the user click or fill in next?\n"
        "3. Are there errors, CAPTCHAs, or blockers visible?\n"
        "Be concise and actionable (e.g., 'Click the blue Create API Key button at top right')."
    )

    try:
        resp = await httpx.AsyncClient(timeout=30).post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            json={
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/png", "data": b64}},
                    ]
                }]
            },
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"[Vision API error: {e}]"
