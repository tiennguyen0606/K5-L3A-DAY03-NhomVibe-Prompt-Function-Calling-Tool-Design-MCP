from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


def fallback_after_tool_rejection(error: Exception, model: str | None) -> str | None:
    """Select a different model when Groq rejects the generated tool call."""
    if getattr(error, "status_code", None) != 400 or getattr(error, "code", None) != "tool_use_failed":
        return None
    return "openai/gpt-oss-120b" if model == "openai/gpt-oss-20b" else "openai/gpt-oss-20b"


class GroqProvider(OpenAIProvider):
    """Groq OpenAI-compatible Chat Completions API (tool calling supported)."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="GROQ_API_KEY",
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            # Free-tier accounts often lack llama-3.3-70b; gpt-oss models support tool calling.
            default_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),

        )
