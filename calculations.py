"""
utils/calculations.py

Provides functions to compute health-related metrics:
- Body Mass Index (BMI)
- Waist-to-Hip Ratio (WHR)
- Body fat percentage using the U.S. Navy method
- Aggregation of all available metrics
"""

import math

def calculate_bmi(weight_kg, height_cm):
    """
    Calculates Body Mass Index (BMI).

    Args:
        weight_kg (float): Weight in kilograms
        height_cm (float): Height in centimeters

    Returns:
        float: BMI value rounded to two decimals, or None if inputs are invalid
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
        float: WHR value rounded to two decimals, or None if inputs are invalid
    """
    if not waist_cm or not hip_cm or waist_cm <= 0 or hip_cm <= 0:
        return None
    whr = waist_cm / hip_cm
    return round(whr, 2)

def calculate_body_fat_navy(gender, height_cm, neck_cm, waist_cm, hip_cm=None):
    """
    Estimates body fat percentage using the U.S. Navy method.

    Args:
        gender (str): "male" or "female"
        height_cm (float): Height in centimeters
        neck_cm (float): Neck circumference in centimeters
        waist_cm (float): Waist circumference in centimeters
        hip_cm (float, optional): Hip circumference in centimeters (required for females)

    Returns:
        float: Estimated body fat percentage rounded to two decimals, or None if inputs are invalid
    """
    if not all([gender, height_cm, neck_cm, waist_cm]):
        return None
    if height_cm <= 0 or neck_cm <= 0 or waist_cm <= 0:
        return None

    gender = gender.lower()

    if gender == "male":
        if waist_cm <= neck_cm:
            return None
        try:
            bfp = 86.010 * math.log10(waist_cm - neck_cm) \
                  - 70.041 * math.log10(height_cm) + 36.76
        except ValueError:
            return None
    elif gender == "female":
        if not hip_cm or hip_cm <= 0:
            return None
        if (waist_cm + hip_cm) <= neck_cm:
            return None
        try:
            bfp = 163.205 * math.log10(waist_cm + hip_cm - neck_cm) \
                  - 97.684 * math.log10(height_cm) - 78.387
        except ValueError:
            return None
    else:
        return None

    return round(bfp, 2) if bfp > 0 else None

def calculate_all_metrics(measurements, gender=None):
    """
    Calculates a set of health metrics based on raw measurements.

    Args:
        measurements (dict):
            - weight_kg (float)
            - height_cm (float)
            - waist_cm (float)
            - hip_cm (float)
            - neck_cm (float)
        gender (str, optional): "male" or "female" to enable body fat calculation

    Returns:
        dict: Keys may include 'bmi', 'whr', and 'bfp_from_measurements_navy'
    """
    if not measurements:
        return {}

    calculated_metrics = {}

    bmi = calculate_bmi(
        measurements.get('weight_kg'),
        measurements.get('height_cm')
    )
    if bmi is not None:
        calculated_metrics['bmi'] = bmi

    whr = calculate_whr(
        measurements.get('waist_cm'),
        measurements.get('hip_cm')
    )
    if whr is not None:
        calculated_metrics['whr'] = whr

    if gender:
        bfp_navy = calculate_body_fat_navy(
            gender,
            measurements.get('height_cm'),
            measurements.get('neck_cm'),
            measurements.get('waist_cm'),
            measurements.get('hip_cm') if gender.lower() == 'female' else None
        )
        if bfp_navy is not None:
            calculated_metrics['bfp_from_measurements_navy'] = bfp_navy

    return calculated_metrics
