from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("fireworks-ai")
class FireworksHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "+ Create Key", "Generate Key"]
    key_pattern = KEY_PATTERNS["fireworks-ai"]
    landing_wait_url_substring = "fireworks.ai"
