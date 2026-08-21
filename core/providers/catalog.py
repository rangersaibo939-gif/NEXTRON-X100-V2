"""Built-in provider/model catalog.

Only metadata lives here. API keys never belong in source control.
"""

from __future__ import annotations

import os

from .openai_compatible import OpenAICompatibleProvider


def build_providers() -> dict[str, OpenAICompatibleProvider]:
    providers: dict[str, OpenAICompatibleProvider] = {}

    if os.getenv("GROQ_API_KEY"):
        provider = OpenAICompatibleProvider(
            name="groq",
            base_url="https://api.groq.com/openai/v1",
            model=os.getenv("NEXTRON_GROQ_MODEL", "openai/gpt-oss-20b"),
            api_key_env="GROQ_API_KEY",
            capabilities={"coding": 94, "reasoning": 92, "research": 70},
            reliability=92,
            speed=96,
            max_tokens=int(os.getenv("NEXTRON_GROQ_MAX_TOKENS", "1024")),
        )
        providers[provider.name] = provider

    if os.getenv("OPENROUTER_API_KEY"):
        provider = OpenAICompatibleProvider(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            model=os.getenv("NEXTRON_OPENROUTER_MODEL", "openrouter/free"),
            api_key_env="OPENROUTER_API_KEY",
            capabilities={"coding": 88, "reasoning": 90, "vision": 70, "research": 82},
            reliability=86,
            speed=82,
            max_tokens=int(os.getenv("NEXTRON_OPENROUTER_MAX_TOKENS", "1024")),
        )
        providers[provider.name] = provider

    return providers
