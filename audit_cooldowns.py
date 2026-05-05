import os
import subprocess
import re

HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")

def check_worker(wid):
    worker_path = os.path.join(HIVE_HOME, f"worker_{wid}")
    env = os.environ.copy()
    env["GEMINI_CLI_HOME"] = worker_path
    env["GEMINI_CLI_AUTH_METHOD"] = "oauth-personal"
    env["GEMINI_CLI_TRUST_WORKSPACE"] = "true"
    
    # Run a tiny prompt with YOLO and risk acceptance to avoid interactive hangs
    cmd = "gemini --skip-trust --raw-output --accept-raw-output-risk --approval-mode yolo --prompt \"hi\""
    
    try:
        # Increased timeout to 60s to allow for 5s retry loops to resolve
        result = subprocess.run(cmd, env=env, shell=True, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        
        # Look for the reset time (handles 'reset after 5s' or 'reset after 19h...')
        match = re.search(r"reset after ([\w\s]+)\.", output)
        if match:
            return f"EXHAUSTED (Reset in {match.group(1)})"
        elif "exhausted your capacity" in output:
            return "EXHAUSTED (Unknown cooldown)"
        elif result.returncode == 0:
            return "READY (Has Quota)"
        else:
            return f"ERROR (Exit {result.returncode})"
    except subprocess.TimeoutExpired:
        return "TIMEOUT (Likely deep retry loop)"
    except Exception as e:
        return f"CRITICAL ERROR: {str(e)}"

print("=== HIVE FLEET COOLDOWN AUDIT ===")
for i in range(5):
    print(f"Worker {i}: Probing...", end="\r")
    status = check_worker(i)
    print(f"Worker {i}: {status}")
