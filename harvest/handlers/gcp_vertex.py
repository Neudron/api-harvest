from harvest.handlers import register
from harvest.handlers.recipes import CloudConsoleRecipe


@register("google-vertex-ai")
class GcpVertexHandler(CloudConsoleRecipe):
    cc_pause_reason = (
        "Google Cloud requires a credit card and an upgrade from free trial to paid billing "
        "before Vertex AI works. Card WILL be charged if you exceed the $300 credit."
    )
    manual_capture_message = (
        "Create or download a Service Account key JSON, then paste its absolute path here "
        "(it goes to GOOGLE_APPLICATION_CREDENTIALS)."
    )
