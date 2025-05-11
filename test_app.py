import requests
import json
import os
from datetime import datetime
import base64
from dotenv import load_dotenv
from google_calendar_service import calendar_service

# Load environment variables from .env file
load_dotenv()

def parse_client_config():
    """Parse and validate the Google client config JSON (or load it from file)."""
    config_str = os.getenv('GOOGLE_CLIENT_CONFIG_JSON', '').strip()
    print("\n=== Raw GOOGLE_CLIENT_CONFIG_JSON ===")
    print(config_str)

    # If this looks like a path to an existing file, load it instead of treating as raw JSON
    if os.path.isfile(config_str):
        print(f"Detected file at {config_str}, loading its contents…")
        with open(config_str, 'r', encoding='utf-8') as f:
            config_str = f.read().strip()

    # Strip surrounding quotes if present
    if (config_str.startswith("'") and config_str.endswith("'")) or \
       (config_str.startswith('"') and config_str.endswith('"')):
        config_str = config_str[1:-1]

    try:
        config = json.loads(config_str)
        print("\n=== Parsed Client Config ===")
        print(json.dumps(config, indent=2))

        # Validate required fields
        if "web" not in config:
            print("Error: Missing 'web' section in config")
            return None

        web_config = config["web"]
        required_fields = ["client_id", "client_secret", "redirect_uris", "javascript_origins"]
        missing = [f for f in required_fields if f not in web_config]
        if missing:
            print(f"Error: Missing required fields: {', '.join(missing)}")
            return None

        print("\n=== Config Validation ===")
        print(f"Client ID exists: {'Yes' if web_config.get('client_id') else 'No'}")
        print(f"Client Secret exists: {'Yes' if web_config.get('client_secret') else 'No'}")
        print(f"Redirect URIs: {web_config.get('redirect_uris')}")
        print(f"Authorized JavaScript Origins: {web_config.get('javascript_origins')}")
        return config

    except json.JSONDecodeError as e:
        print(f"\nError parsing JSON: {e}")
        print("Final raw string being parsed:")
        print(config_str)
        return None
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return None


# Debug: Print ALL environment variables
print("\n=== Environment Variables Debug ===")
print("GOOGLE_CLIENT_CONFIG_JSON:")
print(os.getenv('GOOGLE_CLIENT_CONFIG_JSON'))
print("\nGOOGLE_REDIRECT_URI:")
print(os.getenv('GOOGLE_REDIRECT_URI'))
print("\nGOOGLE_CALENDAR_SCOPES:")
print(os.getenv('GOOGLE_CALENDAR_SCOPES'))
print("\nFLASK_SECRET_KEY:")
print(os.getenv('FLASK_SECRET_KEY'))
print("\nFLASK_ENV:")
print(os.getenv('FLASK_ENV'))
print("\nFLASK_RUN_PORT:")
print(os.getenv('FLASK_RUN_PORT'))

# Parse and validate client config
client_config = parse_client_config()
if not client_config:
    print("\n❌ Failed to parse Google client config. Please check your .env file.")
    exit(1)

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER_ID = "test_user_123"

