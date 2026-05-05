import os
import subprocess
import threading
import time
import json
from queue import Queue

HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")
BLACKBOARD = os.path.join(HIVE_HOME, "HIVE_CONTEXT.md")
QUOTA_FILE = os.path.join(HIVE_HOME, "quota_usage.json")

# Shared lock for console and file access
console_lock = threading.Lock()

class QuotaMeter:
    def __init__(self, max_quota=50):
        self.max_quota = max_quota
        self.load()

    def load(self):
        with console_lock:
            if os.path.exists(QUOTA_FILE):
                try:
                    with open(QUOTA_FILE, "r") as f:
                        self.usage = json.load(f)
                except:
                    self.usage = {str(i): {"requests": 0, "exhausted": False} for i in range(5)}
            else:
                self.usage = {str(i): {"requests": 0, "exhausted": False} for i in range(5)}

    def save(self):
        with console_lock:
            with open(QUOTA_FILE, "w") as f:
                json.dump(self.usage, f, indent=4)

    def record_request(self, worker_id):
        self.load()
        wid = str(worker_id)
        if wid not in self.usage:
            self.usage[wid] = {"requests": 0, "exhausted": False}
        self.usage[wid]["requests"] += 1
        self.save()

    def mark_exhausted(self, worker_id):
        self.load()
        wid = str(worker_id)
        self.usage[wid]["exhausted"] = True
        self.save()

    def display(self):
        parts = []
        self.load()
        for i in range(5):
            wid = str(i)
            stats = self.usage.get(wid, {"requests": 0, "exhausted": False})
            pct = min(100, int((stats.get("requests", 0) / self.max_quota) * 100))
            status_char = "!" if stats.get("exhausted") else "√" if stats.get("requests", 0) > 0 else "."
            parts.append(f"W{i}:{pct}%{status_char}")
        with console_lock:
            print(f" [HIVE_QUOTA] {' | '.join(parts)}")

