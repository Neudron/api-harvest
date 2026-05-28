from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("mistral-codestral-separate-endpoint")
class CodestralHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create new key", "Create API Key", "Generate"]
    key_pattern = KEY_PATTERNS["mistral-codestral-separate-endpoint"]
    landing_wait_url_substring = "codestral.mistral.ai"
