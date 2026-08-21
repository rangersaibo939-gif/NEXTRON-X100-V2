from __future__ import annotations

import json
import re

from core.app_plan import AppPlan
from core.providers.base import AIProvider


class AIPlanner:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    def plan(self, request: str) -> AppPlan:
        prompt = f"""Create an Android app plan for this request:

{request}

Return ONLY valid JSON with exactly these fields:
app_name, package_name, description, platform, screens, features, theme, data_model, actions

Rules:
- platform must be "android"
- package_name must be lowercase dotted Android package name
- screens, features and actions must be arrays of strings
- theme and data_model must be JSON objects
- no markdown
- no explanation
"""

        last_error = None

        for attempt in range(3):
            response = self.provider.generate(prompt)

            if not response.success:
                last_error = response.error or "AI planning failed"
                continue

            text = response.text.strip()

            # Remove optional Markdown code fences.
            text = re.sub(
                r"^```(?:json)?\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )
            text = re.sub(r"\s*```$", "", text)

            # First try the complete response directly.
            try:
                data = json.loads(text)
                return AppPlan.from_dict(data)
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = str(exc)

            # If the model added surrounding text, extract the JSON object.
            start = text.find("{")
            end = text.rfind("}")

            if start == -1 or end == -1 or end <= start:
                last_error = "AI did not return a JSON object"
                continue

            candidate = text[start:end + 1]

            try:
                data = json.loads(candidate)
                return AppPlan.from_dict(data)
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = str(exc)

        raise ValueError(
            f"AI planning failed after 3 attempts: {last_error}"
        )
