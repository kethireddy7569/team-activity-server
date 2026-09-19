import requests
import time
from datetime import datetime, timezone, timedelta

# =========================================================
# CONFIGURATION
# =========================================================

EMPLOYEE_ID = "CRFT-IT-260601"

ACTIVITYWATCH_URL = "http://127.0.0.1:5600"

SERVER_URL = "https://team-activity-server.vercel.app"

INTERVAL = 60


# =========================================================
# ACTIVITYWATCH CONNECTION
# =========================================================

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


# =========================================================
# FIND WINDOW BUCKET
# =========================================================

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


# =========================================================
# GET EVENTS
# =========================================================

def get_events(bucket_id):

    if not bucket_id:

        return []

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


# =========================================================
# PARSE TIMESTAMP
# =========================================================

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


# =========================================================
# APPLICATION NAME
# =========================================================

def clean_application_name(event):

    data = event.get(
        "data",
        {}
    )

    application = (
        data.get("app")
        or data.get("application")
        or data.get("title")
        or "Unknown"
    )

    application = str(
        application
    )

    if application.lower().endswith(".exe"):

        application = application[:-4]

    application = application.replace(
        "_",
        " "
    )

    return application.strip()


# =========================================================
# GET EVENT INTERVALS
# =========================================================

def get_application_intervals(events):

    intervals = []

    for event in events:

        timestamp = event.get(
            "timestamp"
        )

        if not timestamp:

            continue

        start = parse_timestamp(
            timestamp
        )

        if start is None:

            continue

        try:

            duration = float(
                event.get(
                    "duration",
                    0
                )
            )

        except Exception:

            continue

        if duration <= 0:

            continue

        end = start + timedelta(
            seconds=duration
        )

        application = clean_application_name(
            event
        )

        intervals.append(
            (
                start,
                end,
                application
            )
        )

    return intervals


# =========================================================
# MERGE OVERLAPPING INTERVALS
# =========================================================

def merge_intervals(intervals):

    if not intervals:

        return []

    sorted_intervals = sorted(
        intervals,
        key=lambda x: x[0]
    )

    merged = []

    current_start = sorted_intervals[0][0]
    current_end = sorted_intervals[0][1]

    for start, end in sorted_intervals[1:]:

        if start <= current_end:

            if end > current_end:

                current_end = end

        else:

            merged.append(
                (
                    current_start,
                    current_end
                )
            )

            current_start = start
            current_end = end

    merged.append(
        (
            current_start,
            current_end
        )
    )

    return merged


# =========================================================
# CALCULATE TOTAL OBSERVED ACTIVITY
# =========================================================

def calculate_observed_activity(events):

    intervals = get_application_intervals(
        events
    )

    if not intervals:

        return 0

    merged = merge_intervals(
        [
            (
                start,
                end
            )
            for start, end, app in intervals
        ]
    )

    total_seconds = 0

    for start, end in merged:

        seconds = (
            end - start
        ).total_seconds()

        if seconds > 0:

            total_seconds += seconds

    return int(
        total_seconds
    )


# =========================================================
# CALCULATE APPLICATION USAGE
# =========================================================

def calculate_application_usage(events):

    intervals = get_application_intervals(
        events
    )

    if not intervals:

        return {}

    application_usage = {}

    for start, end, application in intervals:

        seconds = (
            end - start
        ).total_seconds()

        if seconds <= 0:

            continue

        application_usage[application] = (
            application_usage.get(
                application,
                0
            )
            + seconds
        )

    return application_usage


# =========================================================
# GET LATEST APPLICATION
# =========================================================

def get_latest_application(events):

    valid_events = []

    for event in events:

        timestamp = event.get(
            "timestamp"
        )

        if not timestamp:

            continue

        parsed = parse_timestamp(
            timestamp
        )

        if parsed:

            valid_events.append(
                (
                    parsed,
                    event
                )
            )

    if not valid_events:

        return "Unknown"

    latest_event = max(
        valid_events,
        key=lambda x: x[0]
    )[1]

    return clean_application_name(
        latest_event
    )


# =========================================================
# FORMAT DURATION
# =========================================================

def format_duration(seconds):

    seconds = int(
        max(seconds, 0)
    )

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    return f"{hours}h {minutes}m"


# =========================================================
# SEND DATA TO SERVER
# =========================================================

def send_activity(
    latest_application,
    application_usage,
    active_seconds
):

    payload = {

        "employee_id":
            EMPLOYEE_ID,

        "status":
            "active"
            if active_seconds > 0
            else "inactive",

        "application":
            latest_application,

        "window_title":
            latest_application,

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "active_seconds":
            int(active_seconds),

        "active_time":
            format_duration(
                active_seconds
            ),

        "application_usage":
            {
                app:
                    format_duration(
                        seconds
                    )
                for app, seconds
                in application_usage.items()
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


# =========================================================
# MAIN
# =========================================================

def main():

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
        "Tracking: Laptop Activity Session"
    )

    print(
        "AFK/Idle tracking: Disabled"
    )

    print(
        "======================================"
    )


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


    print(
        "Tracker started successfully."
    )

    print(
        "Press CTRL+C to stop during testing."
    )

    print(
        "======================================"
    )


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


        window_events = get_events(
            window_bucket
        )


        application_usage = (
            calculate_application_usage(
                window_events
            )
        )


        active_seconds = (
            calculate_observed_activity(
                window_events
            )
        )


        latest_application = (
            get_latest_application(
                window_events
            )
        )


        print(
            "--------------------------------------"
        )

        print(
            "Latest Application:",
            latest_application
        )

        print(
            "Observed Active Time:",
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


        send_activity(
            latest_application,
            application_usage,
            active_seconds
        )


        time.sleep(
            INTERVAL
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()

        print(
            "Tracker stopped."
        )