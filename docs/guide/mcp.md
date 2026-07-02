# MCP Server

Unihra ships a built-in **MCP (Model Context Protocol) server** that lets AI assistants — Cursor, Claude Desktop, or any MCP-compatible client — run SEO analyses and query results without any manual setup.

## Installation

```bash
pip install "unihra[mcp]"   # requires Python 3.10+
```

## Cursor / Claude Desktop Config

Add to your MCP configuration file:

::: code-group

```json [Claude Desktop]
{
  "mcpServers": {
    "unihra": {
      "command": "python",
      "args": ["-m", "unihra.mcp_server"],
      "env": {
        "UNIHRA_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

```json [Cursor]
{
  "mcpServers": {
    "unihra": {
      "command": "python",
      "args": ["-m", "unihra.mcp_server", "--key", "YOUR_KEY_HERE"]
    }
  }
}
```

:::

## Available Tools

| Tool | Description |
|------|-------------|
| `unihra_health` | Check API availability |
| `unihra_get_limits` | Show API key balance and daily limits |
| `unihra_analyze` | Run SEO analysis (standard or extended) |
| `unihra_list_results` | List saved analysis results |
| `unihra_delete_result` | Delete a saved result |
| `unihra_get_page_status` | List requested URLs included in the analysis and not included |
| `unihra_get_gaps` | Get Umbrella Analysis gaps with optional filtering |
| `unihra_get_anchors` | Get anchor analysis |
| `unihra_get_word_actions` | Get TF-IDF word actions (add/increase/decrease) |
| `unihra_get_ngrams` | Get phrase patterns |
| `unihra_get_triplets` | Get Knowledge Graph entities and gaps *(extended mode)* |
| `unihra_get_page_structure` | Get heading structure and meta tags |

## How It Works

1. You tell the AI: *"Compare my page X with competitors Y and Z"*
2. The AI calls `unihra_analyze` — analysis runs server-side (30–120 seconds)
3. A compact summary is returned immediately with a `result_id`
4. The AI calls specific `unihra_get_*` tools to retrieve focused data slices

Results are saved locally in `~/.unihra_mcp/results/` and persist between sessions.

## Cost Awareness

The AI is instructed to use **standard mode (1 credit)** by default and escalate to **extended mode (5 credits)** only when you explicitly ask for Knowledge Graph analysis or fact-level content briefs. Use `unihra_get_limits` to check your balance.

## Manual Start

```bash
UNIHRA_API_KEY=your_key python -m unihra.mcp_server

# With options:
python -m unihra.mcp_server \
  --key YOUR_KEY \
  --retries 3 \
  --results-dir /tmp/unihra_results
```

## Example Prompts

```
"Compare https://mysite.com/product with https://comp1.com and https://comp2.com"
"What words should I add to my page to rank for 'buy mattress online'?"
"Do a fact coverage audit — what entities do competitors cover that I miss?"
"Show me the heading structure of all analyzed pages"
```
