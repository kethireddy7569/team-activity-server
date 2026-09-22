from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import os
import json

import firebase_admin
from firebase_admin import credentials, firestore


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

SERVICE_ACCOUNT_FILE = (
    BASE_DIR / "serviceAccountKey.json"
)

IST = ZoneInfo("Asia/Kolkata")

# Tracker sends data every 60 seconds.
# If no data is received for 3 minutes,
# employee will be considered OFFLINE.
OFFLINE_THRESHOLD_SECONDS = 180


# =========================================================
# FIREBASE INITIALIZATION
# =========================================================

if not firebase_admin._apps:

    firebase_json = os.environ.get(
        "FIREBASE_SERVICE_ACCOUNT_JSON"
    )

    if firebase_json:

        try:
            service_account_info = json.loads(
                firebase_json
            )

            cred = credentials.Certificate(
                service_account_info
            )

            firebase_admin.initialize_app(cred)

            print(
                "Firebase initialized using environment variable."
            )

        except Exception as e:

            print(
                "Firebase environment variable error:",
                e
            )

            raise

    elif SERVICE_ACCOUNT_FILE.exists():

        cred = credentials.Certificate(
            str(SERVICE_ACCOUNT_FILE)
        )

        firebase_admin.initialize_app(cred)

        print(
            "Firebase initialized using serviceAccountKey.json."
        )

    else:

        raise RuntimeError(
            "Firebase credentials not found."
        )


db = firestore.client()


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Team Activity Monitoring Server"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def format_duration(seconds):

    seconds = int(max(seconds, 0))

    hours = seconds // 3600

    minutes = (seconds % 3600) // 60

    return f"{hours}h {minutes}m"


