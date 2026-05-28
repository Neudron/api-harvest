from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("novita")
class NovitaHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "+ New Key", "Generate"]
    key_pattern = KEY_PATTERNS["novita"]
    landing_wait_url_substring = "novita.ai"
