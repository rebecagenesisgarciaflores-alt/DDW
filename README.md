# Gemini Hive Mind

A parallel orchestration layer for running multiple Gemini CLI instances with different Google accounts. This system distributes quota usage and enables collaborative, iterative task completion across multiple workers.

## Overview

**Gemini Hive Mind** is designed to:
- Spawn and manage multiple Gemini CLI workers in parallel
- Distribute tasks across available workers based on quota and availability
- Enable shared context through a blackboard-style communication system
- Provide failover and quota management across accounts

## Architecture

### Core Components

- **`hive_manager.py`**: Main orchestrator that manages worker processes and task dispatch
- **`hive_auth.py`**: One-time authentication setup for each worker profile
- **`hive_ui.py`**: User interface for monitoring and controlling workers
- **`hive_quota.py`**: Quota tracking and management
- **`hive_cleanup.py`**: Cleanup and maintenance utilities

### Worker Model

The system uses a hierarchical worker model:
- **Worker 0 (The Queen)**: Reserved for critical tasks and emergency workflows
- **Workers 1-4 (Drones)**: Standard task execution units

### State Management

Worker state is stored in `hive_state/` with each worker maintaining:
- Individual profile isolation via `GEMINI_CLI_HOME`
- Separate `oauth_creds.json` for account-specific credentials
- Input prompts and workspace for task execution
- `HIVE_CONTEXT.md` for shared information sharing

## Quick Start

### 1. Authentication Setup

```bash
python hive_auth.py
```

This will walk through OAuth setup for each worker profile.

### 2. Verify Installation

```bash
python verify_workers.py
```

### 3. Run Your First Task

```bash
python hive_manager.py
```

## Configuration

Edit `hive_state/settings.json` to configure:
- Number of workers
- Quota limits per account
- Task routing preferences
- Communication protocols

## Development

Check `PLAN.md` for implementation details and `CHANGELOG.md` for version history.

## License

[Specify your license here]
