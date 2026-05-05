
import os
import shutil

HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")
BASE_SETTINGS = os.path.expanduser("~/.gemini/settings.json")

for i in range(5):
    worker_gemini = os.path.join(HIVE_HOME, f"worker_{i}", ".gemini")
    if not os.path.exists(worker_gemini):
        os.makedirs(worker_gemini)
    
    dst = os.path.join(worker_gemini, "settings.json")
    print(f"Copying to {dst}")
    shutil.copy(BASE_SETTINGS, dst)
