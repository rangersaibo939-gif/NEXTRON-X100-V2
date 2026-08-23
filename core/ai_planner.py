from __future__ import annotations

import json
import re

from core.app_plan import AppPlan
from core.providers.base import AIProvider


class AIPlanner:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    @staticmethod
    def _offline_plan(request: str) -> AppPlan:
        """Create a safe deterministic plan when the remote planner is unavailable.

        The builder must remain usable even when an AI provider is blocked,
        rate-limited, offline, or missing credentials. This fallback intentionally
        favors a small, buildable Android app over another network retry loop.
        """
        text = request.strip()
        lowered = text.lower()

        if "expense" in lowered or "spending" in lowered or "budget" in lowered:
            app_name = "Expense Tracker"
            package_name = "com.nextron.expenses"
            screens = ("Home", "Add Expense")
            features = ["Monthly totals", "Categories"]
            actions = ["Add Expense", "Delete Expense"]
            data_model = {"expense": "amount, category, date", "currency": "INR"}
        else:
            words = re.findall(r"[A-Za-z0-9]+", text)
            app_name = " ".join(words[:4]).title() or "NEXTRON App"
            package_slug = re.sub(r"[^a-z0-9]+", ".", app_name.lower()).strip(".")
            package_name = f"com.nextron.{package_slug or 'app'}"
            screens = ("Home",)
            features = []
            actions = ["Primary Action"]
            data_model = {}

            if "dark" in lowered:
                features.append("Dark mode")
            if "category" in lowered or "categories" in lowered:
                features.append("Categories")
            if "total" in lowered:
                features.append("Totals")

        if "dark" in lowered and "Dark mode" not in features:
            features.append("Dark mode")
        if not features:
            features = ["Simple navigation"]

        if "add" in lowered and "Add Item" not in actions and "Add Expense" not in actions:
            actions.insert(0, "Add Item")
        if "delete" in lowered and "Delete Item" not in actions and "Delete Expense" not in actions:
            actions.append("Delete Item")

        return AppPlan.from_dict(
            {
                "app_name": app_name,
                "package_name": package_name,
                "description": text or "NEXTRON generated Android application",
                "platform": "android",
                "screens": list(screens),
                "features": features,
                "theme": {"mode": "dark" if "dark" in lowered else "light"},
                "data_model": data_model,
                "actions": actions,
            }
        )

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
                # Cloudflare/provider access errors are not transient. Stop the
                # retry loop and use the deterministic builder fallback instead.
                if "403" in last_error or "cloudflare" in last_error.lower():
                    break
                continue

            text = response.text.strip()

            text = re.sub(
                r"^```(?:json)?\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )
            text = re.sub(r"\s*```$", "", text)

            try:
                data = json.loads(text)
                return AppPlan.from_dict(data)
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = str(exc)

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

        # Do not let a provider outage prevent NEXTRON from building an APK.
        return self._offline_plan(request)
