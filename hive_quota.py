
import os
import json

HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")
QUOTA_FILE = os.path.join(HIVE_HOME, "quota_usage.json")

def load_quota():
    if os.path.exists(QUOTA_FILE):
        with open(QUOTA_FILE, "r") as f:
            return json.load(f)
    return {str(i): {"requests": 0, "exhausted": False, "last_used": None} for i in range(5)}

def save_quota(usage):
    with open(QUOTA_FILE, "w") as f:
        json.dump(usage, f, indent=4)

def display_meter():
    usage = load_quota()
    print("\n" + "="*45)
    print("       GEMINI HIVE - QUOTA MONITOR")
    print("="*45)
    print(f"{'WORKER':<10} | {'REQUESTS':<10} | {'STATUS':<12}")
    print("-" * 45)
    
    for i in range(5):
        stats = usage.get(str(i), {"requests": 0, "exhausted": False})
        worker_name = f"Worker {i}"
        requests = stats["requests"]
        
        if stats["exhausted"]:
            status = " [EXHAUSTED]"
            color_mark = "!"
        elif requests > 0:
            status = " [ACTIVE]"
            color_mark = ">"
        else:
            status = " [IDLE]"
            color_mark = "."
            
        # Simple ASCII bar representing activity (up to 15 marks)
        bar_len = min(requests, 15)
        bar = color_mark * bar_len + " " * (15 - bar_len)
        
        print(f"{worker_name:<10} | {requests:<10} | {status:<12} [{bar}]")
    
    print("="*45)
    print("Run 'python hive_quota.py --reset' to clear counts.\n")

if __name__ == "__main__":
    import sys
    if "--reset" in sys.argv:
        usage = {str(i): {"requests": 0, "exhausted": False, "last_used": None} for i in range(5)}
        save_quota(usage)
        print("Quota counts have been reset.")
    else:
        display_meter()
