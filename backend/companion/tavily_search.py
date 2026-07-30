from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


def tavily_search_external_citations(query: str, max_results: int = 3) -> list[dict[str, str]]:
    """Search Tavily for official documentation and external web citations.

    Returns a list of dicts: [{'title': '...', 'url': '...', 'snippet': '...'}]
    """
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return []

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results: list[dict[str, str]] = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", "").strip(),
                    "url": item.get("url", "").strip(),
                    "snippet": item.get("content", "").strip()[:180],
                })
            return results
    except Exception as exc:
        print(f"Tavily search fallback (offline or key missing): {exc}")
        return []
