# UnihraClient

```python
from unihra import UnihraClient
```

## Constructor

```python
UnihraClient(
    api_key: str,
    base_url: str = "https://unihra.ru",
    max_retries: int = 0,
    storage_dir: str = "unihra_results",
)
```

| Parameter | Description |
|-----------|-------------|
| `api_key` | Your Unihra API key |
| `base_url` | Override the API base URL (for self-hosted) |
| `max_retries` | Number of HTTP retries on server errors (`429`, `5xx`) |
| `storage_dir` | Directory for `analyze_and_save()` output |

---

## Core Analysis

### `analyze()`

```python
def analyze(
    own_page: str,
    competitors: List[str],
    queries: Optional[List[str]] = None,
    lang: Literal['ru', 'en'] = 'ru',
    url_cookies: Optional[Dict[str, str]] = None,
    triplet_analysis: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]
```

Runs a full analysis and blocks until completion.

**Returns:** dict with keys `umbrella_analysis`, `block_comparison`, `ngrams_analysis`, `anchors_analysis`, `page_structure`, optionally `triplets_analysis`, and `_meta`.

---

### `analyze_stream()`

```python
def analyze_stream(
    own_page: str,
    competitors: List[str],
    queries: Optional[List[str]] = None,
    lang: str = 'ru',
    url_cookies: Optional[Dict[str, str]] = None,
    triplet_analysis: bool = False,
) -> Generator[Dict, None, None]
```

Returns a generator of SSE event dicts. Each event has a `state` key: `PENDING`, `PROCESSING`, `PROGRESS`, `SUCCESS`, or `FAILURE`.

---

### `analyze_and_save()`

```python
def analyze_and_save(**kwargs) -> Dict[str, Any]
```

Runs `analyze(**kwargs)` and saves each section as a separate JSON file under `storage_dir/{task_id}/`.

**Returns:** manifest dict with `analysis_id` and `files` (map of section → absolute path).

---

## Data Access

### `get_dataframe()`

```python
def get_dataframe(
    result: Dict[str, Any],
    section: str = "block_comparison",
) -> pd.DataFrame
```

Converts a result section to a pandas DataFrame. Requires `pandas`.

**Supported sections:**

| Section | Description |
|---------|-------------|
| `block_comparison` | Word TF-IDF data |
| `umbrella_analysis` | Umbrella gap items (old key `semantic_context_analysis` is accepted as fallback) |
| `ngrams_analysis` | N-gram phrase data |
| `anchors_analysis` | Anchor text data |
| `page_structure` | Flattened page structure |
| `triplets_analysis` | Knowledge graph — one row per fact |
| `triplets_gaps` | Missing topics — one row per gap item |

---

### `get_page_structure()`

```python
def get_page_structure(task_id: str) -> List[Dict[str, Any]]
```

Fetches page structure data from the API by task ID. Called automatically by `analyze()`.

---

## Export

### `save_report()`

```python
def save_report(
    result: Dict[str, Any],
    filename: str = "report.xlsx",
    style_output: bool = True,
) -> None
```

Saves result to `.xlsx` (multi-sheet with color coding) or `.csv` (block_comparison only). Requires `openpyxl` and `pandas`.

---

## Account & Sharing

### `get_limits()`

```python
def get_limits() -> Dict[str, Any]
```

Returns current API key limits and balance.

```python
{
    "plan": "pro",
    "daily_limit": 5000,
    "used_today": 12,
    "remaining_today": 4988,
    "rate_limit": 6000
}
```

---

### `list_analyses()`

```python
def list_analyses() -> List[Dict[str, Any]]
```

Returns all analyses saved under this API key.

---

### `get_analysis()`

```python
def get_analysis(task_id: str) -> Dict[str, Any]
```

Fetches a previously created analysis result. Analyses are retained for **90 days**.

---

### `share_analysis()`

```python
def share_analysis(task_id: str) -> Dict[str, Any]
```

Creates a public share link.

**Returns:** `{"share_url": "https://unihra.ru/s/abc123"}`

---

### `unshare_analysis()`

```python
def unshare_analysis(task_id: str) -> None
```

Revokes the share link. Returns `None` on success.

---

### `health()`

```python
def health() -> Dict[str, Any]
```

Checks API availability. Returns `{"status": "ok"}` or raises `UnihraConnectionError`.
