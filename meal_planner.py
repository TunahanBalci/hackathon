def generate_diet_plan_with_gemini(user_profile_data):

    print(f"--- MOCK/Actual: Calling Gemini Meal Planner ---")
    print(f"User Profile for Meal Plan: {user_profile_data}")

    mock_diet_plan = {
        "summary": "Mock plan considering body comp. info: " + user_profile_data['body_composition_assessment_info'],
        "monday": {"breakfast": "...", "lunch": "...", "dinner": "..."},
        "notes_from_gemini": user_profile_data.get('body_composition_assessment_info', '')
    }
    return mock_diet_plan
