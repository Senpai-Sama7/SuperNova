"""Built-in web search tool using Tavily or SerpAPI."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from supernova.infrastructure.tools.registry import Capability, Tool

logger = logging.getLogger(__name__)

_TAVILY_URL = "https://api.tavily.com/search"
_SERPAPI_URL = "https://serpapi.com/search"


async def _web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Execute web search via Tavily (preferred) or SerpAPI fallback."""
    tavily_key = os.environ.get("TAVILY_API_KEY")
    serp_key = os.environ.get("SERPAPI_KEY")

    async with httpx.AsyncClient(timeout=15.0) as client:
        if tavily_key:
            resp = await client.post(
                _TAVILY_URL,
                json={"api_key": tavily_key, "query": query, "max_results": max_results},
            )
            resp.raise_for_status()
            return [
                {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
                for r in resp.json().get("results", [])
            ]

        if serp_key:
            resp = await client.get(
                _SERPAPI_URL,
                params={"api_key": serp_key, "q": query, "num": max_results},
            )
            resp.raise_for_status()
            return [
                {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
                for r in resp.json().get("organic_results", [])
            ]

    raise RuntimeError("No search API key configured (TAVILY_API_KEY or SERPAPI_KEY)")


def create_web_search_tool() -> Tool:
    """Factory returning a web search Tool for ToolRegistry."""
    return Tool(
        name="web_search",
        description="Search the web for information using Tavily or SerpAPI.",
        required_capabilities=Capability.WEB_SEARCH,
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results", "default": 5},
            },
            "required": ["query"],
        },
        fn=_web_search,
        is_safe_parallel=True,
    )
