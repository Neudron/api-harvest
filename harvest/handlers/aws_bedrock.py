from harvest.handlers import register
from harvest.handlers.recipes import CloudConsoleRecipe


@register("amazon-bedrock")
class AwsBedrockHandler(CloudConsoleRecipe):
    cc_pause_reason = (
        "AWS requires a credit card and identity verification at signup. "
        "AWS credentials apply across all AWS services — easy to burn the $200 credits."
    )
    manual_capture_message = (
        "In IAM → Security credentials, create an Access key for CLI. "
        "Paste the Access Key ID here (Secret will be prompted next via env file)."
    )
