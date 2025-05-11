# backend/app.py
import os
import json
import tempfile
import datetime
from flask import Flask, request, jsonify, redirect, session, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_session import Session
import google.generativeai as genai

load_dotenv()  # Load environment variables from .env

# Allow OAuth2 over HTTP in development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Import your utility, Gemini, and Google Calendar modules
from utils.calculations import calculate_all_metrics
from gemini.meal_planner import generate_diet_plan_with_gemini
from gemini.fat_analyzer import analyze_fat_percentage_with_gemini
from google_calendar_service import calendar_service

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("No FLASK_SECRET_KEY set. Please set it in your .env file.")

# Configure session settings
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to False for local development
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(minutes=30),
    SESSION_REFRESH_EACH_REQUEST=True,  # Refresh session on each request
    SESSION_TYPE='filesystem',  # Use filesystem for session storage
    SESSION_FILE_DIR=os.path.join(os.getcwd(), 'flask_session')  # Store sessions in flask_session directory
)

# Initialize Flask-Session
Session(app)

# Configure CORS with specific settings for OAuth
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Set-Cookie"]
    }
})

# --- Configuration from .env ---
USER_DATA_FOLDER = os.getenv('USER_DATA_FOLDER', 'user_data')
app.config['USER_DATA_FOLDER'] = USER_DATA_FOLDER  # Make it accessible via app.config
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure user_data folder exists
if not os.path.exists(USER_DATA_FOLDER):
    os.makedirs(USER_DATA_FOLDER)


# --- Helper Functions for User Profile Data ---
def get_user_profile_path(user_id):
    safe_user_id = "".join(c if c.isalnum() else "_" for c in str(user_id))
    if not safe_user_id:
        raise ValueError("Invalid user_id for file path generation.")
    return os.path.join(app.config['USER_DATA_FOLDER'], f"{safe_user_id}.json")


def load_user_profile(user_id):
    try:
        profile_path = get_user_profile_path(user_id)
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                return json.load(f)
        return {}  # Return empty if file doesn't exist (new user)
    except ValueError as e:  # From get_user_profile_path
        app.logger.error(f"Error getting profile path for {user_id}: {e}")
        raise  # Re-raise to be caught by endpoint
    except json.JSONDecodeError:
        app.logger.error(f"Corrupted JSON file for user {user_id}")
        return {}  # Or handle error differently
    except Exception as e:
        app.logger.error(f"Unexpected error loading profile for {user_id}: {e}")
        raise


