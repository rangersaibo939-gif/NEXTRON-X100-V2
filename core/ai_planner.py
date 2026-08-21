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
        response = self.provider.generate(prompt)

        if not response.success:
            raise RuntimeError(response.error or "AI planning failed")

        text = response.text.strip()

        # Extract JSON if the model accidentally adds surrounding text.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("AI did not return a JSON object")

        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ValueError(f"AI returned invalid JSON: {exc}") from exc

        return AppPlan.from_dict(data)
