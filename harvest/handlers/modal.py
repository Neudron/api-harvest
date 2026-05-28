from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("modal")
class ModalHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create token", "New token", "+ Create Token"]
    key_pattern = KEY_PATTERNS["modal"]
    landing_wait_url_substring = "modal.com"
