from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

app = FastAPI(
    title="Team Activity Live Server",
    version="1.0.0"
)

# Allow frontend/dashboard to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stores the latest activity of each employee
latest_activity = {}


# -----------------------------
# Server Health Check
# -----------------------------
@app.get("/")
def home():
    return {
        "status": "success",
        "message": "Team Activity Live Server is running"
    }


# -----------------------------
# Receive Employee Activity
# -----------------------------
@app.post("/api/activity")
def receive_activity(data: dict):

    employee_id = data.get("employee_id")

    if not employee_id:
        return {
            "status": "failed",
            "message": "employee_id is required"
        }

    activity = {
        "employee_id": employee_id,
        "status": data.get("status", "unknown"),
        "application": data.get("application", "unknown"),
        "timestamp": data.get(
            "timestamp",
            datetime.now(timezone.utc).isoformat()
        ),
        "server_received_at": datetime.now(timezone.utc).isoformat()
    }

    # Update latest activity for this employee
    latest_activity[employee_id] = activity

    print("Received activity:", activity)

    return {
        "status": "success",
        "message": "Activity received",
        "employee_id": employee_id
    }


# -----------------------------
# Get Team Activity
# -----------------------------
@app.get("/api/team")
def get_team_activity():

    return {
        "status": "success",
        "count": len(latest_activity),
        "employees": list(latest_activity.values())
    }
