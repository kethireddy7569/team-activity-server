"""Team Activity Monitoring Server (FastAPI + Firestore) - production build.

Environment variables (set in Vercel -> Settings -> Environment Variables):
  FIREBASE_SERVICE_ACCOUNT_JSON  full service-account JSON (one line)
  TRACKER_API_KEY                shared secret sent by tracker.py in X-API-Key
  DASHBOARD_USER / DASHBOARD_PASSWORD  HTTP Basic login for dashboard + read APIs
  ALLOWED_ORIGINS                optional, comma-separated (default: same-origin only)
  EMPLOYEE_NAMES_JSON            optional {"CRFT-IT-260601": "Name", ...} override
"""
# import json
# import logging
# import os
# import secrets
# from datetime import datetime, timezone
# from pathlib import Path
# from zoneinfo import ZoneInfo

# import firebase_admin
# from fastapi import Depends, FastAPI, HTTPException, Query, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse, JSONResponse
# from fastapi.security import HTTPBasic, HTTPBasicCredentials
# from firebase_admin import credentials, firestore
# from pydantic import BaseModel, ConfigDict, Field

# log = logging.getLogger("team-activity")
# logging.basicConfig(level=logging.INFO)

# BASE_DIR = Path(__file__).resolve().parent
# INDEX_FILE = BASE_DIR / "dashboard" / "index.html"
# IST = ZoneInfo("Asia/Kolkata")
# OFFLINE_THRESHOLD_SECONDS = 180
# MAX_HISTORY_ITEMS = 200

# TRACKER_API_KEY = os.environ.get("TRACKER_API_KEY", "")
# DASHBOARD_USER = os.environ.get("DASHBOARD_USER", "")
# DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "")

# DEFAULT_EMPLOYEE_NAMES = {
#     "CRFT-IT-260601": "Akhila Kethireddy",
#     "CRFT-IT-260701": "Gandikota Sudheer Kumar",
#     "CRFT-IT-260702": "Maddike Karthik Reddy",
#     "CRFT-IT-260703": "Pacchikolla Ravi Kiran",
#     "CRFT-IT-260704": "Tallapalli Siva Prasad",
#     "CRFT-IT-260804": "Kota Srinivasa Reddy",
#     "CRFT-IT-260805": "Kavanuru Soundarya",
# }
# try:
#     EMPLOYEE_NAMES = json.loads(os.environ.get("EMPLOYEE_NAMES_JSON", "")) or DEFAULT_EMPLOYEE_NAMES
# except json.JSONDecodeError:
#     EMPLOYEE_NAMES = DEFAULT_EMPLOYEE_NAMES


# # ---------------------------------------------------------------- Firestore
# _db = None


# def get_db():
#     """Lazy init so a credentials problem returns a clear JSON error, not a crash."""
#     global _db
#     if _db is not None:
#         return _db
#     if not firebase_admin._apps:
#         raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
#         key_file = BASE_DIR / "serviceAccountKey.json"
#         if raw:
#             info = json.loads(raw)
#             if isinstance(info.get("private_key"), str):
#                 info["private_key"] = info["private_key"].replace("\\n", "\n")
#             cred = credentials.Certificate(info)
#         elif key_file.exists():
#             cred = credentials.Certificate(str(key_file))
#         else:
#             raise RuntimeError("Firebase credentials not configured")
#         firebase_admin.initialize_app(cred)
#     _db = firestore.client()
#     return _db


# # ---------------------------------------------------------------------- App
# app = FastAPI(title="Team Activity Monitoring Server", docs_url=None, redoc_url=None, openapi_url=None)

# origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
# if origins:
#     app.add_middleware(
#         CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
#         allow_headers=["X-API-Key", "Content-Type", "Authorization"],
#     )

# basic = HTTPBasic(auto_error=False)


# def require_dashboard(creds: HTTPBasicCredentials = Depends(basic)):
#      if not (DASHBOARD_USER and DASHBOARD_PASSWORD):
#          raise HTTPException(503, "Dashboard login not configured")
#      ok = creds is not None and secrets.compare_digest(
#          creds.username.encode(), DASHBOARD_USER.encode()
#      ) and secrets.compare_digest(creds.password.encode(), DASHBOARD_PASSWORD.encode())
#      if not ok:
#         raise HTTPException(401, "Unauthorized", headers={"WWW-Authenticate": 'Basic realm="Team Activity"'})


