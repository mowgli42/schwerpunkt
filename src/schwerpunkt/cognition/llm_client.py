from __future__ import annotations

import json
from typing import Any, Protocol

import httpx


class LlmClientProtocol(Protocol):
    async def complete_json(self, system: str, user: str) -> dict[str, Any]: ...


class LlmClient:
    """OpenAI-compatible chat completions client returning parsed JSON content."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._transport = transport

    @classmethod
    def from_settings(cls, settings: Any) -> LlmClient:
        return cls(
            base_url=settings.llm_api_base,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=60.0, transport=self._transport) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)


class MockLlmClient:
    """Deterministic LLM stub for tests and SCHWERKPUNKT_LLM_MOCK=1 demos."""

    async def complete_json(self, system: str, user: str) -> dict[str, Any]:
        request = json.loads(user)
        phase = request.get("phase")
        if phase == "orient":
            return {
                "use_baseline": True,
                "orientation_confidence": 0.88,
                "requires_human_review": False,
            }
        if phase == "decide":
            return {"chosen_id": request.get("default_chosen_id", "B")}
        return {}
