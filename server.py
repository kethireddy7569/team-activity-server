"""Team Activity Monitoring Server (FastAPI + Supabase)."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from supabase import create_client

load_dotenv()

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
    EMPLOYEE_NAMES = (
        json.loads(os.environ.get("EMPLOYEE_NAMES_JSON", ""))
        or DEFAULT_EMPLOYEE_NAMES
    )
except (json.JSONDecodeError, TypeError):
    EMPLOYEE_NAMES = DEFAULT_EMPLOYEE_NAMES


# ---------------------------------------------------------- Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
_supabase = None


def get_db():
    global _supabase

    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL or SUPABASE_KEY is missing"
            )

        _supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

    return _supabase


# ---------------------------------------------------------------- App
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
        allow_headers=[
            "X-API-Key",
            "Content-Type",
            "Authorization"
        ],
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


# ------------------------------------------------------------- Helpers
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

        return dt if dt.tzinfo else dt.replace(
            tzinfo=timezone.utc
        )

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
            out[str(k)[:150].replace("/", "_")] = max(
                int(v), 0
            )
        except (TypeError, ValueError):
            continue

    return out


def rows(table):
    """Return all rows from a Supabase table."""
    response = get_db().table(table).select("*").execute()
    return response.data or []


class ActivityIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    employee_id: str = Field(min_length=1, max_length=64)
    application: str = Field(default="Unknown", max_length=200)
    window_title: str = Field(default="", max_length=500)
    timestamp: str | None = None
    session_seconds: int = 0
    active_seconds: int = 0
    idle_seconds: int = 0
    application_usage: dict = Field(default_factory=dict)


class HistoryIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    employee_id: str = Field(min_length=1, max_length=64)
    browser: str = "Chrome"
    history: list[dict] = Field(default_factory=list)


# ---------------------------------------------------------------- Routes
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
    return {
        "status": "success",
        "message": "Server is running"
    }


@app.get("/health/deep")
def health_deep():
    try:
        get_db().table("latest_activity").select(
            "employee_id"
        ).limit(1).execute()

        return {
            "status": "success",
            "supabase": "ok"
        }

    except Exception as e:
        log.exception("Supabase health check failed")
        return JSONResponse(
            {
                "status": "failed",
                "supabase": type(e).__name__
            },
            status_code=503
        )


@app.post("/api/activity")
def receive_activity(data: ActivityIn):
    db = get_db()

    ts = parse_timestamp(data.timestamp) or datetime.now(
        timezone.utc
    )
    ts_ist = ts.astimezone(IST)
    date = ts_ist.strftime("%Y-%m-%d")

    session = max(data.session_seconds, 0)
    active = min(max(data.active_seconds, 0), session)
    idle = min(max(data.idle_seconds, 0), session)
    usage = clean_usage(data.application_usage)
    emp = data.employee_id
    iso = ts.isoformat()

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

    latest = {
        **common,
        "status": "active",
        "application": data.application,
        "window_title": data.window_title,
        "timestamp": iso,
        "last_sync_ist": ts_ist.isoformat(),
    }

    daily = {
        **common,
        "employee_id": emp,
        "date": date,
        "last_application": data.application,
        "last_status": "active",
        "last_window": data.window_title,
        "last_sync": iso,
        "last_sync_ist": ts_ist.isoformat(),
    }

    # latest_activity: one row per employee
    db.table("latest_activity").upsert(
        latest,
        on_conflict="employee_id"
    ).execute()

    # daily_activity: one row per employee per date
    db.table("daily_activity").upsert(
        daily,
        on_conflict="employee_id,date"
    ).execute()

    # activity_logs: preserve each incoming activity record
    db.table("activity_logs").insert({
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
    }).execute()

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
    records = []

    for item in data.history[:MAX_HISTORY_ITEMS]:
        url = str(item.get("url", ""))[:2000]

        if not url:
            continue

        records.append({
            "employee_id": data.employee_id,
            "employee_name": name_of(data.employee_id),
            "browser": data.browser,
            "url": url,
            "title": str(
                item.get("title") or "Untitled"
            )[:300],
            "visit_time": item.get("visit_time"),
        })

    if records:
        db.table("browser_history").insert(records).execute()

    return {
        "status": "success",
        "employee_id": data.employee_id,
        "saved_count": len(records),
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

    result = (
        get_db()
        .table("browser_history")
        .select("*")
        .eq("employee_id", employee_id)
        .execute()
    )

    history = []

    for item in result.data or []:
        t = parse_timestamp(item.get("visit_time"))

        if t is None:
            continue

        t_ist = t.astimezone(IST)

        if date and t_ist.strftime("%Y-%m-%d") != date:
            continue

        history.append({
            "employee_id": employee_id,
            "employee_name": item.get(
                "employee_name",
                name_of(employee_id)
            ),
            "browser": item.get("browser", "Chrome"),
            "title": item.get("title") or "Untitled",
            "url": item.get("url", ""),
            "visit_time": t_ist.isoformat(),
        })

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
    db_rows = rows("latest_activity")

    # Keep every configured employee visible, even before
    # their first activity record arrives.
    by_id = {
        emp.get("employee_id"): emp
        for emp in db_rows
        if emp.get("employee_id")
    }

    employees = []

    for employee_id, employee_name in EMPLOYEE_NAMES.items():
        emp = dict(by_id.get(employee_id, {}))
        emp["employee_id"] = employee_id
        emp["employee_name"] = employee_name

        last = parse_timestamp(emp.get("timestamp"))

        if last is None:
            emp["status"] = "offline"
            emp["seconds_since_last_sync"] = None
        else:
            gap = max((now - last).total_seconds(), 0)
            emp["seconds_since_last_sync"] = int(gap)
            emp["status"] = (
                "active"
                if gap <= OFFLINE_THRESHOLD_SECONDS
                else "offline"
            )
            emp["last_sync_ist"] = last.astimezone(
                IST
            ).isoformat()

        employees.append(emp)

    active = sum(
        1 for employee in employees
        if employee["status"] == "active"
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
    selected = date or datetime.now(IST).strftime("%Y-%m-%d")
    valid_date(selected)

    result = (
        get_db()
        .table("daily_activity")
        .select("*")
        .eq("date", selected)
        .execute()
    )

    by_id = {
        emp.get("employee_id"): emp
        for emp in (result.data or [])
        if emp.get("employee_id")
    }

    employees = []

    for employee_id, employee_name in EMPLOYEE_NAMES.items():
        emp = dict(by_id.get(employee_id, {}))
        emp["employee_id"] = employee_id
        emp["employee_name"] = employee_name
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

    result = (
        get_db()
        .table("daily_activity")
        .select("*")
        .eq("employee_id", employee_id)
        .eq("date", today)
        .limit(1)
        .execute()
    )

    if not result.data:
        return {
            "status": "not_found",
            "message": "No activity found for today",
            "employee_id": employee_id,
            "employee_name": name_of(employee_id),
            "date": today
        }

    data = result.data[0]
    data["employee_name"] = name_of(employee_id)

    return {
        "status": "success",
        "data": data
    }