class Worker:
    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.name = f"worker_{worker_id}"
        self.home = os.path.join(HIVE_HOME, self.name)
        self.workspace = os.path.join(self.home, "workspace")
        self.creds_path = os.path.join(self.home, ".gemini", "oauth_creds.json")
        self.is_queen = (worker_id == 0)
        self.exhausted = False
        self._ensure_workspace()

    def _ensure_workspace(self):
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        # Create a .project_root to enable tool usage and workspace detection
        root_file = os.path.join(self.workspace, ".project_root")
        if not os.path.exists(root_file):
            with open(root_file, "w") as f:
                f.write(f"Hive Worker {self.worker_id} Workspace Root")

    def has_creds(self):
        return os.path.exists(self.creds_path)

    def run_task(self, prompt, timeout=300):
        if not self.has_creds():
            return f"Worker Error: Missing credentials at {self.creds_path}."

        with console_lock:
            print(f"[{self.name}] Initiating task...")
        
        # Add a small delay to avoid hitting RPM (Requests Per Minute) limits
        time.sleep(2)
        
        system_instruction = (
            f"You are {self.name} of the Gemini Hive Mind. "
            f"You have a dedicated workspace at: {self.workspace}. "
            "You are authorized to use tools to create, edit, or delete files within your workspace to fulfill your goals. "
            "Always verify the state of your workspace before and after actions. "
            "Respond ONLY with findings and tool outputs. End with [HIVE_GOAL_REACHED] if the overall goal is fully satisfied."
        )
        full_prompt = f"{system_instruction}\n\n{prompt}"
        
        prompt_file = os.path.join(self.home, "input_prompt.txt")
        if not os.path.exists(self.home):
            os.makedirs(self.home)
            
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(full_prompt)

        env = os.environ.copy()
        env["GEMINI_CLI_HOME"] = self.home
        env["GEMINI_CLI_AUTH_METHOD"] = "oauth-personal"
        env["GEMINI_CLI_TRUST_WORKSPACE"] = "true"
        env["PAGER"] = "cat"
        env["PYTHONUNBUFFERED"] = "1"
        
        # Using --raw-output and pointing to the prompt file one level up from workspace
        # We use --approval-mode yolo for automation, assuming the user's overall goal is the 'permission'
        cmd = f'gemini --skip-trust --approval-mode yolo --raw-output --accept-raw-output-risk < "..\\input_prompt.txt"'
        
        full_output = []
        try:
            process = subprocess.Popen(
                cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", shell=True, bufsize=1,
                cwd=self.workspace
            )

            current_category = None
            last_output_time = time.time()
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if not line:
                    if time.time() - last_output_time > 30:
                        with console_lock:
                            print(f"[{self.name}] Heartbeat: Still processing...")
                        last_output_time = time.time()
                    time.sleep(0.1)
                    continue

                last_output_time = time.time()
                clean_line = line.strip()
                if not clean_line:
                    continue

                # 1. Detect Category (Expanded for deeper noise reduction)
                noise_patterns = [
                    "GaxiosError", "code: 429", "RESOURCE_EXHAUSTED", "rateLimitExceeded", 
                    "exhausted your capacity", "MODEL_CAPACITY_EXHAUSTED", "Too Many Requests",
                    "cause: {", "details:", "reason:", "An unexpected critical error occurred",
                    "[object Object]"
                ]
                
                debug_patterns = [
                    "config:", "headers:", "response:", "url:", "method:", "Authorization:",
                    "params:", "responseType:", "body:", "signal:", "retry:", "validateStatus:",
                    "errorRedactor:", "alt-svc:", "content-length:", "content-type:", "date:",
                    "server:", "server-timing:", "vary:", "x-cloudaicompanion", "x-content-type",
                    "x-frame-options", "x-xss-protection", "x-goog-api-client", "User-Agent:",
                    "request:", "responseURL:", "status:", "statusText:", "data:", "Symbol("
                ]

                # Detect if line is likely part of a JSON error dump
                is_json_clutter = (
                    clean_line.startswith('{') or 
                    clean_line.startswith('}') or 
                    clean_line.startswith('[') or 
                    clean_line.startswith(']') or
                    clean_line.startswith('"error":') or
                    clean_line.startswith('"message":') or
                    clean_line.startswith('"code":') or
                    clean_line.startswith('"details":') or
                    clean_line.startswith('cause:') or
                    clean_line.endswith(',')
                )

                if any(x in clean_line for x in noise_patterns):
                    new_category = "[GOOGLE_API_LIMIT]"
                    self.exhausted = True
                    
                    # Detect high cooldown (e.g., '19h' or '20h' reset messages)
                    if any(hr in clean_line for hr in ["12h", "13h", "14h", "15h", "16h", "17h", "18h", "19h", "20h", "21h", "22h", "23h"]):
                        with console_lock:
                            print(f"\n[{self.name}] [!!!] HIGH COOLDOWN DETECTED: Daily Free Tier limit reached.")
                    
                    process.terminate()
                elif any(x in clean_line for x in ["retryWithBackoff", "Retrying after", "Attempt", "failed with status"]):
                    new_category = "[CLI_INTERNAL_RETRY]"
                elif any(x in clean_line for x in ["at ", "file:///", "node:internal", "processTicksAndRejections"]):
                    new_category = "[CLI_STACK_TRACE]"
                elif any(x in clean_line for x in debug_patterns) or is_json_clutter:
                    new_category = "[HTTP_DEBUG_INFO]"
                elif any(x in clean_line for x in ["Windows 10", "True color", "Ripgrep", "YOLO mode"]):
                    new_category = "[SYSTEM_INFO]"
                else:
                    new_category = "CONTENT"

                with console_lock:
                    if new_category == "CONTENT":
                        print(f"[{self.name}] > {clean_line}")
                        full_output.append(line) # ONLY append content to the permanent record
                        current_category = None
                    else:
                        if new_category != current_category:
                            if new_category == "[GOOGLE_API_LIMIT]":
                                print(f"[{self.name}] [!] {new_category}: 429 Too Many Requests (Quota Hit)")
                            elif new_category == "[CLI_INTERNAL_RETRY]":
                                print(f"[{self.name}] [i] {new_category}: CLI is attempting adaptive backoff...")
                            elif new_category == "[CLI_STACK_TRACE]":
                                # Decipher known annoying stack traces
                                if "AttachConsole failed" in clean_line:
                                    print(f"[{self.name}] [s] [SYS_WIN_CONSOLE_ERR]: Known Windows terminal attachment glitch.")
                                else:
                                    print(f"[{self.name}] [s] {new_category}: Internal CLI execution trace hidden.")
                            elif new_category == "[HTTP_DEBUG_INFO]":
                                print(f"[{self.name}] [h] {new_category}: Network metadata suppressed.")
                            current_category = new_category
            
            process.stdout.close()
            return_code = process.wait(timeout=timeout)
            
            combined = "".join(full_output)
            if self.exhausted:
                return f"Worker Error: Quota Exhausted (429).\n{combined}"

            if return_code != 0 and "exhausted your capacity" not in combined:
                return f"Process Error (Exit {return_code}):\n{combined}"
            
            return combined

        except subprocess.TimeoutExpired:
            process.kill()
            with console_lock:
                print(f"[{self.name}] TIMEOUT.")
            return "Worker Error: Task timed out."
        except Exception as e:
            return f"Unexpected Error: {str(e)}"

