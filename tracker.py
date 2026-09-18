# # # import requests
# # # import time
# # # from datetime import datetime, timezone

# # # # --------------------------------------------------
# # # # CONFIGURATION
# # # # --------------------------------------------------

# # # EMPLOYEE_ID = "CRFT-IT-260601"

# # # # ActivityWatch running on the employee's laptop
# # # ACTIVITYWATCH_URL = "http://127.0.0.1:5600"

# # # # Our Vercel live server
# # # SERVER_URL = "https://team-activity-server.vercel.app"

# # # # Send latest activity every 1 second
# # # INTERVAL = 3600


# # # # --------------------------------------------------
# # # # FIND ACTIVITYWATCH WINDOW BUCKET
# # # # --------------------------------------------------

# # # def get_window_bucket():

# # #     try:
# # #         response = requests.get(
# # #             f"{ACTIVITYWATCH_URL}/api/0/buckets",
# # #             timeout=5
# # #         )

# # #         response.raise_for_status()

# # #         buckets = response.json()

# # #         for bucket_id, bucket in buckets.items():

# # #             bucket_type = bucket.get("type", "").lower()

# # #             if bucket_type == "currentwindow":
# # #                 return bucket_id

# # #         # Fallback: find bucket containing "window"
# # #         for bucket_id in buckets:

# # #             if "window" in bucket_id.lower():
# # #                 return bucket_id

# # #         return None

# # #     except Exception as e:

# # #         print("ActivityWatch connection error:", e)
# # #         return None


# # # # --------------------------------------------------
# # # # GET LATEST ACTIVITY
# # # # --------------------------------------------------

# # # def get_latest_activity(bucket_id):

# # #     try:

# # #         response = requests.get(
# # #             f"{ACTIVITYWATCH_URL}/api/0/buckets/{bucket_id}/events",
# # #             timeout=5
# # #         )

# # #         response.raise_for_status()

# # #         events = response.json()

# # #         if not events:
# # #             return {
# # #                 "status": "idle",
# # #                 "application": "unknown"
# # #             }

# # #         # Get latest event
# # #         latest_event = max(
# # #             events,
# # #             key=lambda event: event.get("timestamp", "")
# # #         )

# # #         event_data = latest_event.get("data", {})

# # #         application = (
# # #             event_data.get("app")
# # #             or event_data.get("application")
# # #             or event_data.get("title")
# # #             or "unknown"
# # #         )

# # #         title = event_data.get("title", "")

# # #         return {
# # #             "status": "active",
# # #             "application": application,
# # #             "window_title": title
# # #         }

# # #     except Exception as e:

# # #         print("ActivityWatch data error:", e)

# # #         return {
# # #             "status": "unknown",
# # #             "application": "unknown"
# # #         }


# # # # --------------------------------------------------
# # # # SEND ACTIVITY TO VERCEL SERVER
# # # # --------------------------------------------------

# # # def send_activity(activity):

# # #     payload = {
# # #         "employee_id": EMPLOYEE_ID,
# # #         "status": activity.get("status", "unknown"),
# # #         "application": activity.get("application", "unknown"),
# # #         "timestamp": datetime.now(timezone.utc).isoformat()
# # #     }

# # #     try:

# # #         response = requests.post(
# # #             f"{SERVER_URL}/api/activity",
# # #             json=payload,
# # #             timeout=10
# # #         )

# # #         print(
# # #             "Server:",
# # #             response.status_code,
# # #             response.text
# # #         )

# # #     except Exception as e:

# # #         print("Server connection error:", e)


# # # # --------------------------------------------------
# # # # MAIN TRACKER
# # # # --------------------------------------------------

# # # def main():

# # #     print("===================================")
# # #     print(" Team Activity Tracker Started")
# # #     print(" Employee ID:", EMPLOYEE_ID)
# # #     print(" ActivityWatch:", ACTIVITYWATCH_URL)
# # #     print(" Server:", SERVER_URL)
# # #     print("===================================")

# # #     bucket_id = get_window_bucket()

# # #     if not bucket_id:

# # #         print(
# # #             "ERROR: ActivityWatch window bucket not found."
# # #         )

# # #         print(
# # #             "Please make sure ActivityWatch is running."
# # #         )

# # #         return

# # #     print("ActivityWatch bucket:", bucket_id)

# # #     while True:

# # #         activity = get_latest_activity(bucket_id)

# # #         print("Activity:", activity)

# # #         send_activity(activity)

# # #         time.sleep(INTERVAL)


# # # # --------------------------------------------------
# # # # START
# # # # --------------------------------------------------

# # # if __name__ == "__main__":
# # #     main()

# import requests
# import time
# from datetime import datetime, timezone

# EMPLOYEE_ID = "CRFT-IT-260601"

