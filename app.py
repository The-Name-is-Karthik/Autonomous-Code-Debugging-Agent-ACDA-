import streamlit as st
import os
import time
from acda.executor import run_code_in_docker
from acda.parser import parse_error_message
from acda.solution import generate_solution, read_source_code
from acda.patcher import apply_patch

# --- Page Configuration ---
st.set_page_config(
    page_title="Autonomous Code Debugging Agent",
    layout="wide"
)

# --- App Title and Description ---
st.title(" Autonomous Code Debugging Agent (ACDA)")
st.write(
    "This AI agent can autonomously diagnose and fix syntax and runtime errors in Python code. "
    "Paste your buggy code below and watch the agent work."
)

# --- Agent Configuration ---
MAX_ATTEMPTS = 5

# --- UI Components ---
st.header("Enter Your Buggy Python Code")

# default buggy code for demo
sample_code = """
def greet_user():
  # This script fails because 'user_name' is not defined.
  message = "Hello, " + user_name
  print(message)

greet_user()
"""

code_input = st.text_area("Code Editor", value=sample_code, height=300, key="code_editor")

if st.button(" Fix My Code", use_container_width=True):
    
    # Create a temporary file to work with
    temp_file_path = "temp_buggy_code.py"
    with open(temp_file_path, "w", encoding="utf-8") as f:
        f.write(code_input)

    st.header("Agent's Log")
    status_placeholder = st.empty()
    log_placeholder = st.empty()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        status_placeholder.info(f" **Attempt #{attempt}**")
        log_placeholder.text(f"Executing code...")
        time.sleep(1)

        # 1. EXECUTE
        result = run_code_in_docker(temp_file_path)

        if result['return_code'] == 0:
            status_placeholder.success(" **Code Fixed Successfully!**")
            final_code = read_source_code(temp_file_path)
            log_placeholder.success("The code executed without errors.")
            st.balloons()
            
            st.header("Corrected Code")
            st.code(final_code, language="python")
            break

        # 2. PARSE
        log_placeholder.text("Execution failed. Parsing error...")
        time.sleep(1)
        error_details = parse_error_message(result['stderr'])
        
        if not error_details:
            status_placeholder.error(" **Agent Failed**")
            log_placeholder.error("Could not parse the error message. Stopping.")
            break

        log_placeholder.text(f"Parsed Error: {error_details['error_type']} - {error_details['error_message']}")
        time.sleep(1)
        
        # 3. GENERATE SOLUTION
        log_placeholder.text("Generating solution with the LLM...")
        source_code = read_source_code(temp_file_path)
        solution = generate_solution(source_code, error_details)
        
        if not solution:
            status_placeholder.error(" **Agent Failed**")
            log_placeholder.error("LLM failed to generate a solution. Stopping.")
            break
        
        # 4. APPLY PATCH
        log_placeholder.text("Applying the patch...")
        apply_patch(temp_file_path, solution)
        time.sleep(1)

    else: # If the loop finishes without success
        status_placeholder.error(" **Agent Stopped**")
        log_placeholder.warning(f"Could not fix the code after {MAX_ATTEMPTS} attempts.")

    # Clean up the temporary files
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
    if os.path.exists(temp_file_path + ".bak"):
        os.remove(temp_file_path + ".bak")
