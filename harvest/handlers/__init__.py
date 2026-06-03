from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from harvest.handlers.base import Handler

# Registry populated by importing the handler modules below.
HANDLER_REGISTRY: dict[str, type[Handler]] = {}


def register(slug: str):
    def deco(cls):
        HANDLER_REGISTRY[slug] = cls
        return cls

    return deco


# Import side-effects: each module decorates its class with @register(slug).
from harvest.handlers import (  # noqa: E402,F401
    ai21,
    alibaba_qwen,
    anthropic,
    aws_bedrock,
    azure_openai,
    baseten,
    cerebras,
    cloudflare,
    codestral,
    cohere,
    fireworks,
    gcp_vertex,
    github_models,
    google_aistudio,
    groq,
    huggingface,
    hyperbolic,
    inference_net,
    mistral,
    modal,
    nebius,
    nlpcloud,
    novita,
    nvidia,
    opencode_zen,
    openrouter,
    perplexity,
    sambanova,
    scaleway,
    upstage,
    vercel,
    xai,
)

# Plugin group for third-party handlers distributed as separate packages.
HANDLER_ENTRY_POINT_GROUP = "harvest.handlers"


def load_plugin_handlers(entry_points_fn=None) -> list[str]:
    """Load third-party handlers advertised under the ``harvest.handlers``
    entry-point group, registering each by its entry-point name (the slug).

    Core (in-tree) handlers win slug collisions: a plugin whose slug is already
    registered is ignored. Plugins that fail to import are skipped silently so a
    broken plugin never breaks the whole CLI. ``entry_points_fn`` is injectable
    for testing (a zero-arg callable returning an iterable of entry points);
    by default it reads from ``importlib.metadata``.

    Returns the list of slugs newly added.

    Trust boundary: plugins run arbitrary browser automation in this process.
    Only install handler plugins you trust.
    """
    added: list[str] = []
    try:
        if entry_points_fn is None:
            from importlib.metadata import entry_points

            eps = entry_points(group=HANDLER_ENTRY_POINT_GROUP)
        else:
            eps = entry_points_fn()
    except Exception:
        return added

    for ep in eps:
        slug = getattr(ep, "name", None)
        if not slug or slug in HANDLER_REGISTRY:
            continue  # core wins collisions; skip unnamed/duplicate
        try:
            cls = ep.load()
        except Exception:
            continue  # a broken plugin must not break the CLI
        HANDLER_REGISTRY[slug] = cls
        added.append(slug)
    return added


# Load any installed third-party handler plugins after the in-tree ones, so
# core handlers always win slug collisions.
load_plugin_handlers()
