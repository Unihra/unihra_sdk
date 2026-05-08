# Sharing Analyses

You can create a public share link for any analysis and revoke it at any time.

## Create a Share Link

```python
share = client.share_analysis(task_id="550e8400-e29b-41d4-a716-446655440000")
print(share["share_url"])
# https://unihra.ru/s/abc123xyz
```

The `task_id` is in `result["_meta"]["task_id"]` after `analyze()`.

## Revoke a Share Link

```python
client.unshare_analysis(task_id="550e8400-e29b-41d4-a716-446655440000")
# Returns None on success
```

## List All Your Analyses

```python
analyses = client.list_analyses()
# [
#   {
#     "task_id": "550e8400-...",
#     "created_at": "2026-05-06T12:00:00Z",
#     "own_page": "https://example.com",
#     "triplet_analysis": false,
#     "share_url": null
#   },
#   ...
# ]
```

## Fetch a Saved Analysis

If an analysis was run earlier (even from the web UI), you can retrieve it:

```python
data = client.get_analysis(task_id="550e8400-e29b-41d4-a716-446655440000")
```

Returns the same structure as `analyze()`.

## Full Workflow Example

```python
from unihra import UnihraClient

client = UnihraClient(api_key="YOUR_KEY")

# 1. Run analysis
result = client.analyze(
    own_page="https://example.com/product",
    competitors=["https://comp1.com", "https://comp2.com"],
    queries=["buy product", "best product 2026"],
)

task_id = result["_meta"]["task_id"]

# 2. Save report locally
client.save_report(result, "report.xlsx")

# 3. Share with a colleague
share = client.share_analysis(task_id)
print(f"Share link: {share['share_url']}")

# 4. Later — revoke access
client.unshare_analysis(task_id)
```

::: info Task metadata retention
Analysis metadata (parameters, result pointer) is stored in Redis for **90 days** from creation. After that, `get_analysis()` will return 404.
:::
