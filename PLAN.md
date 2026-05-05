# Plan: Gemini Hive Mind (Parallel Architecture)

## Objective
Create an orchestration layer that allows multiple Gemini CLI instances to run in parallel using different Google accounts. This will distribute quota usage and enable collaborative, iterative task completion.

## Key Files & Context
- **`GEMINI_CLI_HOME`**: The environment variable used to isolate worker profiles.
- **`hive_manager.py`**: The proposed Python orchestrator.
- **`C:\Users\keka\Projects\gemini-hive`**: Root directory for all hive-related state.
- **`HIVE_CONTEXT.md`**: A shared memory file for agents to read and write context.

## Implementation Steps

### 1. Environment Setup
- Create a root hive directory: `C:\Users\keka\.gemini_hive`.
- Create sub-profiles for each account (e.g., `worker_0`, `worker_1`, ..., `worker_4`).
- Initialize each profile with its own `settings.json` and a placeholder `google_accounts.json` targeting the specific account.

### 2. Authentication (One-Time Provisioning)
- Create a script `hive_auth.py` that loops through each worker profile.
- For each profile, set `GEMINI_CLI_HOME` and run a simple command (like `gemini --version`) to trigger the login flow if needed.
- The user will need to complete the OAuth flow for each account to populate the `oauth_creds.json` in each worker's home.

### 3. Orchestration Layer (The "Queen")
- Develop `hive_manager.py`:
    - **Worker Management**: A class to spawn and monitor `gemini` processes with specific environment variables.
    - **Priority Dispatching**: Implements a "Bottom-Up" selection logic. Workers 1-4 are the "Drones" used for all standard tasks. Worker 0 (The Queen) is reserved as the last possible option or for "Emergency 1-Agent" workflows where total context control is required.
    - **Task Dispatcher**: A queue system that assigns "Directives" to available workers.
    - **Shared Blackboard**: A mechanism for workers to append findings to `HIVE_CONTEXT.md`.
    - **Refinement Loop**: Logic that takes Worker A's output and feeds it to Worker B for verification or next-step iteration.

### 4. Communication Protocol
- Agents will be instructed (via their system prompts in the hive) to:
    1. Read `HIVE_CONTEXT.md` before starting.
    2. Write a summary of their progress to `HIVE_CONTEXT.md` before exiting.
    3. Use a specific tag (e.g., `[WORKER_ID: COMPLETED/FAILED]`) for the Manager to track.

## Verification & Testing
- **Isolation Test**: Run two workers simultaneously and verify they use different `oauth_creds.json` and do not collide in history.
- **Quota Test**: Verify that hitting a quota limit in `worker_0` does not prevent `worker_1` from completing its task.
- **Iteration Test**: Task `worker_0` to write a small script and `worker_1` to find a bug in it.

## Future Enhancements
- Automated quota detection and failover.
- Real-time "chat" between workers via a shared socket or local file watcher.
