"""Generic OpenAI-compatible provider for NEXTRON.

Works with providers exposing /chat/completions, including services such as
Groq and OpenRouter. Credentials are read only from environment variables.
"""

from __future__ import annotations

import json
import os
from urllib import error, request

from .base import AIProvider, AIResponse


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, *, name: str, base_url: str, model: str, api_key_env: str, timeout: float = 60.0):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.timeout = timeout

    def is_available(self) -> bool:
        return bool(os.getenv(self.api_key_env))

    def generate(self, prompt: str) -> AIResponse:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            return AIResponse("", self.model, self.name, False, f"Missing {self.api_key_env}")

        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
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
        except (error.URLError, error.HTTPError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            return AIResponse("", self.model, self.name, False, str(exc))
