from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("nlp-cloud")
class NlpCloudHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create new token", "Generate Token", "Create API Key"]
    key_pattern = KEY_PATTERNS["nlp-cloud"]
    landing_wait_url_substring = "nlpcloud.com"
