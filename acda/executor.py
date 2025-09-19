import docker
import os
import logging

# Setting  up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s - %(filename)s')

def run_code_in_docker(file_path: str) -> dict:
    """
    Executes a Python script within a secure, isolated Docker container.

    Args:
        file_path (str): The absolute path to the Python script to execute.

    Returns:
        dict: A dictionary containing the execution result with 'stdout', 
            'stderr', and 'return_code'.
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {"stdout": "", "stderr": f"Error: File not found at {file_path}", "return_code": -1}
        
    client = docker.from_env()
    image_name = "python:3.10-slim"
    
    absolute_file_path = os.path.abspath(file_path)
    volume_path = os.path.dirname(absolute_file_path)
    file_name = os.path.basename(absolute_file_path)

    command = f"python {file_name}"
    container = None           # Initializing  container variable to None
    
    try:
        logging.info(f"Pulling Docker image: {image_name}...")
        client.images.pull(image_name)
        
        logging.info(f"Running script '{file_name}' in a Docker container...")
    
        # detach=True runs the container in the background.
        container = client.containers.run(
            image=image_name,
            command=command,
            volumes={volume_path: {'bind': '/app', 'mode': 'rw'}},
            working_dir="/app",
            detach=True,
            remove=False 
        )

        # We wait for the container to finish and get the result 
        result = container.wait()
        return_code = result['StatusCode']

        # We fetch logs based on the exit code 
        stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
        stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
        
    except docker.errors.ImageNotFound:
        logging.error(f"Docker image '{image_name}' not found.")
        return {"stdout": "", "stderr": f"Docker image {image_name} not found.", "return_code": -1}
        
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return {"stdout": "", "stderr": str(e), "return_code": -1}

    finally:
        # The finally block ensures we ALWAYS clean up 
    
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





