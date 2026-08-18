"""Built-in provider/model catalog.

Only metadata lives here. API keys never belong in source control.
"""

from __future__ import annotations

import os

from .openai_compatible import OpenAICompatibleProvider


def build_providers() -> list[OpenAICompatibleProvider]:
    providers: list[OpenAICompatibleProvider] = []

    if os.getenv("GROQ_API_KEY"):
        providers.append(OpenAICompatibleProvider(
            name="groq",
            base_url="https://api.groq.com/openai/v1",
            model=os.getenv("NEXTRON_GROQ_MODEL", "openai/gpt-oss-20b"),
            api_key_env="GROQ_API_KEY",
        ))

    if os.getenv("OPENROUTER_API_KEY"):
        providers.append(OpenAICompatibleProvider(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            model=os.getenv("NEXTRON_OPENROUTER_MODEL", "openrouter/free"),
            api_key_env="OPENROUTER_API_KEY",
        ))

    return providers
