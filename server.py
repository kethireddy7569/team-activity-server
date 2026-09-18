# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse
# from datetime import datetime, timezone
# from pathlib import Path

# import firebase_admin
# from firebase_admin import credentials, firestore


# # -----------------------------
# # Firebase Configuration
# # -----------------------------

# cred = credentials.Certificate("serviceAccountKey.json")

# if not firebase_admin._apps:
#     firebase_admin.initialize_app(cred)

# db = firestore.client()


# # -----------------------------
# # FastAPI Configuration
# # -----------------------------

# app = FastAPI(title="Team Activity Live Server")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# BASE_DIR = Path(__file__).resolve().parent


# # -----------------------------
# # Home / Dashboard
# # -----------------------------

# @app.get("/")
# def home():
#     return FileResponse(BASE_DIR / "index.html")


# # -----------------------------
# # Receive Activity
# # -----------------------------

# @app.post("/api/activity")
# def receive_activity(data: dict):

#     employee_id = data.get("employee_id")

#     if not employee_id:
#         return {
#             "status": "failed",
#             "message": "employee_id is required"
#         }

#     activity = {
#         "employee_id": employee_id,
#         "status": data.get("status", "unknown"),
#         "application": data.get("application", "unknown"),
#         "window_title": data.get("window_title", ""),
#         "timestamp": data.get(
#             "timestamp",
#             datetime.now(timezone.utc).isoformat()
#         ),
#         "server_received_at": datetime.now(timezone.utc).isoformat()
#     }

#     # Save latest activity
#     db.collection("latest_activity").document(employee_id).set(activity)

#     # Save complete activity history
#     db.collection("activity_logs").add(activity)

#     print("Firebase activity saved:", activity)

#     return {
#         "status": "success",
#         "message": "Activity saved to Firebase",
#         "employee_id": employee_id
#     }


# # -----------------------------
# # Get Team Activity
# # -----------------------------

# @app.get("/api/team")
# def get_team_activity():

#     docs = db.collection("latest_activity").stream()

#     employees = []

#     for doc in docs:
#         employees.append(doc.to_dict())

#     return {
#         "status": "success",
#         "count": len(employees),
#         "employees": employees
#     }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import firebase_admin
from firebase_admin import credentials, firestore


# ============================================================
# FIREBASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceAccountKey.json"

if not firebase_admin._apps:

    cred = credentials.Certificate(
        str(SERVICE_ACCOUNT_FILE)
    )

    firebase_admin.initialize_app(cred)

db = firestore.client()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Team Activity Monitoring Server"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# TIMEZONE
# ============================================================

IST = ZoneInfo("Asia/Kolkata")


# ============================================================
# BASE PATH
# ============================================================

@app.get("/")
def home():

    return FileResponse(
        BASE_DIR / "index.html"
    )


# ============================================================
# ACTIVITY API
# ============================================================

