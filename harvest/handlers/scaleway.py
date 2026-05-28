from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("scaleway-generative-apis")
class ScalewayHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Generate API Key", "Create API Key", "+ Create Key"]
    key_pattern = KEY_PATTERNS["scaleway-generative-apis"]
    landing_wait_url_substring = "console.scaleway.com"
