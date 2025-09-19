import os
from acda.executor import run_code_in_docker
from acda.parser import parse_error_message
from acda.solution import read_source_code, generate_solution
from acda.patcher import apply_patch 

# --- Agent Configuration ---
MAX_ATTEMPTS = 5 

def main():
    """
    The main entry point for the Autonomous Code Debugging Agent.
    """
    print("-----Starting Autonomous Code Debugging Agent-----")
    
    script_path = os.path.join("tests", "buggy_scripts", "syntax_error.py")
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n----- Attempt #{attempt} -----")
        print(f"Analyzing file: {script_path}")
        
        # 1. EXECUTE the code
        result = run_code_in_docker(script_path)
        
        
        if result['return_code'] == 0:
            print("\nAnalysis: Script executed successfully. No errors found.")
            print("----- ACDA Finished -----")
            break
        
        print("\nAnalysis: Script failed. Beginning debugging process...")
        print(result["stderr"])
        # 2. PARSE the error
        error_details = parse_error_message(result['stderr'])
        if not error_details:
            print("Error: Could not parse the error message. Stopping.")
            break
        
        print(f"Parsed Error: {error_details['error_type']}: {error_details['error_message']}")

        # 3. GENERATE a solution
        source_code = read_source_code(script_path)
        if not source_code:
            print("Error: Could not read the source file. Stopping.")
            break
            
        print("Generating a solution with the LLM...")
        solution = generate_solution(source_code, error_details)
        if not solution:
            print("Error: LLM failed to generate a solution. Stopping.")
            break
            
        print("\n--- Proposed Solution ---")
        print(solution)
        print("-------------------------")

        # 4. APPLY the patch
        print("Applying the patch...")
        if not apply_patch(script_path, solution):
            print("Error: Failed to apply the patch. Stopping.")
            break
        
        print("Patch applied. Re-running for validation...")
    
    else: # This 'else' belongs to the 'for' loop
        print(f"\n----- Agent stopped after {MAX_ATTEMPTS} failed attempts. -----")


if __name__ == "__main__":
    main()

