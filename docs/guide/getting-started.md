# Getting Started

Unihra SDK is the official Python client for the [Unihra API](https://unihra.ru). It lets you compare your page against competitors, find content gaps with Umbrella Analysis, and extract knowledge graphs — all from a few lines of Python.

## Prerequisites

- Python **3.8+**
- An Unihra API key — get one in the [dashboard](https://unihra.ru/dashboard) under "API Keys"

## Quick Example

```python
from unihra import UnihraClient

client = UnihraClient(api_key="YOUR_KEY")

result = client.analyze(
    own_page="https://example.com/product",
    competitors=[
        "https://competitor1.com/page",
        "https://competitor2.com/page",
    ],
    queries=["buy product online", "best product 2026"],
    lang="en",
    verbose=True,
)

# Umbrella Analysis — words to add to your page
for gap in result.get("umbrella_analysis", [])[:5]:
    print(f"{gap['lemma']:20s}  gap={gap['gap']:.2f}  → {gap['recommendation']}")
```

## What You Get

A single `result` dict with these sections:

| Key | Description |
|-----|-------------|
| `umbrella_analysis` | Umbrella gap items — lemmas to add, with zone recommendations |
| `block_comparison` | TF-IDF word density comparison (add / increase / decrease / ok) |
| `ngrams_analysis` | 2–3 word phrase patterns used by competitors |
| `anchors_analysis` | Anchor texts with their `href` URLs |
| `page_structure` | Meta title, H1–H6 outline, content volume per page |
| `_meta.page_status` | Requested URL coverage: included and not included |
| `triplets_analysis` | Knowledge graph: entities, facts, topical gaps *(extended mode only)* |
| `_meta` | Task ID, credits spent, analysis mode |

## Next Steps

- [Installation →](./installation) — extras, optional dependencies
- [Running Analysis →](./analysis) — all parameters explained
- [Result Sections →](./result-sections) — what each field means
