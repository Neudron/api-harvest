from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("opencode-zen")
class OpenCodeZenHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "Create Key", "+ New Key"]
    key_pattern = KEY_PATTERNS["opencode-zen"]
    landing_wait_url_substring = "opencode.ai"
