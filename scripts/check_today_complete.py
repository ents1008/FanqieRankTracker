import os
import json
import sys
from datetime import datetime, timezone, timedelta

BEIJING_TZ = timezone(timedelta(hours=8))

def is_today_complete():
    today = datetime.now(BEIJING_TZ).strftime("%Y%m%d")
    state_file = os.path.join("data", "male", f"task_state_{today}.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                completed = json.load(f).get("completed", [])
                if len(completed) >= 19:
                    return True
        except Exception:
            pass
    return False

if __name__ == "__main__":
    if is_today_complete():
        print("true")
    else:
        print("false")
