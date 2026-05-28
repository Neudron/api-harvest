from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("alibaba-qwen-dashscope")
class AlibabaQwenHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create New API-KEY", "Create API Key", "Create"]
    key_pattern = KEY_PATTERNS["alibaba-qwen-dashscope"]
    landing_wait_url_substring = "aliyun.com"
