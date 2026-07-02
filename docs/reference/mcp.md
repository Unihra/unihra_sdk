# MCP Tools Reference

## `unihra_health`

Check API availability.

**Input:** *(none)*

**Output:** `{"status": "ok", "version": "..."}`

---

## `unihra_get_limits`

Show API key usage limits and balance.

**Input:** *(none)*

**Output:**
```json
{
  "plan": "pro",
  "daily_limit": 5000,
  "used_today": 12,
  "remaining_today": 4988
}
```

---

## `unihra_analyze`

Run SEO analysis. **Primary tool** — the model should call this first for any page comparison request.

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `own_page` | string | ✅ | Your page URL |
| `competitors` | string[] | ✅ | Competitor URLs (3–10 recommended) |
| `queries` | string[] | — | Target search queries (up to 5) |
| `lang` | `"ru"` \| `"en"` | — | Page language |
| `url_cookies` | object | — | Per-URL auth cookies |
| `triplet_analysis` | boolean | — | Enable Knowledge Graph (5 credits, default `false`) |

**Output:** Compact summary with `result_id` + top-5 gaps, action counts, missing n-grams, and structure snapshot.

---

## `unihra_list_results`

List all saved analysis results in the current session directory.

**Input:** *(none)*

**Output:** `{"count": N, "results": [{"result_id": "...", "own_page": "...", "saved_at": "...", ...}]}`

---

## `unihra_delete_result`

Delete a saved result from disk.

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `result_id` | string | ✅ | From `unihra_analyze` or `unihra_list_results` |

---

## `unihra_get_page_status`

Get requested URL coverage for a saved analysis. The tool returns only public
page lists: URLs included in the analysis and URLs not included.

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `result_id` | string | ✅ | From `unihra_analyze` |

**Output:**
```json
{
  "result_id": "abc123",
  "parsed_count": 1,
  "failed_count": 1,
  "parsed": [{"url": "https://example.com", "is_own_page": true}],
  "failed": [{"url": "https://competitor.example", "is_own_page": false}]
}
```

---

## `unihra_get_gaps`

Get Umbrella Analysis gaps — words to add to your page.

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `result_id` | string | required | — |
| `top_n` | integer | `50` | Max items to return |
| `min_coverage` | number | `15.0` | Min competitor coverage % |
| `min_gap` | number | `0.0` | Min gap score (0 = show all) |
| `missing_only` | boolean | `false` | Only words absent from own page |
| `group_by_recommendation` | boolean | `false` | Group by placement recommendation |

---

## `unihra_get_anchors`

Get anchor text analysis.

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `result_id` | string | required | — |
| `top_n` | integer | `50` | Max items |
| `missing_only` | boolean | `false` | Only anchors absent from own page |

---

## `unihra_get_word_actions`

Get TF-IDF word actions (add / increase / decrease / ok).

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `result_id` | string | required | — |
| `action` | `"add"` \| `"increase"` \| `"decrease"` \| `"ok"` \| `"all"` | `"all"` | Filter by action |
| `top_n` | integer | `50` | Max items per group |
| `min_frequency` | number | `1.0` | Min word frequency |
| `exclude_ok` | boolean | `true` | Exclude ok-action words |

---

## `unihra_get_ngrams`

Get phrase (n-gram) analysis.

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `result_id` | string | required | — |
| `top_n` | integer | `60` | Max phrases |
| `min_pages_count` | integer | `2` | Min competitor sites using this phrase |
| `missing_only` | boolean | `false` | Only phrases not on own page |
| `ngram_type` | `"all"` \| `"bigrams"` \| `"lemma_trigrams"` | `"all"` | Filter by phrase length |

---

## `unihra_get_triplets`

Get Knowledge Graph entities and topical gaps. **Only available for results created with `triplet_analysis=true`.**

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `result_id` | string | required | — |
| `view` | `"entities"` \| `"gaps"` \| `"both"` | `"both"` | Which view to return |
| `top_entities` | integer | `30` | Max entities |
| `max_triplets_per_entity` | integer | `12` | Max facts per entity |
| `tiers` | string[] | `["core","main"]` | Filter entities by tier |
| `gap_severities` | string[] | `["critical","important"]` | Gap severity buckets to include |
| `max_gaps_per_severity` | integer | `25` | Max gap items per bucket |

---

## `unihra_get_page_structure`

Get heading structure and meta tags.

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `result_id` | string | required | — |
| `own_only` | boolean | `false` | Return only your page structure |