# def require_tracker(request: Request):
#      key = request.headers.get("x-api-key", "")
#      if not TRACKER_API_KEY or not secrets.compare_digest(key.encode(), TRACKER_API_KEY.encode()):
#          raise HTTPException(401, "Invalid API key")


# @app.exception_handler(Exception)
# async def unhandled(request: Request, exc: Exception):
#     log.exception("Unhandled error on %s", request.url.path)
#     return JSONResponse({"status": "failed", "message": "Internal server error"}, status_code=500)


# # ------------------------------------------------------------------ Helpers
# def format_duration(seconds):
#     try:
#         seconds = int(max(float(seconds), 0))
#     except (TypeError, ValueError):
#         seconds = 0
#     return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


# def parse_timestamp(value):
#     if not value:
#         return None
#     try:
#         dt = value.to_datetime() if hasattr(value, "to_datetime") else datetime.fromisoformat(
#             str(value).replace("Z", "+00:00"))
#         return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
#     except Exception:
#         return None


# def name_of(employee_id):
#     return EMPLOYEE_NAMES.get(employee_id, "Employee Name Not Configured")


# def valid_date(value):
#     try:
#         datetime.strptime(value, "%Y-%m-%d")
#     except ValueError:
#         raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")


# def clean_usage(usage):
#     if not isinstance(usage, dict):
#         return {}
#     out = {}
#     for k, v in list(usage.items())[:200]:
#         try:
#             out[str(k)[:150].replace("/", "_")] = max(int(v), 0)
#         except (TypeError, ValueError):
#             continue
#     return out


# class ActivityIn(BaseModel):
#     model_config = ConfigDict(extra="ignore")
#     employee_id: str = Field(min_length=1, max_length=64)
#     application: str = Field(default="Unknown", max_length=200)
#     window_title: str = Field(default="", max_length=500)
#     timestamp: str | None = None
#     session_seconds: int = 0
#     active_seconds: int = 0
#     idle_seconds: int = 0
#     application_usage: dict = Field(default_factory=dict)


# class HistoryIn(BaseModel):
#     model_config = ConfigDict(extra="ignore")
#     employee_id: str = Field(min_length=1, max_length=64)
#     browser: str = "Chrome"
#     history: list[dict] = Field(default_factory=list)


# # ------------------------------------------------------------------- Routes
# @app.get("/")
# def home(_=Depends(require_dashboard)):
#      if INDEX_FILE.exists():
#          return FileResponse(INDEX_FILE)
#      return {"status": "success", "message": "Team Activity Monitoring Server is running"}


# @app.get("/health")
# def health():
#     """Public liveness check. Add ?deep=1 to also test Firestore."""
#     return {"status": "success", "message": "Server is running"}


# @app.get("/health/deep")
# def health_deep(_=Depends(require_dashboard)):
#      try:
#          list(get_db().collection("latest_activity").limit(1).stream())
#          return {"status": "success", "firestore": "ok"}
#      except Exception as e:
#          log.exception("Deep health failed")
#          return JSONResponse({"status": "failed", "firestore": type(e).__name__}, status_code=503)

# @app.post("/api/activity", dependencies=[Depends(require_tracker)])
# def receive_activity(data: ActivityIn):
#     db = get_db()
#     ts = parse_timestamp(data.timestamp) or datetime.now(timezone.utc)
#     ts_ist = ts.astimezone(IST)
#     date = ts_ist.strftime("%Y-%m-%d")

#     session = max(data.session_seconds, 0)
#     active = min(max(data.active_seconds, 0), session)
#     idle = min(max(data.idle_seconds, 0), session)
#     usage = clean_usage(data.application_usage)
#     emp = data.employee_id

#     common = {
#         "employee_id": emp, "employee_name": name_of(emp),
#         "session_seconds": session, "session_time": format_duration(session),
#         "active_seconds": active, "active_time": format_duration(active),
#         "idle_seconds": idle, "idle_time": format_duration(idle),
#         "application_usage": usage,
#     }
#     iso = ts.isoformat()

