# import requests
# import time

# from datetime import (
#     datetime,
#     timezone,
#     timedelta
# )


# EMPLOYEE_ID = "CRFT-IT-260601"



# ACTIVITYWATCH_URL = (
#     "http://127.0.0.1:5600"
# )

# SERVER_URL = (
#     "https://team-activity-server.vercel.app"
# )



# # Send data every 60 seconds

# INTERVAL = 60




# SESSION_START = datetime.now(
#     timezone.utc
# )



# def get_buckets():

#     try:

#         response = requests.get(
#             f"{ACTIVITYWATCH_URL}/api/0/buckets",
#             timeout=10
#         )

#         response.raise_for_status()

#         return response.json()

#     except Exception as e:

#         print(
#             "ActivityWatch connection error:",
#             e
#         )

#         return {}




# def find_window_bucket(buckets):

#     # First preference:
#     # currentwindow bucket

#     for bucket_id, bucket in buckets.items():

#         bucket_type = str(
#             bucket.get(
#                 "type",
#                 ""
#             )
#         ).lower()

#         if bucket_type == "currentwindow":

#             return bucket_id




#     for bucket_id in buckets:

#         if "window" in bucket_id.lower():

#             return bucket_id


#     return None


# def get_events(bucket_id):

#     try:

#         response = requests.get(
#             f"{ACTIVITYWATCH_URL}/api/0/buckets/"
#             f"{bucket_id}/events",
#             timeout=10
#         )

#         response.raise_for_status()

#         return response.json()

#     except Exception as e:

#         print(
#             f"Error reading bucket {bucket_id}:",
#             e
#         )

#         return []



# def parse_timestamp(timestamp):

#     try:

#         dt = datetime.fromisoformat(
#             timestamp.replace(
#                 "Z",
#                 "+00:00"
#             )
#         )

#         if dt.tzinfo is None:

#             dt = dt.replace(
#                 tzinfo=timezone.utc
#             )

#         return dt

#     except Exception:

#         return None



# def clean_application_name(event):

#     data = event.get(
#         "data",
#         {}
#     )

#     application = (
#         data.get("app")
#         or data.get("application")
#         or data.get("title")
#         or "Unknown"
#     )

#     application = str(
#         application
#     )

#     if application.lower().endswith(
#         ".exe"
#     ):

#         application = application[:-4]


#     application = (
#         application
#         .replace("_", " ")
#         .strip()
#     )

#     return application



# def format_duration(seconds):

#     seconds = int(
#         max(seconds, 0)
#     )

#     hours = seconds // 3600

#     minutes = (
#         seconds % 3600
#     ) // 60

#     return f"{hours}h {minutes}m"


# def calculate_application_usage(events):

#     application_usage = {}

#     now = datetime.now(
#         timezone.utc
#     )


#     for event in events:

#         timestamp = event.get(
#             "timestamp"
#         )

#         if not timestamp:

#             continue


#         event_start = parse_timestamp(
#             timestamp
#         )

#         if event_start is None:

#             continue


#         duration = float(
#             event.get(
#                 "duration",
#                 0
#             )
#         )

#         if duration <= 0:

#             continue


#         event_end = (
#             event_start
#             + timedelta(
#                 seconds=duration
#             )
#         )


    

#         if event_end <= SESSION_START:

#             continue


#         # Ignore future events

#         if event_start >= now:

#             continue


#         actual_start = max(
#             event_start,
#             SESSION_START
#         )

#         actual_end = min(
#             event_end,
#             now
#         )


#         actual_duration = (
#             actual_end
#             - actual_start
#         ).total_seconds()


#         if actual_duration <= 0:

#             continue


#         application = (
#             clean_application_name(
#                 event
#             )
#         )


#         application_usage[
#             application
#         ] = (
#             application_usage.get(
#                 application,
#                 0
#             )
#             + actual_duration
#         )


#     return application_usage



# def get_latest_application(events):