def test_google_auth_flow():
    """Test the Google Calendar authorization flow"""
    print("\n=== Testing Google Calendar Authorization Flow ===")
    
    # Debug: Print environment variables (without sensitive data)
    print("\nEnvironment Variables Check:")
    print(f"GOOGLE_REDIRECT_URI: {os.getenv('GOOGLE_REDIRECT_URI')}")
    print(f"GOOGLE_CALENDAR_SCOPES: {os.getenv('GOOGLE_CALENDAR_SCOPES')}")
    print(f"GOOGLE_CLIENT_CONFIG_JSON exists: {'Yes' if os.getenv('GOOGLE_CLIENT_CONFIG_JSON') else 'No'}")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Try to get authorization URL
    auth_url = f"{BASE_URL}/authorize-google-calendar/{TEST_USER_ID}"
    print(f"\nRequesting authorization URL: {auth_url}")
    response = session.get(auth_url, allow_redirects=False)
    print(f"Authorization URL Response:")
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Cookies: {dict(session.cookies)}")
    
    if response.status_code == 302:  # Redirect
        redirect_url = response.headers.get('Location')
        print(f"\n=== IMPORTANT: Please follow these steps ===")
        print("1. Open this URL in your browser:")
        print(f"   {redirect_url}")
        print("\n2. Sign in with your Google account (the one you added as a test user)")
        print("3. Grant the requested permissions")
        print("4. You will be redirected back to the application")
        print("5. Wait for the success message")
        print("\nAfter completing these steps, press Enter to continue...")
        input()
        
        # Step 2: Simulate the OAuth callback
        print("\nSimulating OAuth callback...")
        callback_url = f"{BASE_URL}/oauth2callback"
        callback_response = session.get(callback_url)
        print(f"Callback Response:")
        print(f"Status Code: {callback_response.status_code}")
        print(f"Response Headers: {dict(callback_response.headers)}")
        print(f"Cookies: {dict(session.cookies)}")
        print(f"Response: {json.dumps(callback_response.json(), indent=2) if callback_response.headers.get('content-type') == 'application/json' else callback_response.text}")
        
        # Step 3: Check if user is now authorized
        print("\nChecking if user is authorized...")
        checkup_url = f"{BASE_URL}/profile/{TEST_USER_ID}/schedule-checkup"
        response = session.post(checkup_url, json={
            "day_of_week": "MONDAY",
            "time_of_day": "10:00"
        })
        print(f"Schedule Checkup Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Cookies: {dict(session.cookies)}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            print("\nUser needs to complete Google Calendar authorization:")
            print("1. Visit the authorization URL shown above in your browser")
            print("2. Complete the Google OAuth flow")
            print("3. You'll be redirected back to the application")
            print("4. Run the tests again")
            return False
        elif response.status_code == 500:
            print("\nServer error occurred. This might be due to:")
            print("1. Invalid GOOGLE_CLIENT_CONFIG_JSON format")
            print("2. Mismatched redirect URIs")
            print("3. Server-side error in processing the request")
            return False
        return response.status_code == 200
    else:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("\nError: Expected a redirect to Google's authorization page")
        return False

def test_create_profile():
    """Test creating/updating a user profile"""
    session = requests.Session()
    url = f"{BASE_URL}/profile/{TEST_USER_ID}"
    data = {
        "age": 30,
        "gender": "male",
        "measurements": {
            "height_cm": 180,
            "weight_kg": 80,
            "waist_cm": 90,
            "hip_cm": 95,
            "neck_cm": 40
        },
        "lifestyle": {
            "activity_level": "moderate",
            "goals": "lose_weight",
            "dietary_preferences": ["vegetarian"]
        }
    }
    response = session.post(url, json=data)
    print("\n=== Test Create Profile ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_get_profile():
    """Test retrieving a user profile"""
    session = requests.Session()
    url = f"{BASE_URL}/profile/{TEST_USER_ID}"
    response = session.get(url)
    print("\n=== Test Get Profile ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_analyze_photo():
    """Test body fat analysis from photo"""
    session = requests.Session()
    url = f"{BASE_URL}/analyze-photo/{TEST_USER_ID}"
    
    # Create a test image (1x1 pixel black image)
    test_image = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
    
    files = {
        'photo': ('test_image.png', test_image, 'image/png')
    }
    
    response = session.post(url, files=files)
    print("\n=== Test Analyze Photo ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_generate_diet_plan():
    """Test diet plan generation"""
    session = requests.Session()
    url = f"{BASE_URL}/generate-diet-plan/{TEST_USER_ID}"
    response = session.post(url)
    print("\n=== Test Generate Diet Plan ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_track_progress():
    """Test progress tracking"""
    session = requests.Session()
    url = f"{BASE_URL}/track-progress/{TEST_USER_ID}"
    data = {
        "weight_kg": 79.5,
        "measurements": {
            "height_cm": 180,
            "weight_kg": 79.5,
            "waist_cm": 89,
            "hip_cm": 94,
            "neck_cm": 40
        },
        "notes": "Feeling good, maintaining progress"
    }
    response = session.post(url, json=data)
    print("\n=== Test Track Progress ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_schedule_checkup():
    """Test scheduling a weekly checkup"""
    session = requests.Session()
    url = f"{BASE_URL}/profile/{TEST_USER_ID}/schedule-checkup"
    data = {
        "day_of_week": "MONDAY",
        "time_of_day": "10:00"
    }
    response = session.post(url, json=data)
    print("\n=== Test Schedule Checkup ===")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 401:
        print("\nUser needs to complete Google Calendar authorization:")
        print("1. Visit the authorization URL shown above in your browser")
        print("2. Complete the Google OAuth flow")
        print("3. You'll be redirected back to the application")
        print("4. Run the tests again")
        return False
    elif response.status_code == 500:
        print("\nServer error occurred. This might be due to:")
        print("1. Invalid GOOGLE_CLIENT_CONFIG_JSON format")
        print("2. Mismatched redirect URIs")
        print("3. Server-side error in processing the request")
        return False
    return response.status_code == 200

def run_all_tests():
    """Run all tests and report results"""
    # First check environment variables
    required_env_vars = [
        'GOOGLE_CLIENT_CONFIG_JSON',
        'GOOGLE_REDIRECT_URI',
        'GOOGLE_CALENDAR_SCOPES'
    ]
    
    print("\n=== Environment Variables Check ===")
    missing_vars = []
    for var in required_env_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: Not set")
        else:
            print(f"✅ {var}: Set")
    
    if missing_vars:
        print("\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in your .env file")
        return
    
    # First test the Google Auth flow
    print("\n=== Testing Google Calendar Integration ===")
    auth_success = test_google_auth_flow()
    if not auth_success:
        print("\n❌ Google Calendar authorization failed. Please complete the authorization flow before running other tests.")
        return
    
    tests = [
        ("Create Profile", test_create_profile),
        ("Get Profile", test_get_profile),
        ("Analyze Photo", test_analyze_photo),
        ("Generate Diet Plan", test_generate_diet_plan),
        ("Track Progress", test_track_progress),
        ("Schedule Checkup", test_schedule_checkup)
    ]
    
    print("\n=== Starting Tests ===")
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    print("\n=== Test Results ===")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")

if __name__ == "__main__":
    run_all_tests() 