#     batch = db.batch()
#     batch.set(db.collection("latest_activity").document(emp), {
#         **common, "status": "active", "application": data.application,
#         "window_title": data.window_title, "timestamp": iso, "last_sync_ist": ts_ist.isoformat(),
#     })
#     batch.set(db.collection("daily_activity").document(f"{emp}_{date}"), {
#         **common, "date": date, "last_application": data.application, "last_status": "active",
#         "last_window": data.window_title, "last_sync": iso, "last_sync_ist": ts_ist.isoformat(),
#         "updated_at": firestore.SERVER_TIMESTAMP,
#     }, merge=True)
#     batch.set(db.collection("activity_logs").document(), {
#         "employee_id": emp, "employee_name": name_of(emp), "date": date, "status": "active",
#         "application": data.application, "window_title": data.window_title, "timestamp": iso,
#         "session_seconds": session, "active_seconds": active, "idle_seconds": idle,
#         "application_usage": usage, "created_at": firestore.SERVER_TIMESTAMP,
#     })
#     batch.commit()

#     log.info("activity %s | %s | active %s", emp, data.application, format_duration(active))
#     return {"status": "success", "employee_id": emp, "message": "Activity saved successfully"}


#  @app.post("/api/browser-history", dependencies=[Depends(require_tracker)])
# def receive_browser_history(data: HistoryIn):
#     db = get_db()
#     batch, saved = db.batch(), 0
#     for item in data.history[:MAX_HISTORY_ITEMS]:
#         url = str(item.get("url", ""))[:2000]
#         if not url:
#             continue
#         batch.set(db.collection("browser_history").document(), {
#             "employee_id": data.employee_id, "employee_name": name_of(data.employee_id),
#             "browser": data.browser, "url": url,
#             "title": str(item.get("title") or "Untitled")[:300],
#             "visit_time": item.get("visit_time"), "created_at": firestore.SERVER_TIMESTAMP,
#         })
#         saved += 1
#     if saved:
#         batch.commit()
#     return {"status": "success", "employee_id": data.employee_id, "saved_count": saved,
#             "message": "Browser history saved successfully"}


# app.get("/api/browser-history", dependencies=[Depends(require_dashboard)])
# def get_browser_history(employee_id: str = Query(..., max_length=64),
#                         date: str | None = Query(default=None),
#                         limit: int = Query(default=50, ge=1, le=500)):
#     if date:
#         valid_date(date)
#     docs = get_db().collection("browser_history").where("employee_id", "==", employee_id).stream()
#     history = []
#     for doc in docs:
#         item = doc.to_dict()
#         t = parse_timestamp(item.get("visit_time"))
#         if t is None:
#             continue
#         t_ist = t.astimezone(IST)
#         if date and t_ist.strftime("%Y-%m-%d") != date:
#             continue
#         history.append({
#             "employee_id": employee_id,
#             "employee_name": item.get("employee_name", name_of(employee_id)),
#             "browser": item.get("browser", "Chrome"),
#             "title": item.get("title") or "Untitled",
#             "url": item.get("url", ""),
#             "visit_time": t_ist.isoformat(),
#         })
#     history.sort(key=lambda x: x["visit_time"], reverse=True)
#     history = history[:limit]
#     return {"status": "success", "employee_id": employee_id, "employee_name": name_of(employee_id),
#             "date": date, "count": len(history), "history": history}


# @app.get("/api/team", dependencies=[Depends(require_dashboard)])
# def get_team_activity():
#     now = datetime.now(timezone.utc)
#     employees = []
#     for doc in get_db().collection("latest_activity").stream():
#         emp = doc.to_dict()
#         last = parse_timestamp(emp.get("timestamp"))
#         if last is None:
#             emp["status"], emp["seconds_since_last_sync"] = "offline", None
#         else:
#             gap = max((now - last).total_seconds(), 0)
#             emp["seconds_since_last_sync"] = int(gap)
#             emp["status"] = "active" if gap <= OFFLINE_THRESHOLD_SECONDS else "offline"
#             emp["last_sync_ist"] = last.astimezone(IST).isoformat()
#         emp["employee_name"] = name_of(emp.get("employee_id", ""))
#         employees.append(emp)
#     active = sum(1 for e in employees if e["status"] == "active")
#     return {"status": "success", "count": len(employees), "total_employees": len(employees),
#             "active_employees": active, "offline_employees": len(employees) - active,
#             "employees": employees}


