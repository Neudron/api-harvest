from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("xai-grok")
class XaiGrokHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "+ Create API Key", "New Key"]
    key_pattern = KEY_PATTERNS["xai-grok"]
    landing_wait_url_substring = "console.x.ai"
