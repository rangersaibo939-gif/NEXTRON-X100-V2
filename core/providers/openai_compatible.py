"""Generic OpenAI-compatible provider for NEXTRON.

Works with providers exposing /chat/completions, including Groq and OpenRouter.
Credentials are read only from environment variables.
"""

from __future__ import annotations

import os

import requests

from core.model_registry import ModelProfile
from .base import AIProvider, AIResponse


class OpenAICompatibleProvider(AIProvider):
    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        model: str,
        api_key_env: str,
        capabilities: dict[str, int] | None = None,
        reliability: int = 80,
        speed: int = 80,
        context: int = 0,
        timeout: float = 60.0,
        max_tokens: int = 1024,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.timeout = timeout
        self.max_tokens = max_tokens
        capabilities = capabilities or {}
        self.model_profile = ModelProfile(
            name=f"{name}:{model}",
            provider=name,
            coding=capabilities.get("coding", 0),
            reasoning=capabilities.get("reasoning", 0),
            vision=capabilities.get("vision", 0),
            research=capabilities.get("research", 0),
            image_generation=capabilities.get("image_generation", 0),
            reliability=reliability,
            speed=speed,
            context=context,
        )

    def is_available(self) -> bool:
        return bool(os.getenv(self.api_key_env))

    def generate(self, prompt: str) -> AIResponse:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            return AIResponse("", self.model, self.name, False, f"Missing {self.api_key_env}")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
        }
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "NEXTRON/1.0",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            body = response.json()
            message = body["choices"][0]["message"]
            text = message.get("content") or ""
            if not text.strip():
                return AIResponse(
                    "", self.model, self.name, False,
                    "Provider returned no visible content"
                )
            return AIResponse(text, self.model, self.name)
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            return AIResponse("", self.model, self.name, False, str(exc))
