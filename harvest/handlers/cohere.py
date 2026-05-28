from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("cohere")
class CohereHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create Trial Key", "Create New Trial Key", "Create API Key", "+ New Trial Key"]
    key_pattern = KEY_PATTERNS["cohere"]
    landing_wait_url_substring = "dashboard.cohere.com"
