from harvest.handlers import register
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.selectors import KEY_PATTERNS


@register("vercel-ai-gateway")
class VercelAiGatewayHandler(GoogleSsoCreateKeyRecipe):
    create_button_candidates = ["Create Key", "Create API Key", "+ Create Key", "New Key"]
    key_pattern = KEY_PATTERNS["vercel-ai-gateway"]
    landing_wait_url_substring = "vercel.com"
