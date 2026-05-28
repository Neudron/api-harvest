from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("perplexity")
class PerplexityHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Generate", "Generate API Key", "Create Key"]
    key_pattern = KEY_PATTERNS["perplexity"]
    landing_wait_url_substring = "perplexity.ai"
