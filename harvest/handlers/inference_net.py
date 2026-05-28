from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("inference-net")
class InferenceNetHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create API Key", "+ Create Key", "Generate"]
    key_pattern = KEY_PATTERNS["inference-net"]
    landing_wait_url_substring = "inference.net"
