# CLI Reference

## Synopsis

```
unihra [--key KEY] [--limits] [--own URL] [--comp URL]... [OPTIONS]
```

## Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--key` | str | `$UNIHRA_API_KEY` | API key |
| `--limits` | flag | off | Print key balance and exit |
| `--own` | str | required | Your page URL |
| `--comp` | str (repeatable) | required | Competitor URL (pass multiple times) |
| `--query` | str (repeatable) | — | Target search query (up to 5) |
| `--lang` | `ru`\|`en` | `ru` | Page language |
| `--cookies` | str | — | Auth cookies for own page: `"session=abc; token=xyz"` |
| `--save` | str | stdout | Output file: `.xlsx` or `.csv` |
| `--triplets` | flag | off | Enable Knowledge Graph mode (5 credits) |
| `--verbose` | flag | off | Show progress and result summary |
| `--no-style` | flag | off | Disable Excel color coding and auto-widths |
| `--retries` | int | `0` | HTTP retry attempts on network/server errors |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | API or network error |
| `0` | User interrupted (Ctrl+C) |

## Examples

```bash
# Check balance
unihra --key sk-xxx --limits

# Minimal analysis — outputs JSON to stdout
unihra --own https://example.com --comp https://comp.com

# Full analysis with Excel report
unihra \
  --own https://example.com/product \
  --comp https://comp1.com/product \
  --comp https://comp2.com/product \
  --query "buy product" \
  --query "best product 2026" \
  --lang en \
  --save report.xlsx \
  --verbose

# Knowledge Graph
unihra --own https://example.com --comp https://comp.com --triplets --save kg.xlsx

# Pipe to jq
unihra --own https://example.com --comp https://comp.com | jq '.umbrella_analysis[:10]'
```