def save_user_profile(user_id, data):
    try:
        profile_path = get_user_profile_path(user_id)
        with open(profile_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except ValueError as e:  # From get_user_profile_path
        app.logger.error(f"Error getting profile path for saving {user_id}: {e}")
        return False
    except IOError as e:
        app.logger.error(f"Could not save profile for user {user_id}: {e}")
        return False
    except Exception as e:
        app.logger.error(f"Unexpected error saving profile for {user_id}: {e}")
        return False


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Google OAuth Endpoints ---
@app.route('/authorize-google-calendar/<user_id>')
def authorize_google_calendar_route(user_id):
    if not user_id:
        return jsonify({"error": "user_id is required to start authorization"}), 400
    
    try:
        # Store user_id in session before starting auth flow
        session.clear()  # Clear any existing session data
        session['oauth_user_id'] = user_id
        session.permanent = True  # Make session persistent
        
        # Debug logging
        app.logger.info(f"Starting auth flow for user {user_id}")
        app.logger.info(f"Session contents before auth: {dict(session)}")
        
        authorization_url = calendar_service.start_auth_flow(session)
        
        if authorization_url:
            # Verify that state was properly set in session
            if 'google_oauth_state' not in session:
                app.logger.error("OAuth state not set in session after start_auth_flow")
                return jsonify({"error": "Failed to initialize OAuth state"}), 500
                
            app.logger.info(f"Session contents after auth: {dict(session)}")
            app.logger.info(f"Redirecting user {user_id} to Google for auth: {authorization_url}")
            return redirect(authorization_url)
        else:
            app.logger.error("Failed to get authorization_url from start_google_auth_flow")
            return jsonify({"error": "Failed to start Google authentication flow. Check server logs."}), 500
    except Exception as e:
        app.logger.error(f"Error in authorization flow: {str(e)}")
        return jsonify({"error": f"Authorization flow error: {str(e)}"}), 500

@app.route('/oauth2callback')
def oauth2callback_route():
    try:
        # Debug logging
        app.logger.info(f"OAuth callback received. Session contents: {dict(session)}")
        app.logger.info(f"Callback URL parameters: {dict(request.args)}")
        
        # Get user_id from session
        user_id = session.get('oauth_user_id')
        session_state = session.get('google_oauth_state')
        
        app.logger.info(f"Retrieved from session - user_id: {user_id}, state: {session_state}")
        
        if not user_id:
            app.logger.error("OAuth callback error: User ID missing from session.")
            # Try to get user_id from URL parameters as fallback
            user_id = request.args.get('state', '').split('_')[0] if request.args.get('state') else None
            if not user_id:
                return jsonify({"error": "OAuth callback error: User session context lost."}), 400
            app.logger.info(f"Recovered user_id from state parameter: {user_id}")
        
        if not session_state:
            app.logger.error("OAuth callback error: OAuth state missing from Flask session.")
            # Try to recover state from URL parameters
            google_returned_state = request.args.get('state')
            if google_returned_state:
                app.logger.info(f"Recovering state from URL parameter: {google_returned_state}")
                session_state = google_returned_state
            else:
                return jsonify({"error": "OAuth callback error: Session state missing and not found in URL."}), 400
        
        google_returned_state = request.args.get('state')
        if not google_returned_state:
            app.logger.error("No state parameter in callback URL")
            return jsonify({"error": "OAuth callback error: No state parameter in callback URL"}), 400
            
        if google_returned_state != session_state:
            app.logger.warning(f"OAuth callback state mismatch. Session state: {session_state}, URL state: {google_returned_state}")
            return jsonify({"error": "OAuth callback error: State mismatch."}), 400
        
        if request.args.get('error'):
            auth_error = request.args.get('error')
            app.logger.warning(f"Google Auth Error for user {user_id}: {auth_error}")
            return redirect(url_for('auth_status_page', status='error', message=auth_error, _external=True))
        
        # Now that we've verified everything, we can safely pop the values
        session.pop('oauth_user_id', None)
        session.pop('google_oauth_state', None)
        
        success = calendar_service.process_auth_callback(
            user_id,
            app.config['USER_DATA_FOLDER'],
            request.url,
            session_state
        )
        
        if success:
            app.logger.info(f"Google Calendar successfully authorized for user {user_id}.")
            return redirect(url_for('auth_status_page', status='success', _external=True))
        else:
            app.logger.error(f"Failed to process Google authentication callback for user {user_id}.")
            return redirect(url_for('auth_status_page', status='error', message='processing_failed', _external=True))
            
    except Exception as e:
        app.logger.error(f"Unexpected error in OAuth callback: {str(e)}")
        return jsonify({"error": f"OAuth callback error: {str(e)}"}), 500

@app.route('/auth_status')
def auth_status_page():
    try:
        status = request.args.get('status')
        message = request.args.get('message')
        
        if status == 'success':
            return """
            <html>
                <head>
                    <title>Authorization Successful</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        .success { color: #28a745; }
                        .message { margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <h1 class="success">Google Calendar Authorization Successful!</h1>
                    <p class="message">You can now close this tab and return to the application.</p>
                </body>
            </html>
            """
        else:
            return f"""
            <html>
                <head>
                    <title>Authorization Failed</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                        .error {{ color: #dc3545; }}
                        .message {{ margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <h1 class="error">Google Calendar Authorization Failed</h1>
                    <p class="message">Error: {message or 'Unknown error'}</p>
                    <p>Please try again or contact support.</p>
                </body>
            </html>
            """
    except Exception as e:
        app.logger.error(f"Error in auth status page: {str(e)}")
        return f"<h1>Error</h1><p>An unexpected error occurred: {str(e)}</p>"


# --- Core Application API Endpoints ---
@app.route('/profile/<user_id>', methods=['POST'])
def create_or_update_profile(user_id):
    if not user_id: return jsonify({"error": "user_id is required"}), 400
    data = request.get_json()
    if not data: return jsonify({"error": "No data provided"}), 400

    measurements = data.get('measurements', {})
    if measurements:  # If measurements object exists, height and weight must be there
        if not measurements.get('height_cm') or not measurements.get('weight_kg'):
            return jsonify({"error": "Height and Weight are mandatory in measurements."}), 400

    try:
        current_profile = load_user_profile(user_id)
    except Exception as e:
        app.logger.error(f"Failed to load profile for {user_id} during update: {e}")
        return jsonify({"error": f"Failed to load profile: {str(e)}"}), 500

    current_profile['user_id'] = user_id
    current_profile['age'] = data.get('age', current_profile.get('age'))
    user_gender = data.get('gender', current_profile.get('gender'))
    current_profile['gender'] = user_gender

    if measurements:
        current_profile['measurements'] = measurements
        calculated_metrics = calculate_all_metrics(measurements, user_gender)
        current_profile['calculated_metrics'] = calculated_metrics
        if 'bfp_from_measurements_navy' in calculated_metrics:
            if 'body_fat_estimates' not in current_profile: current_profile['body_fat_estimates'] = {}
            current_profile['body_fat_estimates']['from_measurements'] = {
                "value": calculated_metrics['bfp_from_measurements_navy'],
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "formula_used": "Navy Method"
            }

    lifestyle = data.get('lifestyle')
    if lifestyle: current_profile['lifestyle'] = lifestyle
    if 'progress_history' not in current_profile: current_profile['progress_history'] = []
    if 'body_fat_estimates' not in current_profile: current_profile['body_fat_estimates'] = {}

    if save_user_profile(user_id, current_profile):
        return jsonify({"message": "Profile updated successfully", "profile": current_profile}), 200
    else:
        return jsonify({"error": f"Failed to save profile for user {user_id}"}), 500


@app.route('/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    if not user_id: return jsonify({"error": "user_id is required"}), 400
    try:
        profile_data = load_user_profile(user_id)
        if not profile_data:  # If load_user_profile returns empty dict because file doesn't exist
            return jsonify({"message": f"No profile found for user {user_id}. Please create one."}), 404
        return jsonify(profile_data), 200
    except Exception as e:
        app.logger.error(f"Failed to get profile for {user_id}: {e}")
        return jsonify({"error": f"Failed to retrieve profile: {str(e)}"}), 500


@app.route('/analyze-photo/<user_id>', methods=['POST'])
def analyze_body_photo(user_id):
    if not user_id: return jsonify({"error": "user_id is required"}), 400
    if 'photo' not in request.files: return jsonify({"error": "No photo part"}), 400
    file = request.files['photo']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        temp_file_handler = None
        try:
            # Load user profile
            user_profile = load_user_profile(user_id)
            if not user_profile:
                return jsonify({"error": "User profile not found. Please create a profile first."}), 404

            # Save uploaded file temporarily
            _, ext = os.path.splitext(secure_filename(file.filename))
            temp_file_handler, temp_file_path = tempfile.mkstemp(suffix=ext)
            file.save(temp_file_path)

            # Log the user profile data for debugging
            app.logger.info(f"User profile data: {json.dumps(user_profile, indent=2)}")
            app.logger.info(f"Temporary file path: {temp_file_path}")

            try:
                # Analyze the photo using Gemini
                analysis_result = analyze_fat_percentage_with_gemini(user_profile, temp_file_path)
                app.logger.info(f"Analysis result: {json.dumps(analysis_result, indent=2)}")
            except Exception as e:
                app.logger.error(f"Error in Gemini analysis: {str(e)}")
                return jsonify({"error": f"Gemini analysis failed: {str(e)}"}), 500

            # Update user profile with analysis results
            if 'body_fat_estimates' not in user_profile:
                user_profile['body_fat_estimates'] = {}

            user_profile['body_fat_estimates']['from_photo'] = {
                "value": analysis_result.get('yag_orani'),
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "analysis": analysis_result.get('analiz'),
                "bmi": analysis_result.get('bmi'),
                "bmi_comment": analysis_result.get('bmi_yorum'),
                "bko": analysis_result.get('bko'),
                "bko_comment": analysis_result.get('bko_yorum'),
                "exercise_program": analysis_result.get('egzersiz_programi'),
                "diet_plan": analysis_result.get('diyet_listesi')
            }

            # Save updated profile
            if not save_user_profile(user_id, user_profile):
                return jsonify({"error": "Failed to save analysis results"}), 500

            return jsonify(analysis_result), 200

        except Exception as e:
            app.logger.error(f"Error analyzing photo for user {user_id}: {str(e)}")
            app.logger.exception("Full traceback:")  # This will log the full stack trace
            return jsonify({"error": f"Failed to analyze photo: {str(e)}"}), 500

        finally:
            # Clean up temporary file
            if temp_file_handler:
                os.close(temp_file_handler)
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    app.logger.error(f"Error cleaning up temp file: {str(e)}")

    return jsonify({"error": "Invalid file type"}), 400


@app.route('/generate-diet-plan/<user_id>', methods=['POST'])
def generate_diet(user_id):
    if not user_id: return jsonify({"error": "user_id is required"}), 400
    try:
        user_profile = load_user_profile(user_id)
    except Exception as e:
        return jsonify({"error": f"Failed to load profile for diet plan: {str(e)}"}), 500

    if not user_profile: return jsonify({"error": f"No profile for {user_id}."}), 404
    measurements = user_profile.get('measurements', {})
    if not measurements.get('height_cm') or not measurements.get('weight_kg'):
        return jsonify({"error": "Height and Weight required in profile for diet plan."}), 400
    if not user_profile.get('lifestyle'):
        return jsonify({"error": "Lifestyle details required for diet plan."}), 400

    bf_from_image = user_profile.get('body_fat_estimates', {}).get('from_image', {}).get('value')
    bf_from_measurements = user_profile.get('body_fat_estimates', {}).get('from_measurements', {}).get('value')
    bmi = user_profile.get('calculated_metrics', {}).get('bmi')
    body_comp_context_message = ""
    if bf_from_image is not None:
        body_comp_context_message = f"Plan based on image-estimated body fat: {bf_from_image}%."
    elif bf_from_measurements is not None:
        body_comp_context_message = f"Plan based on measurement-estimated body fat: {bf_from_measurements}%."
    elif bmi is not None:
        body_comp_context_message = "Warning: BFP not available. Plan based on BMI. For personalized plans, provide BFP info."
    else:
        body_comp_context_message = "Warning: Insufficient data for body composition. Plan is generalized."

    data_for_gemini = {
        "user_id": user_id, "age": user_profile.get("age"), "gender": user_profile.get("gender"),
        "measurements": measurements, "calculated_metrics": user_profile.get("calculated_metrics"),
        "lifestyle": user_profile.get("lifestyle"),
        "body_fat_estimates": user_profile.get('body_fat_estimates', {}),
        "body_composition_assessment_info": body_comp_context_message,
        "progress_history": user_profile.get("progress_history", [])
    }
    diet_plan = generate_diet_plan_with_gemini(data_for_gemini)

    if diet_plan and "error" not in diet_plan:
        user_profile['current_diet_plan'] = diet_plan
        if "notes_from_gemini" not in diet_plan: diet_plan["notes_from_gemini"] = ""
        diet_plan["notes_from_gemini"] = body_comp_context_message + "\n" + diet_plan.get("notes_from_gemini", "")
        if save_user_profile(user_id, user_profile):
            return jsonify({"message": "Diet plan generated", "diet_plan": diet_plan,
                            "context_message": body_comp_context_message}), 200
        else:
            return jsonify({"error": "Plan generated, but failed to save profile"}), 500
    else:
        error_msg = diet_plan.get("error") if diet_plan else "Diet plan generation failed"
        return jsonify({"error": f"Diet plan generation failed: {error_msg}"}), 500


@app.route('/profile/<user_id>/schedule-checkup', methods=['POST'])
def schedule_checkup_route(user_id):
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    data = request.get_json()
    if not data or 'day_of_week' not in data or 'time_of_day' not in data:
        return jsonify({"error": "day_of_week and time_of_day are required."}), 400
    
    try:
        user_profile = load_user_profile(user_id)
        if not user_profile:
            return jsonify({"error": f"No profile for {user_id}"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to load profile for scheduling: {str(e)}"}), 500
    
    # Check if user has Google Auth tokens
    calendar_service_instance = calendar_service.get_calendar_service(user_id, app.config['USER_DATA_FOLDER'])
    if not calendar_service_instance:
        auth_url = url_for('authorize_google_calendar_route', user_id=user_id, _external=True)
        return jsonify({
            "error": "Google Calendar not authorized or token invalid.",
            "authorization_needed": True,
            "authorization_url": auth_url
        }), 401
    
    # Delete old event if exists
    old_event_id = user_profile.get("checkup_preference", {}).get("google_calendar_event_id")
    if old_event_id:
        calendar_service.delete_event(user_id, app.config['USER_DATA_FOLDER'], old_event_id)
    
    # Create new event
    event_id = calendar_service.create_weekly_checkup(
        user_id,
        app.config['USER_DATA_FOLDER'],
        data['day_of_week'],
        data['time_of_day']
    )
    
    if event_id:
        user_profile['checkup_preference'] = {
            "day_of_week": data['day_of_week'],
            "time_of_day": data['time_of_day'],
            "google_calendar_event_id": event_id
        }
        
        if save_user_profile(user_id, user_profile):
            return jsonify({
                "message": "Weekly check-up scheduled in your Google Calendar.",
                "event_id": event_id
            }), 200
        else:
            return jsonify({
                "message": "Check-up scheduled, but failed to update profile. Event ID: " + event_id
            }), 500
    else:
        auth_url = url_for('authorize_google_calendar_route', user_id=user_id, _external=True)
        return jsonify({
            "error": "Failed to schedule check-up. Re-authorization might be needed.",
            "authorization_needed": True,
            "authorization_url": auth_url
        }), 500


@app.route('/track-progress/<user_id>', methods=['POST'])
def track_user_progress(user_id):
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        current_profile = load_user_profile(user_id)
        if not current_profile:
            return jsonify({"error": f"No profile found for user {user_id}"}), 404
        
        # Validate required fields
        required_fields = ['weight_kg', 'measurements']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields: weight_kg and measurements"}), 400
        
        # Create progress entry
        progress_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "weight_kg": data['weight_kg'],
            "measurements": data['measurements']
        }
        
        # Add any optional fields if provided
        if 'notes' in data:
            progress_entry['notes'] = data['notes']
        
        # Initialize progress_history if it doesn't exist
        if 'progress_history' not in current_profile:
            current_profile['progress_history'] = []
        
        # Add new progress entry
        current_profile['progress_history'].append(progress_entry)
        
        # Update current measurements
        current_profile['measurements'] = data['measurements']
        
        # Recalculate metrics
        calculated_metrics = calculate_all_metrics(data['measurements'], current_profile.get('gender'))
        current_profile['calculated_metrics'] = calculated_metrics
        
        # Update body fat estimates if available
        if 'bfp_from_measurements_navy' in calculated_metrics:
            if 'body_fat_estimates' not in current_profile:
                current_profile['body_fat_estimates'] = {}
            current_profile['body_fat_estimates']['from_measurements'] = {
                "value": calculated_metrics['bfp_from_measurements_navy'],
                "timestamp": progress_entry['timestamp'],
                "formula_used": "Navy Method"
            }
        
        if save_user_profile(user_id, current_profile):
            return jsonify({
                "message": "Progress tracked successfully",
                "profile": current_profile
            }), 200
        else:
            return jsonify({"error": "Failed to save progress"}), 500
            
    except Exception as e:
        app.logger.error(f"Error tracking progress for user {user_id}: {e}")
        return jsonify({"error": f"Failed to track progress: {str(e)}"}), 500


@app.route('/test-gemini', methods=['GET'])
def test_gemini():
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({"error": "GEMINI_API_KEY not found in environment variables"}), 500
        
        # Try to initialize the model
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        # Try a simple test generation
        response = model.generate_content("Say hello!")
        
        return jsonify({
            "status": "success",
            "message": "Gemini API is properly configured",
            "response": response.text
        }), 200
    except Exception as e:
        app.logger.error(f"Gemini API test failed: {str(e)}")
        return jsonify({
            "error": f"Gemini API test failed: {str(e)}",
            "api_key_exists": bool(os.getenv('GEMINI_API_KEY'))
        }), 500


# --- Main Execution ---
if __name__ == '__main__':
    # Ensure GOOGLE_CLIENT_CONFIG_JSON is valid before starting if OAuth is critical
    if not os.getenv('GOOGLE_CLIENT_CONFIG_JSON'):
        app.logger.warning(
            "GOOGLE_CLIENT_CONFIG_JSON not found or not configured in .env. Google Calendar features will fail.")

    app.run(debug=(os.getenv('FLASK_ENV') == 'development'), port=int(os.getenv('FLASK_RUN_PORT', 5000)))