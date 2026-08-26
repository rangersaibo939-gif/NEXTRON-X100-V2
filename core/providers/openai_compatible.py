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
        api_key_env: str,
        capabilities: dict[str, int] | None = None,
        reliability: int = 80,
        speed: int = 80,
        context: int = 0,
        timeout: float = 60.0,
    ):
        self.name = name
        self.base_url = base_url.strip().rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
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

    @property
    def chat_completions_url(self) -> str:
        """Return exactly one /chat/completions suffix.

        NEXTRON's UI accepts either an OpenAI-compatible base URL such as
        https://api.groq.com/openai/v1 or the full chat-completions endpoint.
        Normalizing here prevents the old double-suffix bug:
        /chat/completions/chat/completions -> HTTP 404.
        """
        suffix = "/chat/completions"
        if self.base_url.endswith(suffix):
            return self.base_url
        return f"{self.base_url}{suffix}"

    def is_available(self) -> bool:
        return bool(os.getenv(self.api_key_env))

    def generate(self, prompt: str) -> AIResponse:
        api_key = os.getenv(self.api_key_env)

        if not api_key:
            return AIResponse(
                "",
                self.model,
                self.name,
                False,
                f"Missing {self.api_key_env}",
            )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are NEXTRON's structured planning engine. "
                        "Follow the user's requested output format exactly. "
                        "When JSON is requested, return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        body_bytes = json.dumps(payload).encode("utf-8")

        req = request.Request(
            self.chat_completions_url,
            data=body_bytes,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")

            body = json.loads(raw)

            choices = body.get("choices")
            if not choices:
                return AIResponse(
                    "",
                    self.model,
                    self.name,
                    False,
                    f"Provider returned no choices: {raw[:500]}",
                )

            message = choices[0].get("message", {})
            text = message.get("content", "")

            if not isinstance(text, str) or not text.strip():
                return AIResponse(
                    "",
                    self.model,
                    self.name,
                    False,
                    f"Provider returned empty content: {raw[:500]}",
                )

            return AIResponse(
                text.strip(),
                self.model,
                self.name,
                True,
                None,
            )

        except error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(exc)

            return AIResponse(
                "",
                self.model,
                self.name,
                False,
                f"HTTP {exc.code}: {detail[:1000]}",
            )

        except (
            error.URLError,
            TimeoutError,
            KeyError,
            IndexError,
            json.JSONDecodeError,
        ) as exc:
            return AIResponse(
                "",
                self.model,
                self.name,
                False,
                str(exc),
            )
