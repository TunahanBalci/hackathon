import os
import json
import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class GoogleCalendarService:
    """
    Handles OAuth2 flow and API interactions for Google Calendar.
    """

    def __init__(self):
        """
        Initialize service by loading environment variables and validating client config.
        """
        self.CLIENT_CONFIG_JSON_STR = os.getenv('GOOGLE_CLIENT_CONFIG_JSON')
        self.SCOPES = [os.getenv('GOOGLE_CALENDAR_SCOPES', 'https://www.googleapis.com/auth/calendar')]
        self.REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

        print("\n=== Google Calendar Service Initialization ===")
        print(f"REDIRECT_URI: {self.REDIRECT_URI}")
        print(f"SCOPES: {self.SCOPES}")
        print(f"CLIENT_CONFIG_JSON exists: {'Yes' if self.CLIENT_CONFIG_JSON_STR else 'No'}")
        print(f"OAUTHLIB_INSECURE_TRANSPORT: {os.getenv('OAUTHLIB_INSECURE_TRANSPORT', 'Not set')}")

        missing_vars = []
        if not self.CLIENT_CONFIG_JSON_STR:
            missing_vars.append('GOOGLE_CLIENT_CONFIG_JSON')
        if not self.REDIRECT_URI:
            missing_vars.append('GOOGLE_REDIRECT_URI')
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        try:
            config = self._parse_client_config()
            print("\n✅ Client config validation successful")
        except Exception as e:
            print(f"\n❌ Client config validation failed: {e}")
            raise

    def _parse_client_config(self) -> Dict[str, Any]:
        """
        Parse and validate the OAuth client configuration, accepting either a JSON string or a file path.

        Returns:
            dict: Parsed client configuration.

        Raises:
            ValueError: If the JSON is invalid or required fields are missing.
        """
        raw = self.CLIENT_CONFIG_JSON_STR.strip()
        if os.path.isfile(raw):
            with open(raw, 'r') as f:
                raw = f.read().strip()

        if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
            raw = raw[1:-1]

        try:
            config = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in client config: {e}")

        if "web" not in config:
            raise ValueError("Missing 'web' section in client config")

        web = config["web"]
        for field in ("client_id", "client_secret", "redirect_uris", "javascript_origins"):
            if field not in web:
                raise ValueError(f"Missing '{field}' in client config")

        if self.REDIRECT_URI not in web["redirect_uris"]:
            raise ValueError(f"Redirect URI {self.REDIRECT_URI} not listed in client config")

        return config

    def _load_user_credentials(self, user_id: str, user_profile_dir: str) -> Optional[Dict[str, Any]]:
        """
        Load stored Google OAuth credentials for a given user.

        Args:
            user_id: Identifier of the user.
            user_profile_dir: Directory where user profiles are stored.

        Returns:
            dict or None: Credential info if found, otherwise None.
        """
        try:
            path = os.path.join(user_profile_dir, f"{user_id}.json")
            if not os.path.exists(path):
                return None
            with open(path) as f:
                profile = json.load(f)
            return profile.get('google_auth_creds')
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None

    def _save_user_credentials(
        self,
        user_id: str,
        user_profile_dir: str,
        creds_dict: Dict[str, Any]
    ) -> bool:
        """
        Save Google OAuth credentials for a given user.

        Args:
            user_id: Identifier of the user.
            user_profile_dir: Directory where user profiles are stored.
            creds_dict: Credential info to save.

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            path = os.path.join(user_profile_dir, f"{user_id}.json")
            profile = {}
            if os.path.exists(path):
                with open(path) as f:
                    profile = json.load(f)
            profile['google_auth_creds'] = creds_dict
            with open(path, 'w') as f:
                json.dump(profile, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False

    def get_calendar_service(self, user_id: str, user_profile_dir: str):
        """
        Retrieve an authorized Google Calendar API client for the user.

        Args:
            user_id: Identifier of the user.
            user_profile_dir: Directory where user profiles are stored.

        Returns:
            Resource or None: Google Calendar service resource, or None if authorization is missing/invalid.
        """
        creds_dict = self._load_user_credentials(user_id, user_profile_dir)
        if not creds_dict:
            return None

        creds = Credentials.from_authorized_user_info(creds_dict, self.SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._save_user_credentials(user_id, user_profile_dir, json.loads(creds.to_json()))
        if not creds.valid:
            return None

        return build('calendar', 'v3', credentials=creds)

    def start_auth_flow(self, session: Dict[str, Any]) -> Optional[str]:
        """
        Initiate the OAuth2 authorization flow and store the state in the session.

        Args:
            session: Flask session dict.

        Returns:
            str or None: URL to redirect the user to for Google consent.
        """
        client_config = self._parse_client_config()
        flow = Flow.from_client_config(
            client_config,
            scopes=self.SCOPES,
            redirect_uri=self.REDIRECT_URI
        )
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        session['google_oauth_state'] = state
        return auth_url

    def process_auth_callback(
        self,
        user_id: str,
        user_profile_dir: str,
        request_url: str,
        session_state: str
    ) -> bool:
        """
        Handle the OAuth2 callback, exchange code for tokens, and save credentials.

        Args:
            user_id: Identifier of the user.
            user_profile_dir: Directory where user profiles are stored.
            request_url: Full callback URL containing query parameters.
            session_state: State value stored in session.

        Returns:
            bool: True if credentials were saved successfully, False otherwise.
        """
        qs = parse_qs(urlparse(request_url).query)
        if qs.get('state', [None])[0] != session_state:
            print(f"State mismatch: expected {session_state}, got {qs.get('state')}")
            return False

        client_config = self._parse_client_config()
        flow = Flow.from_client_config(
            client_config,
            scopes=self.SCOPES,
            state=session_state,
            redirect_uri=self.REDIRECT_URI
        )
        flow.fetch_token(authorization_response=request_url)
        creds = flow.credentials
        return self._save_user_credentials(user_id, user_profile_dir, json.loads(creds.to_json()))

calendar_service = GoogleCalendarService()
