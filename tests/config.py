import json
import os
from datetime import datetime

LOG_FILE = "random_test_execution_log.json"

def log_unique_test_result(test_case_id, resource_name, test_name, result, extra_details=None):
    """Logs unique test executions to a JSON file, avoiding duplicate signatures."""
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", LOG_FILE)
    
    # Load existing logs or initialize an empty list
    existing_logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                existing_logs = json.load(f)
        except json.JSONDecodeError:
            existing_logs = []

    # Build the current log entry
    entry = {
        "test_case_id": test_case_id,
        "resource_name": resource_name,
        "test_name": test_name,
        "result": result,
        "timestamp": datetime.now().isoformat(),
        "details": extra_details or {}
    }

    # Define a unique signature to check for duplicates (e.g., same test name, resource, and specific targeted URL/item)
    is_duplicate = any(
        log["test_case_id"] == test_case_id and 
        log["resource_name"] == resource_name and 
        log["test_name"] == test_name and 
        log["result"] == result
        for log in existing_logs
    )

    if not is_duplicate:
        existing_logs.append(entry)
        with open(log_path, "w") as f:
            json.dump(existing_logs, f, indent=4)