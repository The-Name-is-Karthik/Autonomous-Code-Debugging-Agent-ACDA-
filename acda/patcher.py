import shutil
import logging
# from typing import bool

def apply_patch(file_path: str, new_code: str) -> bool:
    """
    Applies a patch to a file, creating a backup of the original.

    Args:
        file_path (str): The path to the file to be patched.
        new_code (str): The new code content to write to the file.

    Returns:
        bool: True if the patch was applied successfully, False otherwise.
    """
    backup_path = file_path + ".bak"
    try:
        # Create a backup of the original file
        shutil.copyfile(file_path, backup_path)
        logging.info(f"Created backup of original file at: {backup_path}")

        # Write the new code to the original file
        with open(file_path, 'w') as f:
            f.write(new_code)
        
        logging.info(f"Successfully applied patch to: {file_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to apply patch: {e}")
        # Optional: Restore from backup if writing fails
        shutil.copyfile(backup_path, file_path)
        return False