import os
import subprocess
import json
import shutil

HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")
WORKERS = [f"worker_{i}" for i in range(5)]
BASE_GEMINI = os.path.expanduser("~/.gemini")

def setup_worker(worker_name):
    worker_path = os.path.join(HIVE_HOME, worker_name)
    gemini_dir = os.path.join(worker_path, ".gemini")
    print(f"--- Provisioning {worker_name} ---")
    
    if not os.path.exists(gemini_dir):
        os.makedirs(gemini_dir)
    
    # Copy basic settings if they don't exist
    settings_src = os.path.join(BASE_GEMINI, "settings.json")
    settings_dst = os.path.join(gemini_dir, "settings.json")
    if os.path.exists(settings_src) and not os.path.exists(settings_dst):
        shutil.copy(settings_src, settings_dst)
    
    # Set environment variable for this process
    env = os.environ.copy()
    env["GEMINI_CLI_HOME"] = worker_path
    env["GEMINI_CLI_AUTH_METHOD"] = "oauth-personal"
    
    # Check if creds already exist in the .gemini subfolder
    creds_path = os.path.join(gemini_dir, "oauth_creds.json")
    if os.path.exists(creds_path):
        print(f"Credentials already exist for {worker_name}. Skipping...")
        return

    print(f"Please log in for {worker_name}...")
    try:
        # Use PowerShell to set env vars and run the command
        # Add GEMINI_CLI_TRUST_WORKSPACE to bypass trust prompts
        ps_cmd = (
            f'$env:GEMINI_CLI_HOME="{worker_path}"; '
            f'$env:GEMINI_CLI_AUTH_METHOD="oauth-personal"; '
            f'$env:GEMINI_CLI_TRUST_WORKSPACE="true"; '
            f'gemini --prompt "Who are you? Respond with your worker name: {worker_name}" --skip-trust'
        )
        # Use powershell -Command to execute
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
        
        if os.path.exists(creds_path):
            print(f"Successfully provisioned {worker_name}")
        else:
            print(f"Warning: Command finished but {creds_path} was not found.")
    except Exception as e:
        print(f"Error provisioning {worker_name}: {e}")

if __name__ == "__main__":
    if not os.path.exists(HIVE_HOME):
        os.makedirs(HIVE_HOME)
        
    for worker in WORKERS:
        setup_worker(worker)
    
    print("\nAll workers provisioned. You should now have isolated oauth_creds.json in each worker folder.")
