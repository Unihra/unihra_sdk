# Streaming

`analyze_stream()` returns a generator that yields Server-Sent Events as Python dicts. Use it when you want real-time progress without blocking.

## Basic Usage

```python
for event in client.analyze_stream(
    own_page="https://example.com",
    competitors=["https://comp.com"],
    queries=["target query"],
):
    state = event.get("state")

    if state == "PROGRESS":
        pct = event.get("progress", 0)
        msg = event.get("details", {}).get("message", "")
        print(f"[{pct:3d}%] {msg}")

    elif state == "SUCCESS":
        result = event["result"]
        print("Done!", result.keys())
        break

    elif state == "FAILURE":
        print("Error:", event.get("error"))
        break
```

## Event States

| State | Description |
|-------|-------------|
| `PENDING` | Task queued, not started yet |
| `PROCESSING` | Analysis running |
| `PROGRESS` | Progress update with `progress` (0–100) and `details.message` |
| `SUCCESS` | Analysis complete — `event["result"]` contains the full result |
| `FAILURE` | Error — `event["error"]` contains `code` and `message` |

## Progress Details

```python
event = {
    "state": "PROGRESS",
    "progress": 45,
    "details": {
        "step": "analysis_internal",
        "message": "Computing TF-IDF vectors"
    }
}
```

## Example: Custom Progress Bar

```python
from unihra import UnihraClient

client = UnihraClient(api_key="YOUR_KEY")

total = 0
for event in client.analyze_stream("https://mysite.com", ["https://comp.com"]):
    if event.get("state") == "PROGRESS":
        pct = event.get("progress", 0)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r[{bar}] {pct}%", end="", flush=True)
    elif event.get("state") == "SUCCESS":
        print("\nComplete!")
        result = event["result"]
        break
```

::: warning Note
`analyze()` is a convenience wrapper around `analyze_stream()` that blocks until `SUCCESS` and optionally shows a `tqdm` progress bar. Use `analyze_stream()` directly for custom UIs, async wrappers, or long-running pipelines.
:::
