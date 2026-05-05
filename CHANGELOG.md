# Gemini Hive Mind - Project Status & Handoff

## Project Overview
The goal is to orchestrate 5 isolated Gemini CLI instances (Workers 0-4) using different Google accounts to distribute quota and enable collaborative task completion via a shared "Blackboard" (`HIVE_CONTEXT.md`).

## Current Architecture
- **Root Folder:** `C:\Users\keka\Projects\gemini-hive`
- **Worker Home Bases (State):** `C:\Users\keka\Projects\gemini-hive\hive_state\worker_[0-4]`
- **Isolated Agentic Workspaces:** Each worker has a dedicated `workspace/` folder with a `.project_root` file, enabling full tool-calling (file creation, editing, deletion).
- **Parallel Orchestration:** Thread-safe parallel architecture allowing all workers (including the Queen) to work simultaneously.
- **Intelligent Noise Filtering:** Regex-based categorization that suppresses API noise and deciphering system-specific errors.

## Recent Technical Milestones (May 2026 - Modernization Phase)
- **Agentic Expansion:** Integrated `.project_root` and workspace isolation, allowing workers to build software (e.g., Tetris clones) autonomously within their sandboxes.
- **Fast-Kill & Real-Time Quota Tracking:** Implemented immediate process termination upon detecting 429 errors. Workers are now dynamically marked as `EXHAUSTED` in `quota_usage.json`.
- **Intelligent Labeling & Deciphering:** Expanded filters to hide verbose JSON error objects and deciphered Node.js/Windows console glitches into readable labels.
- **Blackboard Purity:** Refined the output processor to ensure ONLY "CONTENT" lines are written to the shared blackboard, keeping context clean for the Queen.
- **Queen-Inclusive Labor Division:** Updated the `HiveQueen` to allow Worker 0 to assign herself tasks, maximizing the hive's 5-worker throughput.
- **RPM Mitigation:** Introduced a mandatory 2-second stagger delay before worker tasks to prevent hitting "Requests Per Minute" burst limits.
- **UI Enhancements:** Added "Review Plan" toggle to allow user approval of the labor plan before execution.

## Core Scripts
1. **`hive_manager.py`**: The parallel orchestrator and heart of the system.
2. **`hive_ui.py`**: NiceGUI-based dashboard with real-time health and blackboard monitoring.
3. **`hive_quota.py`**: Persistent JSON-based quota meter and manual reset tool.
4. **`audit_cooldowns.py`**: Fleet-wide probe that checks API reset times for every worker.
5. **`hive_cleanup.py`**: Resets the blackboard and clears worker temporary files.

## Authenticated Accounts & Quota Status (Current)
- **Worker 0 (Queen):** `gotyetter@gmail.com` | **STATUS:** ACTIVE.
- **Worker 1:** `rebecagenesisgarciaflores@gmail.com` | **STATUS:** EXHAUSTED (19h+ cooldown).
- **Worker 2:** `zafox6969@gmail.com` | **STATUS:** ACTIVE.
- **Worker 3:** `thedibonner@gmail.com` | **STATUS:** EXHAUSTED (19h+ cooldown).
- **Worker 4:** `nico22260@gmail.com` | **STATUS:** EXHAUSTED (18h+ cooldown).

---

## 🤖 AI & Developer Implementation Guide

If you are an AI or developer tasked with modifying this hive, you MUST adhere to these architectural mandates:

### 1. **Workspace Isolation & Tool Safety**
- **The Workspace Rule:** Workers MUST only operate within their `workspace/` subdirectory.
- **Tool-Calling:** Always ensure a `.project_root` exists in the workspace. The CLI is invoked with `--approval-mode yolo`, so the logic in `hive_manager.py` is the only "gatekeeper." 
- **Relative Pathing:** Use `os.path.join(os.path.dirname(__file__), ...)` for all internal file references.

### 2. **Thread Safety & Logging**
- **The Console Lock:** All `print()` calls and disk I/O (especially `quota_usage.json`) MUST be wrapped in `with console_lock:`.
- **Parallel Writes:** Do not allow drones to write to the `HIVE_CONTEXT.md` simultaneously. The current model uses a `Queue` to collect results and has the Queen write them sequentially.

### 3. **Output Processing (Noise vs. Signal)**
- **Intelligent Labeling:** The `Worker.run_task` loop uses a category-based detector. 
- **Blackboard Purity:** NEVER allow `[GOOGLE_API_LIMIT]`, `[HTTP_DEBUG_INFO]`, or `[CLI_STACK_TRACE]` labels to be written to `HIVE_CONTEXT.md`. Only append lines categorized as `CONTENT`.

### 4. **Orchestration Logic (Queen/Drone)**
- **Worker 0 (The Queen):** She is the planner and synthesizer. She can now take sub-tasks, but her primary role is maintaining the "Plan" integrity.
- **Labor Division Format:** The Queen expects the plan format `WORKER_N: [Task]`. The dispatcher parses these lines to assign sub-tasks.

### 5. **Quota & RPM Management**
- **Fast Failover:** If a worker returns a 429 error, the `HiveQueen` terminates the process immediately and marks the worker as exhausted.
- **The Stagger Delay:** Always maintain a `time.sleep(2)` before `subprocess.Popen` in `run_task` to prevent RPM burst limits.
