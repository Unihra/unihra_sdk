# Installation

## Minimal (core only)

```bash
pip install unihra
```

Includes: `analyze()`, `analyze_stream()`, `get_page_structure()`, `share_analysis()`, CLI.  
No heavy dependencies — just `requests`.

## With Report Export

```bash
pip install "unihra[report]"
```

Adds `pandas` + `openpyxl` — required for `save_report()` (Excel) and `get_dataframe()`.

## Full (recommended)

```bash
pip install "unihra[full]"
```

Adds `pandas` + `openpyxl` + `tqdm` — enables the progress bar in `analyze(verbose=True)`.

## With MCP Server

```bash
pip install "unihra[mcp]"
```

Requires Python **3.10+**. Adds the MCP server for AI assistant integrations (Cursor, Claude Desktop).

## All Extras

```bash
pip install "unihra[full,mcp]"
```

## Verify Installation

```bash
python -c "import unihra; print(unihra.__version__)"
# 1.7.0
```

## Environment Variable

Set your API key once instead of passing it each time:

```bash
export UNIHRA_API_KEY="your_key_here"   # Linux / macOS
set UNIHRA_API_KEY=your_key_here        # Windows CMD
$env:UNIHRA_API_KEY = "your_key_here"  # Windows PowerShell
```

Then in Python:

```python
import os
from unihra import UnihraClient

client = UnihraClient(api_key=os.getenv("UNIHRA_API_KEY"))
```
