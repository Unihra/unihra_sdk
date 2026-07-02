# Changelog

## v1.8.0 (2026-07-03)

### New Features

- **`_meta.page_status` coverage metadata** — lists requested URLs that were included in the analysis and requested URLs that were not included. Available in `analyze()`, `get_dataframe()`, segmented JSON saves, Excel reports, and MCP via `unihra_get_page_status`.
- **`InsufficientCreditsError`** — HTTP 402 (balance below the task cost) now raises a dedicated exception with the task cost in the message, instead of surfacing as a generic network error. The CLI prints a hint to run `--limits`.

### Fixes

- `ParserError` (code 1001) description clarified: a requested page was not included in the analysis.

## v1.7.1 (2026-05-09)

### Fixes

- Result normalization: the legacy `n_grams_analysis` key is renamed to `ngrams_analysis` during key normalization, so the public surface stays single-source-of-truth.

## v1.7.0 (2026-05-06)

### Breaking (backward-compatible)

- **Renamed:** `umbrella_analysis` replaces `semantic_context_analysis` as the result key for umbrella gap data. The old key is accepted as a fallback in `save_report()`, `get_dataframe()`, `analyze_and_save()`, and the MCP server.
- **Renamed:** `missing_triplets` replaces `gaps` inside `triplets_analysis`. The old key is accepted as a fallback.

### New Features

- **`get_limits()`** — check API key balance and daily limits (`GET /api/v1/key/limits`).
- **`list_analyses()`** — list all analyses saved under this API key.
- **`get_analysis(task_id)`** — fetch a previously created analysis result.
- **`share_analysis(task_id)`** — create a public share link for any analysis.
- **`unshare_analysis(task_id)`** — revoke a share link.
- **CLI `--limits` flag** — print key balance and exit without running an analysis.
- **MCP tool `unihra_get_limits`** — exposes key balance to AI assistants.
- **MCP `unihra_get_gaps` default `min_gap` lowered to `0.0`** — the API now applies adaptive thresholds; no need to filter client-side.

---

## v1.6.0

- Added Anchors analysis with `links` (href URLs) per anchor text.
- `save_report()` — new Anchors sheet with href link column.
- MCP: added `unihra_get_anchors` tool.

## v1.5.0

- Added `triplet_analysis` mode (Knowledge Graph, 5 credits).
- `save_report()` — new Triplets and Triplets Gaps sheets.
- MCP: added `unihra_get_triplets` tool.
- Streaming: surfaced triplet progress events.

## v1.4.0

- Added `queries` parameter for target-query-aware analysis.
- Added `url_cookies` for pages behind authentication.
- Added `get_page_structure()` — auto-called after every successful analysis.

## v1.3.0

- Added MCP server (`pip install "unihra[mcp]"`).
- Result local storage and segment JSON files.

## v1.2.0

- Added Excel export with color-coded styling.
- Added `get_dataframe()` for pandas integration.

## v1.1.0

- Added streaming via `analyze_stream()`.
- Added CLI (`unihra` command).

## v1.0.0

- Initial release. `analyze()`, `health()`, basic HTTP retry support.
