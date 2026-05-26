"""Modal provider — email-only free tier."""

from src.providers.base import BaseProvider


class ModalProvider(BaseProvider):
    name = "Modal"
    env_var = "MODAL_API_KEY"
    tier = "email"
    signup_url = "https://modal.com/"
    api_key_url = "https://modal.com/"
    free_models = [
        "Any supported model — pay by compute time",
    ]
    credits = "$5/month recurring without CC ($30/month with CC)"
    rate_limits = "Pay by compute time"
    gotchas = "Serverless compute platform — you deploy and run models. Good for custom inference."
