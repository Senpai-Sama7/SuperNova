"""Async Ollama client for local LLM inference and embedding fallback.

Provides OllamaClient for chat completions and embeddings via a local
Ollama server. Used as the zero-cost fallback when API budgets are exceeded.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from supernova.config import get_settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for Ollama local inference.

    Args:
        host: Ollama server URL (default from settings).
        model: Default model for completions.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        s = get_settings().ollama
        self._host = (host or s.host).rstrip("/")
        self._model = model or s.default_model
        self._timeout = timeout
        self._enabled = s.enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a chat completion request to Ollama.

        Returns dict with 'content', 'model', 'total_duration', 'eval_count'.
        """
        payload = {
            "model": model or self._model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._host}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        return {
            "content": data.get("message", {}).get("content", ""),
            "model": data.get("model", ""),
            "total_duration": data.get("total_duration", 0),
            "eval_count": data.get("eval_count", 0),
        }

    async def embed(
        self,
        text: str | list[str],
        model: str = "nomic-embed-text",
    ) -> list[list[float]]:
        """Generate embeddings via Ollama. Fallback for API embedding budget.

        Args:
            text: Single string or list of strings to embed.
            model: Embedding model (default: nomic-embed-text).

        Returns:
            List of embedding vectors.
        """
        inputs = [text] if isinstance(text, str) else text
        payload = {"model": model, "input": inputs}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._host}/api/embed", json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data.get("embeddings", [])

    async def is_available(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._host}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List locally available models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._host}/api/tags")
                resp.raise_for_status()
                data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