# ACTIVITYWATCH_URL = "http://127.0.0.1:5600"

# SERVER_URL = "https://team-activity-server.vercel.app"

# INTERVAL = 10


# def get_window_bucket():
#       try:
#           response = requests.get(
#               f"{ACTIVITYWATCH_URL}/api/0/buckets",
#               timeout=5
#           )

#           response.raise_for_status()

#           buckets = response.json()

#           for bucket_id, bucket in buckets.items():
#               if bucket.get("type", "").lower() == "currentwindow":
#                   return bucket_id

#           for bucket_id in buckets:
#               if "window" in bucket_id.lower():
#                   return bucket_id

#           return None

#       except Exception as e:
#           print("ActivityWatch connection error:", e)
#           return None


# def get_latest_activity(bucket_id):
#       try:
#           response = requests.get(
#               f"{ACTIVITYWATCH_URL}/api/0/buckets/{bucket_id}/events",
#              timeout=5
#           )

#           response.raise_for_status()

#           events = response.json()

#           if not events:
#               return {
#                   "status": "idle",
#                   "application": "unknown",
#                   "window_title": ""
#               }

#           latest_event = max(
#               events,
#               key=lambda event: event.get("timestamp", "")
#          )

#           data = latest_event.get("data", {})

#           return {
#               "status": "active",
#               "application": (
#                   data.get("app")
#                   or data.get("application")
#                   or "unknown"
#               ),
#               "window_title": data.get("title", "")
#           }

#       except Exception as e:
#           print("ActivityWatch data error:", e)

#           return {
#               "status": "unknown",
#               "application": "unknown",
#               "window_title": ""
#           }


# def send_activity(activity):

#       payload = {
#           "employee_id": EMPLOYEE_ID,
#           "status": activity.get("status", "unknown"),
#           "application": activity.get("application", "unknown"),
#           "window_title": activity.get("window_title", ""),
#           "timestamp": datetime.now(timezone.utc).isoformat()
#       }

#       try:
#           response = requests.post(
#               f"{SERVER_URL}/api/activity",
#               json=payload,
#               timeout=10
#           )

#           print("Server:", response.status_code, response.text)

#       except Exception as e:
#           print("Server connection error:", e)


# def main():

#       print("===================================")
#       print(" Team Activity Tracker Started")
#       print(" Employee ID:", EMPLOYEE_ID)
#       print(" ActivityWatch:", ACTIVITYWATCH_URL)
#       print(" Server:", SERVER_URL)
#       print("===================================")

#       bucket_id = get_window_bucket()

#       if not bucket_id:
#           print("ERROR: ActivityWatch window bucket not found.")
#           print("Please make sure ActivityWatch is running.")
#           return

#       print("ActivityWatch bucket:", bucket_id)

#       while True:

#           activity = get_latest_activity(bucket_id)

#           print("Activity:", activity)

#           send_activity(activity)

#           time.sleep(INTERVAL)


# if __name__ == "__main__":
#       main()

# # import requests
# # import time
# # from datetime import datetime, timezone


# # # ==========================================
# # # CONFIGURATION
# # # ==========================================

# # EMPLOYEE_ID = "CRFT-IT-260601"

# # ACTIVITYWATCH_URL = "http://127.0.0.1:5600"

# # SERVER_URL = "https://team-activity-server.vercel.app"
# # #SERVER_URL = "http://127.0.0.1:8000"

# # # 3600 seconds = 1 hour
# # INTERVAL = 3600


# # # ==========================================
# # # FIND ACTIVITYWATCH WINDOW BUCKET
# # # ==========================================

# # def get_window_bucket():

# #     try:
# #         response = requests.get(
# #             f"{ACTIVITYWATCH_URL}/api/0/buckets",
# #             timeout=5
# #         )

# #         response.raise_for_status()

# #         buckets = response.json()

# #         # First preference: currentwindow bucket
# #         for bucket_id, bucket in buckets.items():

# #             bucket_type = bucket.get("type", "").lower()

# #             if bucket_type == "currentwindow":
# #                 return bucket_id

# #         # Fallback: any bucket containing "window"
# #         for bucket_id in buckets:

# #             if "window" in bucket_id.lower():
# #                 return bucket_id

# #         return None

# #     except Exception as e:

# #         print("ActivityWatch connection error:", e)

# #         return None


# # # ==========================================
# # # GET LATEST ACTIVITY
# # # ==========================================

# # def get_latest_activity(bucket_id):

# #     try:

# #         response = requests.get(
# #             f"{ACTIVITYWATCH_URL}/api/0/buckets/{bucket_id}/events",
# #             timeout=5
# #         )

# #         response.raise_for_status()

# #         events = response.json()

# #         # No activity found
# #         if not events:

