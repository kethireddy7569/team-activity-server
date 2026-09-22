import requests
import time
from datetime import datetime, timezone, timedelta

# ============================================================
# CONFIGURATION
# ============================================================

EMPLOYEE_ID = "CRFT-IT-260601"

ACTIVITYWATCH_URL = "http://127.0.0.1:5600"

SERVER_URL = "https://team-activity-server.vercel.app"

# Data will be sent every 60 seconds
INTERVAL = 60


# ============================================================
# SESSION START
# ============================================================

# Tracker start ayina time ni current session start ga consider chestunnam
SESSION_START = datetime.now(timezone.utc)

print("Session started at:", SESSION_START.isoformat())


# ============================================================
# GET ACTIVITYWATCH BUCKETS
# ============================================================

def get_buckets():

    try:

        response = requests.get(
            f"{ACTIVITYWATCH_URL}/api/0/buckets",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        print("ActivityWatch connection error:", e)

        return {}


# ============================================================
# FIND WINDOW BUCKET
# ============================================================

def find_window_bucket(buckets):

    for bucket_id, bucket in buckets.items():

        bucket_type = str(
            bucket.get("type", "")
        ).lower()

        if bucket_type == "currentwindow":

            return bucket_id


    for bucket_id in buckets:

        if "window" in bucket_id.lower():

            return bucket_id


    return None


# ============================================================
# GET EVENTS
# ============================================================

def get_events(bucket_id):

    try:

        response = requests.get(
            f"{ACTIVITYWATCH_URL}/api/0/buckets/{bucket_id}/events",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        print(
            f"Error reading bucket {bucket_id}:",
            e
        )

        return []


# ============================================================
# PARSE TIMESTAMP
# ============================================================

def parse_timestamp(timestamp):

    try:

        dt = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt

    except Exception:

        return None


# ============================================================
# APPLICATION NAME
# ============================================================

def clean_application_name(event):

    data = event.get("data", {})

    application = (
        data.get("app")
        or data.get("application")
        or data.get("title")
        or "Unknown"
    )

    application = str(application)

    if application.lower().endswith(".exe"):

        application = application[:-4]

    application = application.replace(
        "_",
        " "
    )

    return application.strip()


# ============================================================
# FORMAT DURATION
# ============================================================

def format_duration(seconds):

    seconds = int(
        max(seconds, 0)
    )

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    return f"{hours}h {minutes}m"


# ============================================================
# CALCULATE APPLICATION USAGE
# ============================================================

def calculate_application_usage(events):

    application_usage = {}

    # Current time
    now = datetime.now(timezone.utc)

    for event in events:

        timestamp = event.get(
            "timestamp"
        )

        if not timestamp:

            continue

        event_start = parse_timestamp(
            timestamp
        )

        if event_start is None:

            continue

        duration = float(
            event.get(
                "duration",
                0
            )
        )

        if duration <= 0:

            continue

        event_end = (
            event_start
            + timedelta(
                seconds=duration
            )
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Ignore events BEFORE current tracker session
        # ----------------------------------------------------

        if event_end <= SESSION_START:

            continue

        # Ignore events that haven't happened yet

        if event_start >= now:

            continue

        # ----------------------------------------------------
        # Limit event to current session
        # ----------------------------------------------------

        actual_start = max(
            event_start,
            SESSION_START
        )

        actual_end = min(
            event_end,
            now
        )

        actual_duration = (
            actual_end - actual_start
        ).total_seconds()

        if actual_duration <= 0:

            continue

        application = clean_application_name(
            event
        )

        application_usage[application] = (
            application_usage.get(
                application,
                0
            )
            + actual_duration
        )

    return application_usage


# ============================================================
# GET LATEST APPLICATION
# ============================================================

def get_latest_application(events):

    if not events:

        return "Unknown"

    now = datetime.now(timezone.utc)

    valid_events = []

    for event in events:

        timestamp = event.get(
            "timestamp"
        )

        if not timestamp:

            continue

        event_time = parse_timestamp(
            timestamp
        )

        if event_time is None:

            continue

        if event_time < SESSION_START:

            continue

        if event_time > now:

            continue

        valid_events.append(event)

    if not valid_events:

        return "Unknown"

    latest_event = max(
        valid_events,
        key=lambda e: e.get(
            "timestamp",
            ""
        )
    )

    return clean_application_name(
        latest_event
    )


# ============================================================
# SEND DATA TO VERCEL
# ============================================================

def send_activity(
    latest_application,
    application_usage
):

    now = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # Session duration
    # --------------------------------------------------------

    session_seconds = (
        now - SESSION_START
    ).total_seconds()

    if session_seconds < 0:

        session_seconds = 0

    # --------------------------------------------------------
    # Total application usage
    # --------------------------------------------------------

    total_application_seconds = sum(
        application_usage.values()
    )

    # Active application time cannot exceed session time
    active_seconds = min(
        total_application_seconds,
        session_seconds
    )

    payload = {

        "employee_id":
            EMPLOYEE_ID,

        "status":
            "active"
            if latest_application != "Unknown"
            else "unknown",

        "application":
            latest_application,

        "window_title":
            latest_application,

        "timestamp":
            now.isoformat(),

        # ----------------------------------------------------
        # SESSION INFORMATION
        # ----------------------------------------------------

        "session_start":
            SESSION_START.isoformat(),

        "session_seconds":
            int(session_seconds),

        "session_time":
            format_duration(
                session_seconds
            ),

        # ----------------------------------------------------
        # ACTIVE APPLICATION TIME
        # ----------------------------------------------------

        "active_seconds":
            int(active_seconds),

        "active_time":
            format_duration(
                active_seconds
            ),

        # ----------------------------------------------------
        # AFK / IDLE NOT USED
        # ----------------------------------------------------

        "idle_seconds":
            0,

        "idle_time":
            "0h 0m",

        # ----------------------------------------------------
        # APPLICATION-WISE USAGE
        # ----------------------------------------------------

        "application_usage": {

            app: format_duration(seconds)

            for app, seconds
            in sorted(
                application_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )
        }
    }


    try:

        response = requests.post(

            f"{SERVER_URL}/api/activity",

            json=payload,

            timeout=15

        )

        print(
            "Server:",
            response.status_code
        )


        if response.status_code == 200:

            print(
                "Data sent successfully"
            )

        else:

            print(
                response.text
            )


    except Exception as e:

        print(
            "Server connection error:",
            e
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "======================================"
    )

    print(
        "       TEAM ACTIVITY TRACKER"
    )

    print(
        "======================================"
    )

    print(
        "Employee ID:",
        EMPLOYEE_ID
    )

    print(
        "ActivityWatch:",
        ACTIVITYWATCH_URL
    )

    print(
        "Server:",
        SERVER_URL
    )

    print(
        "Session Start:",
        SESSION_START.astimezone().strftime(
            "%d-%m-%Y %I:%M:%S %p"
        )
    )

    print(
        "======================================"
    )


    # --------------------------------------------------------
    # CHECK ACTIVITYWATCH
    # --------------------------------------------------------

    buckets = get_buckets()

    if not buckets:

        print(
            "ERROR: ActivityWatch is not running."
        )

        return


    window_bucket = find_window_bucket(
        buckets
    )


    print(
        "Window bucket:",
        window_bucket
    )


    if not window_bucket:

        print(
            "ERROR: Window bucket not found."
        )

        return


    print()
    print(
        "Tracker started successfully."
    )

    print(
        "Historical ActivityWatch data will NOT be counted."
    )

    print(
        "Only current session data will be counted."
    )

    print(
        "Press CTRL+C to stop during testing."
    )

    print(
        "======================================"
    )


    # ========================================================
    # TRACKING LOOP
    # ========================================================

    while True:

        buckets = get_buckets()

        window_bucket = find_window_bucket(
            buckets
        )


        if not window_bucket:

            print(
                "Window bucket unavailable."
            )

            time.sleep(
                INTERVAL
            )

            continue


        # ----------------------------------------------------
        # Get window events
        # ----------------------------------------------------

        window_events = get_events(
            window_bucket
        )


        # ----------------------------------------------------
        # Application usage
        # ----------------------------------------------------

        application_usage = (
            calculate_application_usage(
                window_events
            )
        )


        # ----------------------------------------------------
        # Latest application
        # ----------------------------------------------------

        latest_application = (
            get_latest_application(
                window_events
            )
        )


        # ----------------------------------------------------
        # Session duration
        # ----------------------------------------------------

        now = datetime.now(
            timezone.utc
        )

        session_seconds = (
            now - SESSION_START
        ).total_seconds()


        # ----------------------------------------------------
        # Active application duration
        # ----------------------------------------------------

        active_seconds = min(
            sum(
                application_usage.values()
            ),
            session_seconds
        )


        # ====================================================
        # DISPLAY
        # ====================================================

        print()
        print(
            "--------------------------------------"
        )

        print(
            "Latest Application:",
            latest_application
        )

        print(
            "Session Time:",
            format_duration(
                session_seconds
            )
        )

        print(
            "Application Active Time:",
            format_duration(
                active_seconds
            )
        )

        print(
            "Application Usage:"
        )


        for app, seconds in sorted(

            application_usage.items(),

            key=lambda x: x[1],

            reverse=True

        ):

            print(
                "  ",
                app,
                "→",
                format_duration(
                    seconds
                )
            )


        print(
            "--------------------------------------"
        )


        # ----------------------------------------------------
        # SEND TO SERVER
        # ----------------------------------------------------

        send_activity(

            latest_application,

            application_usage

        )


        # ----------------------------------------------------
        # Wait
        # ----------------------------------------------------

        time.sleep(
            INTERVAL
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()
        print(
            "Tracker stopped."
        )