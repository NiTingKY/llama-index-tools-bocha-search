import os
from typing import Any, Dict, List, Optional

import requests
from llama_index.core.schema import Document
from llama_index.core.tools.tool_spec.base import BaseToolSpec

DEFAULT_BOCHA_SEARCH_API_URL = "https://api.bochaai.com/v1/web-search?utm_source=ollama"


class BochaSearchToolSpec(BaseToolSpec):
    """Bocha Web Search tool spec."""

    spec_functions = ["web_search"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        default_count: int = 10,
        max_count: int = 20,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the Bocha Web Search tool.

        Args:
            api_key: Bocha API key. Defaults to BOCHA_SEARCH_API_KEY.
            api_url: Bocha web-search endpoint. Defaults to BOCHA_SEARCH_API_URL
                or the public Bocha web-search endpoint.
            default_count: Default number of search results to request.
            max_count: Maximum allowed result count.
            timeout: HTTP request timeout in seconds.

        """
        api_key = api_key or os.getenv("BOCHA_SEARCH_API_KEY")
        if not api_key or not api_key.strip():
            raise ValueError(
                "BochaSearchToolSpec requires an API key. Pass api_key or set "
                "BOCHA_SEARCH_API_KEY."
            )

        if default_count < 1:
            raise ValueError("default_count must be greater than zero")
        if max_count < 1:
            raise ValueError("max_count must be greater than zero")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self.api_key = api_key
        self.api_url = (
            api_url or os.getenv("BOCHA_SEARCH_API_URL") or DEFAULT_BOCHA_SEARCH_API_URL
        )
        self.default_count = min(default_count, max_count)
        self.max_count = max_count
        self.timeout = timeout

    def web_search(
        self,
        query: str,
        count: Optional[int] = None,
        freshness: str = "noLimit",
        summary: bool = True,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
    ) -> List[Document]:
        """
        Search the web with Bocha and return source-linked LlamaIndex documents.

        Args:
            query: Search query.
            count: Number of results to return. Clamped to max_count.
            freshness: Bocha freshness filter. Defaults to "noLimit".
            summary: Whether Bocha should return summaries when supported.
            include: Optional pipe-delimited allow-list domains.
            exclude: Optional pipe-delimited deny-list domains.

        Returns:
            A list of Document objects containing Bocha search results.

        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")

        result_count = self._clamp_count(count)
        payload: Dict[str, Any] = {
            "query": query,
            "freshness": freshness,
            "summary": summary,
            "count": result_count,
        }
        if include is not None:
            payload["include"] = include
        if exclude is not None:
            payload["exclude"] = exclude

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", "unknown")
            response_text = getattr(exc.response, "text", "")
            raise RuntimeError(
                f"Bocha web search failed with HTTP {status_code}: {response_text}"
            ) from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"Bocha web search request failed: {exc}") from exc

        return self._documents_from_response(response.json())

    def _clamp_count(self, count: Optional[int]) -> int:
        if count is None:
            count = self.default_count
        if count < 1:
            raise ValueError("count must be greater than zero")
        return min(count, self.max_count)

    def _documents_from_response(self, payload: Dict[str, Any]) -> List[Document]:
        web_pages = payload.get("data", {}).get("webPages") or payload.get("webPages")
        results = []
        if isinstance(web_pages, dict):
            results = web_pages.get("value") or []

        documents: List[Document] = []
        for result in results:
            title = result.get("name") or result.get("title") or ""
            url = result.get("url") or result.get("displayUrl") or ""
            text = (
                result.get("summary")
                or result.get("snippet")
                or result.get("description")
                or title
                or url
            )
            published_date = (
                result.get("datePublished") or result.get("dateLastCrawled") or ""
            )

            documents.append(
                Document(
                    text=text,
                    metadata={
                        "title": title,
                        "url": url,
                        "site_name": result.get("siteName") or "",
                        "published_date": published_date,
                    },
                )
            )

        return documents
