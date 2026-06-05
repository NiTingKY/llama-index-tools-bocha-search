# LlamaIndex Bocha Search Tool

LlamaIndex ToolSpec integration for [Bocha Web Search](https://bochaai.com/).

This package exposes Bocha search as a native LlamaIndex tool, so agents can call
web search through `BochaSearchToolSpec().to_tool_list()`.

## Installation

```bash
pip install llama-index-tools-bocha-search
```

For local development:

```bash
uv sync
uv run -- pytest
```

## Usage

Set your Bocha API key:

```bash
export BOCHA_SEARCH_API_KEY="your-api-key"
```

Windows PowerShell:

```powershell
$env:BOCHA_SEARCH_API_KEY = "your-api-key"
```

Create LlamaIndex tools:

```python
from llama_index.tools.bocha_search import BochaSearchToolSpec

bocha_spec = BochaSearchToolSpec()
tools = bocha_spec.to_tool_list()
```

Use the tool with a LlamaIndex agent:

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from llama_index.tools.bocha_search import BochaSearchToolSpec

agent = FunctionAgent(
    name="search_agent",
    description="An agent that can search the web with Bocha.",
    llm=OpenAI(model="gpt-4o-mini"),
    tools=BochaSearchToolSpec().to_tool_list(),
    system_prompt="Use web search when current source-linked information is needed.",
)

response = await agent.run("What changed in LlamaIndex this week?")
```

## Configuration

`BochaSearchToolSpec` accepts these parameters:

- `api_key`: Bocha API key. Defaults to `BOCHA_SEARCH_API_KEY`.
- `api_url`: Bocha web-search endpoint. Defaults to `BOCHA_SEARCH_API_URL` or
  `https://api.bochaai.com/v1/web-search?utm_source=ollama`.
- `default_count`: Default number of results, clamped by `max_count`.
- `max_count`: Maximum number of results the tool can request.
- `timeout`: HTTP timeout in seconds.

The `web_search` tool accepts:

- `query`
- `count`
- `freshness`
- `summary`
- `include`
- `exclude`

Results are returned as LlamaIndex `Document` objects with source metadata:
`title`, `url`, `site_name`, and `published_date`.

## MCP

If you already run a Bocha MCP server, LlamaIndex can consume it through
`llama-index-tools-mcp`. This package is for the native ToolSpec path, matching
other LlamaIndex search integrations such as Brave, DuckDuckGo, Exa, and Tavily.
