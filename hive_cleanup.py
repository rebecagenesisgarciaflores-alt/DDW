import os
import shutil
import hashlib

HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")
WORKERS = [f"worker_{i}" for i in range(5)]

def get_file_hash(file_path):
    """Calculate the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def cleanup():
    if not os.path.exists(HIVE_HOME):
        print("Hive home does not exist.")
        return

    print(f"--- Starting Hive Cleanup in {HIVE_HOME} ---")
    
    # 1. Reset the Blackboard
    blackboard = os.path.join(HIVE_HOME, "HIVE_CONTEXT.md")
    if os.path.exists(blackboard):
        with open(blackboard, "w", encoding="utf-8") as f:
            f.write("# Hive Progress Blackboard\n\n(Cleaned and ready for new goals)\n")
        print("[1/4] Reset HIVE_CONTEXT.md")

    # 2. Remove temporary files inside worker directories
    for worker in WORKERS:
        worker_path = os.path.join(HIVE_HOME, worker)
        if os.path.exists(worker_path):
            to_delete = ["current_prompt.txt", "prompt.txt"]
            for filename in to_delete:
                file_path = os.path.join(worker_path, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"      Removed temp: {file_path}")
            
            # 4. Clear the .gemini/tmp inside workers
            tmp_path = os.path.join(worker_path, ".gemini", "tmp")
            if os.path.exists(tmp_path):
                shutil.rmtree(tmp_path)
                os.makedirs(tmp_path)
                print(f"      Cleared tmp for {worker}")

    print("[2/4] Temporary files and tmp folders cleared.")

    # 3. De-duplicate files (Logic for finding redundant .tmp files in .gemini folders)
    print("[3/4] Searching for duplicates/redundant files...")
    for worker in WORKERS:
        gemini_dir = os.path.join(HIVE_HOME, worker, ".gemini")
        if os.path.exists(gemini_dir):
            for item in os.listdir(gemini_dir):
                item_path = os.path.join(gemini_dir, item)
                # Remove known redundant pattern (e.g., projects.json.xxxx.tmp)
                if ".tmp" in item and os.path.isfile(item_path):
                    os.remove(item_path)
                    print(f"      Removed redundant file: {item}")

    print("[4/4] Hive Cleanup Complete.")

if __name__ == "__main__":
    cleanup()
