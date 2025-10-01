
import streamlit as st
import os
import difflib
from streamlit_ace import st_ace
from acda.executor import run_code_in_docker
from acda.parser import parse_error_message
from acda.solution import generate_solution, read_source_code
from acda.patcher import apply_patch
from datetime import datetime

# --- Page Config ---
st.set_page_config(
    page_title="ACDA - Autonomous Code Debugger Agent",
    layout="wide"
)

# --- Custom Styling ---
st.markdown("""
<style>
    /* Background */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(145deg, #0e1117, #161b22);
        color: #e1e4e8;
    }

    /* Headers */
    h1 {
        font-weight: 700;
        background: linear-gradient(90deg, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    h2, h3 {
        font-weight: 600;
        color: #f5f5f5;
    }

    /* Glass panels */
    .glass {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        backdrop-filter: blur(8px);
    }

    /* Buttons */
    div.stButton > button {
        border-radius: 8px;
        border: none;
        color: white;
        background: linear-gradient(90deg, #2563eb, #9333ea);
        padding: 0.7rem 1.5rem;
        font-weight: 500;
        transition: transform 0.2s ease, box-shadow 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(37, 99, 235, 0.3);
    }

    /* Logs */
    .log-box {
        background: #0d1117;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Source Code Pro', monospace;
        font-size: 14px;
        line-height: 1.5;
        color: #c9d1d9;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #21262d;
    }
    .log-line {
        color: #9ca3af;
    }
    .log-error {
        color: #f87171;
    }
    .log-success {
        color: #4ade80;
    }

    /* Diff */
    pre code.diff {
        font-size: 14px;
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("Autonomous Code Debugging Agent")
st.caption("AI-powered debugging for Python & JavaScript — sleek, modern, and professional.")

MAX_ATTEMPTS = 5

# --- Languages & Samples ---
LANGUAGES = {
    "python": {
        "file_extension": "py",
        "sample_code": """def greet_user():
    # This script fails because 'user_name' is not defined.
    message = "Hello, " + user_name
    print(message)

greet_user()"""
    },
    "javascript": {
        "file_extension": "js",
        "sample_code": """// This script fails because 'console.log' is misspelled.
function greetUser() {
    const message = "Hello, World!";
    consol.log(message);
}

greetUser();"""
    }
}

# --- Session State ---
def initialize_state():
    defaults = {
        "start_processing": False,
        "attempt": 0,
        "log_messages": [],
        "original_code": "",
        "proposed_solution": None,
        "language": "python",
        "editor_content": LANGUAGES["python"]["sample_code"],
        "prev_language": "python"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

initialize_state()

# --- Sidebar ---
with st.sidebar:
    st.header("Configuration ⚙️")
    st.session_state.language = st.selectbox(
        "Language",
        options=list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(st.session_state.language)
    )
    if st.session_state.language != st.session_state.prev_language:
        st.session_state.editor_content = LANGUAGES[st.session_state.language]["sample_code"]
        st.session_state.prev_language = st.session_state.language
        st.rerun()

# --- Main Layout ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Editor")
    with st.container():
        user_code = st_ace(
            value=st.session_state.editor_content,
            language=st.session_state.language,
            theme="monokai",
            keybinding="vscode",
            height=400,
            auto_update=True,
            key="ace_editor"
        )

    b1, b2 = st.columns([1,1])
    with b1:
        if st.button("Run Debugger", use_container_width=True):
            code_to_process = user_code if user_code != st.session_state.editor_content else st.session_state.editor_content
            st.session_state.start_processing = True
            st.session_state.attempt = 1
            st.session_state.log_messages = [f"[{datetime.now().strftime('%H:%M:%S')}] Debug session started for {st.session_state.language}"]
            st.session_state.original_code = code_to_process
            st.session_state.proposed_solution = None
            with open(f"temp_buggy_code.{LANGUAGES[st.session_state.language]['file_extension']}", "w", encoding="utf-8") as f:
                f.write(code_to_process)
            st.rerun()
    with b2:
        if st.button("Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

with col2:
    st.subheader("Logs")
    st.markdown('<div class="log-box">' + "<br>".join(st.session_state.log_messages) + "</div>", unsafe_allow_html=True)

# --- Processing ---
file_extension = LANGUAGES[st.session_state.language]["file_extension"]
TEMP_FILE_PATH = f"temp_buggy_code.{file_extension}"

if st.session_state.start_processing and st.session_state.attempt <= MAX_ATTEMPTS:
    if not st.session_state.get('proposed_solution'):
        with st.spinner("Analyzing code..."):
            st.session_state.log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {st.session_state.attempt}")
            result = run_code_in_docker(TEMP_FILE_PATH, language=st.session_state.language)

            if result['return_code'] == 0:
                st.session_state.log_messages.append(f"<span class='log-success'>[{datetime.now().strftime('%H:%M:%S')}] ✅ Code executed successfully.</span>")
                st.session_state.start_processing = False
            else:
                st.session_state.log_messages.append(f"<span class='log-error'>[{datetime.now().strftime('%H:%M:%S')}] ❌ Execution failed</span>")
                error_details = parse_error_message(result['stderr'], language=st.session_state.language)
                if not error_details:
                    st.session_state.log_messages.append("Error parsing failed.")
                    st.session_state.start_processing = False
                else:
                    st.session_state.log_messages.append(f"Error → {error_details['error_type']}: {error_details['error_message']}")
                    st.session_state.log_messages.append("Requesting fix from LLM...")
                    solution_dict = generate_solution(read_source_code(TEMP_FILE_PATH), error_details, language=st.session_state.language)
                    if not solution_dict or 'code' not in solution_dict:
                        st.session_state.log_messages.append("Solution generation failed.")
                        st.session_state.start_processing = False
                    else:
                        st.session_state.proposed_solution = solution_dict
                        st.session_state.log_messages.append("Proposed solution ready.")
        st.rerun()

# --- Solution Review ---
if st.session_state.get('proposed_solution'):
    st.subheader("Proposed Fix")
    explanation = st.session_state.proposed_solution.get('explanation', "No explanation provided.")
    st.info(explanation)

    with st.expander("Code Diff", expanded=True):
        diff_text = "".join(
            difflib.unified_diff(
                st.session_state.original_code.splitlines(keepends=True),
                st.session_state.proposed_solution['code'].splitlines(keepends=True),
                fromfile="Original",
                tofile="Proposed"
            )
        )
        st.code(diff_text, language="diff")

    a1, a2 = st.columns([1,1])
    with a1:
        if st.button("Accept & Apply", use_container_width=True):
            apply_patch(TEMP_FILE_PATH, st.session_state.proposed_solution['code'])
            st.session_state.original_code = st.session_state.proposed_solution['code']
            st.session_state.proposed_solution = None
            st.session_state.attempt += 1
            st.session_state.log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] Fix applied. Retesting...")
            st.rerun()
    with a2:
        if st.button("Reject", use_container_width=True):
            st.session_state.log_messages.append("Fix rejected. Stopping.")
            st.session_state.start_processing = False
            st.rerun()

# --- Final Result ---
if not st.session_state.start_processing and st.session_state.attempt > 0 and not st.session_state.get('proposed_solution'):
    final_code = read_source_code(TEMP_FILE_PATH)
    result = run_code_in_docker(TEMP_FILE_PATH, language=st.session_state.language)

    if result['return_code'] == 0:
        st.success("Code fixed successfully.")
        with st.expander("Final Corrected Code", expanded=True):
            st.code(final_code, language=st.session_state.language)
    else:
        st.error(f"Stopped after {st.session_state.attempt} attempts. Could not fix the code.")

    if os.path.exists(TEMP_FILE_PATH):
        os.remove(TEMP_FILE_PATH)
    if os.path.exists(TEMP_FILE_PATH + ".bak"):
        os.remove(TEMP_FILE_PATH + ".bak")














