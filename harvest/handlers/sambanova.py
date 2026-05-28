from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("sambanova-cloud")
class SambaNovaHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create new API key", "Create API Key", "+ New Key"]
    key_pattern = KEY_PATTERNS["sambanova-cloud"]
    landing_wait_url_substring = "cloud.sambanova.ai"