# @app.get("/api/team/daily", dependencies=[Depends(require_dashboard)])
# def get_daily_team_activity(date: str | None = Query(default=None)):
#     selected = date or datetime.now(IST).strftime("%Y-%m-%d")
#     valid_date(selected)
#     employees = []
#     for doc in get_db().collection("daily_activity").where("date", "==", selected).stream():
#         emp = doc.to_dict()
#         emp["employee_name"] = name_of(emp.get("employee_id", ""))
#         emp.pop("updated_at", None)  # Firestore timestamp is not JSON-serialisable by default
#         employees.append(emp)
#     return {"status": "success", "date": selected, "count": len(employees), "employees": employees}


# @app.get("/api/employee/{employee_id}", dependencies=[Depends(require_dashboard)])
# def get_employee_activity(employee_id: str):
#     today = datetime.now(IST).strftime("%Y-%m-%d")
#     doc = get_db().collection("daily_activity").document(f"{employee_id}_{today}").get()
#     if not doc.exists:
#         return {"status": "not_found", "message": "No activity found for today",
#                 "employee_id": employee_id, "date": today}
#     data = doc.to_dict()
#     data["employee_name"] = name_of(employee_id)
#     data.pop("updated_at", None)
#     return {"status": "success", "data": data}
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import firebase_admin
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from firebase_admin import credentials, firestore
from pydantic import BaseModel, ConfigDict, Field

log = logging.getLogger("team-activity")
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "dashboard" / "index.html"
IST = ZoneInfo("Asia/Kolkata")
OFFLINE_THRESHOLD_SECONDS = 180
MAX_HISTORY_ITEMS = 200

DEFAULT_EMPLOYEE_NAMES = {
    "CRFT-IT-260601": "Akhila Kethireddy",
    "CRFT-IT-260701": "Gandikota Sudheer Kumar",
    "CRFT-IT-260702": "Maddike Karthik Reddy",
    "CRFT-IT-260703": "Pacchikolla Ravi Kiran",
    "CRFT-IT-260704": "Tallapalli Siva Prasad",
    "CRFT-IT-260804": "Kota Srinivasa Reddy",
    "CRFT-IT-260805": "Kavanuru Soundarya",
}

try:
    EMPLOYEE_NAMES = json.loads(
        os.environ.get("EMPLOYEE_NAMES_JSON", "")
    ) or DEFAULT_EMPLOYEE_NAMES
except json.JSONDecodeError:
    EMPLOYEE_NAMES = DEFAULT_EMPLOYEE_NAMES


# ---------------------------------------------------------------- Firestore
_db = None


def get_db():
    """Lazy init so a credentials problem returns a clear JSON error, not a crash."""
    global _db

    if _db is not None:
        return _db

    if not firebase_admin._apps:
        raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        key_file = BASE_DIR / "serviceAccountKey.json"

        if raw:
            info = json.loads(raw)

            if isinstance(info.get("private_key"), str):
                info["private_key"] = info["private_key"].replace("\\n", "\n")

            cred = credentials.Certificate(info)

        elif key_file.exists():
            cred = credentials.Certificate(str(key_file))

        else:
            raise RuntimeError("Firebase credentials not configured")

        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db


# ---------------------------------------------------------------------- App
app = FastAPI(
    title="Team Activity Monitoring Server",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

origins = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]

if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["X-API-Key", "Content-Type", "Authorization"],
    )


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        {
            "status": "failed",
            "message": "Internal server error"
        },
        status_code=500
    )


# ------------------------------------------------------------------ Helpers
def format_duration(seconds):
    try:
        seconds = int(max(float(seconds), 0))
    except (TypeError, ValueError):
        seconds = 0

    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def parse_timestamp(value):
    if not value:
        return None

    try:
        dt = (
            value.to_datetime()
            if hasattr(value, "to_datetime")
            else datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        )

        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    except Exception:
        return None


