# Running Analysis

## Basic Call

```python
result = client.analyze(
    own_page="https://example.com/page",
    competitors=["https://comp1.com", "https://comp2.com"],
)
```

## All Parameters

```python
result = client.analyze(
    own_page: str,                          # Your page URL (required)
    competitors: List[str],                 # Competitor URLs — 3-10 recommended (required)
    queries: Optional[List[str]] = None,    # Target search queries (up to 5)
    lang: Literal['ru', 'en'] = 'ru',      # Page language
    url_cookies: Optional[Dict[str, str]] = None,  # Per-URL auth cookies
    triplet_analysis: bool = False,         # Enable Knowledge Graph (5 credits)
    verbose: bool = False,                  # Show tqdm progress bar
)
```

### `queries` — Target Queries

::: tip Why queries matter
Queries define which words are used as **anchor points** for the Umbrella Analysis. All query lemmas are combined and used to locate contextually important words on each page. Without queries, the umbrella analysis has no anchor points and may return fewer or no results.
:::

```python
result = client.analyze(
    own_page="https://example.com/mattress",
    competitors=["https://comp1.com/mattress", "https://comp2.com/sleep"],
    queries=[
        "buy mattress online",
        "orthopedic mattress 180x200",
        "best spring mattress",
    ],
)
```

Up to **5 queries**. Longer is better — the more target queries, the more coverage points in the HTML.

### `lang`

Affects lemmatization and corpus used for frequency analysis.

| Value | Language |
|-------|----------|
| `'ru'` | Russian (default) |
| `'en'` | English |

When `lang='en'`, action values in `block_comparison` are returned in English (`add`, `increase`, `decrease`, `ok`).

### `url_cookies`

For pages behind authentication or geo-gates:

```python
url_cookies = {
    "https://example.com/private-page": "session=abc123; region=us",
    "https://comp.com/restricted": "auth=xyz",
}
```

### `triplet_analysis`

Standard mode (1 credit) covers lexical analysis. Extended mode (5 credits) additionally extracts a **Knowledge Graph** from all competitor pages:

```python
result = client.analyze(
    own_page=..., competitors=...,
    triplet_analysis=True,  # adds triplets_analysis to result
)
```

Use extended mode when you need:
- Fact-level content brief (which entities and properties competitors cover)
- E-E-A-T / completeness audit
- Topical gap analysis at entity level (critical / important / unique)

## Analysis Duration

| Mode | Typical Duration |
|------|-----------------|
| Standard | 30–90 seconds |
| Extended (triplets) | 60–180 seconds |

Duration depends on page size, number of competitors, and server load.

## Credits

| Mode | Credits |
|------|---------|
| Standard | 1 credit per analysis |
| Extended | 5 credits per analysis |

Check your balance before running expensive analyses:

```python
limits = client.get_limits()
print(f"Remaining today: {limits['remaining_today']}")
```

## Retry on Network Errors

```python
client = UnihraClient(api_key="YOUR_KEY", max_retries=3)
```

Retries on status codes `429`, `500`, `502`, `503`, `504` with exponential backoff.
