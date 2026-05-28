from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("cerebras")
class CerebrasHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "Generate API Key", "New key"]
    key_pattern = KEY_PATTERNS["cerebras"]
    landing_wait_url_substring = "cloud.cerebras.ai"