class HiveQueen:
    def __init__(self):
        self.drones = [Worker(i) for i in range(1, 5)]
        self.queen = Worker(0)
        self.meter = QuotaMeter()

    def initialize_blackboard(self, initial_goal):
        if not os.path.exists(HIVE_HOME):
            os.makedirs(HIVE_HOME)
        with open(BLACKBOARD, "w", encoding="utf-8") as f:
            f.write(f"# Hive Goal: {initial_goal}\n\n## Progress Log\n")

    def dispatch(self, goal, skip_exhausted=False, selected_worker_ids=None, review=False):
        self.initialize_blackboard(goal)
        with console_lock:
            print(f"Queen: Initializing Parallel Hive for goal: {goal}")
        
        # 1. THE PLAN PHASE: Queen divides the labor
        with console_lock:
            print("Queen (Worker 0): Analyzing goal and dividing labor...")
        available_drones = [w for w in self.drones if w.has_creds()]
        
        # Include the Queen (Worker 0) in the planning if she has creds
        all_workers = []
        if self.queen.has_creds():
            all_workers.append(self.queen)
        all_workers.extend(available_drones)

        if selected_worker_ids is not None:
            all_workers = [w for w in all_workers if w.worker_id in selected_worker_ids]
        
        if skip_exhausted:
            self.meter.load()
            all_workers = [w for w in all_workers if not self.meter.usage.get(str(w.worker_id), {}).get("exhausted")]

        if not all_workers:
            with console_lock:
                print("Queen: No workers available. Hive standing down.")
            return

        plan_prompt = (
            f"GOAL: {goal}\n\n"
            f"AVAILABLE WORKERS: {[w.name for w in all_workers]}\n\n"
            "TASK: Create a divided labor plan. For each available worker, assign a SPECIFIC and INDEPENDENT sub-task. "
            "IMPORTANT: WORKER_0 is the Queen, but she can ALSO perform sub-tasks. "
            "Respond ONLY with a list of tasks in this format: "
            "WORKER_N: [Task description]"
        )
        
        plan_response = self.queen.run_task(plan_prompt)
        with console_lock:
            print(f"Queen: Labor Division Plan created.\n{plan_response}")

        if review:
            with console_lock:
                choice = input("\nDo you approve this plan? (y/n): ").strip().lower()
                if choice != 'y':
                    print("Queen: Plan rejected. Hive standing down.")
                    return

        # 2. THE EXECUTION PHASE: Parallel Workers
        with console_lock:
            print(f"Queen: Dispatching {len(all_workers)} workers in parallel...")
        results_queue = Queue()

        def worker_thread(worker, task_description):
            prompt = (
                f"OVERALL GOAL: {goal}\n"
                f"YOUR SPECIFIC SUB-TASK: {task_description}\n\n"
                "Provide your findings clearly. Do not repeat previous context."
            )
            self.meter.record_request(worker.worker_id)
            response = worker.run_task(prompt)
            if worker.exhausted:
                self.meter.mark_exhausted(worker.worker_id)
            results_queue.put((worker.name, response))

        threads = []
        # Parse the plan to match tasks to workers
        for worker in all_workers:
            # Try to find the specific task for this worker in the plan_response
            task_desc = "Contribute to the overall goal."
            for line in plan_response.split("\n"):
                if worker.name.upper() in line.upper():
                    task_desc = line.split(":", 1)[1].strip() if ":" in line else line
            
            t = threading.Thread(target=worker_thread, args=(worker, task_desc))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # 3. THE SYNTHESIS PHASE: Queen condenses everything
        with console_lock:
            print("Queen: Collecting results for final synthesis...")
        all_contributions = []
        while not results_queue.empty():
            w_name, resp = results_queue.get()
            all_contributions.append(f"### Findings from {w_name}:\n{resp}\n")
            # Update Blackboard
            with open(BLACKBOARD, "a", encoding="utf-8") as f:
                f.write(f"\n### Contribution from {w_name}:\n{resp}\n")

        if not all_contributions:
            with console_lock:
                print("Queen: No contributions were received from drones. Hive standing down.")
            return

        synthesis_prompt = (
            f"OVERALL GOAL: {goal}\n\n"
            f"DRONE CONTRIBUTIONS:\n{''.join(all_contributions)}\n\n"
            "TASK: Condense the above findings into a single, high-quality, professional report for the user. "
            "Highlight the most important data points and provide a clear conclusion."
        )
        
        with console_lock:
            print("Queen: Synthesizing final report...")
        final_report = self.queen.run_task(synthesis_prompt)
        
        with open(BLACKBOARD, "a", encoding="utf-8") as f:
            f.write(f"\n## FINAL SYNTHESIZED REPORT\n{final_report}\n[HIVE_GOAL_REACHED]\n")
        
        with console_lock:
            print("\n" + "="*50)
            print("FINAL REPORT FROM THE QUEEN")
            print("="*50)
            print(final_report)
            print("="*50)




