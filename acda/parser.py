import re
from typing import Dict, Optional


def parse_error_message(stderr: str) -> Optional[Dict[str, str]]:
    """
    Parses a standard Python traceback from stderr to extract key information.

    This new version is more robust and handles a wider variety of runtime
    errors (like NameError, TypeError) in addition to SyntaxError.

    Args:
        stderr (str): The standard error string captured from a script execution.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing the parsed error
        details ('file_path', 'line_number', 'error_type', 'error_message')
        or None if no standard traceback is found.
    """
    if not stderr:
        return None


    # This pattern looks for the "File '...', line ..." structure and then
    # captures the last line, which is the error type and message.
    # It's designed to be flexible for different kinds of errors.
    traceback_pattern = re.compile(
        r'File "(?P<file_path>.+?)", line (?P<line_number>\d+), in .+\n(?:.+\n)*?(?P<error_type>\w+Error): (?P<error_message>.+)',
        re.DOTALL
    )

    match = traceback_pattern.search(stderr)

    # --- FALLBACK FOR SYNTAXERROR (which has a slightly different format) ---
    if not match:
        traceback_pattern = re.compile(
            r'File "(?P<file_path>.+?)", line (?P<line_number>\d+)\n(?:.+\n)?(?P<error_type>SyntaxError): (?P<error_message>.+)',
            re.DOTALL
        )
        match = traceback_pattern.search(stderr)

    if match:
        error_details = match.groupdict()
        # Clean up the error message
        error_details['error_message'] = error_details['error_message'].strip()
        return error_details

    return None


