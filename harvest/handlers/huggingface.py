from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("huggingface-inference-providers")
class HuggingFaceHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create new token", "+ Create new token", "Generate"]
    key_pattern = KEY_PATTERNS["huggingface-inference-providers"]
    landing_wait_url_substring = "huggingface.co"
