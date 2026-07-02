# Saving & Export

Requires `pip install "unihra[report]"` (pandas + openpyxl).

## Excel Report

```python
client.save_report(result, "report.xlsx")
```

Generates a multi-sheet workbook:

| Sheet | Content |
|-------|---------|
| **Anchors** | Anchor text analysis with frequency and href links |
| **Parsed Pages** | URLs included in the analysis |
| **Failed Pages** | Requested URLs not included in the analysis |
| **Page Structure** | Meta titles, H1, headings, content volume |
| **Umbrella Gaps** | Umbrella analysis — lemmas to add with recommendations |
| **Word Analysis** | TF-IDF words with action labels |
| **N-Grams** | Phrase patterns |
| **Triplets** | Knowledge graph entities and facts *(if triplet_analysis=True)* |
| **Triplets Gaps** | Missing topics by severity *(if triplet_analysis=True)* |

Color coding is applied automatically:
- 🔴 Red — word/anchor absent from your page
- 🟢 Green — word/anchor present on your page
- 🟠 Amber — important / main tier in triplets

### Disable Styling

```python
client.save_report(result, "report.xlsx", style_output=False)
```

## CSV Report

Exports only `block_comparison` (word analysis) to CSV:

```python
client.save_report(result, "report.csv")
```

## Pandas DataFrame

```python
# Requires pandas: pip install "unihra[report]"

df_gaps    = client.get_dataframe(result, "umbrella_analysis")
df_words   = client.get_dataframe(result, "block_comparison")
df_ngrams  = client.get_dataframe(result, "ngrams_analysis")
df_anchors = client.get_dataframe(result, "anchors_analysis")
df_parsed  = client.get_dataframe(result, "parsed_pages")
df_failed  = client.get_dataframe(result, "failed_pages")
df_struct  = client.get_dataframe(result, "page_structure")

# Triplets (extended mode only)
df_entities = client.get_dataframe(result, "triplets_analysis")
df_gaps_t   = client.get_dataframe(result, "triplets_gaps")
```

::: tip Backward compatibility
`umbrella_analysis` replaces the old `semantic_context_analysis` key. Both are accepted by `get_dataframe()`.
:::

## Save Raw JSON (Segmented)

Splits the result into separate JSON files per section:

```python
manifest = client.analyze_and_save(
    own_page="https://example.com",
    competitors=["https://comp.com"],
)
# {
#   "analysis_id": "550e8400-...",
#   "files": {
#     "gaps":      "/path/to/550e8400-.../gaps.json",
#     "words":     "/path/to/.../words.json",
#     "ngrams":    "/path/to/.../ngrams.json",
#     "anchors":   "/path/to/.../anchors.json",
#     "triplets":  "/path/to/.../triplets.json",
#     "structure": "/path/to/.../structure.json"
#   }
# }

print(manifest["files"]["gaps"])
```

Files are saved to `./unihra_results/{task_id}/` by default. Change it:

```python
client = UnihraClient(api_key="YOUR_KEY", storage_dir="/data/seo_results")
```
