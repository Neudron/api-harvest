from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("mistral-la-plateforme")
class MistralHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create new key", "Create API Key", "Create key"]
    key_pattern = KEY_PATTERNS["mistral-la-plateforme"]
    consent_required = True
    landing_wait_url_substring = "console.mistral.ai"
