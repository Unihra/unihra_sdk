# Unihra Python SDK

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/unihra.svg?style=flat-square&color=blue)](https://pypi.org/project/unihra/)
[![Python Versions](https://img.shields.io/pypi/pyversions/unihra.svg?style=flat-square)](https://pypi.org/project/unihra/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://github.com/Unihra/unihra_sdk/blob/main/LICENSE)

**SEO and semantic analysis for your pages and competitors.**  
Compare content, surface semantic gaps, and get actionable recommendations using zone analysis and vector semantics.

English · [Русский](docs/README.ru.md)

---

### Resources

| | |
| :---: | :--- |
| **Product** | [unihra.ru](https://unihra.ru) — web interface |
| **API reference** | [unihra.ru/docs](https://unihra.ru/docs) |
| **API key** | Telegram: [@UniHRA_bot](https://t.me/UniHRA_bot) |
| **Updates** | [@mncosine](https://t.me/mncosine) |

</div>

---

## Features

- **Semantic context (zones)** — weights words by where they appear (title, H1–H6, body) and distance to your target queries, with concrete recommendations (for example, what to add to title or headings).
- **Page structure** — headings, meta tags, and content metrics for your URL and each competitor URL.
- **Word comparison (TF‑IDF)** — suggested actions per term (add, increase, decrease, ok).
- **Phrases (n‑grams)** — recurring phrases across competitor pages.
- **Vector / LSI terms (DrMaxs)** — semantically related vocabulary for the topic.
- **Cookies** — optional per‑URL cookie strings for pages behind login or gates.
- **Streaming** — the client handles the live analysis stream and waits for completion.
- **Retries** — optional HTTP retries with backoff for unstable networks.
- **Reports** — export multi‑sheet Excel reports with formatting (optional dependencies).
- **Progress** — optional progress bar in notebooks when `tqdm` is installed.

---

## Installation

```bash
pip install unihra
```

**Optional bundles** (install what you need):

| Command | Includes |
|--------|----------|
| `pip install "unihra[report]"` | Excel export (`pandas`, `openpyxl`) |
| `pip install "unihra[full]"` | Report export + progress bar (`tqdm`) |
| `pip install "unihra[mcp]"` | MCP server for Cursor / Claude Code (requires **Python 3.10+**) |

Or install pieces manually, for example: `pip install pandas openpyxl tqdm`.

---

## Quick start

### 1. Run an analysis

Pass **`queries`** — the search intents you care about — so zone recommendations and gap analysis are meaningful.

```python
from unihra import UnihraClient

client = UnihraClient(api_key="YOUR_API_KEY", max_retries=3)

result = client.analyze(
    own_page="https://example.com/my-product",
    competitors=[
        "https://competitor.com/top-product",
        "https://market-leader.com/item",
    ],
    queries=["buy widget", "best widgets 2025"],
    lang="en",
    url_cookies={
        "https://example.com/my-product": "session_id=abc123; auth=true",
    },
    verbose=True,
)

gaps = result.get("semantic_context_analysis", [])
pages = result.get("page_structure", [])

print(f"Semantic gap rows: {len(gaps)}")
for p in pages:
    print(p["url"], "—", p["meta_tags"]["title"])
```

### 2. Save an Excel report

Sheet names typically include *Page Structure*, *Semantic Gaps*, *Word Analysis*, *N‑Grams*, and vector sections.

```python
client.save_report(result, "seo_report.xlsx")
```

---

## What’s in the result

The SDK returns a **Python dictionary** aligned with the API. Keys are normalized to **snake_case**.

<details>
<summary><b>1. Page structure</b></summary>

A **list** of pages (yours first, then competitors). Each item includes:

- `url`
- `meta_tags` — `title`, `description`, etc.
- `content` — `h1_heading`, `heading_structure_raw` (heading outline as text)
- `metrics` — e.g. `char_count_no_spaces`, `uniqueness_percentage`

</details>

<details>
<summary><b>2. Semantic context analysis</b></summary>

Zone‑weighted comparison of lemmas vs your queries:

- `lemma` — base form  
- `competitor_avg_score`, `own_score` — weighted scores (0.0 on your side often means missing or weak placement)  
- `gap` — how far behind competitors you are (higher = higher priority)  
- `coverage_percent` — share of competitors using the term in a strong context  
- `context_snippet` — short example from competitors  
- `recommendation` — suggested action (e.g. add to title/H1)

```json
{
  "lemma": "battery",
  "competitor_avg_score": 10.5,
  "own_score": 0.0,
  "gap": 10.5,
  "coverage_percent": 80.0,
  "context_snippet": "long lasting battery life",
  "recommendation": "Add to Title/H1"
}
```

</details>

<details>
<summary><b>3. Block comparison (lexical)</b></summary>

TF‑IDF style comparison:

- `frequency`, `frequency_own_page`, `pct_target_comp_avg`
- `action_needed` — `add`, `increase`, `decrease`, `ok` (after normalization for English)

```json
{
  "word": "price",
  "frequency": 12.5,
  "pct_target_comp_avg": 2.5,
  "action_needed": "increase",
  "present_on_own_page": true
}
```

</details>

<details>
<summary><b>4. N‑grams</b></summary>

Phrases (bigrams / trigrams) and how many competitor pages contain them.

- `ngram`, `pages_count`, etc.

</details>

<details>
<summary><b>5. DrMaxs (vector / LSI)</b></summary>

Semantic neighbours of the topic, grouped (e.g. `by_frequency`, `by_tfidf`), with `similarity_score` and whether the word appears on your page.

```json
{
  "word": "logistics",
  "similarity_score": 0.89,
  "present_on_own_page": false
}
```

</details>

---

## Command line

```bash
python -m unihra \
  --key "YOUR_API_KEY" \
  --own "https://mysite.com" \
  --comp "https://comp1.com" \
  --comp "https://comp2.com" \
  --query "main keyword" \
  --cookies "session=secret_123" \
  --save report.xlsx \
  --verbose
```

| Option | Meaning |
|--------|---------|
| `--own` | Your page URL (required) |
| `--comp` | Competitor URL (repeat for multiple; at least one required) |
| `--query` | Target query (repeatable; recommended) |
| `--lang` | `ru` or `en` (default `ru`) |
| `--cookies` | Cookie string for your own page |
| `--save` | Write `.xlsx` or `.csv` report |
| `--retries` | HTTP retry count |
| `--verbose` | Show progress |
| `--no-style` | Plain Excel without extra styling |

You can omit `--key` if the environment variable **`UNIHRA_API_KEY`** is set.  
Without `--save` and without `--verbose`, JSON is printed to the terminal.

---

## Cursor, Claude, and other MCP clients

The optional **MCP server** lets compatible assistants call Unihra as **tools** instead of fetching pages themselves.

1. Install: `pip install "unihra[mcp]"` (Python **3.10+**).
2. Set your API key: environment variable **`UNIHRA_API_KEY`**, or pass `--key` when starting the server.
3. Start: `python -m unihra.mcp_server` or the command `unihra-mcp`.
4. Point your client’s MCP settings at that Python and module (see below).

**Large results:** the `unihra_analyze` tool returns **filtered, compact** data (plus a small `_meta` summary) so answers fit typical LLM context limits. For a full raw API‑size payload, use the Python SDK or API directly. You can adjust filter parameters exposed by the tool where needed.

**Available tools (summary)**

| Tool | Purpose |
|------|---------|
| `unihra_health` | Check that the service is reachable |
| `unihra_analyze` | Full analysis with default noise filtering |
| `unihra_analyze_stream_events` | Same run as step‑by‑step stream events (e.g. to read `task_id`) |
| `unihra_get_page_structure` | Fetch heading/meta report for a finished `task_id` |
| `unihra_get_gaps` | Re‑group semantic gaps from an existing result |
| `unihra_get_vectors` | LSI / vector terms from an existing result |
| `unihra_get_word_actions` | TF‑IDF words grouped by action |
| `unihra_get_ngrams` | Phrase list from an existing result |

**Example MCP configuration** (adjust paths to your Python executable):

```json
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

Optional: `examples/mcp_server_usage.py` prints a sample config and shows how to launch the server locally.

---

<div align="center">

**Unihra Team**

[Telegram — news](https://t.me/mncosine) · [unihra.ru](https://unihra.ru) · [API key — @UniHRA_bot](https://t.me/UniHRA_bot)

</div>
