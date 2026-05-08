# Result Sections

`client.analyze()` returns a dict with the following top-level keys.

## `umbrella_analysis`

**Umbrella gap items** — words your competitors use near the target queries that your page is missing or underuses. Scored by proximity to query terms across competitor pages.

```python
gaps = result["umbrella_analysis"]
# [
#   {
#     "lemma": "warranty",
#     "competitor_avg_score": 1.84,
#     "own_score": 0.0,
#     "gap": 1.84,
#     "coverage_percent": 75.0,
#     "recommendation": "Add to H2/H3",
#     "context_snippet": "12-month warranty included"
#   },
#   ...
# ]
```

| Field | Type | Description |
|-------|------|-------------|
| `lemma` | str | Base (lemmatized) form of the word |
| `competitor_avg_score` | float | Average proximity score across competitors |
| `own_score` | float | Score on your page (`0.0` = absent or far from query context) |
| `gap` | float | `competitor_avg_score − own_score`. Higher = more urgent |
| `coverage_percent` | float | % of competitors where this lemma appears in strong context |
| `recommendation` | str | Where to place the word: Title/H1, H2/H3, body, etc. |
| `context_snippet` | str | Example phrase from competitor pages |

Results are sorted by `gap` descending. The API applies **adaptive thresholds** — you'll always get results unless competitors genuinely don't cover the topic differently from your page.

## `block_comparison`

**TF-IDF word density comparison** — each word on competitor pages vs. your page.

```python
words = result["block_comparison"]
# [
#   {
#     "word": "warranty",
#     "lemma": "warranty",
#     "frequency": 8.3,
#     "frequency_own_page": 0,
#     "pct_target_comp_avg": -100.0,
#     "action_needed": "add",
#     "present_on_own_page": false
#   },
#   ...
# ]
```

| Field | Description |
|-------|-------------|
| `word` | Original form |
| `lemma` | Lemmatized form |
| `frequency` | Average frequency on competitor pages |
| `frequency_own_page` | Frequency on your page |
| `pct_target_comp_avg` | Density difference vs competitor average (%) |
| `action_needed` | `add` / `increase` / `decrease` / `ok` |
| `present_on_own_page` | Whether the word appears at all |

## `ngrams_analysis`

**2–3 word phrase patterns** extracted from competitor pages.

```python
ngrams = result["ngrams_analysis"]
# [
#   {
#     "ngram": "free shipping",
#     "ngram_type": "bigrams",
#     "pages_count": 4,
#     "frequency_avg": 2.5,
#     "present_on_own_page": false
#   },
#   ...
# ]
```

| Field | Description |
|-------|-------------|
| `ngram` | The phrase |
| `ngram_type` | `bigrams` (2 words) or `lemma_trigrams` (3 words) |
| `pages_count` | Number of competitor pages using this phrase |
| `frequency_avg` | Average occurrences per competitor page |
| `present_on_own_page` | Whether your page contains this exact phrase |

## `anchors_analysis`

**Link text (anchor) comparison** across all pages, including `href` URLs.

```python
anchors = result["anchors_analysis"]
# [
#   {
#     "anchor": "shop now",
#     "frequency_own": 0,
#     "frequency_comp_avg": 3.2,
#     "pages_count": 3,
#     "links": ["https://comp1.com/shop", "https://comp2.com/store"]
#   },
#   ...
# ]
```

| Field | Description |
|-------|-------------|
| `anchor` | Anchor text (lowercase) |
| `frequency_own` | Count on your page |
| `frequency_comp_avg` | Average count across competitor pages |
| `pages_count` | Number of competitor pages with this anchor |
| `links` | All unique `href` URLs where this anchor was found |

## `page_structure`

**Meta tags, headings, and content metrics** for each page (yours + all competitors).

```python
struct = result["page_structure"]
own = struct[0]  # first item is usually your page
# {
#   "url": "https://example.com/page",
#   "meta_tags": {
#     "title": "Buy Widget — Example Store",
#     "title_length": 30,
#     "description": "High-quality widgets with free shipping.",
#     "description_length": 42
#   },
#   "content": {
#     "h1_heading": "Premium Widgets",
#     "heading_structure_raw": "H1: Premium Widgets; H2: Features; H2: Shipping"
#   },
#   "metrics": {
#     "char_count_no_spaces": 4821,
#     "uniqueness_percentage": 91.3
#   }
# }
```

## `triplets_analysis` *(extended mode only)*

Available when `triplet_analysis=True`. Contains a **Knowledge Graph** extracted from all competitor pages.

```python
ta = result["triplets_analysis"]

# Top-level keys:
ta["entities"]          # List of subject entities with facts
ta["missing_triplets"]  # Topical gaps absent from your page
ta["stats"]             # Summary counts
```

### `entities`

```python
# [
#   {
#     "subject": "GPU",
#     "tier": "core",           # core / main / additional / unique
#     "triplets_count": 12,
#     "sources_count": 4,
#     "triplets": [
#       {
#         "predicate": "memory",
#         "object": "8 GB GDDR6",
#         "sources": ["comp1.com", "comp2.com"]
#       },
#       ...
#     ]
#   },
#   ...
# ]
```

**Tier meanings:**

| Tier | Description |
|------|-------------|
| `core` | Appears on 3+ competitor sources |
| `main` | Appears on 2 sources |
| `additional` | Appears on 1 source |
| `unique` | Mentioned once by a single competitor |

### `missing_triplets`

Subjects that appear on competitor pages but **not on your page**, grouped by importance:

```python
mt = ta["missing_triplets"]
mt["critical"]   # subjects on 3+ competitor sites
mt["important"]  # subjects on 2 competitor sites
mt["unique"]     # subjects on 1 competitor site
```

### `stats`

```python
ta["stats"] = {
    "total_triplets": 87,
    "sources_with_content": 5,
    "gaps_critical": 3,
    "gaps_important": 8,
    "gaps_unique": 21,
    "gaps_total": 32,
    "batches": 5
}
```

## `_meta`

```python
result["_meta"] = {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "triplet_analysis": False,
    "credits_spent": 1
}
```
