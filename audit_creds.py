
import os
import json
import hashlib

HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")

def get_file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

results = []
hashes = {}

for i in range(5):
    worker_name = f"worker_{i}"
    path = os.path.join(HIVE_HOME, worker_name, ".gemini", "oauth_creds.json")
    
    if os.path.exists(path):
        file_hash = get_file_hash(path)
        results.append({
            "worker": worker_name,
            "path": path,
            "hash": file_hash,
            "status": "EXISTS"
        })
        if file_hash in hashes:
            hashes[file_hash].append(worker_name)
        else:
            hashes[file_hash] = [worker_name]
    else:
        results.append({
            "worker": worker_name,
            "path": path,
            "status": "MISSING"
        })

print("=== Credential Location & Integrity Report ===")
for r in results:
    print(f"{r['worker']}: {r['status']}")
    print(f"  Path: {r['path']}")
    if r['status'] == "EXISTS":
        print(f"  Fingerprint (MD5): {r['hash']}")
    print("-" * 40)

duplicates = {h: ws for h, ws in hashes.items() if len(ws) > 1}

if duplicates:
    print("\n!!! WARNING: DUPLICATE CREDENTIALS DETECTED !!!")
    for h, ws in duplicates.items():
        print(f"The following workers share the SAME credentials (Fingerprint: {h}):")
        print(f"  -> {', '.join(ws)}")
else:
    print("\nNo duplicate credentials detected among existing files.")
