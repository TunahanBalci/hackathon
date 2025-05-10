# backend/app.py
import os
import json
import tempfile
import datetime
from flask import Flask, request, jsonify, redirect, session, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

# Import your utility, Gemini, and Google Calendar modules
from utils.calculations import calculate_all_metrics
from gemini.meal_planner import generate_diet_plan_with_gemini
from gemini.fat_analyzer import analyze_fat_percentage_with_gemini
from google_calendar_service import (
    start_google_auth_flow,
    process_google_auth_callback,
    create_weekly_checkup_event_for_user,
    delete_calendar_event_for_user,
    get_calendar_service_for_user  # For checking if user is authenticated
)

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("No FLASK_SECRET_KEY set. Please set it in your .env file.")

CORS(app)  # Enable CORS for frontend interaction

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
def authorize_google_calendar_route(user_id):  # Renamed to avoid conflict
    if not user_id:
        return jsonify({"error": "user_id is required to start authorization"}), 400
    session['oauth_user_id'] = user_id  # Store user_id for the callback

    # Pass the Flask session object to your auth flow function
    authorization_url = start_google_auth_flow(session)

    if authorization_url:
        app.logger.info(f"Redirecting user {user_id} to Google for auth: {authorization_url}")
        return redirect(authorization_url)
    else:
        app.logger.error("Failed to get authorization_url from start_google_auth_flow")
        return jsonify({"error": "Failed to start Google authentication flow. Check server logs."}), 500


@app.route('/oauth2callback')  # This MUST match your GOOGLE_REDIRECT_URI
def oauth2callback_route():  # Renamed to avoid conflict
    user_id = session.pop('oauth_user_id', None)
    session_state_from_flask = session.pop('google_oauth_state', None)  # State stored by start_google_auth_flow

    if not user_id:
        app.logger.error("OAuth callback error: User ID missing from session.")
        return jsonify({"error": "OAuth callback error: User session context lost."}), 400
    if not session_state_from_flask:
        app.logger.error("OAuth callback error: OAuth state missing from Flask session.")
        return jsonify({"error": "OAuth callback error: Session state missing."}), 400

    google_returned_state = request.args.get('state')
    if google_returned_state != session_state_from_flask:
        app.logger.warning(f"OAuth callback state mismatch for user {user_id}. CSRF attempt?")
        return jsonify({"error": "OAuth callback error: State mismatch."}), 400

    if request.args.get('error'):
        auth_error = request.args.get('error')
        app.logger.warning(f"Google Auth Error for user {user_id}: {auth_error}")
        # Provide a more user-friendly redirect or message
        return redirect(url_for('auth_status_page', status='error', message=auth_error, _external=True))

    success = process_google_auth_callback(
        user_id,
        app.config['USER_DATA_FOLDER'],
        request.url,  # Pass the full callback URL
        session_state_from_flask  # Pass the original state for verification
    )

    if success:
        app.logger.info(f"Google Calendar successfully authorized for user {user_id}.")
        # Redirect to a frontend page indicating success
        # For hackathon, a simple message or redirect to a known frontend route
        return redirect(url_for('auth_status_page', status='success', _external=True))

    else:
        app.logger.error(f"Failed to process Google authentication callback for user {user_id}.")
        return redirect(url_for('auth_status_page', status='error', message='processing_failed', _external=True))


