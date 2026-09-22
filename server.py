# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse

# from datetime import datetime, timezone
# from pathlib import Path
# from zoneinfo import ZoneInfo

# import os
# import json

# import firebase_admin
# from firebase_admin import credentials, firestore


# # =========================================================
# # PATH
# # =========================================================

# BASE_DIR = Path(__file__).resolve().parent

# SERVICE_ACCOUNT_FILE = (
#     BASE_DIR / "serviceAccountKey.json"
# )


# # =========================================================
# # FIREBASE INITIALIZATION
# # =========================================================

# if not firebase_admin._apps:

#     firebase_json = os.environ.get(
#         "FIREBASE_SERVICE_ACCOUNT_JSON"
#     )

#     if firebase_json:

#         try:

#             service_account_info = json.loads(
#                 firebase_json
#             )

#             cred = credentials.Certificate(
#                 service_account_info
#             )

#             firebase_admin.initialize_app(
#                 cred
#             )

#             print(
#                 "Firebase initialized using environment variable."
#             )

#         except Exception as e:

#             print(
#                 "Firebase environment variable error:",
#                 e
#             )

#             raise

#     elif SERVICE_ACCOUNT_FILE.exists():

#         cred = credentials.Certificate(
#             str(SERVICE_ACCOUNT_FILE)
#         )

#         firebase_admin.initialize_app(
#             cred
#         )

#         print(
#             "Firebase initialized using serviceAccountKey.json."
#         )

#     else:

#         raise RuntimeError(
#             "Firebase credentials not found."
#         )


# db = firestore.client()


# # =========================================================
# # FASTAPI
# # =========================================================

# app = FastAPI(
#     title="Team Activity Monitoring Server"
# )


# # =========================================================
# # CORS
# # =========================================================

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # =========================================================
# # TIMEZONE
# # =========================================================

# IST = ZoneInfo(
#     "Asia/Kolkata"
# )


# # =========================================================
# # FORMAT DURATION
# # =========================================================

# def format_duration(seconds):

#     seconds = int(
#         max(seconds, 0)
#     )

#     hours = seconds // 3600

#     minutes = (
#         seconds % 3600
#     ) // 60

#     return f"{hours}h {minutes}m"


# # =========================================================
# # HOME
# # =========================================================

# @app.get("/")
# def home():

#     return FileResponse(
#         BASE_DIR / "index.html"
#     )


# # =========================================================
# # RECEIVE ACTIVITY
# # =========================================================

# @app.post("/api/activity")
# def receive_activity(data: dict):

#     employee_id = data.get(
#         "employee_id"
#     )

#     if not employee_id:

#         return {
#             "status": "failed",
#             "message":
#                 "employee_id is required"
#         }


#     timestamp = data.get(
#         "timestamp"
#     )


#     if timestamp:

#         try:

#             activity_time = datetime.fromisoformat(
#                 timestamp.replace(
#                     "Z",
#                     "+00:00"
#                 )
#             )

#         except Exception:

#             activity_time = datetime.now(
#                 timezone.utc
#             )

#     else:

#         activity_time = datetime.now(
#             timezone.utc
#         )


#     activity_time_ist = (
#         activity_time.astimezone(
#             IST
#         )
#     )


#     activity_date = (
#         activity_time_ist.strftime(
#             "%Y-%m-%d"
#         )
#     )


#     # -----------------------------------------------------
#     # Activity details
#     # -----------------------------------------------------

#     latest_application = data.get(
#         "application",
#         "Unknown"
#     )

#     status = data.get(
#         "status",
#         "unknown"
#     )

#     window_title = data.get(
#         "window_title",
#         ""
#     )


#     active_seconds = int(
#         data.get(
#             "active_seconds",
#             0
#         )
#     )


#     application_usage = data.get(
#         "application_usage",
#         {}
#     )


#     if not isinstance(
#         application_usage,
#         dict
#     ):

#         application_usage = {}


#     # =====================================================
#     # LATEST ACTIVITY
#     # =====================================================

#     latest_activity = {

#         "employee_id":
#             employee_id,

#         "status":
#             status,

#         "application":
#             latest_application,

#         "window_title":
#             window_title,

#         "timestamp":
#             timestamp,

#         "last_sync_ist":
#             activity_time_ist.isoformat(),

