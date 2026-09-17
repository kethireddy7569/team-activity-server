import requests
import time
from datetime import datetime, timezone

# -----------------------------
# Employee Details
# -----------------------------

EMPLOYEE_ID = "CRFT-IT-260601"

# ActivityWatch running on employee laptop
ACTIVITYWATCH_URL = "http://127.0.0.1:5600"

# Render Live Server URL
# Deploy అయిన తర్వాత మీ actual Render URL ఇక్కడ పెట్టాలి
SERVER_URL = "https://YOUR-RENDER-URL.onrender.com"


# -----------------------------
# Get ActivityWatch Data
# -----------------------------

def get_activitywatch_data():

    try:
        response = requests.get(
            f"{ACTIVITYWATCH_URL}/api/0/buckets",
            timeout=5
        )

        response.raise_for_status()

        buckets = response.json()

        return buckets

    except Exception as e:
        print("ActivityWatch Error:", e)
        return None


# -----------------------------
# Send Activity To Live Server
# -----------------------------

def send_activity():

    buckets = get_activitywatch_data()

    if buckets is None:
        return

    data = {
        "employee_id": EMPLOYEE_ID,
        "status": "active",
        "application": "ActivityWatch",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:

        response = requests.post(
            f"{SERVER_URL}/api/activity",
            json=data,
            timeout=10
        )

        print(
            "Server:",
            response.status_code,
            response.text
        )

    except Exception as e:

        print("Server Connection Error:", e)


# -----------------------------
# Continuous Tracking
# -----------------------------

print("Team Activity Tracker Started")
print("Employee ID:", EMPLOYEE_ID)

while True:

    send_activity()

    time.sleep(1)