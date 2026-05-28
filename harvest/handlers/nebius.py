from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("nebius")
class NebiusHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "Generate Key", "+ New Key"]
    key_pattern = KEY_PATTERNS["nebius"]
    landing_wait_url_substring = "nebius.com"
