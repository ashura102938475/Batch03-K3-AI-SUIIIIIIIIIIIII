from __future__ import annotations

from typing import Any
from companion.tavily_search import tavily_search_external_citations


def tavily_search_tool(query: str, max_results: int = 3) -> dict[str, Any]:
    """Search Tavily for external documentation & web citations."""
    results = tavily_search_external_citations(query=query, max_results=max_results)
    return {
        "count": len(results),
        "query": query,
        "results": results,
    }
