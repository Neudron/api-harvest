from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("anthropic")
class AnthropicHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create Key", "Create API Key", "+ Create Key"]
    key_pattern = KEY_PATTERNS["anthropic"]
    landing_wait_url_substring = "console.anthropic.com"
