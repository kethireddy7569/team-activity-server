from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from pathlib import Path

app = FastAPI(title="Team Activity Live Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_activity = {}

BASE_DIR = Path(__file__).resolve().parent


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")


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
        "window_title": data.get("window_title", ""),
        "timestamp": data.get(
            "timestamp",
            datetime.now(timezone.utc).isoformat()
        ),
        "server_received_at": datetime.now(timezone.utc).isoformat()
    }

    latest_activity[employee_id] = activity

    print("Received activity:", activity)

    return {
        "status": "success",
        "message": "Activity received",
        "employee_id": employee_id
    }


@app.get("/api/team")
def get_team_activity():

    return {
        "status": "success",
        "count": len(latest_activity),
        "employees": list(latest_activity.values())
    }