#     if not events:

#         return "Unknown"


#     now = datetime.now(
#         timezone.utc
#     )

#     valid_events = []


#     for event in events:

#         timestamp = event.get(
#             "timestamp"
#         )

#         if not timestamp:

#             continue


#         event_time = parse_timestamp(
#             timestamp
#         )

#         if event_time is None:

#             continue


#         if event_time < SESSION_START:

#             continue


#         if event_time > now:

#             continue


#         valid_events.append(
#             event
#         )


#     if not valid_events:

#         return "Unknown"


#     latest_event = max(
#         valid_events,
#         key=lambda event:
#             event.get(
#                 "timestamp",
#                 ""
#             )
#     )


#     return clean_application_name(
#         latest_event
#     )


# def send_activity(
#     latest_application,
#     application_usage
# ):

#     now = datetime.now(
#         timezone.utc
#     )


#     session_seconds = (
#         now - SESSION_START
#     ).total_seconds()


#     session_seconds = max(
#         session_seconds,
#         0
#     )


#     total_application_seconds = sum(
#         application_usage.values()
#     )


#     active_seconds = min(
#         total_application_seconds,
#         session_seconds
#     )


#     payload = {

#         "employee_id":
#             EMPLOYEE_ID,

        

#         "status":
#             "active",

#         "application":
#             latest_application,

#         "window_title":
#             latest_application,

#         "timestamp":
#             now.isoformat(),

#         "session_start":
#             SESSION_START.isoformat(),

#         "session_seconds":
#             int(session_seconds),

#         "session_time":
#             format_duration(
#                 session_seconds
#             ),

#         "active_seconds":
#             int(active_seconds),

#         "active_time":
#             format_duration(
#                 active_seconds
#             ),

#         "application_usage": {

#             app:
#                 format_duration(seconds)

#             for app, seconds
#             in sorted(
#                 application_usage.items(),
#                 key=lambda item:
#                     item[1],
#                 reverse=True
#             )
#         }
#     }


#     try:

#         response = requests.post(

#             f"{SERVER_URL}/api/activity",

#             json=payload,

#             timeout=15
#         )


#         print(
#             "Server:",
#             response.status_code
#         )


#         if response.status_code == 200:

#             print(
#                 "Data sent successfully"
#             )

#         else:

#             print(
#                 "Server response:",
#                 response.text
#             )


#     except Exception as e:

#         print(
#             "Server connection error:",
#             e
#         )


# def main():

#     print()
#     print(
#         "======================================"
#     )
#     print(
#         "       TEAM ACTIVITY TRACKER"
#     )
#     print(
#         "======================================"
#     )

#     print(
#         "Employee ID:",
#         EMPLOYEE_ID
#     )

#     print(
#         "ActivityWatch:",
#         ACTIVITYWATCH_URL
#     )

#     print(
#         "Server:",
#         SERVER_URL
#     )

#     print(
#         "Session Start:",
#         SESSION_START
#         .astimezone()
#         .strftime(
#             "%d-%m-%Y %I:%M:%S %p"
#         )
#     )

#     print(
#         "======================================"
#     )

#     buckets = get_buckets()


#     if not buckets:

#         print(
#             "ERROR: ActivityWatch is not running."
#         )

#         return


#     window_bucket = (
#         find_window_bucket(
#             buckets
#         )
#     )


#     if not window_bucket:

#         print(
#             "ERROR: Window bucket not found."
#         )

#         return


#     print(
#         "Window bucket:",
#         window_bucket
#     )

#     print()

#     print(
#         "Tracker started successfully."
#     )

#     print(
#         "Data will be sent every 60 seconds."
#     )

#     print(
#         "Historical ActivityWatch data will NOT be counted."
#     )

#     print(
#         "Press CTRL+C to stop during testing."
#     )

#     print(
#         "======================================"
#     )


    

#     while True:

#         buckets = get_buckets()


