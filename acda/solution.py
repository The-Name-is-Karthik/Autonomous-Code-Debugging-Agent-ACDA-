import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import hashlib
import json
from typing import Dict, Optional

# --- Constants ---
CACHE_DIR = ".acda_cache"

# --- Prompt Configuration ---
PROMPT_CONFIG = {
    "python": {
        "expert_role": "Python programmer",
        "code_lang": "python"
    },
    "javascript": {
        "expert_role": "JavaScript programmer",
        "code_lang": "javascript"
    }
}

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    logging.info("Google AI API configured successfully.")
except ValueError as e:
    logging.error(e)

# --- Caching Functions ---
def _get_cache_key(code_content: str, error_details: Dict[str, str], language: str) -> str:
    """Creates a unique SHA-256 hash for the code, error, and language combination."""
    error_string = json.dumps(error_details, sort_keys=True)
    return hashlib.sha256((code_content + error_string + language).encode()).hexdigest()

def _read_from_cache(key: str) -> Optional[Dict[str, str]]:
    """Reads a solution from the cache if it exists."""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                logging.info(f"Cache hit! Reading solution from {cache_file}")
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"Could not read or parse cache file {cache_file}: {e}")
    return None

def _write_to_cache(key: str, solution: Dict[str, str]):
    """Writes a solution to the cache."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        with open(cache_file, 'w') as f:
            json.dump(solution, f)
            logging.info(f"Cache miss. Writing solution to {cache_file}")
    except IOError as e:
        logging.error(f"Could not write to cache file {cache_file}: {e}")

# --- File I/O ---
def read_source_code(file_path: str) -> Optional[str]:
    """Reads the full content of a specified file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Source code file not found at: {file_path}")
        return None
    except Exception as e:
        logging.error(f"Error reading source code file: {e}")
        return None

# --- LLM Solution Generation ---
def generate_solution(code_content: str, error_details: Dict[str, str], language: str = "python") -> Optional[Dict[str, str]]:
    """
    Generates a corrected code solution using the LLM, with caching and language support.
    """
    cache_key = _get_cache_key(code_content, error_details, language)
    cached_solution = _read_from_cache(cache_key)
    if cached_solution:
        return cached_solution

    logging.info(f"Cache miss. Generating {language} solution with the LLM...")
    
    config = PROMPT_CONFIG.get(language, PROMPT_CONFIG["python"]) # Default to Python config
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    You are an expert {config['expert_role']} and an automated debugging assistant.
    Your task is to fix a single error in the provided script and explain the fix.

    **Example 1: Python NameError**
    Buggy Code:
    ```python
    def greet():
        message = "Hello, " + name
        print(message)
    greet()
    ```
    Explanation:
    The error is a `NameError` because the variable 'name' was used before it was assigned a value. The fix is to define the `name` variable with a string literal before it is used in the message.
    ---
    Corrected Code:
    ```python
    def greet():
        name = "Alice"
        message = "Hello, " + name
        print(message)
    greet()
    ```

    **Example 2: JavaScript TypeError**
    Buggy Code:
    ```javascript
    function add(a, b) {{
        return a + b;
    }}
    add("1", 2);
    ```
    Explanation:
    The error is a `TypeError` because you cannot implicitly convert types in this operation. The fix is to ensure both arguments are numbers, for instance by parsing the string argument with `parseInt`.
    ---
    Corrected Code:
    ```javascript
    function add(a, b) {{
        return a + b;
    }}
    add(parseInt("1"), 2);
    ```

    **Context:**
    The script failed with the following error:
    - Error Type: {error_details['error_type']}
    - Line Number: {error_details['line_number']}
    - Error Message: {error_details['error_message']}

    **Buggy Code:**
    ```{config['code_lang']}
    {code_content}
    ```

    **Instructions:**
    1. Analyze the error and the provided code.
    2. Provide a brief, one-paragraph explanation of the fix.
    3. Use '---' as a separator between the explanation and the code.
    4. Provide the fully corrected {config['code_lang']} code.
    5. IMPORTANT: Your response must ONLY contain the explanation, the separator, and the raw code. Do not include apologies or any markdown formatting for the code block.

    **Explanation:**
    ---
    **Corrected Code:**
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if "---" in response_text:
            explanation, corrected_code = response_text.split("---", 1)
        else:
            explanation = "The LLM did not provide an explanation in the expected format."
            corrected_code = response_text

        explanation = explanation.replace("Explanation:", "").strip()
        corrected_code = corrected_code.replace("Corrected Code:", "").strip()
        
        # Clean up markdown code blocks, if any
        lang_tag = f"```{config['code_lang']}"
        if corrected_code.startswith(lang_tag):
            corrected_code = corrected_code[len(lang_tag):].strip()
        if corrected_code.endswith("```"):
            corrected_code = corrected_code[:-len("```")].strip()
            
        solution = {"explanation": explanation, "code": corrected_code}
        
        _write_to_cache(cache_key, solution)
        
        return solution
    
    except Exception as e:
        logging.error(f"Failed to generate solution from LLM: {e}")
        return None



















