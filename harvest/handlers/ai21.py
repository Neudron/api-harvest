from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("ai21")
class Ai21Handler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "+ Create Key", "Generate"]
    key_pattern = KEY_PATTERNS["ai21"]
    landing_wait_url_substring = "ai21.com"