#         "active_seconds":
#             active_seconds,

#         "active_time":
#             format_duration(
#                 active_seconds
#             ),

#         "application_usage":
#             application_usage
#     }


#     db.collection(
#         "latest_activity"
#     ).document(
#         employee_id
#     ).set(
#         latest_activity
#     )


#     # =====================================================
#     # DAILY ACTIVITY
#     # =====================================================

#     daily_document_id = (
#         f"{employee_id}_{activity_date}"
#     )


#     daily_data = {

#         "employee_id":
#             employee_id,

#         "date":
#             activity_date,

#         "last_application":
#             latest_application,

#         "last_status":
#             status,

#         "last_window":
#             window_title,

#         "last_sync":
#             timestamp,

#         "last_sync_ist":
#             activity_time_ist.isoformat(),

#         "active_seconds":
#             active_seconds,

#         "active_time":
#             format_duration(
#                 active_seconds
#             ),

#         "application_usage":
#             application_usage,

#         "updated_at":
#             firestore.SERVER_TIMESTAMP
#     }


#     db.collection(
#         "daily_activity"
#     ).document(
#         daily_document_id
#     ).set(
#         daily_data,
#         merge=True
#     )


#     # =====================================================
#     # ACTIVITY LOG
#     # =====================================================

#     log_data = {

#         "employee_id":
#             employee_id,

#         "date":
#             activity_date,

#         "status":
#             status,

#         "application":
#             latest_application,

#         "window_title":
#             window_title,

#         "timestamp":
#             timestamp,

#         "active_seconds":
#             active_seconds,

#         "application_usage":
#             application_usage,

#         "created_at":
#             firestore.SERVER_TIMESTAMP
#     }


#     db.collection(
#         "activity_logs"
#     ).add(
#         log_data
#     )


#     # =====================================================
#     # SERVER LOG
#     # =====================================================

#     print(
#         "======================================"
#     )

#     print(
#         "Firebase activity received"
#     )

#     print(
#         "Employee:",
#         employee_id
#     )

#     print(
#         "Date:",
#         activity_date
#     )

#     print(
#         "Application:",
#         latest_application
#     )

#     print(
#         "Active:",
#         format_duration(
#             active_seconds
#         )
#     )

#     print(
#         "======================================"
#     )


#     return {

#         "status":
#             "success",

#         "message":
#             "Activity saved successfully",

#         "employee_id":
#             employee_id,

#         "date":
#             activity_date,

#         "active_time":
#             format_duration(
#                 active_seconds
#             )
#     }


# # =========================================================
# # CURRENT TEAM
# # =========================================================

# @app.get("/api/team")
# def get_team_activity():

#     docs = (
#         db.collection(
#             "latest_activity"
#         ).stream()
#     )


#     employees = [
#         doc.to_dict()
#         for doc in docs
#     ]


#     return {

#         "status":
#             "success",

#         "count":
#             len(employees),

#         "employees":
#             employees
#     }


# # =========================================================
# # DAILY TEAM
# # =========================================================

# @app.get("/api/team/daily")
# def get_daily_team_activity():

#     today = datetime.now(
#         IST
#     ).strftime(
#         "%Y-%m-%d"
#     )


#     docs = (
#         db.collection(
#             "daily_activity"
#         )
#         .where(
#             "date",
#             "==",
#             today
#         )
#         .stream()
#     )


#     employees = [
#         doc.to_dict()
#         for doc in docs
#     ]


#     return {

#         "status":
#             "success",

#         "date":
#             today,

#         "count":
#             len(employees),

#         "employees":
#             employees
#     }


# # =========================================================
# # PARTICULAR EMPLOYEE
# # =========================================================

# @app.get(
#     "/api/employee/{employee_id}"
# )
# def get_employee_activity(
#     employee_id: str
# ):

#     today = datetime.now(
#         IST
#     ).strftime(
#         "%Y-%m-%d"
#     )


#     document_id = (
#         f"{employee_id}_{today}"
#     )


#     doc = (
#         db.collection(
#             "daily_activity"
#         )
#         .document(
#             document_id
#         )
#         .get()
#     )


#     if not doc.exists:

#         return {

#             "status":
#                 "not_found",

#             "message":
#                 "No activity found for today",

