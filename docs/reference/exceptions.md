# Exceptions

All exceptions inherit from `UnihraError`.

```python
from unihra.exceptions import (
    UnihraError,
    UnihraConnectionError,
    UnihraValidationError,
    UnihraDependencyError,
    UnihraStorageError,
    UnihraApiError,
    ParserError,
    AnalysisServiceError,
    CriticalOwnPageError,
    ReportGenerationError,
    TripletAnalysisError,
)
```

## Hierarchy

```
UnihraError
├── UnihraConnectionError     # Network / timeout failures
├── UnihraValidationError     # Bad input (empty competitors, etc.)
├── UnihraDependencyError     # Missing optional package (pandas, openpyxl)
├── UnihraStorageError        # Failed to write files in analyze_and_save()
└── UnihraApiError            # API returned an error response
    ├── ParserError           # code 1001 — a requested page was not included
    ├── AnalysisServiceError  # code 1002 — internal analysis failure
    ├── CriticalOwnPageError  # code 1003 — your own page is unreachable
    ├── ReportGenerationError # code 1004 — failed to generate the report
    └── TripletAnalysisError  # code 1005 — Knowledge Graph extraction failed
```

## Usage

```python
from unihra import UnihraClient, UnihraError
from unihra.exceptions import CriticalOwnPageError, ParserError

client = UnihraClient(api_key="YOUR_KEY")

try:
    result = client.analyze(
        own_page="https://example.com",
        competitors=["https://comp.com"],
    )
except CriticalOwnPageError:
    print("Your page is unreachable. Check the URL and try again.")
except ParserError as e:
    print(f"A requested competitor page was not included: {e}")
except UnihraError as e:
    print(f"API error: {e}")
```

## `UnihraApiError` Attributes

```python
try:
    result = client.analyze(...)
except UnihraApiError as e:
    print(e.code)     # int, e.g. 1001
    print(e.message)  # str, human-readable
    print(e.raw)      # dict, full API error payload
```

## Error Code Reference

| Code | Exception | Cause |
|------|-----------|-------|
| 1001 | `ParserError` | A requested page was not included in the analysis |
| 1002 | `AnalysisServiceError` | Internal analysis service failure |
| 1003 | `CriticalOwnPageError` | Your own page returned an error or is unreachable |
| 1004 | `ReportGenerationError` | Failed to compile the final report |
| 1005 | `TripletAnalysisError` | Knowledge Graph extraction failed |
| 9999 | `UnihraApiError` | Unknown error |