def name_of(employee_id):
    return EMPLOYEE_NAMES.get(
        employee_id,
        "Employee Name Not Configured"
    )


def valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            400,
            "Invalid date format. Use YYYY-MM-DD."
        )


def clean_usage(usage):
    if not isinstance(usage, dict):
        return {}

    out = {}

    for k, v in list(usage.items())[:200]:
        try:
            out[str(k)[:150].replace("/", "_")] = max(int(v), 0)
        except (TypeError, ValueError):
            continue

    return out


class ActivityIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    employee_id: str = Field(
        min_length=1,
        max_length=64
    )

    application: str = Field(
        default="Unknown",
        max_length=200
    )

    window_title: str = Field(
        default="",
        max_length=500
    )

    timestamp: str | None = None

    session_seconds: int = 0
    active_seconds: int = 0
    idle_seconds: int = 0

    application_usage: dict = Field(
        default_factory=dict
    )


class HistoryIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    employee_id: str = Field(
        min_length=1,
        max_length=64
    )

    browser: str = "Chrome"

    history: list[dict] = Field(
        default_factory=list
    )


# ------------------------------------------------------------------- Routes
@app.get("/")
def home():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)

    return {
        "status": "success",
        "message": "Team Activity Monitoring Server is running"
    }


@app.get("/health")
def health():
    """Public liveness check. Add ?deep=1 to also test Firestore."""
    return {
        "status": "success",
        "message": "Server is running"
    }


@app.get("/health/deep")
def health_deep():
    try:
        list(
            get_db()
            .collection("latest_activity")
            .limit(1)
            .stream()
        )

        return {
            "status": "success",
            "firestore": "ok"
        }

    except Exception as e:
        log.exception("Deep health failed")

        return JSONResponse(
            {
                "status": "failed",
                "firestore": type(e).__name__
            },
            status_code=503
        )


