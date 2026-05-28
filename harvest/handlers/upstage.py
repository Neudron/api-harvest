from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("upstage")
class UpstageHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "+ Create Key", "Generate Key"]
    key_pattern = KEY_PATTERNS["upstage"]
    landing_wait_url_substring = "upstage.ai"