#             "employee_id":
#                 employee_id,

#             "date":
#                 today
#         }


#     return {

#         "status":
#             "success",

#         "data":
#             doc.to_dict()
#     }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import firebase_admin
from firebase_admin import credentials, firestore


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceAccountKey.json"

IST = ZoneInfo("Asia/Kolkata")

# If no tracker data is received for this many seconds,
# employee will be considered OFFLINE.
OFFLINE_AFTER_SECONDS = 120


# =========================================================
# FIREBASE INITIALIZATION
# =========================================================

if not firebase_admin._apps:
    cred = credentials.Certificate(str(SERVICE_ACCOUNT_FILE))
    firebase_admin.initialize_app(cred)

db = firestore.client()


# =========================================================
# FASTAPI APP
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
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HELPER FUNCTION
# =========================================================

def format_duration(seconds):
    seconds = int(max(seconds, 0))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return f"{hours}h {minutes}m"


# =========================================================
# PARSE TIMESTAMP
# =========================================================

def parse_timestamp(timestamp):

    if not timestamp:
        return None

    try:

        dt = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt

    except Exception:
        return None


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.get("/")
def home():

    return FileResponse(
        BASE_DIR / "index.html"
    )


# =========================================================
# RECEIVE ACTIVITY FROM EMPLOYEE TRACKER
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

        activity_time = datetime.now(timezone.utc)


    # Convert UTC → IST

    activity_time_ist = activity_time.astimezone(IST)

    activity_date = activity_time_ist.strftime(
        "%Y-%m-%d"
    )


    # -----------------------------------------------------
    # Activity Information
    # -----------------------------------------------------

    latest_application = data.get(
        "application",
        "Unknown"
    )

    window_title = data.get(
        "window_title",
        ""
    )


    # -----------------------------------------------------
    # Time Information
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Application Usage
    # -----------------------------------------------------

    application_usage = data.get(
        "application_usage",
        {}
    )

    if not isinstance(
        application_usage,
        dict
    ):

        application_usage = {}


    # -----------------------------------------------------
    # Tracker is currently sending data
    # Therefore latest status = active
    # Server will later convert it to OFFLINE
    # if no new sync arrives.
    # -----------------------------------------------------

    current_status = "active"


    # =====================================================
    # LATEST ACTIVITY
    # =====================================================

    latest_activity = {

        "employee_id": employee_id,

        "status": current_status,

        "application": latest_application,

        "window_title": window_title,

        "timestamp": activity_time.isoformat(),

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


    # Save latest employee activity

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
            current_status,

        "last_window":
            window_title,

        "last_sync":
            activity_time.isoformat(),

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


    # =====================================================
    # ACTIVITY LOG
    # =====================================================

    log_data = {

        "employee_id":
            employee_id,

        "date":
            activity_date,

        "status":
            current_status,

        "application":
            latest_application,

        "window_title":
            window_title,

        "timestamp":
            activity_time.isoformat(),

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


    # =====================================================
    # RESPONSE
    # =====================================================

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


# =========================================================
# TEAM ACTIVITY
# =========================================================

@app.get("/api/team")
def get_team_activity():

    docs = db.collection(
        "latest_activity"
    ).stream()


    employees = []

    now = datetime.now(
        timezone.utc
    )


    for doc in docs:

        employee = doc.to_dict()


        # -------------------------------------------------
        # Check last sync
        # -------------------------------------------------

        last_sync = employee.get(
            "timestamp"
        )

        last_time = parse_timestamp(
            last_sync
        )


        if last_time is None:

            employee["status"] = "offline"

        else:

            seconds_since_sync = (
                now - last_time
            ).total_seconds()


            # ---------------------------------------------
            # ACTIVE
            # ---------------------------------------------

            if (
                seconds_since_sync
                <= OFFLINE_AFTER_SECONDS
            ):

                employee["status"] = "active"


            # ---------------------------------------------
            # OFFLINE
            # ---------------------------------------------

            else:

                employee["status"] = "offline"


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
        if employee.get("status")
        == "active"
    )

    offline_employees = sum(
        1
        for employee in employees
        if employee.get("status")
        == "offline"
    )


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
# DAILY TEAM ACTIVITY
# =========================================================

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
# INDIVIDUAL EMPLOYEE
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