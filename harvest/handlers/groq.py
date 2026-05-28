from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("groq")
class GroqHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "+ Create API Key", "New key"]
    key_pattern = KEY_PATTERNS["groq"]
    landing_wait_url_substring = "console.groq.com"
