## Summary

Bocha Web Search is now available as an external LlamaIndex ToolSpec package:

https://github.com/NiTingKY/llama-index-tools-bocha-search

The package follows the external-integration guidance in this repository's
CONTRIBUTING.md instead of adding a new integration package to the monorepo.

## What it provides

- Package name: `llama-index-tools-bocha-search`
- Import path: `llama_index.tools.bocha_search`
- ToolSpec: `BochaSearchToolSpec`
- Tool exposed to agents: `web_search`
- Auth: `api_key` parameter or `BOCHA_SEARCH_API_KEY`
- Optional endpoint override: `BOCHA_SEARCH_API_URL`
- Result type: LlamaIndex `Document` objects with source metadata:
  `title`, `url`, `site_name`, and `published_date`

## Usage

```python
from llama_index.tools.bocha_search import BochaSearchToolSpec

tools = BochaSearchToolSpec().to_tool_list()
```

## Verification

The package has local coverage for:

- API key loading and missing-key errors
- Bocha request payload and authorization headers
- Defensive response mapping for both `data.webPages.value` and `webPages.value`
- Result count clamping
- LlamaIndex `to_tool_list()` conversion and tool invocation

Commands run locally:

```bash
uv run -- ruff check .
uv run -- pytest tests -q
uv build
```

Results:

- `ruff`: all checks passed
- `pytest`: 7 passed
- `uv build`: generated wheel and sdist successfully

A mocked LlamaIndex tool-call smoke test also confirmed that `to_tool_list()`
exposes `web_search` and returns a `Document` result through the ToolSpec path.

I could not run a live Bocha API smoke test in this environment because
`BOCHA_SEARCH_API_KEY` was not configured.

## Question

Is there a preferred place in LlamaIndex docs or examples to reference external
ToolSpec packages like this one, now that new integration packages are maintained
outside the monorepo?
