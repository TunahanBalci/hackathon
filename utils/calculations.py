# backend/utils/calculations.py
import math

def calculate_bmi(weight_kg, height_cm):
    """
    Calculates Body Mass Index (BMI).
    Args:
        weight_kg (float): Weight in kilograms
        height_cm (float): Height in centimeters
    Returns:
        float: BMI value, or None if inputs are invalid
    """
    if not weight_kg or not height_cm or weight_kg <= 0 or height_cm <= 0:
        return None
    height_m = height_cm / 100
    bmi = weight_kg / (height_m * height_m)
    return round(bmi, 2)

def calculate_whr(waist_cm, hip_cm):
    """
    Calculates Waist-to-Hip Ratio (WHR).
    Args:
        waist_cm (float): Waist circumference in centimeters
        hip_cm (float): Hip circumference in centimeters
    Returns:
        float: WHR value, or None if inputs are invalid
    """
    if not waist_cm or not hip_cm or waist_cm <= 0 or hip_cm <= 0:
        return None
    whr = waist_cm / hip_cm
    return round(whr, 2)

# ... (calculate_bmi, calculate_whr, calculate_all_metrics from before) ...

def calculate_body_fat_navy(gender, height_cm, neck_cm, waist_cm, hip_cm=None):
    """
    Estimates body fat percentage using the U.S. Navy method.
    Args:
        gender (str): "male" or "female".
        height_cm (float): Height in centimeters.
        neck_cm (float): Neck circumference in centimeters.
        waist_cm (float): Waist circumference in centimeters.
        hip_cm (float, optional): Hip circumference in centimeters (required for females).

    Returns:
        float: Estimated body fat percentage, or None if inputs are invalid.
    """
    if not all([gender, height_cm, neck_cm, waist_cm]):
        return None
    if height_cm <= 0 or neck_cm <= 0 or waist_cm <= 0:
        return None

    gender = gender.lower()

    if gender == "male":
        # Formula for men:
        # BFP = 86.010 * log10(waist - neck) - 70.041 * log10(height) + 36.76
        # Ensure waist - neck is positive for log
        if waist_cm <= neck_cm:
            return None # Or handle as very low body fat, but formula might break
        try:
            bfp = 86.010 * math.log10(waist_cm - neck_cm) - 70.041 * math.log10(height_cm) + 36.76
        except ValueError: # log of non-positive number
            return None
    elif gender == "female":
        if not hip_cm or hip_cm <= 0:
            return None
        # Formula for women:
        # BFP = 163.205 * log10(waist + hip - neck) - 97.684 * log10(height) - 78.387
        # Ensure waist + hip - neck is positive
        if (waist_cm + hip_cm) <= neck_cm:
            return None
        try:
            bfp = 163.205 * math.log10(waist_cm + hip_cm - neck_cm) - 97.684 * math.log10(height_cm) - 78.387
        except ValueError:
            return None
    else:
        return None # Invalid gender

    return round(bfp, 2) if bfp > 0 else None # Body fat should be positive


# Update calculate_all_metrics to include body fat from measurements
def calculate_all_metrics(measurements, gender=None): # Add gender here
    """
    Calculates all relevant metrics from raw measurements.
    """
    if not measurements:
        return {}

    calculated_metrics = {}
    bmi = calculate_bmi(measurements.get('weight_kg'), measurements.get('height_cm'))
    if bmi is not None:
        calculated_metrics['bmi'] = bmi

    whr = calculate_whr(measurements.get('waist_cm'), measurements.get('hip_cm'))
    if whr is not None:
        calculated_metrics['whr'] = whr

    if gender: # Only calculate if gender is provided
        bfp_navy = calculate_body_fat_navy(
            gender,
            measurements.get('height_cm'),
            measurements.get('neck_cm'), # Ensure neck_cm is in measurements
            measurements.get('waist_cm'),
            measurements.get('hip_cm') if gender == 'female' else None
        )
        if bfp_navy is not None:
            # This will be stored under calculated_metrics,
            # app.py will then move it to body_fat_estimates.from_measurements
            calculated_metrics['bfp_from_measurements_navy'] = bfp_navy

    return calculated_metrics