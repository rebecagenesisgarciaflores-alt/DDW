
import os

HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")

for i in range(5):
    path = os.path.join(HIVE_HOME, f"worker_{i}", ".gemini", "oauth_creds.json")
    status = "EXISTS" if os.path.exists(path) else "MISSING"
    print(f"worker_{i}: {status}")