@app.post("/api/activity")
def receive_activity(data: ActivityIn):
    db = get_db()

    ts = parse_timestamp(data.timestamp) or datetime.now(timezone.utc)

    ts_ist = ts.astimezone(IST)

    date = ts_ist.strftime("%Y-%m-%d")

    session = max(data.session_seconds, 0)

    active = min(
        max(data.active_seconds, 0),
        session
    )

    idle = min(
        max(data.idle_seconds, 0),
        session
    )

    usage = clean_usage(data.application_usage)

    emp = data.employee_id

    common = {
        "employee_id": emp,
        "employee_name": name_of(emp),

        "session_seconds": session,
        "session_time": format_duration(session),

        "active_seconds": active,
        "active_time": format_duration(active),

        "idle_seconds": idle,
        "idle_time": format_duration(idle),

        "application_usage": usage,
    }

    iso = ts.isoformat()

    batch = db.batch()

    batch.set(
        db.collection("latest_activity").document(emp),
        {
            **common,
            "status": "active",
            "application": data.application,
            "window_title": data.window_title,
            "timestamp": iso,
            "last_sync_ist": ts_ist.isoformat(),
        }
    )

    batch.set(
        db.collection("daily_activity").document(
            f"{emp}_{date}"
        ),
        {
            **common,
            "date": date,
            "last_application": data.application,
            "last_status": "active",
            "last_window": data.window_title,
            "last_sync": iso,
            "last_sync_ist": ts_ist.isoformat(),
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True
    )

    batch.set(
        db.collection("activity_logs").document(),
        {
            "employee_id": emp,
            "employee_name": name_of(emp),
            "date": date,
            "status": "active",
            "application": data.application,
            "window_title": data.window_title,
            "timestamp": iso,
            "session_seconds": session,
            "active_seconds": active,
            "idle_seconds": idle,
            "application_usage": usage,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )

    batch.commit()

    log.info(
        "activity %s | %s | active %s",
        emp,
        data.application,
        format_duration(active)
    )

    return {
        "status": "success",
        "employee_id": emp,
        "message": "Activity saved successfully"
    }


@app.post("/api/browser-history")
def receive_browser_history(data: HistoryIn):
    db = get_db()

    batch, saved = db.batch(), 0

    for item in data.history[:MAX_HISTORY_ITEMS]:

        url = str(item.get("url", ""))[:2000]

        if not url:
            continue

        batch.set(
            db.collection("browser_history").document(),
            {
                "employee_id": data.employee_id,
                "employee_name": name_of(data.employee_id),
                "browser": data.browser,
                "url": url,
                "title": str(
                    item.get("title") or "Untitled"
                )[:300],
                "visit_time": item.get("visit_time"),
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )

        saved += 1

    if saved:
        batch.commit()

    return {
        "status": "success",
        "employee_id": data.employee_id,
        "saved_count": saved,
        "message": "Browser history saved successfully"
    }


@app.get("/api/browser-history")
def get_browser_history(
    employee_id: str = Query(..., max_length=64),
    date: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500)
):
    if date:
        valid_date(date)

    docs = (
        get_db()
        .collection("browser_history")
        .where("employee_id", "==", employee_id)
        .stream()
    )

    history = []

    for doc in docs:
        item = doc.to_dict()

        t = parse_timestamp(
            item.get("visit_time")
        )

        if t is None:
            continue

        t_ist = t.astimezone(IST)

        if date and t_ist.strftime("%Y-%m-%d") != date:
            continue

        history.append(
            {
                "employee_id": employee_id,
                "employee_name": item.get(
                    "employee_name",
                    name_of(employee_id)
                ),
                "browser": item.get(
                    "browser",
                    "Chrome"
                ),
                "title": item.get("title") or "Untitled",
                "url": item.get("url", ""),
                "visit_time": t_ist.isoformat(),
            }
        )

    history.sort(
        key=lambda x: x["visit_time"],
        reverse=True
    )

    history = history[:limit]

    return {
        "status": "success",
        "employee_id": employee_id,
        "employee_name": name_of(employee_id),
        "date": date,
        "count": len(history),
        "history": history
    }


@app.get("/api/team")
def get_team_activity():
    now = datetime.now(timezone.utc)

    employees = []

    for doc in (
        get_db()
        .collection("latest_activity")
        .stream()
    ):
        emp = doc.to_dict()

        last = parse_timestamp(
            emp.get("timestamp")
        )

        if last is None:
            emp["status"] = "offline"
            emp["seconds_since_last_sync"] = None

        else:
            gap = max(
                (now - last).total_seconds(),
                0
            )

            emp["seconds_since_last_sync"] = int(gap)

            emp["status"] = (
                "active"
                if gap <= OFFLINE_THRESHOLD_SECONDS
                else "offline"
            )

            emp["last_sync_ist"] = (
                last.astimezone(IST).isoformat()
            )

        emp["employee_name"] = name_of(
            emp.get("employee_id", "")
        )

        employees.append(emp)

    active = sum(
        1
        for e in employees
        if e["status"] == "active"
    )

    return {
        "status": "success",
        "count": len(employees),
        "total_employees": len(employees),
        "active_employees": active,
        "offline_employees": len(employees) - active,
        "employees": employees
    }


@app.get("/api/team/daily")
def get_daily_team_activity(
    date: str | None = Query(default=None)
):
    selected = (
        date
        or datetime.now(IST).strftime("%Y-%m-%d")
    )

    valid_date(selected)

    employees = []

    for doc in (
        get_db()
        .collection("daily_activity")
        .where("date", "==", selected)
        .stream()
    ):
        emp = doc.to_dict()

        emp["employee_name"] = name_of(
            emp.get("employee_id", "")
        )

        emp.pop(
            "updated_at",
            None
        )

        employees.append(emp)

    return {
        "status": "success",
        "date": selected,
        "count": len(employees),
        "employees": employees
    }


@app.get("/api/employee/{employee_id}")
def get_employee_activity(employee_id: str):
    today = datetime.now(IST).strftime("%Y-%m-%d")

    doc = (
        get_db()
        .collection("daily_activity")
        .document(
            f"{employee_id}_{today}"
        )
        .get()
    )

    if not doc.exists:
        return {
            "status": "not_found",
            "message": "No activity found for today",
            "employee_id": employee_id,
            "date": today
        }

    data = doc.to_dict()

    data["employee_name"] = name_of(
        employee_id
    )

    data.pop(
        "updated_at",
        None
    )

    return {
        "status": "success",
        "data": data
    }