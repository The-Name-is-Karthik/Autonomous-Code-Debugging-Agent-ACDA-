import re
from typing import Dict, Optional, Callable

def _parse_python_error(stderr: str) -> Optional[Dict[str, str]]:
    """
    Parses a standard Python traceback to extract file path, line number,
    error type, and error message. It's designed to be robust for
    multi-line stack traces and different error types like SyntaxError.
    """
    if not stderr:
        return None

    stack_trace = stderr.strip()

    # More robust pattern for runtime errors (NameError, TypeError, etc.)
    # It captures the last file path and line number before the error.
    traceback_pattern = re.compile(
        r'.*File "(?P<file_path>.+?)", line (?P<line_number>\d+).*\n(?:.*\n)*?(?P<error_type>\w+Error): (?P<error_message>.+)',
        re.DOTALL
    )
    match = traceback_pattern.search(stack_trace)

    if match:
        error_details = match.groupdict()
        error_details['stack_trace'] = stack_trace
        error_details['error_message'] = error_details['error_message'].strip()
        return error_details
    
    # Fallback for SyntaxError, which has a different format
    syntax_error_pattern = re.compile(
        r'File "(?P<file_path>.+?)", line (?P<line_number>\d+)\n(?:.*\n)?^\s*(?P<error_type>SyntaxError): (?P<error_message>.+)',
        re.MULTILINE | re.DOTALL
    )
    match = syntax_error_pattern.search(stack_trace)
    if match:
        error_details = match.groupdict()
        error_details['stack_trace'] = stack_trace
        error_details['error_message'] = error_details['error_message'].strip()
        return error_details
    
    return None

def _parse_javascript_error(stderr: str) -> Optional[Dict[str, str]]:
    """
    Parses a standard Node.js error traceback to extract file path, line number,
    error type, and error message.
    """
    if not stderr:
        return None

    stack_trace = stderr.strip()

    # Pattern for standard runtime errors (ReferenceError, TypeError, etc.)
    error_pattern = re.compile(
        r"^(?P<file_path>.+?):(?P<line_number>\d+)\n(?:.*\n)*?(?P<error_type>\w+Error): (?P<error_message>.+)",
        re.MULTILINE
    )
    match = error_pattern.search(stack_trace)

    if match:
        error_details = match.groupdict()
        error_details['stack_trace'] = stack_trace
        error_details['error_message'] = error_details['error_message'].strip()
        return error_details

    return None


# --- Language to Parser Mapping ---
PARSER_MAPPING: Dict[str, Callable[[str], Optional[Dict[str, str]]]] = {
    "python": _parse_python_error,
    "javascript": _parse_javascript_error,
}

def parse_error_message(stderr: str, language: str = "python") -> Optional[Dict[str, str]]:
    """
    Routes the stderr to the appropriate language-specific parser.
    Now provides the full stack trace for better context.
    """
    if not stderr:
        return None

    parser = PARSER_MAPPING.get(language)
    if not parser:
        return None

    return parser(stderr)








