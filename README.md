# 🛠️ Unihra Python SDK

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/unihra.svg?style=flat-square&color=blue)](https://pypi.org/project/unihra/)
[![Python Versions](https://img.shields.io/pypi/pyversions/unihra.svg?style=flat-square)](https://pypi.org/project/unihra/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://github.com/Unihra/unihra_sdk/blob/main/LICENSE)

**Enterprise-grade SEO & Semantic Analysis SDK.**<br>
*Compare content, find semantic gaps, and generate structure recommendations using Vector AI & Zone Analysis.*

[🇬🇧 English](#-english-documentation) | [🇷🇺 Русский](docs/README.ru.md)

---

### 🚀 Ecosystem & Resources

| **Web UI** | **API Docs** | **Get API Key** | **News Channel** |
| :---: | :---: | :---: | :---: |
| 🖥️ [**unihra.ru**](https://unihra.ru) | 📚 [**unihra.ru/docs**](https://unihra.ru/docs) | 🔑 [**@UniHRA_bot**](https://t.me/UniHRA_bot) | 📢 [**@mncosine**](https://t.me/mncosine) |
| *Visual Sandbox* | *REST API Spec* | *Get Free Key Here* | *Updates & Tips* |

</div>

---

## 🇬🇧 English Documentation

### ✨ Key Features

*   **🧠 Semantic Context Analysis**: Goes beyond simple keyword frequency. It analyzes HTML zones (`H1`, `Title`, `Strong`) and the distance of terms to your target query to provide "Add to Title/H1" recommendations.
*   **🏗️ Page Structure Analysis**: Automatically extracts and compares H1-H6 headers, Meta Tags, and Technical uniqueness metrics for **all** analyzed pages (Own + Competitors).
*   **🍪 Authorized Content Support**: Pass custom cookies to analyze pages behind login walls or age verification.
*   **⚡️ SSE Streaming Abstraction**: Automatically handles server-sent events, queue polling, and connection stability.
*   **🐼 Pandas & Excel Ready**: Export multi-sheet reports (`.xlsx`) with conditional formatting in one line of code.
*   **🛡️ Smart Retries**: Built-in exponential backoff strategy for network resilience.
*   **🪐 Jupyter Native**: Interactive HTML progress bars for Notebook environments.

### 📦 Installation

```bash
pip install unihra
```
*Optional: Install dependencies for Excel export and progress bars:*
```bash
pip install pandas openpyxl tqdm
```

### ⚡️ Quick Start

#### 1. Full Analysis with Context
To enable Zone Analysis and Gap detection, you must provide `queries` (the main keywords you want to rank for).

```python
from unihra import UnihraClient

# Initialize client
client = UnihraClient(api_key="YOUR_API_KEY", max_retries=3)

# Run Analysis
result = client.analyze(
    own_page="https://example.com/my-product",
    competitors=[
        "https://competitor.com/top-product", 
        "https://market-leader.com/item"
    ],
    queries=["buy widget", "best widgets 2025"], # <--- Required for Structure Recommendations
    lang="en",
    # Optional: Pass cookies for specific URLs (e.g. for staging or private content)
    url_cookies={
        "https://example.com/my-product": "session_id=abc123; auth=true"
    },
    verbose=True # Shows interactive progress bar
)

# Access the data
gaps = result.get('semantic_context_analysis', [])
structures = result.get('page_structure', [])

print(f"Found {len(gaps)} semantic gaps.")

# Print titles of all analyzed pages
for page in structures:
    print(f"URL: {page['url']}")
    print(f"Title: {page['meta_tags']['title']}\n")
```

#### 2. Export to Excel
Generate a professional SEO report with multiple sheets: *Page Structure*, *Semantic Gaps*, *Word Analysis*, *N-Grams*, and *Vectors*.

```python
client.save_report(result, "seo_report.xlsx")
```

### 📊 Data Model & Internals

The SDK returns a Python dictionary mirroring the API response. Here is a breakdown of each logic block:

<details>
<summary><b>1. Page Structure</b></summary>

Returns a **List** of objects (for your page and all competitors). Each object contains:

*   `url`: Page URL.
*   `meta_tags`: Dictionary with `title`, `description`, etc.
*   `content`: Dictionary with `h1_heading`, `heading_structure_raw` (all headers).
*   `metrics`: Dictionary with `char_count_no_spaces`, `uniqueness_percentage`.

</details>

<details>
<summary><b>2. Semantic Context Analysis (Zone Analysis)</b></summary>

**This is the most critical part of the analysis.** It calculates a weighted score based on *where* a word appears (Title > H1 > H2 > Text) and *how close* it is to the target query.

*   `lemma`: The base form of the word.
*   `competitor_avg_score`: The weighted score of this word across top competitors.
*   `own_score`: Your weighted score. If `0.0`, the word is missing or used in a very weak zone (e.g., footer).
*   `gap`: The difference between competitors and you. Higher gap = higher priority.
*   `coverage_percent`: Percentage of competitors that use this word in a significant context.
*   `context_snippet`: A 3-word phrase (trigram) showing how competitors use this word.
*   `recommendation`: Actionable advice based on the gap (e.g., *"Add to Title/H1"*, *"Add to H2/H3"*, *"Mention in Body"*).

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
<summary><b>3. Block Comparison (Lexical Analysis)</b></summary>

Classical TF-IDF comparison. Useful for finding over-optimization (spam) or general content relevancy.

*   `frequency`: Weighted frequency (TF).
*   `frequency_own_page`: How many times it appears on your page.
*   `pct_target_comp_avg`: Average density (%) on competitor pages.
*   `action_needed`: Simple recommendation (`add`, `increase`, `decrease`, `ok`).

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
<summary><b>4. N-grams Analysis (Phrases)</b></summary>

Analyzes stable word combinations (Bigrams and Trigrams).

*   `ngram`: The phrase (e.g., "fast delivery").
*   `pages_count`: On how many competitor sites this exact phrase appears.

</details>

<details>
<summary><b>5. DrMaxs (Vector AI)</b></summary>

Uses Neural Network Embeddings to find **Latent Semantic Indexing (LSI)** words. These are words that are semantically close to your topic but might not be direct synonyms.

*   `by_frequency`: Most frequent semantically related words.
*   `by_tfidf`: Most unique/important semantically related words.
*   `similarity_score`: Cosine similarity to the topic vector (0.0 to 1.0).

```json
{
  "word": "logistics",
  "similarity_score": 0.89,
  "present_on_own_page": false
}
```
</details>

### 💻 CLI Usage

You can use the SDK directly from your terminal.

```bash
# Run analysis and save to Excel
python -m unihra \
  --key "YOUR_KEY" \
  --own "https://mysite.com" \
  --comp "https://comp1.com" \
  --comp "https://comp2.com" \
  --query "main keyword" \
  --cookies "session=secret_123" \
  --save report.xlsx \
  --verbose
```

### 🤖 MCP Server (Model Context Protocol)

The SDK ships an optional **MCP server** so tools like **Cursor** or **Claude Code** can call Unihra analysis over the [Model Context Protocol](https://modelcontextprotocol.io/). It wraps the same `UnihraClient` as the rest of the package; core SDK usage is unchanged if you do not install the extra.

**Requirements:** Python **3.10+** and the `mcp` extra (the `mcp` PyPI package is only resolved on supported Python versions).

```bash
pip install "unihra[mcp]"
```

**Run** (API key via flag or `UNIHRA_API_KEY`):

```bash
python -m unihra.mcp_server --key YOUR_API_KEY
# or
export UNIHRA_API_KEY=YOUR_API_KEY
python -m unihra.mcp_server
```

The package also exposes the console entry point `unihra-mcp` (same behavior as `python -m unihra.mcp_server`).

**Optional flags:** `--retries` (HTTP retries, default `3`), `--base-url` (override API base URL, default `https://unihra.ru`).

**Tools:** `unihra_health`, `unihra_analyze`, `unihra_analyze_stream_events`, `unihra_get_page_structure`, `unihra_extract_section`, `unihra_summarize_gaps`, `unihra_summarize_vectors`, `unihra_word_actions`.

**Example MCP config** (Cursor / Claude Code–style):

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

A small helper that prints this JSON and shows how to start the server locally: `examples/mcp_server_usage.py`.

**Russian documentation** (full guide, including MCP): [docs/README.ru.md](docs/README.ru.md).

---

<div align="center">
    <p>Developed with ❤️ by <b>Unihra Team</b></p>
    <p>
        <a href="https://t.me/mncosine">Telegram News</a> • 
        <a href="https://unihra.ru">Web Service</a> • 
        <a href="https://t.me/UniHRA_bot">Get API Key Bot</a>
    </p>
</div>