# #             return {
# #                 "status": "idle",
# #                 "application": "Unknown",
# #                 "window_title": ""
# #             }

# #         # Get latest event
# #         latest_event = max(
# #             events,
# #             key=lambda event: event.get("timestamp", "")
# #         )

# #         event_data = latest_event.get("data", {})

# #         # Application name
# #         application_raw = (
# #             event_data.get("app")
# #             or event_data.get("application")
# #             or event_data.get("title")
# #             or "Unknown"
# #         )

# #         # Clean application name
# #         application_name = str(application_raw)

# #         if application_name.lower().endswith(".exe"):
# #             application_name = application_name[:-4]

# #         application_name = application_name.replace("_", " ").strip()

# #         # Window title
# #         title = event_data.get("title", "")

# #         return {
# #             "status": "active",
# #             "application": application_name,
# #             "window_title": application_name
# #         }

# #     except Exception as e:

# #         print("ActivityWatch data error:", e)

# #         return {
# #             "status": "unknown",
# #             "application": "Unknown",
# #             "window_title": ""
# #         }


# # # ==========================================
# # # SEND ACTIVITY TO SERVER
# # # ==========================================

# # def send_activity(activity):

# #     payload = {

# #         "employee_id": EMPLOYEE_ID,

# #         "status": activity.get(
# #             "status",
# #             "unknown"
# #         ),

# #         "application": activity.get(
# #             "application",
# #             "Unknown"
# #         ),

# #         "window_title": activity.get(
# #             "window_title",
# #             ""
# #         ),

# #         "timestamp": datetime.now(
# #             timezone.utc
# #         ).isoformat()
# #     }

# #     try:

# #         response = requests.post(

# #             f"{SERVER_URL}/api/activity",

# #             json=payload,

# #             timeout=10
# #         )

# #         print(
# #             "Server:",
# #             response.status_code,
# #             response.text
# #         )

# #     except Exception as e:

# #         print(
# #             "Server connection error:",
# #             e
# #         )


# # # ==========================================
# # # MAIN TRACKER
# # # ==========================================

# # def main():

# #     print("===================================")
# #     print(" Team Activity Tracker Started")
# #     print("===================================")

# #     print(
# #         "Employee ID:",
# #         EMPLOYEE_ID
# #     )

# #     print(
# #         "ActivityWatch:",
# #         ACTIVITYWATCH_URL
# #     )

# #     print(
# #         "Server:",
# #         SERVER_URL
# #     )

# #     print(
# #         "Interval:",
# #         INTERVAL,
# #         "seconds"
# #     )

# #     print("===================================")

# #     # Find ActivityWatch bucket
# #     bucket_id = get_window_bucket()

# #     if not bucket_id:

# #         print(
# #             "ERROR: ActivityWatch window bucket not found."
# #         )

# #         print(
# #             "Please make sure ActivityWatch is running."
# #         )

# #         return

# #     print(
# #         "ActivityWatch bucket:",
# #         bucket_id
# #     )

# #     print("Tracker is running...")
# #     print("===================================")

# #     # Continuous tracking
# #     while True:

# #         # Get latest ActivityWatch activity
# #         activity = get_latest_activity(bucket_id)

# #         print(
# #             "Activity:",
# #             activity
# #         )

# #         # Send activity to server
# #         send_activity(activity)

# #         # Wait for next interval
# #         time.sleep(INTERVAL)


# # # ==========================================
# # # START PROGRAM
# # # ==========================================

# # if __name__ == "__main__":
# #     main()
import requests
import time
from datetime import datetime, timezone, timedelta


EMPLOYEE_ID = "CRFT-IT-260601"

# ActivityWatch local server
ACTIVITYWATCH_URL = "http://127.0.0.1:5600"

# Your Vercel API
SERVER_URL = "https://team-activity-server.vercel.app"

# Check/send interval
INTERVAL = 60

# Company working hours
WORK_START_HOUR = 10
WORK_START_MINUTE = 0

WORK_END_HOUR = 19
WORK_END_MINUTE = 0

# Expected working time
EXPECTED_WORKING_SECONDS = 8 * 60 * 60



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


def find_afk_bucket(buckets):
    for bucket_id, bucket in buckets.items():

        bucket_type = str(
            bucket.get("type", "")
        ).lower()

        if bucket_type == "afkstatus":
            return bucket_id

    for bucket_id in buckets:

        if "afk" in bucket_id.lower():
            return bucket_id

    return None


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

    application = application.replace("_", " ")

    return application.strip()


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


def get_working_window():

    now = datetime.now().astimezone()

    start = now.replace(
        hour=WORK_START_HOUR,
        minute=WORK_START_MINUTE,
        second=0,
        microsecond=0
    )

    end = now.replace(
        hour=WORK_END_HOUR,
        minute=WORK_END_MINUTE,
        second=0,
        microsecond=0
    )

    return start, end



