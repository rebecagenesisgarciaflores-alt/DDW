
import os
import subprocess

def test_run():
    home = r"C:\Users\keka\Projects\gemini-hive\hive_state\worker_1"
    prompt = "Say hello"
    
    env = os.environ.copy()
    env["GEMINI_CLI_HOME"] = home
    env["GEMINI_CLI_AUTH_METHOD"] = "oauth-personal"
    env["GEMINI_CLI_TRUST_WORKSPACE"] = "true"
    env["PAGER"] = "cat"
    
    print("Running gemini...")
    try:
        # Trying to pass prompt via stdin and using --prompt without value if supported, 
        # or just passing it as an argument but properly escaped by subprocess.run
        result = subprocess.run(
            ["gemini", "--prompt", prompt, "--skip-trust", "--approval-mode", "yolo", "--raw-output"],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            shell=True
        )
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_run()
