from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("hyperbolic")
class HyperbolicHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "+ Create Key", "Generate"]
    key_pattern = KEY_PATTERNS["hyperbolic"]
    landing_wait_url_substring = "hyperbolic.ai"