#         window_bucket = (
#             find_window_bucket(
#                 buckets
#             )
#         )


#         if not window_bucket:

#             print(
#                 "Window bucket unavailable."
#             )

#             time.sleep(
#                 INTERVAL
#             )

#             continue


#         window_events = get_events(
#             window_bucket
#         )


#         application_usage = (
#             calculate_application_usage(
#                 window_events
#             )
#         )


#         latest_application = (
#             get_latest_application(
#                 window_events
#             )
#         )


#         now = datetime.now(
#             timezone.utc
#         )


#         session_seconds = (
#             now - SESSION_START
#         ).total_seconds()


#         active_seconds = min(
#             sum(
#                 application_usage.values()
#             ),
#             session_seconds
#         )


#         print()
#         print(
#             "--------------------------------------"
#         )

#         print(
#             "Latest Application:",
#             latest_application
#         )

#         print(
#             "Session Time:",
#             format_duration(
#                 session_seconds
#             )
#         )

#         print(
#             "Application Active Time:",
#             format_duration(
#                 active_seconds
#             )
#         )

#         print(
#             "Application Usage:"
#         )


#         for app, seconds in sorted(
#             application_usage.items(),
#             key=lambda item:
#                 item[1],
#             reverse=True
#         ):

#             print(
#                 "  ",
#                 app,
#                 "→",
#                 format_duration(
#                     seconds
#                 )
#             )


#         print(
#             "--------------------------------------"
#         )



#         send_activity(
#             latest_application,
#             application_usage
#         )


#         time.sleep(
#             INTERVAL
#         )



# if __name__ == "__main__":

#     try:

#         main()

#     except KeyboardInterrupt:

#         print()
#         print(
#             "Tracker stopped."
#         )

import requests
import time

from datetime import datetime, timezone, timedelta


# =========================================================
# CONFIGURATION
# =========================================================

EMPLOYEE_ID = "CRFT-IT-260601"

ACTIVITYWATCH_URL = "http://127.0.0.1:5600"

SERVER_URL = "https://team-activity-server.vercel.app"

# Send data every 60 seconds
INTERVAL = 60

# Tracker session starts when the tracker starts.
SESSION_START = datetime.now(timezone.utc)


# =========================================================
# ACTIVITYWATCH - BUCKETS
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

        print(
            "ActivityWatch connection error:",
            e
        )

        return {}


# =========================================================
# FIND WINDOW BUCKET
# =========================================================

def find_window_bucket(buckets):

    # First preference:
    # currentwindow bucket

    for bucket_id, bucket in buckets.items():

        bucket_type = str(
            bucket.get("type", "")
        ).lower()

        if bucket_type == "currentwindow":

            return bucket_id


    # Fallback:
    # any bucket containing "window"

    for bucket_id in buckets:

        if "window" in bucket_id.lower():

            return bucket_id


    return None


# =========================================================
# FIND AFK BUCKET
# =========================================================

def find_afk_bucket(buckets):

    # First preference:
    # bucket type containing afk

    for bucket_id, bucket in buckets.items():

        bucket_type = str(
            bucket.get("type", "")
        ).lower()

        bucket_id_lower = bucket_id.lower()

        if (
            "afk" in bucket_type
            or "afk" in bucket_id_lower
        ):

            return bucket_id


    return None


# =========================================================
# GET EVENTS
# =========================================================

