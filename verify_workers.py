
import os
import subprocess

HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")

def check_worker(worker_id):
    worker_name = f"worker_{worker_id}"
    worker_path = os.path.join(HIVE_HOME, worker_name)
    
    ps_cmd = (
        f'$env:GEMINI_CLI_HOME="{worker_path}"; '
        f'$env:GEMINI_CLI_AUTH_METHOD="oauth-personal"; '
        f'$env:GEMINI_CLI_TRUST_WORKSPACE="true"; '
        f'gemini --prompt "Status check for {worker_name}" --skip-trust --approval-mode yolo'
    )
    
    print(f"Checking {worker_name}...")
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30 # 30 second timeout per worker
        )
        if result.returncode == 0:
            print(f"[{worker_name}] OK: {result.stdout.strip()[:50]}...")
        else:
            print(f"[{worker_name}] FAILED (Code {result.returncode}): {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print(f"[{worker_name}] TIMEOUT (Hanging?)")
    except Exception as e:
        print(f"[{worker_name}] ERROR: {str(e)}")

if __name__ == "__main__":
    for i in range(5):
        check_worker(i)
