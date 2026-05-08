# CLI

The `unihra` command-line tool lets you run analysis and manage your account without writing Python.

## Installation

```bash
pip install "unihra[full]"
```

## Check Balance

```bash
unihra --key YOUR_KEY --limits
```

```json
{
  "plan": "pro",
  "daily_limit": 5000,
  "used_today": 12,
  "remaining_today": 4988
}
```

## Run Analysis

```bash
unihra \
  --key YOUR_KEY \
  --own https://example.com/product \
  --comp https://comp1.com/product \
  --comp https://comp2.com/product \
  --query "buy product online" \
  --query "best product 2026" \
  --lang en \
  --verbose
```

## Save to Excel

```bash
unihra \
  --own https://example.com/product \
  --comp https://comp1.com \
  --query "target keyword" \
  --save report.xlsx \
  --verbose
```

## Extended Analysis (Knowledge Graph)

```bash
unihra \
  --own https://example.com \
  --comp https://comp1.com \
  --comp https://comp2.com \
  --triplets \
  --save report_extended.xlsx \
  --verbose
```

## Dump JSON to stdout

```bash
unihra --own https://example.com --comp https://comp.com | jq '.umbrella_analysis[:5]'
```

## All Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--key` | API key (`UNIHRA_API_KEY` env var also works) | — |
| `--own` | Your page URL | required |
| `--comp` | Competitor URL (repeatable) | required |
| `--query` | Target query (repeatable, up to 5) | — |
| `--lang` | Language: `ru` or `en` | `ru` |
| `--cookies` | Auth cookies for own page: `"session=abc"` | — |
| `--save` | Output filename: `.xlsx` or `.csv` | stdout JSON |
| `--triplets` | Enable Knowledge Graph (5 credits) | off |
| `--limits` | Show key balance and exit | — |
| `--verbose` | Show progress and summary | off |
| `--no-style` | Disable Excel color coding | off |
| `--retries` | HTTP retry count | `0` |

## Environment Variable

```bash
export UNIHRA_API_KEY="your_key_here"
unihra --own https://example.com --comp https://comp.com --verbose
```
