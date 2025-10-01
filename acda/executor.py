import docker
import os
import logging

# --- Constants ---
LANGUAGE_CONFIGS = {
    "python": {
        "image": "python:3.10-slim",
        "command": "python"
    },
    "javascript": {
        "image": "node:18-slim",
        "command": "node"
    }
}

# Setting up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_code_in_docker(file_path: str, language: str = "python") -> dict:
    """
    Executes a script in a secure, isolated Docker container based on the language.

    Args:
        file_path (str): The path to the script to execute.
        language (str): The programming language ('python' or 'javascript').

    Returns:
        dict: A dictionary with 'stdout', 'stderr', and 'return_code'.
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {"stdout": "", "stderr": f"Error: File not found at {file_path}", "return_code": -1}

    if language not in LANGUAGE_CONFIGS:
        logging.error(f"Unsupported language: {language}")
        return {"stdout": "", "stderr": f"Unsupported language: {language}", "return_code": -1}

    client = docker.from_env()
    config = LANGUAGE_CONFIGS[language]
    image_name = config["image"]

    absolute_file_path = os.path.abspath(file_path)
    volume_path = os.path.dirname(absolute_file_path)
    file_name = os.path.basename(absolute_file_path)

    command = f"{config['command']} {file_name}"
    container = None

    try:
        logging.info(f"Pulling Docker image: {image_name}...")
        client.images.pull(image_name)
        
        logging.info(f"Running {language} script '{file_name}' in a Docker container...")
        container = client.containers.run(
            image=image_name,
            command=command,
            volumes={volume_path: {'bind': '/app', 'mode': 'rw'}},
            working_dir="/app",
            detach=True,
            remove=False
        )

        result = container.wait()
        return_code = result['StatusCode']

        stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
        stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
        
    except docker.errors.ImageNotFound:
        logging.error(f"Docker image '{image_name}' not found.")
        return {"stdout": "", "stderr": f"Docker image {image_name} not found.", "return_code": -1}
        
    except Exception as e:
        logging.error(f"An unexpected error occurred during Docker execution: {e}")
        return {"stdout": "", "stderr": str(e), "return_code": -1}

    finally:
        if container:
            try:
                container.remove()
                logging.info(f"Successfully removed container {container.short_id}.")
            except docker.errors.APIError as e:
                logging.warning(f"Could not remove container {container.short_id}: {e}")

    return {
        "stdout": stdout,
        "stderr": stderr,
        "return_code": return_code
    }