def calculate_application_usage(events):

    work_start, work_end = get_working_window()

    application_usage = {}

    for event in events:

        timestamp = event.get("timestamp")

        if not timestamp:
            continue

        event_start = parse_timestamp(timestamp)

        if event_start is None:
            continue

        duration = float(
            event.get("duration", 0)
        )

        if duration <= 0:
            continue

        event_end = (
            event_start +
            timedelta(seconds=duration)
        )

        # Ignore events outside working hours
        if event_end <= work_start:
            continue

        if event_start >= work_end:
            continue

        # Limit event to working hours
        actual_start = max(
            event_start,
            work_start
        )

        actual_end = min(
            event_end,
            work_end
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


def calculate_afk_time(events):

    work_start, work_end = get_working_window()

    afk_seconds = 0

    for event in events:

        timestamp = event.get("timestamp")

        if not timestamp:
            continue

        event_start = parse_timestamp(timestamp)

        if event_start is None:
            continue

        duration = float(
            event.get("duration", 0)
        )

        if duration <= 0:
            continue

        event_end = (
            event_start +
            timedelta(seconds=duration)
        )

        status = str(
            event.get("data", {}).get(
                "status",
                ""
            )
        ).lower()

        # ActivityWatch AFK commonly uses "afk"
        if status != "afk":
            continue

        if event_end <= work_start:
            continue

        if event_start >= work_end:
            continue

        actual_start = max(
            event_start,
            work_start
        )

        actual_end = min(
            event_end,
            work_end
        )

        seconds = (
            actual_end - actual_start
        ).total_seconds()

        if seconds > 0:
            afk_seconds += seconds

    return afk_seconds


def format_duration(seconds):

    seconds = int(max(seconds, 0))

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    return f"{hours}h {minutes}m"


def send_activity(
    latest_application,
    application_usage,
    afk_seconds
):

    total_app_seconds = sum(
        application_usage.values()
    )

    # Do not allow active time to exceed 8 hours
    active_seconds = min(
        total_app_seconds,
        EXPECTED_WORKING_SECONDS
    )

    payload = {

        "employee_id": EMPLOYEE_ID,

        "status": "active"
        if active_seconds > 0
        else "idle",

        "application":
            latest_application,

        "window_title":
            latest_application,

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "expected_working_seconds":
            EXPECTED_WORKING_SECONDS,

        "active_seconds":
            int(active_seconds),

        "idle_seconds":
            int(afk_seconds),

        "expected_working_time":
            format_duration(
                EXPECTED_WORKING_SECONDS
            ),

        "active_time":
            format_duration(
                active_seconds
            ),

        "idle_time":
            format_duration(
                afk_seconds
            ),

        "application_usage": {

            app: format_duration(seconds)

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


def main():

    print("======================================")
    print("     TEAM ACTIVITY TRACKER")
    print("======================================")

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
        "Working Hours: 10:00 AM - 7:00 PM"
    )

    print(
        "Expected Working Time: 8 hours"
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

    afk_bucket = find_afk_bucket(
        buckets
    )

    print(
        "Window bucket:",
        window_bucket
    )

    print(
        "AFK bucket:",
        afk_bucket
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

        afk_bucket = find_afk_bucket(
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

        afk_events = []

        if afk_bucket:

            afk_events = get_events(
                afk_bucket
            )

       

        application_usage = (
            calculate_application_usage(
                window_events
            )
        )

        

        afk_seconds = (
            calculate_afk_time(
                afk_events
            )
        )

        
        latest_application = "Unknown"

        if window_events:

            valid_events = []

            for event in window_events:

                if event.get("timestamp"):

                    valid_events.append(
                        event
                    )

            if valid_events:

                latest_event = max(
                    valid_events,
                    key=lambda e:
                    e.get(
                        "timestamp",
                        ""
                    )
                )

                latest_application = (
                    clean_application_name(
                        latest_event
                    )
                )

    

        total_active = sum(
            application_usage.values()
        )

        print("--------------------------------------")

        print(
            "Latest Application:",
            latest_application
        )

        print(
            "Active Time:",
            format_duration(
                total_active
            )
        )

        print(
            "AFK / Idle Time:",
            format_duration(
                afk_seconds
            )
        )

        print(
            "Expected Time:",
            format_duration(
                EXPECTED_WORKING_SECONDS
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
                format_duration(seconds)
            )

        # --------------------------------
        # Send to server
        # --------------------------------

        send_activity(
            latest_application,
            application_usage,
            afk_seconds
        )

        time.sleep(
            INTERVAL
        )



if __name__ == "__main__":
    try:

        main()

    except KeyboardInterrupt:

        print()
        print(
            "Tracker stopped."
        )