if __name__ == "__main__":
    import sys
    queen = HiveQueen()
    
    args = sys.argv[1:]
    
    # Check for --skip-exhausted
    skip_exhausted = False
    if "--skip-exhausted" in args:
        skip_exhausted = True
        args.remove("--skip-exhausted")
    
    # Check for --workers
    selected_workers = None
    for arg in args[:]:
        if arg.startswith("--workers="):
            try:
                worker_list = arg.split("=")[1]
                selected_workers = [int(x) for x in worker_list.split(",")]
                args.remove(arg)
            except:
                print("Error parsing --workers flag. Format: --workers=1,2,3")
        
    # Check for --review
    review = False
    if "--review" in args:
        review = True
        args.remove("--review")
    
    if args:
        # Use provided goal from CLI
        goal = " ".join(args)
    else:
        # Default fallback goal
        goal = (
            "Goal: Find the most efficient way to implement a consumer-grade UI into this hive. "
            "DISTRIBUTION: "
            "Worker 1: Research lightweight web frameworks (Streamlit, Flask, etc.) that can read local files. "
            "Worker 2: Research how to visualize the Blackboard (HIVE_CONTEXT.md) in real-time. "
            "Worker 3: Research aesthetic CSS frameworks or design systems suitable for a dashboard. "
            "Worker 4: Synthesize a technical blueprint for the Hive Dashboard."
        )
    
    queen.dispatch(goal, skip_exhausted=skip_exhausted, selected_worker_ids=selected_workers, review=review)
