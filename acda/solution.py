import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from typing import Dict, Optional

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API client
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    logging.info("Google AI API configured successfully.")
except ValueError as e:
    logging.error(e)
    

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



def generate_solution(code_content: str, error_details: Dict[str, str]) -> Optional[str]:
    """
    Generates a corrected code solution using the Gemini LLM.

    Args:
        code_content (str): The full source code of the buggy script.
        error_details (Dict[str, str]): The parsed details of the error.

    Returns:
        Optional[str]: The corrected code block as a string, or None if an error occurs.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')


    prompt = f"""
    You are an expert Python programmer and an automated debugging assistant.
    Your task is to fix a single error in the provided Python script.

    **Context:**
    The script failed with the following error:
    - Error Type: {error_details['error_type']}
    - Line Number: {error_details['line_number']}
    - Error Message: {error_details['error_message']}

    **Buggy Code:**
    ```python
    {code_content}
    ```

    **Instructions:**
    1. Analyze the error and the provided code.
    2. Provide the fully corrected Python code.
    3. IMPORTANT: Your response must ONLY contain the raw code. Do not include explanations, apologies, or any markdown like ```python.

    **Corrected Code:**
    """

    try:
        logging.info("Generating solution with Gemini...")
        response = model.generate_content(prompt)
        
        # Clean up the response to ensure it's just code
        corrected_code = response.text.strip()
        
        # A simple check to remove markdown code blocks if the LLM adds them
        if corrected_code.startswith("```python"):
            corrected_code = corrected_code[len("```python"):].strip()
        if corrected_code.endswith("```"):
            corrected_code = corrected_code[:-len("```")].strip()
            
        return corrected_code
    
    except Exception as e:
        logging.error(f"Failed to generate solution from LLM: {e}")
        return None