def get_events(bucket_id):

    try:

        response = requests.get(
            f"{ACTIVITYWATCH_URL}/api/0/buckets/"
            f"{bucket_id}/events",
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
# CLEAN APPLICATION NAME
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


    application = (
        application
        .replace("_", " ")
        .strip()
    )

    if not application:

        application = "Unknown"


    return application


# =========================================================
# FORMAT DURATION
# =========================================================

def format_duration(seconds):

    try:

        seconds = int(
            max(float(seconds), 0)
        )

    except Exception:

        seconds = 0


    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    return f"{hours}h {minutes}m"


# =========================================================
# CALCULATE APPLICATION USAGE
# =========================================================

def calculate_application_usage(events):

    application_usage = {}

    now = datetime.now(
        timezone.utc
    )


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


        # Ignore events that finished
        # before current tracker session.

        if event_end <= SESSION_START:

            continue


        # Ignore future events.

        if event_start >= now:

            continue


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


        application = (
            clean_application_name(
                event
            )
        )


        application_usage[
            application
        ] = (
            application_usage.get(
                application,
                0
            )
            + actual_duration
        )


    return application_usage


# =========================================================
# GET LATEST APPLICATION
# =========================================================

def get_latest_application(events):

    if not events:

        return "Unknown"


    now = datetime.now(
        timezone.utc
    )

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


        valid_events.append(
            event
        )


    if not valid_events:

        return "Unknown"


    latest_event = max(
        valid_events,
        key=lambda event:
        parse_timestamp(
            event.get(
                "timestamp",
                ""
            )
        ) or datetime.min.replace(
            tzinfo=timezone.utc
        )
    )


    return clean_application_name(
        latest_event
    )


# =========================================================
# CALCULATE AFK / IDLE TIME
# =========================================================

def calculate_idle_time(events):

    now = datetime.now(
        timezone.utc
    )

    total_idle_seconds = 0


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


        # Ignore events before tracker session.

        if event_end <= SESSION_START:

            continue


        # Ignore future events.

        if event_start >= now:

            continue


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


        data = event.get(
            "data",
            {}
        )


        status = str(
            data.get(
                "status",
                ""
            )
        ).lower()


        # ActivityWatch AFK watcher normally
        # reports status as "afk" or "not-afk".

        if status == "afk":

            total_idle_seconds += (
                actual_duration
            )


    return int(
        max(
            total_idle_seconds,
            0
        )
    )


# =========================================================
# SEND ACTIVITY TO SERVER
# =========================================================

def send_activity(
    latest_application,
    application_usage,
    idle_seconds
):

    now = datetime.now(
        timezone.utc
    )


    # Total tracker session time.

    session_seconds = (
        now - SESSION_START
    ).total_seconds()


    session_seconds = int(
        max(
            session_seconds,
            0
        )
    )


    # Active time = session time - AFK time.

    active_seconds = (
        session_seconds
        - idle_seconds
    )


    active_seconds = max(
        active_seconds,
        0
    )


    # Prevent active time from
    # exceeding session time.

    active_seconds = min(
        active_seconds,
        session_seconds
    )


    # IMPORTANT:
    # Application usage is sent as
    # numeric seconds, NOT "2h 30m" strings.

    application_usage_seconds = {

        app: int(
            max(seconds, 0)
        )

        for app, seconds
        in application_usage.items()

    }


    payload = {

        "employee_id":
            EMPLOYEE_ID,

        "status":
            "active",

        "application":
            latest_application,

        "window_title":
            latest_application,

        "timestamp":
            now.isoformat(),

        "session_start":
            SESSION_START.isoformat(),

        "session_seconds":
            session_seconds,

        "session_time":
            format_duration(
                session_seconds
            ),

        "active_seconds":
            int(active_seconds),

        "active_time":
            format_duration(
                active_seconds
            ),

        # NEW:
        # Total AFK / idle time

        "idle_seconds":
            int(idle_seconds),

        "idle_time":
            format_duration(
                idle_seconds
            ),

        # Application-wise usage
        # stored as seconds

        "application_usage":
            application_usage_seconds
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
                "Server response:",
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
        SESSION_START
        .astimezone()
        .strftime(
            "%d-%m-%Y %I:%M:%S %p"
        )
    )

    print(
        "======================================"
    )


    # -----------------------------------------------------
    # CHECK ACTIVITYWATCH
    # -----------------------------------------------------

    buckets = get_buckets()


    if not buckets:

        print(
            "ERROR: ActivityWatch is not running."
        )

        return


    # -----------------------------------------------------
    # FIND WINDOW BUCKET
    # -----------------------------------------------------

    window_bucket = (
        find_window_bucket(
            buckets
        )
    )


    if not window_bucket:

        print(
            "ERROR: Window bucket not found."
        )

        return


    # -----------------------------------------------------
    # FIND AFK BUCKET
    # -----------------------------------------------------

    afk_bucket = (
        find_afk_bucket(
            buckets
        )
    )


    print(
        "Window bucket:",
        window_bucket
    )


    if afk_bucket:

        print(
            "AFK bucket:",
            afk_bucket
        )

    else:

        print(
            "WARNING: AFK bucket not found."
        )

        print(
            "Idle time will remain 0."
        )


    print()

    print(
        "Tracker started successfully."
    )

    print(
        "Data will be sent every 60 seconds."
    )

    print(
        "Application usage is calculated"
        " from the current tracker session."
    )

    print(
        "AFK / idle time is calculated"
        " from ActivityWatch."
    )

    print(
        "Press CTRL+C to stop during testing."
    )

    print(
        "======================================"
    )


    # =====================================================
    # TRACKING LOOP
    # =====================================================

    while True:

        try:

            buckets = get_buckets()


            if not buckets:

                print(
                    "ActivityWatch unavailable."
                )

                time.sleep(
                    INTERVAL
                )

                continue


            # -------------------------------------------------
            # WINDOW BUCKET
            # -------------------------------------------------

            window_bucket = (
                find_window_bucket(
                    buckets
                )
            )


            if not window_bucket:

                print(
                    "Window bucket unavailable."
                )

                time.sleep(
                    INTERVAL
                )

                continue


            # -------------------------------------------------
            # WINDOW EVENTS
            # -------------------------------------------------

            window_events = (
                get_events(
                    window_bucket
                )
            )


            # -------------------------------------------------
            # APPLICATION USAGE
            # -------------------------------------------------

            application_usage = (
                calculate_application_usage(
                    window_events
                )
            )


            # -------------------------------------------------
            # CURRENT APPLICATION
            # -------------------------------------------------

            latest_application = (
                get_latest_application(
                    window_events
                )
            )


            # -------------------------------------------------
            # AFK / IDLE
            # -------------------------------------------------

            idle_seconds = 0


            if afk_bucket:

                afk_events = (
                    get_events(
                        afk_bucket
                    )
                )


                idle_seconds = (
                    calculate_idle_time(
                        afk_events
                    )
                )


            # -------------------------------------------------
            # SESSION
            # -------------------------------------------------

            now = datetime.now(
                timezone.utc
            )


            session_seconds = int(
                max(
                    (
                        now - SESSION_START
                    ).total_seconds(),
                    0
                )
            )


            # -------------------------------------------------
            # ACTIVE TIME
            # -------------------------------------------------

            active_seconds = (
                session_seconds
                - idle_seconds
            )


            active_seconds = max(
                active_seconds,
                0
            )


            active_seconds = min(
                active_seconds,
                session_seconds
            )


            # -------------------------------------------------
            # DISPLAY
            # -------------------------------------------------

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
                "Active Time:",
                format_duration(
                    active_seconds
                )
            )

            print(
                "Idle / AFK Time:",
                format_duration(
                    idle_seconds
                )
            )

            print(
                "Application Usage:"
            )


            if application_usage:

                for app, seconds in sorted(

                    application_usage.items(),

                    key=lambda item:
                    item[1],

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

            else:

                print(
                    "  No application usage data"
                )


            print(
                "--------------------------------------"
            )


            # -------------------------------------------------
            # SEND TO SERVER
            # -------------------------------------------------

            send_activity(

                latest_application,

                application_usage,

                idle_seconds

            )


        except Exception as e:

            print()

            print(
                "Tracker loop error:",
                e
            )


        # -----------------------------------------------------
        # WAIT
        # -----------------------------------------------------

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