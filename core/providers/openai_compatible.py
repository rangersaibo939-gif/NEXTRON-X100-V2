"""Generic OpenAI-compatible provider for NEXTRON.

Works with providers exposing /chat/completions, including Groq and OpenRouter.
Credentials are read only from environment variables.
"""

from __future__ import annotations

import os
import time

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
        max_retries: int = 2,
        retry_base_seconds: float = 1.0,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.max_retries = max(0, max_retries)
        self.retry_base_seconds = max(0.0, retry_base_seconds)
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

    @staticmethod
    def _retry_delay(response: requests.Response, attempt: int, base: float) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, min(float(retry_after), 30.0))
            except ValueError:
                pass
        return min(base * (2 ** attempt), 8.0)

    @staticmethod
    def _http_error(response: requests.Response) -> str:
        """Return a useful provider error without exposing credentials."""
        detail = response.text.strip()
        if len(detail) > 1000:
            detail = detail[:1000] + "..."
        return f"HTTP {response.status_code}: {detail}" if detail else f"HTTP {response.status_code}"

    def generate(self, prompt: str) -> AIResponse:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            return AIResponse("", self.model, self.name, False, f"Missing {self.api_key_env}")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
        }

        for attempt in range(self.max_retries + 1):
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
                if response.status_code == 429 and attempt < self.max_retries:
                    time.sleep(self._retry_delay(response, attempt, self.retry_base_seconds))
                    continue
                if response.status_code >= 400:
                    return AIResponse("", self.model, self.name, False, self._http_error(response))

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

        return AIResponse("", self.model, self.name, False, "Provider rate limited after retries")
