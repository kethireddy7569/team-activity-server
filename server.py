from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import os
import json

import firebase_admin
from firebase_admin import credentials, firestore


# ============================================================
# BASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SERVICE_ACCOUNT_FILE = (
    BASE_DIR / "serviceAccountKey.json"
)

IST = ZoneInfo("Asia/Kolkata")

OFFLINE_THRESHOLD_SECONDS = 180


# ============================================================
# FIREBASE INITIALIZATION
# ============================================================

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

            firebase_admin.initialize_app(
                cred
            )

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

        firebase_admin.initialize_app(
            cred
        )

        print(
            "Firebase initialized using serviceAccountKey.json."
        )

    else:

        raise RuntimeError(
            "Firebase credentials not found."
        )


db = firestore.client()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Team Activity Monitoring Server"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# EMPLOYEE MAPPING
# ============================================================

EMPLOYEE_NAMES = {

    "CRFT-IT-260601":
        "Akhila Kethireddy",

    "CRFT-IT-260701":
        "Gandikota Sudheer Kumar",

    "CRFT-IT-260702":
        "Maddike Karthik Reddy",

    "CRFT-IT-260703":
        "Pacchikolla Ravi Kiran",

    "CRFT-IT-260704":
        "Tallapalli Siva Prasad",

    "CRFT-IT-260804":
        "Kota Srinivasa Reddy",

    "CRFT-IT-260805":
        "Kavanuru Soundarya"
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_duration(seconds):

    try:

        seconds = int(
            max(
                float(seconds),
                0
            )
        )

    except Exception:

        seconds = 0

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    return (
        f"{hours}h {minutes}m"
    )


def parse_timestamp(timestamp):

    if not timestamp:

        return None

    try:

        # Firestore Timestamp
        if hasattr(
            timestamp,
            "to_datetime"
        ):

            dt = timestamp.to_datetime()

        else:

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


def get_employee_name(employee_id):

    return EMPLOYEE_NAMES.get(
        employee_id,
        "Employee Name Not Configured"
    )


def add_employee_details(employee):

    employee_id = employee.get(
        "employee_id",
        ""
    )

    employee["employee_name"] = (
        get_employee_name(
            employee_id
        )
    )

    return employee


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    index_file = (
        BASE_DIR / "index.html"
    )

    if index_file.exists():

        return FileResponse(
            index_file
        )

    return {

        "status":
            "success",

        "message":
            "Team Activity Monitoring Server is running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {

        "status":
            "success",

        "message":
            "Server is running"
    }


# ============================================================
# RECEIVE ACTIVITY
# ============================================================

@app.post("/api/activity")
def receive_activity(data: dict):

    employee_id = data.get(
        "employee_id"
    )

    if not employee_id:

        return {

            "status":
                "failed",

            "message":
                "employee_id is required"
        }


    timestamp = data.get(
        "timestamp"
    )


    activity_time = (
        parse_timestamp(
            timestamp
        )
    )


    if activity_time is None:

        activity_time = (
            datetime.now(
                timezone.utc
            )
        )

        timestamp = (
            activity_time.isoformat()
        )


    activity_time_ist = (
        activity_time.astimezone(
            IST
        )
    )


    activity_date = (
        activity_time_ist.strftime(
            "%Y-%m-%d"
        )
    )


    latest_application = data.get(
        "application",
        "Unknown"
    )


    window_title = data.get(
        "window_title",
        ""
    )


    session_seconds = int(
        data.get(
            "session_seconds",
            0
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


    application_usage = data.get(
        "application_usage",
        {}
    )


    if not isinstance(
        application_usage,
        dict
    ):

        application_usage = {}


    session_seconds = max(
        session_seconds,
        0
    )


    active_seconds = max(
        active_seconds,
        0
    )


    idle_seconds = max(
        idle_seconds,
        0
    )


    active_seconds = min(
        active_seconds,
        session_seconds
    )


    idle_seconds = min(
        idle_seconds,
        session_seconds
    )


    # ========================================================
    # LATEST ACTIVITY
    # ========================================================

    latest_activity = {

        "employee_id":
            employee_id,

        "employee_name":
            get_employee_name(
                employee_id
            ),

        "status":
            "active",

        "application":
            latest_application,

        "window_title":
            window_title,

        "timestamp":
            timestamp,

        "last_sync_ist":
            activity_time_ist.isoformat(),

        "session_seconds":
            session_seconds,

        "session_time":
            format_duration(
                session_seconds
            ),

        "active_seconds":
            active_seconds,

        "active_time":
            format_duration(
                active_seconds
            ),

        "idle_seconds":
            idle_seconds,

        "idle_time":
            format_duration(
                idle_seconds
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


    # ========================================================
    # DAILY ACTIVITY
    # ========================================================

    daily_document_id = (
        f"{employee_id}_{activity_date}"
    )


    daily_data = {

        "employee_id":
            employee_id,

        "employee_name":
            get_employee_name(
                employee_id
            ),

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

        "session_seconds":
            session_seconds,

        "session_time":
            format_duration(
                session_seconds
            ),

        "active_seconds":
            active_seconds,

        "active_time":
            format_duration(
                active_seconds
            ),

        "idle_seconds":
            idle_seconds,

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


    # ========================================================
    # ACTIVITY LOG
    # ========================================================

    log_data = {

        "employee_id":
            employee_id,

        "employee_name":
            get_employee_name(
                employee_id
            ),

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

        "session_seconds":
            session_seconds,

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


    print(
        f"[ACTIVITY] "
        f"{employee_id} | "
        f"{latest_application} | "
        f"Active: "
        f"{format_duration(active_seconds)} | "
        f"Idle: "
        f"{format_duration(idle_seconds)} | "
        f"{timestamp}"
    )


    return {

        "status":
            "success",

        "employee_id":
            employee_id,

        "message":
            "Activity saved successfully"
    }


# ============================================================
# RECEIVE BROWSER HISTORY
# ============================================================

@app.post("/api/browser-history")
def receive_browser_history(data: dict):

    employee_id = data.get(
        "employee_id"
    )

    if not employee_id:

        return {

            "status":
                "failed",

            "message":
                "employee_id is required"
        }


    browser = data.get(
        "browser",
        "Chrome"
    )


    history_items = data.get(
        "history",
        []
    )


    if not isinstance(
        history_items,
        list
    ):

        return {

            "status":
                "failed",

            "message":
                "history must be a list"
        }


    saved_count = 0


    for item in history_items:

        if not isinstance(
            item,
            dict
        ):

            continue


        url = item.get(
            "url",
            ""
        )


        title = item.get(
            "title",
            ""
        )


        visit_time = item.get(
            "visit_time"
        )


        if not url:

            continue


        history_data = {

            "employee_id":
                employee_id,

            "employee_name":
                get_employee_name(
                    employee_id
                ),

            "browser":
                browser,

            "url":
                url,

            "title":
                title or "Untitled",

            "visit_time":
                visit_time,

            "created_at":
                firestore.SERVER_TIMESTAMP
        }


        db.collection(
            "browser_history"
        ).add(
            history_data
        )


        saved_count += 1


    print(
        f"[BROWSER HISTORY] "
        f"{employee_id} | "
        f"{browser} | "
        f"Saved: {saved_count}"
    )


    return {

        "status":
            "success",

        "employee_id":
            employee_id,

        "saved_count":
            saved_count,

        "message":
            "Browser history saved successfully"
    }


# ============================================================
# GET BROWSER HISTORY
# DATE FILTER INCLUDED
# ============================================================

@app.get("/api/browser-history")
def get_browser_history(

    employee_id: str = Query(...),

    date: str = Query(
        default=None
    ),

    limit: int = Query(
        default=50,
        ge=1,
        le=500
    )

):

    # --------------------------------------------------------
    # Validate selected date
    # --------------------------------------------------------

    if date:

        try:

            datetime.strptime(
                date,
                "%Y-%m-%d"
            )

        except ValueError:

            return {

                "status":
                    "failed",

                "message":
                    "Invalid date format. Use YYYY-MM-DD."
            }


    # --------------------------------------------------------
    # Get employee browser history
    # --------------------------------------------------------

    docs = (
        db.collection(
            "browser_history"
        )
        .where(
            "employee_id",
            "==",
            employee_id
        )
        .stream()
    )


    history = []


    for doc in docs:

        item = doc.to_dict()


        visit_time = item.get(
            "visit_time"
        )


        parsed_time = (
            parse_timestamp(
                visit_time
            )
        )


        if parsed_time is None:

            continue


        # Convert to IST
        visit_time_ist = (
            parsed_time.astimezone(
                IST
            )
        )


        # ----------------------------------------------------
        # DATE FILTER
        # ----------------------------------------------------

        if date:

            visit_date = (
                visit_time_ist.strftime(
                    "%Y-%m-%d"
                )
            )


            if visit_date != date:

                continue


        # ----------------------------------------------------
        # Prepare response
        # ----------------------------------------------------

        history.append({

            "employee_id":
                employee_id,

            "employee_name":
                item.get(
                    "employee_name",
                    get_employee_name(
                        employee_id
                    )
                ),

            "browser":
                item.get(
                    "browser",
                    "Chrome"
                ),

            "title":
                item.get(
                    "title"
                ) or "Untitled",

            "url":
                item.get(
                    "url",
                    ""
                ),

            "visit_time":
                visit_time_ist.isoformat()

        })


    # --------------------------------------------------------
    # Latest first
    # --------------------------------------------------------

    history.sort(
        key=lambda x:
            x.get(
                "visit_time",
                ""
            ),
        reverse=True
    )


    # Apply limit AFTER date filtering
    history = history[:limit]


    return {

        "status":
            "success",

        "employee_id":
            employee_id,

        "employee_name":
            get_employee_name(
                employee_id
            ),

        "date":
            date,

        "count":
            len(history),

        "history":
            history
    }


# ============================================================
# LIVE TEAM ACTIVITY
# ============================================================

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


    for doc in docs:

        employee = doc.to_dict()


        last_sync = employee.get(
            "timestamp"
        )


        last_time = (
            parse_timestamp(
                last_sync
            )
        )


        if last_time is None:

            employee["status"] = (
                "offline"
            )

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


            if (
                seconds_since_sync
                <= OFFLINE_THRESHOLD_SECONDS
            ):

                employee["status"] = (
                    "active"
                )

            else:

                employee["status"] = (
                    "offline"
                )


            employee[
                "last_sync_ist"
            ] = (
                last_time
                .astimezone(
                    IST
                )
                .isoformat()
            )


        add_employee_details(
            employee
        )


        employees.append(
            employee
        )


    total_employees = len(
        employees
    )


    active_employees = sum(

        1

        for employee
        in employees

        if employee.get(
            "status"
        ) == "active"

    )


    offline_employees = (
        total_employees
        - active_employees
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


# ============================================================
# DAILY TEAM ACTIVITY
# ============================================================

@app.get("/api/team/daily")
def get_daily_team_activity(

    date: str = Query(
        default=None
    )

):

    if not date:

        selected_date = (
            datetime.now(
                IST
            ).strftime(
                "%Y-%m-%d"
            )
        )

    else:

        try:

            datetime.strptime(
                date,
                "%Y-%m-%d"
            )

            selected_date = date

        except ValueError:

            return {

                "status":
                    "failed",

                "message":
                    "Invalid date format. Use YYYY-MM-DD."
            }


    docs = (
        db.collection(
            "daily_activity"
        )
        .where(
            "date",
            "==",
            selected_date
        )
        .stream()
    )


    employees = []


    for doc in docs:

        employee = doc.to_dict()


        add_employee_details(
            employee
        )


        employees.append(
            employee
        )


    return {

        "status":
            "success",

        "date":
            selected_date,

        "count":
            len(employees),

        "employees":
            employees
    }


# ============================================================
# SINGLE EMPLOYEE
# ============================================================

@app.get(
    "/api/employee/{employee_id}"
)
def get_employee_activity(
    employee_id: str
):

    today = (
        datetime.now(
            IST
        ).strftime(
            "%Y-%m-%d"
        )
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


    employee_data = (
        doc.to_dict()
    )


    add_employee_details(
        employee_data
    )


    return {

        "status":
            "success",

        "data":
            employee_data
    }


# ============================================================
# LOCAL RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn


    uvicorn.run(

        "server:app",

        host="0.0.0.0",

        port=8000,

        reload=True
    )