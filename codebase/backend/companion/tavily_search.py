from __future__ import annotations

import json
import os
import urllib.request
from typing import Any
from urllib.parse import urlparse

TRUSTED_HOSTS = (
    "pytorch.org",
    "tensorflow.org",
    "scikit-learn.org",
    "python.org",
    "developer.apple.com",
    "learn.microsoft.com",
    "cloud.google.com",
    "huggingface.co",
    "ibm.com",
)
COMMUNITY_HOSTS = ("medium.com", "stackoverflow.com", "geeksforgeeks.org")


def _source_priority(url: str) -> int:
    host = urlparse(url).hostname or ""
    host = host.casefold()
    if host.endswith((".edu", ".gov")) or any(host == item or host.endswith(f".{item}") for item in TRUSTED_HOSTS):
        return 0
    if any(host == item or host.endswith(f".{item}") for item in COMMUNITY_HOSTS):
        return 2
    return 1


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
            return sorted(results, key=lambda item: _source_priority(item["url"]))
    except Exception as exc:
        print(f"Tavily search fallback (offline or key missing): {exc}")
        return []
