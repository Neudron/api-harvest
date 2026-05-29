"""Provider registry for AI API Key Harvester."""

from src.providers.base import BaseProvider

# Tier 1 — Email-only providers
from src.providers.tier1.gemini import GeminiProvider
from src.providers.tier1.groq import GroqProvider
from src.providers.tier1.cerebras import CerebrasProvider
from src.providers.tier1.openrouter import OpenRouterProvider
from src.providers.tier1.cohere import CohereProvider
from src.providers.tier1.vercel import VercelProvider
from src.providers.tier1.cloudflare import CloudflareProvider
from src.providers.tier1.huggingface import HuggingFaceProvider
from src.providers.tier1.opencode import OpenCodeProvider
from src.providers.tier1.xai import XAIProvider
from src.providers.tier1.alibaba import AlibabaProvider
from src.providers.tier1.anthropic import AnthropicProvider
from src.providers.tier1.sambanova import SambanovaProvider
from src.providers.tier1.perplexity import PerplexityProvider
from src.providers.tier1.fireworks import FireworksProvider
from src.providers.tier1.baseten import BasetenProvider
from src.providers.tier1.nebius import NebiusProvider
from src.providers.tier1.ai21 import AI21Provider
from src.providers.tier1.upstage import UpstageProvider
from src.providers.tier1.modal import ModalProvider
from src.providers.tier1.hyperbolic import HyperbolicProvider
from src.providers.tier1.inference_net import InferenceNetProvider
from src.providers.tier1.scaleway import ScalewayProvider
from src.providers.tier1.novita import NovitaProvider
from src.providers.tier1.github import GitHubModelsProvider

# Tier 2 — SMS/Phone providers
from src.providers.tier2.mistral import MistralProvider
from src.providers.tier2.mistral_codestral import MistralCodestralProvider
from src.providers.tier2.nvidia import NvidiaProvider
from src.providers.tier2.nlpcloud import NlpcloudProvider

# Tier 3 — Credit card providers
from src.providers.tier3.aws import AWSProvider
from src.providers.tier3.vertex import VertexProvider
from src.providers.tier3.azure import AzureProvider

# Instantiate all providers

_email_providers: list[BaseProvider] = [
    GeminiProvider(),
    GroqProvider(),
    CerebrasProvider(),
    OpenRouterProvider(),
    CohereProvider(),
    VercelProvider(),
    CloudflareProvider(),
    HuggingFaceProvider(),
    OpenCodeProvider(),
    XAIProvider(),
    AlibabaProvider(),
    AnthropicProvider(),
    SambanovaProvider(),
    PerplexityProvider(),
    FireworksProvider(),
    BasetenProvider(),
    NebiusProvider(),
    AI21Provider(),
    UpstageProvider(),
    ModalProvider(),
    HyperbolicProvider(),
    InferenceNetProvider(),
    ScalewayProvider(),
    NovitaProvider(),
    GitHubModelsProvider(),
]

_sms_providers: list[BaseProvider] = [
    MistralProvider(),
    MistralCodestralProvider(),
    NvidiaProvider(),
    NlpcloudProvider(),
]

_cc_providers: list[BaseProvider] = [
    AWSProvider(),
    VertexProvider(),
    AzureProvider(),
]

PROVIDERS_BY_TIER: dict[str, list[BaseProvider]] = {
    "email": _email_providers,
    "sms": _sms_providers,
    "cc": _cc_providers,
}

ALL_PROVIDERS: list[BaseProvider] = _email_providers + _sms_providers + _cc_providers
