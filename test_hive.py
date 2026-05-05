
import os
from hive_manager import HiveQueen

if __name__ == "__main__":
    queen = HiveQueen()
    # Simple 1-worker task to test for hangs
    queen.dispatch(
        "Goal: Say 'Hello from Worker 1' if you are Worker 1."
    )
