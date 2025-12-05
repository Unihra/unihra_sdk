from typing import Optional, Any

class UnihraError(Exception):
    """Base class for all Unihra exceptions."""
    pass

class UnihraConnectionError(UnihraError):
    """Network errors, timeouts, or API unavailability."""
    pass

class UnihraValidationError(UnihraError):
    """Client-side validation errors (e.g. empty lists)."""
    pass

class UnihraDependencyError(UnihraError):
    """Raised when optional dependencies (pandas, openpyxl) are missing."""
    pass

class UnihraApiError(UnihraError):
    """Errors returned by the API."""
    def __init__(self, message: str, code: Optional[int] = None, details: Any = None):
        self.code = code
        self.details = details
        super().__init__(f"[{code}] {message}" if code else message)

class ParserError(UnihraApiError):
    """Code 1001: Failed to download/parse the target page."""
    pass

class AnalysisServiceError(UnihraApiError):
    """Code 1002: Internal analysis engine failure."""
    pass

class CriticalOwnPageError(UnihraApiError):
    """Code 1003: Your page is unavailable (404/500)."""
    pass

class ReportGenerationError(UnihraApiError):
    """Code 1004: Failed to generate the report."""
    pass

# Mapping specific business logic errors from API codes
ERROR_CODE_MAP = {
    1001: ParserError,
    1002: AnalysisServiceError,
    1003: CriticalOwnPageError,
    1004: ReportGenerationError,
}

def raise_for_error_code(code: int, message: str, details: Any = None):
    exc_class = ERROR_CODE_MAP.get(code, UnihraApiError)
    raise exc_class(message, code, details)