def parse_timestamp(timestamp):

    if not timestamp:
        return None

    try:

        dt = datetime.fromisoformat(
            str(timestamp).replace(
                "Z",
                "+00:00"
            )
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt

    except Exception:

        return None


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    index_file = BASE_DIR / "index.html"

    if index_file.exists():

        return FileResponse(index_file)

    return {
        "status": "success",
        "message": "Team Activity Monitoring Server is running"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "success",
        "message": "Server is running"
    }


# =========================================================
# RECEIVE ACTIVITY FROM TRACKER
# =========================================================

@app.post("/api/activity")
def receive_activity(data: dict):

    employee_id = data.get("employee_id")

    if not employee_id:

        return {
            "status": "failed",
            "message": "employee_id is required"
        }


    # -----------------------------------------------------
    # Timestamp
    # -----------------------------------------------------

    timestamp = data.get("timestamp")

    activity_time = parse_timestamp(timestamp)

    if activity_time is None:

        activity_time = datetime.now(
            timezone.utc
        )

        timestamp = activity_time.isoformat()


    activity_time_ist = (
        activity_time.astimezone(IST)
    )

    activity_date = (
        activity_time_ist.strftime(
            "%Y-%m-%d"
        )
    )


    # -----------------------------------------------------
    # Activity details
    # -----------------------------------------------------

    latest_application = data.get(
        "application",
        "Unknown"
    )

    window_title = data.get(
        "window_title",
        ""
    )

    active_seconds = int(
        data.get(
            "active_seconds",
            0
        )
    )

    application_usage = data.get(
        "application_usage",
        {}
    )

    if not isinstance(
        application_usage,
        dict
    ):

        application_usage = {}


    # =====================================================
    # LATEST ACTIVITY
    # =====================================================

    latest_activity = {

        "employee_id": employee_id,

        "status": "active",

        "application": latest_application,

        "window_title": window_title,

        "timestamp": timestamp,

        "last_sync_ist":
            activity_time_ist.isoformat(),

        "active_seconds":
            active_seconds,

        "active_time":
            format_duration(
                active_seconds
            ),

        "application_usage":
            application_usage
    }


    db.collection(
        "latest_activity"
    ).document(
        employee_id
    ).set(
        latest_activity
    )


    # =====================================================
    # DAILY ACTIVITY
    # =====================================================

    daily_document_id = (
        f"{employee_id}_{activity_date}"
    )

    daily_data = {

        "employee_id":
            employee_id,

        "date":
            activity_date,

        "last_application":
            latest_application,

        "last_status":
            "active",

        "last_window":
            window_title,

        "last_sync":
            timestamp,

        "last_sync_ist":
            activity_time_ist.isoformat(),

        "active_seconds":
            active_seconds,

        "active_time":
            format_duration(
                active_seconds
            ),

        "application_usage":
            application_usage,

        "updated_at":
            firestore.SERVER_TIMESTAMP
    }


    db.collection(
        "daily_activity"
    ).document(
        daily_document_id
    ).set(
        daily_data,
        merge=True
    )


    # =====================================================
    # ACTIVITY LOG
    # =====================================================

    log_data = {

        "employee_id":
            employee_id,

        "date":
            activity_date,

        "status":
            "active",

        "application":
            latest_application,

        "window_title":
            window_title,

        "timestamp":
            timestamp,

        "active_seconds":
            active_seconds,

        "application_usage":
            application_usage,

        "created_at":
            firestore.SERVER_TIMESTAMP
    }


    db.collection(
        "activity_logs"
    ).add(
        log_data
    )


    print(
        f"[ACTIVITY] {employee_id} | "
        f"{latest_application} | "
        f"{format_duration(active_seconds)} | "
        f"{timestamp}"
    )


    return {

        "status": "success",

        "employee_id":
            employee_id,

        "message":
            "Activity saved successfully"
    }


# =========================================================
# CURRENT TEAM
# =========================================================

@app.get("/api/team")
def get_team_activity():

    docs = (
        db.collection(
            "latest_activity"
        ).stream()
    )

    employees = []

    now = datetime.now(
        timezone.utc
    )


    # =====================================================
    # CHECK EVERY EMPLOYEE
    # =====================================================

    for doc in docs:

        employee = doc.to_dict()

        last_sync = employee.get(
            "timestamp"
        )

        last_time = parse_timestamp(
            last_sync
        )


        # -------------------------------------------------
        # NO VALID TIMESTAMP
        # -------------------------------------------------

        if last_time is None:

            employee["status"] = "offline"

            employee[
                "seconds_since_last_sync"
            ] = None


        else:

            seconds_since_sync = (
                now - last_time
            ).total_seconds()

            seconds_since_sync = max(
                seconds_since_sync,
                0
            )

            employee[
                "seconds_since_last_sync"
            ] = int(
                seconds_since_sync
            )


            # -------------------------------------------------
            # ACTIVE / OFFLINE
            # -------------------------------------------------

            if (
                seconds_since_sync
                <= OFFLINE_THRESHOLD_SECONDS
            ):

                employee["status"] = "active"

            else:

                employee["status"] = "offline"


            # -------------------------------------------------
            # IST LAST SYNC
            # -------------------------------------------------

            employee[
                "last_sync_ist"
            ] = (
                last_time
                .astimezone(IST)
                .isoformat()
            )


        employees.append(
            employee
        )


    # =====================================================
    # COUNTS
    # =====================================================

    total_employees = len(
        employees
    )

    active_employees = sum(
        1
        for employee in employees
        if employee.get(
            "status"
        ) == "active"
    )

    offline_employees = (
        total_employees
        - active_employees
    )


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "status":
            "success",

        "count":
            total_employees,

        "total_employees":
            total_employees,

        "active_employees":
            active_employees,

        "offline_employees":
            offline_employees,

        "employees":
            employees
    }


# =========================================================
# DAILY TEAM
# =========================================================

@app.get("/api/team/daily")
def get_daily_team_activity():

    today = datetime.now(
        IST
    ).strftime(
        "%Y-%m-%d"
    )

    docs = (
        db.collection(
            "daily_activity"
        )
        .where(
            "date",
            "==",
            today
        )
        .stream()
    )

    employees = [
        doc.to_dict()
        for doc in docs
    ]

    return {

        "status":
            "success",

        "date":
            today,

        "count":
            len(employees),

        "employees":
            employees
    }


# =========================================================
# PARTICULAR EMPLOYEE
# =========================================================

@app.get(
    "/api/employee/{employee_id}"
)
def get_employee_activity(
    employee_id: str
):

    today = datetime.now(
        IST
    ).strftime(
        "%Y-%m-%d"
    )

    document_id = (
        f"{employee_id}_{today}"
    )

    doc = (
        db.collection(
            "daily_activity"
        )
        .document(
            document_id
        )
        .get()
    )

    if not doc.exists:

        return {

            "status":
                "not_found",

            "message":
                "No activity found for today",

            "employee_id":
                employee_id,

            "date":
                today
        }

    return {

        "status":
            "success",

        "data":
            doc.to_dict()
    }


# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )