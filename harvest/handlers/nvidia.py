from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("nvidia-nim")
class NvidiaNimHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Generate API Key", "Get API Key", "Create API Key"]
    key_pattern = KEY_PATTERNS["nvidia-nim"]
    landing_wait_url_substring = "build.nvidia.com"
