# backend/google_calendar_service.py
import os
import json
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow # For web server flow
from google.auth.transport.requests import Request # Make sure this is imported
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

# Load the JSON content string from .env
CLIENT_CONFIG_JSON_STR = os.getenv('GOOGLE_CLIENT_CONFIG_JSON')
SCOPES = [os.getenv('GOOGLE_CALENDAR_SCOPES', 'https://www.googleapis.com/auth/calendar')]
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

# --- Helper: Load/Save User's Google Tokens (from their profile JSON) ---
# These remain the same, as they store the obtained tokens, not the client config
def _load_user_google_creds(user_id, user_profile_dir):
    profile_path = os.path.join(user_profile_dir, f"{''.join(c if c.isalnum() else '_' for c in user_id)}.json")
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        return profile.get('google_auth_creds')
    return None

def _save_user_google_creds(user_id, user_profile_dir, creds_dict):
    profile_path = os.path.join(user_profile_dir, f"{''.join(c if c.isalnum() else '_' for c in user_id)}.json")
    profile = {}
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            profile = json.load(f)
    profile['google_auth_creds'] = creds_dict
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=4)
# --- End Helper ---

def get_calendar_service_for_user(user_id, user_profile_dir):
    creds_dict = _load_user_google_creds(user_id, user_profile_dir)
    if not creds_dict:
        print(f"User {user_id} has not authorized Google Calendar access.")
        return None

    # The client_id and client_secret are needed for token refresh if they are not in creds_dict
    # It's better if creds_dict (from credentials.to_json()) already contains them.
    creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            print(f"Refreshing token for user {user_id}")
            # For refreshing, the original client_id and client_secret might be needed
            # if they weren't part of the stored creds_dict.
            # The Credentials object should ideally have them if constructed correctly.
            # If not, you'd parse CLIENT_CONFIG_JSON_STR here to get them.
            # However, `creds.refresh(Request())` should work if refresh_token is valid.
            creds.refresh(Request())
            _save_user_google_creds(user_id, user_profile_dir, json.loads(creds.to_json()))
        except Exception as e:
            print(f"Failed to refresh token for user {user_id}: {e}")
            return None
    elif not creds or not creds.valid:
        print(f"User {user_id} needs to re-authenticate with Google Calendar.")
        return None

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Failed to build calendar service for user {user_id}: {e}")
        return None

def get_client_config_from_env():
    """Parses the client config JSON string from the environment variable."""
    if not CLIENT_CONFIG_JSON_STR:
        print("ERROR: GOOGLE_CLIENT_CONFIG_JSON not found in .env or is empty.")
        return None
    try:
        client_config = json.loads(CLIENT_CONFIG_JSON_STR)
        # Basic validation for expected structure
        if "web" not in client_config or not all(k in client_config["web"] for k in ["client_id", "client_secret"]):
            print("ERROR: GOOGLE_CLIENT_CONFIG_JSON has invalid structure.")
            return None
        return client_config
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse GOOGLE_CLIENT_CONFIG_JSON: {e}")
        return None

def start_google_auth_flow(session):
    client_config = get_client_config_from_env()
    if not client_config:
        return None

    flow = Flow.from_client_config( # CHANGED HERE
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    session['google_oauth_state'] = state
    return authorization_url

def process_google_auth_callback(user_id, user_profile_dir, request_url, session_state):
    client_config = get_client_config_from_env()
    if not client_config:
        return False

    flow = Flow.from_client_config( # CHANGED HERE
        client_config,
        scopes=SCOPES,
        state=session_state,
        redirect_uri=REDIRECT_URI
    )
    try:
        flow.fetch_token(authorization_response=request_url)
    except Exception as e:
        print(f"Error fetching token during OAuth callback: {e}")
        return False

    credentials = flow.credentials
    creds_json_str = credentials.to_json()
    _save_user_google_creds(user_id, user_profile_dir, json.loads(creds_json_str))
    print(f"Successfully authenticated Google Calendar for user {user_id}")
    return True

# create_weekly_checkup_event_for_user and delete_calendar_event_for_user
# remain the same as they rely on get_calendar_service_for_user which handles creds.
def create_weekly_checkup_event_for_user(user_id, user_profile_dir, day_of_week_str, time_str, calendar_id='primary'):
    service = get_calendar_service_for_user(user_id, user_profile_dir)
    if not service:
        print(f"Cannot create event: User {user_id} not authenticated or token invalid.")
        return None

    day_map = {"SUNDAY": "SU", "MONDAY": "MO", "TUESDAY": "TU", "WEDNESDAY": "WE",
               "THURSDAY": "TH", "FRIDAY": "FR", "SATURDAY": "SA"}
    gcal_day = day_map.get(day_of_week_str.upper())
    if not gcal_day: return None
    try: hours, minutes = map(int, time_str.split(':'))
    except ValueError: return None

    now = datetime.datetime.utcnow()
    days_ahead = (["MO", "TU", "WE", "TH", "FR", "SA", "SU"].index(gcal_day) - now.weekday() + 7) % 7
    if days_ahead == 0 and (now.hour > hours or (now.hour == hours and now.minute >= minutes)): days_ahead = 7

    start_datetime_obj = (datetime.datetime(now.year, now.month, now.day, hours, minutes) + datetime.timedelta(days=days_ahead))
    end_datetime_obj = start_datetime_obj + datetime.timedelta(minutes=30)

    event_body = {
        'summary': f'Diet App: Weekly Check-in',
        'description': f'Time to update your progress in the Diet App!',
        'start': {'dateTime': start_datetime_obj.isoformat() + 'Z', 'timeZone': 'UTC'},
        'end': {'dateTime': end_datetime_obj.isoformat() + 'Z', 'timeZone': 'UTC'},
        'recurrence': [f'RRULE:FREQ=WEEKLY;BYDAY={gcal_day}'],
        'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 60},{'method': 'popup', 'minutes': 10}]},
    }
    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        print(f"Event created for user {user_id}: {created_event.get('htmlLink')}")
        return created_event.get('id')
    except HttpError as e:
        print(f"An error occurred creating calendar event for user {user_id}: {e.content}")
        if e.resp.status in [401, 403]: print("Token might be invalid or scopes insufficient.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def delete_calendar_event_for_user(user_id, user_profile_dir, event_id, calendar_id='primary'):
    service = get_calendar_service_for_user(user_id, user_profile_dir)
    if not service or not event_id: return False
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print(f"Event {event_id} deleted for user {user_id}.")
        return True
    except Exception as e:
        print(f"Failed to delete event {event_id} for user {user_id}: {e}")
        return False