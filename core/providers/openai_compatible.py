"""Generic OpenAI-compatible provider for NEXTRON.

Works with providers exposing /chat/completions, including Groq and OpenRouter.
Credentials are read only from environment variables.
"""

from __future__ import annotations

import json
import os
from urllib import error, request

from core.model_registry import ModelProfile
from .base import AIProvider, AIResponse


class OpenAICompatibleProvider(AIProvider):
    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        model: str,
        api_key_env: str | list[str] | tuple[str, ...],
        capabilities: dict[str, int] | None = None,
        reliability: int = 80,
        speed: int = 80,
        context: int = 0,
        timeout: float = 60.0,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_envs = self._normalize_key_envs(api_key_env)
        # Preserve the existing public attribute and single-key behavior.
        self.api_key_env = self.api_key_envs[0]
        self.timeout = timeout
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

    @staticmethod
    def _normalize_key_envs(api_key_env: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:
        if isinstance(api_key_env, str):
            envs = (api_key_env,)
        else:
            envs = tuple(api_key_env)
        return tuple(env for env in envs if env)

    def _configured_keys(self) -> list[tuple[str, str]]:
        return [(env, key) for env in self.api_key_envs if (key := os.getenv(env))]

    def is_available(self) -> bool:
        return bool(self._configured_keys())

    def generate(self, prompt: str) -> AIResponse:
        configured_keys = self._configured_keys()
        if not configured_keys:
            return AIResponse("", self.model, self.name, False, f"Missing {self.api_key_env}")

        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")

        for index, (_, api_key) in enumerate(configured_keys):
            req = request.Request(
                f"{self.base_url}/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=self.timeout) as response:
                    body = json.loads(response.read().decode("utf-8"))
                text = body["choices"][0]["message"]["content"]
                return AIResponse(text, self.model, self.name)
            except error.HTTPError as exc:
                # Only authentication/rate-limit failures are safe key-rotation cases.
                if exc.code not in (401, 403, 429) or index == len(configured_keys) - 1:
                    return AIResponse("", self.model, self.name, False, "Provider request failed")
            except (error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError):
                return AIResponse("", self.model, self.name, False, "Provider request failed")

        return AIResponse("", self.model, self.name, False, "Provider request failed")
