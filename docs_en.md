# Unihra API — Documentation
![Version](https://img.shields.io/badge/API-v1.4.0-blue?style=flat-square) ![Uptime](https://img.shields.io/badge/Uptime-99.9%25-green?style=flat-square)

**Unihra API** is a tool for semantic content analysis. It compares your page against competitors across lexicon, n-grams, anchors, and zonal coverage — and in extended mode builds a **knowledge graph** (triplets: subject → predicate → object) from competitor texts, highlighting content gaps on your page.

---

## 📚 Table of Contents
- [🚀 Access & Authentication](#-access--authentication)
- [🏗 Integration Architecture](#-integration-architecture)
- [🛠 API Methods](#-api-methods)
  - [1. Create Task (POST)](#1-create-task-post)
  - [2. Monitor Status (GET / SSE)](#2-monitor-status-get--sse)
  - [3. Page Structure (GET)](#3-page-structure-get)
- [📊 Response Structure](#-response-structure)
  - [Block Comparison — Lexicon](#block-comparison--lexicon)
  - [N-grams Analysis — Phrases](#n-grams-analysis--phrases)
  - [Anchors Analysis — Anchors](#anchors-analysis--anchors)
  - [Semantic Context Analysis — Zonal Analysis](#semantic-context-analysis--zonal-analysis)
  - [Triplets Analysis — Knowledge Graph 🆕](#triplets-analysis--knowledge-graph-)
- [🛑 Error Codes & Limits](#-error-codes--limits)
- [📝 Changelog](#-changelog)

---

## 🚀 Access & Authentication

API keys are created in your personal dashboard at [unihra.ru](https://unihra.ru) (section **Keys**). Each user may have up to 5 keys.

All API requests require the header:

```http
Authorization: Bearer unh_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Base URL:** `https://unihra.ru/api/v1`

---

## 🏗 Integration Architecture

Semantic analysis is resource-intensive. The API operates **asynchronously**:

1. **Create task** → `POST /process` → receive `task_id`.
2. **Processing** → task is queued; typical time: 15–60 sec (longer with triplets).
3. **Get result** → `GET /process/status/{task_id}` (SSE stream).
4. **Technical audit** → `GET /report/structure/{task_id}` — meta tags and page headings.

---

## 🛠 API Methods

### 1. Create Task (POST)

`POST /process`

#### Request Body Parameters (JSON)

| Parameter | Type | Required | Description | Limits |
| :--- | :--- | :---: | :--- | :--- |
| `own_page` | `string` | **Yes** | URL of your target page. | Must return HTTP 200. |
| `competitor_urls` | `string[]` | **Yes** | Array of competitor URLs. | 1–**20** URLs. |
| `queries` | `string[]` | No | Key phrases for analysis. | Up to **5** phrases, ≤ 1000 chars each. |
| `lang` | `string` | No | Analysis language. | `"ru"` or `"en"` (default `"ru"`). |
| `url_cookies` | `object` | No | Cookies for private pages. | Format: `{"URL": "cookie_string"}`. |
| `triplet_analysis` | `boolean` | No | Enable triplets analysis (5 credits). | Default `false` (1 credit). |

**Cost:**
- Standard analysis (`triplet_analysis: false`) → **1 credit**
- Extended analysis with triplets (`triplet_analysis: true`) → **5 credits**

#### Example Request

```json
{
  "own_page": "https://mysite.com/page",
  "competitor_urls": [
    "https://competitor1.com/page",
    "https://competitor2.com/page"
  ],
  "queries": ["insulation for exterior walls"],
  "lang": "en",
  "triplet_analysis": true,
  "url_cookies": {
    "https://mysite.com/page": "session_id=abc123"
  }
}
```

#### Response (200)

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status_url": "/api/v1/process/status/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 2. Monitor Status (GET / SSE)

`GET /process/status/{task_id}`

Supports **SSE (Server-Sent Events)**. Each message is JSON.

#### Progress Frame Format

```json
{
  "state": "PROGRESS",
  "progress": 45,
  "details": {
    "step": "parsing_complete",
    "message": "Pages fetched, starting analysis..."
  }
}
```

#### Progress Steps

| Step | Standard | With Triplets |
| :--- | :---: | :---: |
| `parsing` | 5% | 5% |
| `parsing_complete` | 45% | 30% |
| `analyzing` | 60% | 40% |
| `generating_report` | 95% | 55% |
| `triplet_analysis` | — | 65% |
| `SUCCESS` | 100% | 100% |

#### Final Frame (SUCCESS)

```json
{
  "state": "SUCCESS",
  "progress": 100,
  "result": { ... }
}
```

#### Error Frame

```json
{
  "state": "FAILURE",
  "progress": 0,
  "error": { "code": 1003, "message": "Could not fetch target page." }
}
```

After receiving `SUCCESS` or `FAILURE`, the stream is closed by the server — no need to reopen it.

---

### 3. Page Structure (GET)

`GET /report/structure/{task_id}`

Technical report for each page in the task (meta tags, headings, metrics).

```json
[
  {
    "url": "https://mysite.com/page",
    "meta_tags": {
      "title": "Mineral Wool Insulation — Buy Wholesale",
      "title_length": 42,
      "description": "...",
      "description_length": 148
    },
    "content": {
      "h1_heading": "Mineral Wool for Insulation",
      "heading_structure_raw": "H1: Mineral Wool; H2: Specifications; H2: Applications"
    },
    "metrics": {
      "char_count_no_spaces": 5200,
      "uniqueness_percentage": 71.3
    }
  }
]
```

---

## 📊 Response Structure

### Block Comparison — Lexicon

Compares word/lemma frequency (TF-IDF) between your page and competitors.

```json
[
  {
    "word": "insulation",
    "lemma": "insulation",
    "frequency_own_page": 3,
    "pct_target_comp_avg": 4.7,
    "action_needed": "Add",
    "present_on_own_page": false
  }
]
```

| Field | Description |
| :--- | :--- |
| `pct_target_comp_avg` | Density difference (%) between average competitor and your page. |
| `action_needed` | Recommendation: `"Add"`, `"Remove"`, `"OK"`. |
| `present_on_own_page` | `false` — word is absent from your page. |

---

### N-grams Analysis — Phrases

Stable bigrams and trigrams appearing across competitor pages.

```json
[
  {
    "ngram": "basalt mineral wool",
    "ngram_type": "lemma_trigrams",
    "pages_count": 9,
    "present_on_own_page": false
  }
]
```

`ngram_type`: `"bigrams"` or `"lemma_trigrams"`.

---

### Anchors Analysis — Anchors

Analysis of link texts (`<a>` tags). Shows how competitors use internal and external linking.

```json
[
  {
    "anchor": "insulation catalog",
    "frequency_own": 0,
    "frequency_comp_avg": 6.2,
    "pages_count": 11,
    "links": [
      "https://comp1.com/catalog",
      "https://comp2.com/insulation"
    ]
  }
]
```

The `links` field is an array of unique `href` values from `<a>` tags with this anchor text, collected across all analyzed pages. May be empty `[]`.

---

### Semantic Context Analysis — Zonal Analysis

Zonal weight algorithm: considers lemma placement in headings, density, and proximity to the target query.

```json
[
  {
    "lemma": "vapor permeability",
    "competitor_avg_score": 9.8,
    "own_score": 0.0,
    "gap": 9.8,
    "coverage_percent": 78.0,
    "context_snippet": "vapor permeability of basalt wool",
    "recommendation": "Add to Title/H1"
  }
]
```

| Field | Description |
| :--- | :--- |
| `gap` | Difference between competitors' average score and yours. |
| `coverage_percent` | Share of competitors mentioning this lemma (%). |
| `context_snippet` | Example context snippet from competitor texts. |
| `recommendation` | Where to add: `Title/H1`, `H2`, `Body`, etc. |

---

### Triplets Analysis — Knowledge Graph 🆕

> Available only when `triplet_analysis: true` (5 credits).

Extracts **facts and statements** from competitor texts in the form **subject → predicate → object** and compares them to your page, identifying topical coverage gaps.

#### Response Structure

```json
{
  "entities": [
    {
      "subject": "Mineral Wool",
      "triplets_count": 14,
      "sources_count": 7,
      "tier": "core",
      "triplets": [
        {
          "predicate": "does not burn",
          "object": "yes",
          "sources": ["comp1.com", "comp2.com", "comp3.com"]
        },
        {
          "predicate": "operating temperature",
          "object": "up to 700°C",
          "sources": ["comp1.com", "comp4.com"]
        }
      ]
    }
  ],
  "gaps": {
    "critical": [ ... ],
    "important": [ ... ],
    "unique": [ ... ]
  },
  "stats": {
    "total_triplets": 412,
    "sources_with_content": 10,
    "gaps_critical": 5,
    "gaps_important": 18,
    "gaps_unique": 51,
    "gaps_total": 74,
    "batches": 2
  }
}
```

#### entities[] Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `subject` | `string` | Entity/topic being described (triplet subject). |
| `tier` | `string` | Entity importance: `core` → `main` → `additional` → `unique`. |
| `triplets_count` | `number` | Total number of extracted facts. |
| `sources_count` | `number` | Number of sources mentioning this entity. |
| `triplets[].predicate` | `string` | Relationship or attribute. |
| `triplets[].object` | `string` | Value or description. |
| `triplets[].sources` | `string[]` | Source domains (without `www.`). |

#### gaps{} Fields

Contains subjects **absent from your page**, grouped by frequency across competitor sources:

| Key | Criterion |
| :--- | :--- |
| `critical` | Topic appears in **3 or more** sources. |
| `important` | Topic appears in **2** sources. |
| `unique` | Topic appears in **1** source. |

---

## 🛑 Error Codes & Limits

### HTTP Codes

| Code | Description | Resolution |
| :--- | :--- | :--- |
| `400` | Bad Request | Invalid JSON, exceeded URL limit (20) or queries (5). |
| `401` | Unauthorized | Invalid or revoked API key. |
| `429` | Too Many Requests | Rate limit exceeded for your plan. |
| `500` | Internal Error | Internal server error. |

### Internal Codes (in `error.code` field)

| Code | Cause |
| :--- | :--- |
| `1001` | Parser error: failed to fetch one or more competitor pages. |
| `1002` | Analysis service temporarily unavailable. |
| `1003` | Critical error: target page (`own_page`) is unreachable or blocked. |
| `1004` | Report generation failure. |
| `1005` | Triplets analysis failure. |
| `9999` | Unknown internal error. |

---

## 📝 Changelog

### v1.4.0 — Triplets Analysis (2026-04-25)
- Added `triplet_analysis` parameter (`bool`, default `false`)
- New response section `Triplets Analysis`: knowledge graph, content gaps, statistics
- Extended analysis cost: 5 credits
- Internal error code `1005` for triplet analysis failures
- Removed DrMaxs module (vector LSI analysis)

### v1.2.0 — Anchor Links Support (2026-04-04)
- Added `links` field to `Anchors Analysis`
- Each anchor now includes an array of unique `href` values from `<a>` tags
- Backward compatible: `links` field is optional

### v1.3.5
- Stability improvements and performance optimizations
