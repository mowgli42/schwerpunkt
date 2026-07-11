from __future__ import annotations

from typing import Any, Protocol

from schwerpunkt.models import Observation, Signal


class McpBridge(Protocol):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


class MockMcpBridge:
    """Fixture-backed MCP tool responses for tests and SCHWERKPUNKT_MCP_MOCK=1."""

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "fetch_sensor":
            scenario = arguments.get("scenario", "default")
            if scenario == "contradiction_case":
                return {
                    "signals": [
                        {"key": "case_status", "value": "open", "confidence": 0.85, "source": "mcp_case_api"}
                    ],
                    "confidence": 0.85,
                }
            return {
                "signals": [
                    {"key": "status", "value": "ok", "confidence": 0.9, "source": "mcp_mock"}
                ],
                "confidence": 0.9,
            }
        return {"signals": [], "confidence": 0.0}


class HttpMcpBridge:
    """Minimal JSON-RPC-style MCP HTTP client (live mode opt-in)."""

    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        import httpx

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.base_url}/mcp", headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
        result = body.get("result", body)
        if isinstance(result, dict) and "content" in result:
            return result["content"]
        return result if isinstance(result, dict) else {"raw": result}


def observation_from_mcp_result(result: dict[str, Any]) -> Observation:
    signals = [Signal(**s) for s in result.get("signals", [])]
    return Observation(
        signals=signals,
        failed_sensors=result.get("failed_sensors", []),
        confidence=float(result.get("confidence", 1.0)),
        pattern_id=result.get("pattern_id", "mcp"),
    )


def create_mcp_bridge(settings: Any) -> McpBridge | None:
    import os

    if not settings.mcp_enabled:
        return None
    if os.environ.get("SCHWERKPUNKT_MCP_MOCK") == "1":
        return MockMcpBridge()
    if settings.mcp_server_url:
        return HttpMcpBridge(settings.mcp_server_url, settings.mcp_api_key)
    return MockMcpBridge()