@app.post("/api/activity")
def receive_activity(data: dict):

    # --------------------------------------------------------
    # Employee ID
    # --------------------------------------------------------

    employee_id = data.get(
        "employee_id"
    )

    if not employee_id:

        return {
            "status": "failed",
            "message": "employee_id is required"
        }


    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    timestamp = data.get(
        "timestamp"
    )

    if timestamp:

        try:

            activity_time = datetime.fromisoformat(
                timestamp.replace(
                    "Z",
                    "+00:00"
                )
            )

        except Exception:

            activity_time = datetime.now(
                timezone.utc
            )

    else:

        activity_time = datetime.now(
            timezone.utc
        )


    # Convert to IST

    activity_time_ist = activity_time.astimezone(
        IST
    )


    # Date

    activity_date = activity_time_ist.strftime(
        "%Y-%m-%d"
    )


    # --------------------------------------------------------
    # Activity information
    # --------------------------------------------------------

    latest_application = data.get(
        "application",
        "Unknown"
    )

    status = data.get(
        "status",
        "unknown"
    )

    window_title = data.get(
        "window_title",
        ""
    )


    # --------------------------------------------------------
    # Working time
    # --------------------------------------------------------

    expected_working_seconds = int(
        data.get(
            "expected_working_seconds",
            8 * 60 * 60
        )
    )

    active_seconds = int(
        data.get(
            "active_seconds",
            0
        )
    )

    idle_seconds = int(
        data.get(
            "idle_seconds",
            0
        )
    )


    # --------------------------------------------------------
    # Application usage
    # --------------------------------------------------------

    application_usage = data.get(
        "application_usage",
        {}
    )

    if not isinstance(
        application_usage,
        dict
    ):

        application_usage = {}


    # --------------------------------------------------------
    # Latest activity document
    # --------------------------------------------------------

    latest_activity = {

        "employee_id":
            employee_id,

        "status":
            status,

        "application":
            latest_application,

        "window_title":
            window_title,

        "timestamp":
            timestamp,

        "last_sync_ist":
            activity_time_ist.isoformat(),

        "expected_working_seconds":
            expected_working_seconds,

        "active_seconds":
            active_seconds,

        "idle_seconds":
            idle_seconds,

        "expected_working_time":
            format_duration(
                expected_working_seconds
            ),

        "active_time":
            format_duration(
                active_seconds
            ),

        "idle_time":
            format_duration(
                idle_seconds
            ),

        "application_usage":
            application_usage
    }


    # --------------------------------------------------------
    # Save latest activity
    # --------------------------------------------------------

    db.collection(
        "latest_activity"
    ).document(
        employee_id
    ).set(
        latest_activity
    )


    # --------------------------------------------------------
    # Daily activity document
    #
    # One document per employee per day
    #
    # Example:
    # CRFT-IT-260601_2026-09-18
    # --------------------------------------------------------

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
            status,

        "last_window":
            window_title,

        "last_sync":
            timestamp,

        "last_sync_ist":
            activity_time_ist.isoformat(),

        "expected_working_seconds":
            expected_working_seconds,

        "active_seconds":
            active_seconds,

        "idle_seconds":
            idle_seconds,

        "expected_working_time":
            format_duration(
                expected_working_seconds
            ),

        "active_time":
            format_duration(
                active_seconds
            ),

        "idle_time":
            format_duration(
                idle_seconds
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


    # --------------------------------------------------------
    # Activity log
    #
    # Every sync creates a historical record
    # --------------------------------------------------------

    log_data = {

        "employee_id":
            employee_id,

        "date":
            activity_date,

        "status":
            status,

        "application":
            latest_application,

        "window_title":
            window_title,

        "timestamp":
            timestamp,

        "active_seconds":
            active_seconds,

        "idle_seconds":
            idle_seconds,

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


    # --------------------------------------------------------
    # Console
    # --------------------------------------------------------

    print(
        "======================================"
    )

    print(
        "Firebase activity received"
    )

    print(
        "Employee:",
        employee_id
    )

    print(
        "Date:",
        activity_date
    )

    print(
        "Application:",
        latest_application
    )

    print(
        "Active:",
        format_duration(
            active_seconds
        )
    )

    print(
        "Idle:",
        format_duration(
            idle_seconds
        )
    )

    print(
        "======================================"
    )


    return {

        "status":
            "success",

        "message":
            "Activity saved successfully",

        "employee_id":
            employee_id,

        "date":
            activity_date,

        "active_time":
            format_duration(
                active_seconds
            ),

        "idle_time":
            format_duration(
                idle_seconds
            )
    }


# ============================================================
# GET TEAM LATEST ACTIVITY
# ============================================================

@app.get("/api/team")
def get_team_activity():

    docs = db.collection(
        "latest_activity"
    ).stream()


    employees = []


    for doc in docs:

        employee = doc.to_dict()

        employees.append(
            employee
        )


    return {

        "status":
            "success",

        "count":
            len(employees),

        "employees":
            employees
    }


# ============================================================
# GET DAILY TEAM DATA
# ============================================================

@app.get("/api/team/daily")
def get_daily_team_activity():

    today = datetime.now(
        IST
    ).strftime(
        "%Y-%m-%d"
    )


    docs = db.collection(
        "daily_activity"
    ).where(
        "date",
        "==",
        today
    ).stream()


    employees = []


    for doc in docs:

        employee = doc.to_dict()

        employees.append(
            employee
        )


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


# ============================================================
# GET PARTICULAR EMPLOYEE DAILY DATA
# ============================================================

@app.get("/api/employee/{employee_id}")
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


    doc = db.collection(
        "daily_activity"
    ).document(
        document_id
    ).get()


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


# ============================================================
# FORMAT DURATION
# ============================================================

def format_duration(
    seconds
):

    seconds = int(
        max(
            seconds,
            0
        )
    )


    hours = (
        seconds // 3600
    )


    minutes = (
        seconds % 3600
    ) // 60


    return (
        f"{hours}h {minutes}m"
    )