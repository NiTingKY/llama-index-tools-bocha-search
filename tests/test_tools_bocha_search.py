import pytest
from llama_index.core.schema import Document
from llama_index.core.tools.tool_spec.base import BaseToolSpec

from llama_index.tools.bocha_search import BochaSearchToolSpec


class MockResponse:
    def __init__(self, payload=None, status_code=200, text="OK"):
        self._payload = payload or {}
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(response=self)


def test_class():
    names_of_base_classes = [b.__name__ for b in BochaSearchToolSpec.__mro__]
    assert BaseToolSpec.__name__ in names_of_base_classes


def test_init_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("BOCHA_SEARCH_API_KEY", "env-key")

    tool = BochaSearchToolSpec()

    assert tool.api_key == "env-key"


def test_init_rejects_missing_api_key(monkeypatch):
    monkeypatch.delenv("BOCHA_SEARCH_API_KEY", raising=False)

    with pytest.raises(ValueError, match="BOCHA_SEARCH_API_KEY"):
        BochaSearchToolSpec()


def test_web_search_posts_expected_payload_and_maps_documents(monkeypatch):
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return MockResponse(
            {
                "data": {
                    "webPages": {
                        "value": [
                            {
                                "name": "Result title",
                                "url": "https://example.com/page",
                                "summary": "Useful result summary",
                                "siteName": "Example",
                                "datePublished": "2026-06-01",
                            }
                        ]
                    }
                }
            }
        )

    monkeypatch.setattr("requests.post", fake_post)

    tool = BochaSearchToolSpec(api_key="test-key", timeout=7.5)
    documents = tool.web_search(
        "llamaindex bocha",
        count=3,
        freshness="oneMonth",
        summary=False,
        include="example.com",
        exclude="spam.example",
    )

    assert calls == [
        {
            "url": "https://api.bochaai.com/v1/web-search?utm_source=ollama",
            "json": {
                "query": "llamaindex bocha",
                "freshness": "oneMonth",
                "summary": False,
                "count": 3,
                "include": "example.com",
                "exclude": "spam.example",
            },
            "headers": {
                "Authorization": "Bearer test-key",
                "Content-Type": "application/json",
            },
            "timeout": 7.5,
        }
    ]
    assert len(documents) == 1
    assert isinstance(documents[0], Document)
    assert documents[0].text == "Useful result summary"
    assert documents[0].metadata == {
        "title": "Result title",
        "url": "https://example.com/page",
        "site_name": "Example",
        "published_date": "2026-06-01",
    }


def test_web_search_supports_root_webpages_response(monkeypatch):
    def fake_post(url, json, headers, timeout):
        return MockResponse(
            {
                "webPages": {
                    "value": [
                        {
                            "title": "Root title",
                            "displayUrl": "https://example.org",
                            "snippet": "Snippet text",
                            "dateLastCrawled": "2026-06-02",
                        }
                    ]
                }
            }
        )

    monkeypatch.setattr("requests.post", fake_post)

    documents = BochaSearchToolSpec(api_key="test-key").web_search("query")

    assert documents[0].text == "Snippet text"
    assert documents[0].metadata["title"] == "Root title"
    assert documents[0].metadata["url"] == "https://example.org"
    assert documents[0].metadata["published_date"] == "2026-06-02"


def test_web_search_clamps_count(monkeypatch):
    captured_payloads = []

    def fake_post(url, json, headers, timeout):
        captured_payloads.append(json)
        return MockResponse({"data": {"webPages": {"value": []}}})

    monkeypatch.setattr("requests.post", fake_post)

    tool = BochaSearchToolSpec(api_key="test-key", max_count=8)
    assert tool.web_search("query", count=50) == []

    assert captured_payloads[0]["count"] == 8


def test_to_tool_list_exposes_web_search(monkeypatch):
    def fake_post(url, json, headers, timeout):
        return MockResponse({"data": {"webPages": {"value": []}}})

    monkeypatch.setattr("requests.post", fake_post)

    tool = BochaSearchToolSpec(api_key="test-key")
    tools = tool.to_tool_list()

    assert [tool.metadata.name for tool in tools] == ["web_search"]
    assert tools[0].call(query="llamaindex").raw_output == []