@app.route('/auth_status')  # Simple page to show auth status after redirect
def auth_status_page():
    status = request.args.get('status')
    message = request.args.get('message')
    if status == 'success':
        return "<h1>Google Calendar Authorization Successful!</h1><p>You can now close this tab and return to the application.</p>"
    else:
        return f"<h1>Google Calendar Authorization Failed</h1><p>Error: {message or 'Unknown error'}. Please try again or contact support.</p>"


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
        temp_file_handler = None  # Use a more descriptive name
        try:
            _, ext = os.path.splitext(secure_filename(file.filename))
            # delete=False is important as we pass path, then manually delete
            temp_file_handler = tempfile.NamedTemporaryFile(delete=False, suffix=ext, prefix=f"{user_id}_photo_")
            file.save(temp_file_handler.name)
            temp_filepath = temp_file_handler.name
            temp_file_handler.close()  # Close file before passing path

            current_profile = load_user_profile(user_id)
            analysis_result = analyze_fat_percentage_with_gemini(temp_filepath, current_profile)

            if analysis_result and "error" not in analysis_result:
                if 'body_fat_estimates' not in current_profile: current_profile['body_fat_estimates'] = {}
                current_profile['body_fat_estimates']['from_image'] = {
                    "value": analysis_result.get("estimated_body_fat_percentage"),
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                    "confidence_score": analysis_result.get("confidence_score"),
                    "feedback": analysis_result.get("feedback")
                }
                if save_user_profile(user_id, current_profile):
                    return jsonify(
                        {"message": "Photo analyzed", "analysis": analysis_result, "profile": current_profile}), 200
                else:
                    return jsonify({"error": "Analyzed, but failed to update profile"}), 500
            else:
                error_msg = analysis_result.get("error") if analysis_result else "Fat analysis failed"
                return jsonify({"error": f"Fat analysis failed: {error_msg}"}), 500
        except Exception as e:
            app.logger.error(f"Photo analysis error for {user_id}: {e}")
            return jsonify({"error": "Internal error during photo analysis."}), 500
        finally:
            if temp_file_handler and os.path.exists(temp_file_handler.name):
                try:
                    os.remove(temp_file_handler.name)
                except OSError as e_del:
                    app.logger.error(f"Error deleting temp file {temp_file_handler.name}: {e_del}")
    else:
        return jsonify({"error": "File type not allowed"}), 400


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
def schedule_checkup_route(user_id):  # Renamed to avoid conflict
    if not user_id: return jsonify({"error": "user_id is required"}), 400
    data = request.get_json()
    if not data or 'day_of_week' not in data or 'time_of_day' not in data:
        return jsonify({"error": "day_of_week and time_of_day are required."}), 400

    day_of_week = data['day_of_week']
    time_of_day = data['time_of_day']

    try:
        user_profile = load_user_profile(user_id)
        if not user_profile: return jsonify({"error": f"No profile for {user_id}"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to load profile for scheduling: {str(e)}"}), 500

    # Check if user has Google Auth tokens by trying to get the service
    # The get_calendar_service_for_user will return None if not authenticated
    calendar_service = get_calendar_service_for_user(user_id, app.config['USER_DATA_FOLDER'])
    if not calendar_service:
        auth_url = url_for('authorize_google_calendar_route', user_id=user_id, _external=True)
        return jsonify({
            "error": "Google Calendar not authorized or token invalid.",
            "authorization_needed": True,
            "authorization_url": auth_url
        }), 401

    old_event_id = user_profile.get("checkup_preference", {}).get("google_calendar_event_id")
    if old_event_id:
        delete_calendar_event_for_user(user_id, app.config['USER_DATA_FOLDER'], old_event_id)  # Pass user_profile_dir

    event_id = create_weekly_checkup_event_for_user(
        user_id,
        app.config['USER_DATA_FOLDER'],  # Pass user_profile_dir
        day_of_week,
        time_of_day
    )

    if event_id:
        user_profile['checkup_preference'] = {
            "day_of_week": day_of_week, "time_of_day": time_of_day,
            "google_calendar_event_id": event_id
        }
        if save_user_profile(user_id, user_profile):
            return jsonify({"message": "Weekly check-up scheduled in your Google Calendar.", "event_id": event_id}), 200
        else:
            return jsonify({
                               "message": "Check-up scheduled, but failed to update profile. Event ID: " + event_id}), 500  # Partial success
    else:
        auth_url = url_for('authorize_google_calendar_route', user_id=user_id, _external=True)
        return jsonify({
            "error": "Failed to schedule check-up. Re-authorization might be needed.",
            "authorization_needed": True,
            "authorization_url": auth_url
        }), 500


@app.route('/track-progress/<user_id>', methods=['POST'])
def track_user_progress(user_id):
    if not user_id: return jsonify({"error": "user_id is required"}), 400
    data = request.get_json()
    if not data or 'measurements' not in data:
        return jsonify({"error": "No new measurement data provided"}), 400
    try:
        current_profile = load_user_profile(user_id)
        if not current_profile: return jsonify({"error": f"No profile for {user_id}"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to load profile for progress tracking: {str(e)}"}), 500

    new_measurements = data['measurements']
    user_gender = current_profile.get('gender')
    if 'height_cm' not in new_measurements: new_measurements['height_cm'] = current_profile.get('measurements', {}).get(
        'height_cm')
    if not new_measurements.get('height_cm') or not new_measurements.get('weight_kg'):
        return jsonify({"error": "Height and Weight are mandatory for progress tracking."}), 400

    calculated_metrics_progress = calculate_all_metrics(new_measurements, user_gender)
    progress_entry = {
        "date": data.get("date", datetime.datetime.utcnow().isoformat() + "Z"),
        "measurements": new_measurements,
        "calculated_metrics": calculated_metrics_progress
    }
    if 'progress_history' not in current_profile or not isinstance(current_profile['progress_history'], list):
        current_profile['progress_history'] = []
    current_profile['progress_history'].append(progress_entry)
    current_profile['measurements'] = new_measurements
    current_profile['calculated_metrics'] = calculated_metrics_progress
    if 'bfp_from_measurements_navy' in calculated_metrics_progress:
        if 'body_fat_estimates' not in current_profile: current_profile['body_fat_estimates'] = {}
        current_profile['body_fat_estimates']['from_measurements'] = {
            "value": calculated_metrics_progress['bfp_from_measurements_navy'],
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "formula_used": "Navy Method"
        }

    response_message = "Progress tracked successfully."
    response_data_payload = {"profile": current_profile}

    if data.get('regenerate_plan', False):
        # Re-use logic from generate_diet for consistency
        bf_img = current_profile.get('body_fat_estimates', {}).get('from_image', {}).get('value')
        bf_msr = current_profile.get('body_fat_estimates', {}).get('from_measurements', {}).get('value')
        bmi_val = current_profile.get('calculated_metrics', {}).get('bmi')
        ctx_msg = ""
        if bf_img is not None:
            ctx_msg = f"Plan based on image BFP: {bf_img}%."
        elif bf_msr is not None:
            ctx_msg = f"Plan based on measurement BFP: {bf_msr}%."
        elif bmi_val is not None:
            ctx_msg = "Warning: BFP not available. Plan based on BMI."
        else:
            ctx_msg = "Warning: Insufficient data for body comp."

        data_gemini_prog = {
            "user_id": user_id, "age": current_profile.get("age"), "gender": user_gender,
            "measurements": current_profile.get("measurements"),
            "calculated_metrics": current_profile.get("calculated_metrics"),
            "lifestyle": current_profile.get("lifestyle"),
            "body_fat_estimates": current_profile.get('body_fat_estimates', {}),
            "body_composition_assessment_info": ctx_msg, "progress_history": current_profile.get("progress_history", [])
        }
        new_diet_plan = generate_diet_plan_with_gemini(data_gemini_prog)
        if new_diet_plan and "error" not in new_diet_plan:
            current_profile['current_diet_plan'] = new_diet_plan
            if "notes_from_gemini" not in new_diet_plan: new_diet_plan["notes_from_gemini"] = ""
            new_diet_plan["notes_from_gemini"] = ctx_msg + "\n" + new_diet_plan.get("notes_from_gemini", "")
            response_message += " New diet plan generated."
            response_data_payload['new_diet_plan'] = new_diet_plan
            response_data_payload['context_message'] = ctx_msg
        else:
            response_message += " Failed to regenerate diet plan."

    if save_user_profile(user_id, current_profile):
        return jsonify({"message": response_message, "data": response_data_payload}), 200
    else:
        return jsonify({"error": "Progress tracked, but failed to save updated profile"}), 500


# --- Main Execution ---
if __name__ == '__main__':
    # Ensure GOOGLE_CLIENT_SECRET_FILE is valid before starting if OAuth is critical
    if not os.getenv('GOOGLE_CLIENT_SECRET_FILE') or not os.path.exists(os.getenv('GOOGLE_CLIENT_SECRET_FILE')):
        app.logger.warning(
            "GOOGLE_CLIENT_SECRET_FILE not found or not configured in .env. Google Calendar features will fail.")

    app.run(debug=(os.getenv('FLASK_ENV') == 'development'), port=int(os.getenv('FLASK_RUN_PORT', 5000)))