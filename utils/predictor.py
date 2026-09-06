"""
SafeCross AI - Prediction Utilities
Handles model inference and risk scoring.
"""

import numpy as np
import pandas as pd
from utils.data_loader import (
    load_severity_model, load_fatality_model, 
    load_encoders, load_target_encoder, load_feature_meta,
    load_severity_model_v2, load_encoders_v2, load_feature_meta_v2
)

def _build_full_features(weather, road_condition, accident_cause, traffic_density,
                         vehicles_involved, nearby_accidents, hour, day_of_week, 
                         latitude=0.0, longitude=0.0, month=None):
    """
    Build the complete 26-feature set for the honest model (leakage-free).
    """
    if month is None:
        month = 6  # Default to June
    
    features = {
        # Base categorical
        'road_condition': road_condition,
        'weather': weather,
        'accident_cause': accident_cause,
        'traffic_density': traffic_density,
        'lane_utilization': 'Unknown',  # Not used in honest model but required for schema
        
        # Base numeric
        'vehicles_involved': vehicles_involved,
        'nearby_accidents': nearby_accidents,
        'hour': hour,
        'day_of_week': day_of_week,
        'month': month,
        
        # Binary flags
        'is_night': 1 if (hour >= 20 or hour < 6) else 0,
        'is_rush_hour': 1 if ((7 <= hour <= 9) or (17 <= hour <= 19)) else 0,
        'is_weekend': 1 if day_of_week >= 5 else 0,
        
        # Geographic (used in honest model)
        'latitude': latitude,
        'longitude': longitude,
        
        # Interaction features (6 total)
        'weather_x_road_condition': f"{weather}_{road_condition}",
        'weather_x_accident_cause': f"{weather}_{accident_cause}",
        'weather_x_traffic_density': f"{weather}_{traffic_density}",
        'road_condition_x_accident_cause': f"{road_condition}_{accident_cause}",
        'road_condition_x_traffic_density': f"{road_condition}_{traffic_density}",
        'accident_cause_x_traffic_density': f"{accident_cause}_{traffic_density}",
        
        # Severity scores
        'weather_severity_score': _get_weather_severity(weather),
        'road_severity_score': _get_road_severity(road_condition),
        'combined_severity_score': _get_weather_severity(weather) + _get_road_severity(road_condition),
        
        # Bins
        'vehicles_bin': _bin_vehicles(vehicles_involved),
        'nearby_bin': _bin_nearby(nearby_accidents),
    }
    
    return features

def _get_weather_severity(weather):
    """Convert weather to severity score."""
    severity_map = {'Clear': 0, 'Cloudy': 1, 'Rain': 2, 'Fog': 3, 'Heavy Rain': 4, 'Dust Storm': 5}
    return severity_map.get(weather, 0)

def _get_road_severity(road_condition):
    """Convert road condition to severity score."""
    severity_map = {'Dry': 0, 'Wet': 1, 'Construction': 2, 'Potholed': 3, 'Muddy': 4, 'Flooding': 5}
    return severity_map.get(road_condition, 0)

def _bin_vehicles(v):
    """Bin vehicles_involved according to honest model schema."""
    if v <= 1:
        return "1"
    elif v == 2:
        return "2"
    elif v == 3:
        return "3"
    elif v <= 5:
        return "4-5"
    else:
        return "6+"

def _bin_nearby(n):
    """Bin nearby_accidents according to honest model schema."""
    if n <= 5:
        return "0-5"
    elif n <= 10:
        return "6-10"
    elif n <= 15:
        return "11-15"
    elif n <= 20:
        return "16-20"
    else:
        return "21+"

def predict_severity(weather, road_condition, accident_cause, traffic_density,
                     vehicles_involved, nearby_accidents, hour, day_of_week, is_night,
                     latitude=0.0, longitude=0.0, month=None):
    """
    Predict accident severity using the trained honest model (53.5% accuracy, leakage-free).
    
    Returns:
        dict: {
            'severity': str,
            'probabilities': dict,
            'risk_score': float,
            'risk_level': str,
            'risk_color': str,
            'confidence': float
        }
    """
    model = load_severity_model()
    encoders_data = load_encoders()
    meta = load_feature_meta()
    
    # Handle both old and new encoder formats
    if 'y_encoder' in encoders_data:
        # New honest model format
        y_encoder = encoders_data['y_encoder']
        feature_encoders = encoders_data['feature_encoders']
    else:
        # Old format - need to extract y_encoder from target_encoder
        from utils.data_loader import load_target_encoder
        y_encoder = load_target_encoder()
        feature_encoders = encoders_data
    
    # Build full 26-feature set
    features = _build_full_features(
        weather, road_condition, accident_cause, traffic_density,
        vehicles_involved, nearby_accidents, hour, day_of_week,
        latitude, longitude, month
    )
    
    # Encode categorical features
    X_encoded = {}
    feature_names = meta.get('features', [])
    
    # Identify categorical features that need encoding
    categorical_cols = ['road_condition', 'weather', 'accident_cause', 'traffic_density', 
                        'lane_utilization', 'vehicles_bin', 'nearby_bin',
                        'weather_x_road_condition', 'weather_x_accident_cause', 
                        'weather_x_traffic_density', 'road_condition_x_accident_cause',
                        'road_condition_x_traffic_density', 'accident_cause_x_traffic_density']
    
    for col in feature_names:
        if col in categorical_cols and col in feature_encoders:
            le = feature_encoders[col]
            val = str(features.get(col, ""))
            # Handle unseen categories
            if val not in le.classes_:
                val = le.classes_[0]
            X_encoded[col] = le.transform([val])[0]
        else:
            # Numeric or no encoder needed
            X_encoded[col] = features.get(col, 0)
    
    # Create feature array in correct order
    X_array = np.array([[X_encoded.get(col, 0) for col in feature_names]])
    
    # Defensive validation
    expected_features = model.n_features_in_
    actual_features = X_array.shape[1]
    if actual_features != expected_features:
        raise ValueError(
            f"Severity model feature mismatch: expected {expected_features} features, "
            f"got {actual_features}. Schema: {feature_names}"
        )
    
    # Predict
    prediction = model.predict(X_array)[0]
    probabilities = model.predict_proba(X_array)[0]
    
    severity = y_encoder.inverse_transform([prediction])[0]
    prob_dict = {
        y_encoder.inverse_transform([i])[0]: float(prob)
        for i, prob in enumerate(probabilities)
    }
    
    # Calculate risk score (0-100)
    severity_weights = {'Low': 0, 'Medium': 33, 'High': 66, 'Critical': 100}
    risk_score = sum(prob_dict[sev] * severity_weights[sev] for sev in prob_dict)
    
    # Confidence = max probability
    confidence = max(probabilities)
    
    # Determine risk level
    if risk_score >= 75:
        risk_level = "Critical"
        risk_color = "#ef4444"
    elif risk_score >= 50:
        risk_level = "High"
        risk_color = "#f97316"
    elif risk_score >= 25:
        risk_level = "Medium"
        risk_color = "#f59e0b"
    else:
        risk_level = "Low"
        risk_color = "#10b981"
    
    return {
        'severity': severity,
        'probabilities': prob_dict,
        'risk_score': risk_score,
        'risk_level': risk_level,
        'risk_color': risk_color,
        'confidence': float(confidence)
    }

# --- V2 cause mapping: UI options → V2 encoder classes ---
_V2_CAUSE_MAP = {
    "Human Error": "Human Error",
    "Signal Violation": "Signal Violation",
    "Weather": "Weather",
    "Poor Road": "Human Error",       # No "Poor Road" in V2; closest safe fallback
    "Mechanical Failure": "Mechanical Failure",
    "Animal Crossing": "Animal Crossing",
}

def _derive_lighting(hour):
    """Derive lighting condition from hour of day."""
    if 6 <= hour <= 17:
        return "Daylight"
    elif hour in (5, 18):
        return "Dawn-Dusk"
    elif 19 <= hour <= 21:
        return "Street-lit"
    else:
        return "Unlit"

def _derive_peak_off_peak(hour):
    """Derive peak/off-peak from hour."""
    if (7 <= hour <= 9) or (17 <= hour <= 19):
        return "Peak"
    return "Off-peak"

def predict_severity_v2(weather, road_condition, accident_cause, traffic_density,
                        vehicles_involved, nearby_accidents, hour, day_of_week, is_night,
                        speed_at_impact_kmh, collision_type,
                        accident_date_str, accident_time_str,
                        latitude=0.0, longitude=0.0):
    """
    Predict accident severity using the Pakistan V2 model (HistGradientBoosting, 98.5% accuracy).
    
    Builds all 39 features: 10 from UI, 2 derived from time, 27 from documented dataset
    medians/modes. Falls back to honest model if V2 artifacts are missing.
    
    Returns same dict format as predict_severity().
    """
    model = load_severity_model_v2()
    encoders_data = load_encoders_v2()
    meta = load_feature_meta_v2()

    if model is None or encoders_data is None or meta is None:
        return None

    y_encoder = encoders_data['y_encoder']
    feature_encoders = encoders_data['feature_encoders']
    feature_names = meta['features']

    v2_cause = _V2_CAUSE_MAP.get(accident_cause, "Human Error")

    features = {
        # --- From UI inputs ---
        'weather': weather,
        'road_condition': road_condition,
        'accident_cause': v2_cause,
        'num_vehicles': int(vehicles_involved),
        'speed_at_impact_kmh': float(speed_at_impact_kmh),
        'collision_type': collision_type,
        'date': accident_date_str,
        'time': accident_time_str,

        # --- Derived from hour ---
        'lighting': _derive_lighting(hour),
        'peak_off_peak': _derive_peak_off_peak(hour),

        # --- Categorical defaults (dataset mode) ---
        'province': 'Punjab',
        'district': 'Islamabad',
        'road_type': 'Urban',
        'surface_material': 'Asphalt',
        'road_curvature': 'Straight',
        'road_gradient': 'Flat',
        'median_type': 'Physical',
        'shoulder_available': 'Yes',
        'vehicle_types': 'Motorcycle;Motorcycle',
        'overloading_detected': 'No',
        'helmet_usage': 'No',
        'seatbelt_usage': 'Yes',
        'mobile_phone_suspected': 'No',
        'alcohol_drug_suspected': 'No',
        'evasive_action': 'Braking',
        'impact_point': 'Front',

        # --- Numeric defaults (dataset median) ---
        'latitude': float(latitude),
        'longitude': float(longitude),
        'visibility_meters': 267.0,
        'temperature_c': 29.8,
        'wind_speed_kmh': 8.4,
        'number_of_lanes': 2.0,
        'speed_limit_kmh': 60.0,
        'vehicle_avg_age_years': 10.9,
        'driver_age': 34.0,
        'num_collisions': 1.0,
        'traffic_volume_per_hour': 1023.0,
        'distance_to_hospital_km': 8.4,
        'expected_response_min': 15.6,
    }

    cat_cols = set(meta['cat_cols'])
    num_cols = set(meta['num_cols'])

    X_encoded = {}
    for col in feature_names:
        if col in cat_cols and col in feature_encoders:
            le = feature_encoders[col]
            val = str(features.get(col, ""))
            if val not in le.classes_:
                val = le.classes_[0]
            X_encoded[col] = le.transform([val])[0]
        else:
            X_encoded[col] = float(features.get(col, 0))

    X_array = np.array([[X_encoded.get(col, 0) for col in feature_names]])

    expected_features = model.n_features_in_
    actual_features = X_array.shape[1]
    if actual_features != expected_features:
        raise ValueError(
            f"V2 severity model feature mismatch: expected {expected_features} features, "
            f"got {actual_features}. Schema: {feature_names}"
        )

    prediction = model.predict(X_array)[0]
    probabilities = model.predict_proba(X_array)[0]

    severity = y_encoder.inverse_transform([prediction])[0]
    prob_dict = {
        y_encoder.inverse_transform([i])[0]: float(prob)
        for i, prob in enumerate(probabilities)
    }

    severity_weights = {'Low': 0, 'Medium': 33, 'High': 66, 'Critical': 100}
    risk_score = sum(prob_dict[sev] * severity_weights[sev] for sev in prob_dict)
    confidence = max(probabilities)

    if risk_score >= 75:
        risk_level = "Critical"
        risk_color = "#ef4444"
    elif risk_score >= 50:
        risk_level = "High"
        risk_color = "#f97316"
    elif risk_score >= 25:
        risk_level = "Medium"
        risk_color = "#f59e0b"
    else:
        risk_level = "Low"
        risk_color = "#10b981"

    return {
        'severity': severity,
        'probabilities': prob_dict,
        'risk_score': risk_score,
        'risk_level': risk_level,
        'risk_color': risk_color,
        'confidence': float(confidence)
    }

def predict_fatality_risk(weather, road_condition, accident_cause, traffic_density,
                          vehicles_involved, nearby_accidents, hour, day_of_week, is_night,
                          month=None):
    """
    Predict fatality risk using the trained model.
    
    Returns:
        dict: {
            'fatality_risk': bool,
            'probability': float,
            'risk_level': str,
            'risk_color': str
        }
    """
    model = load_fatality_model()
    
    # Fatality model uses ORIGINAL 9-feature schema (not advanced)
    # Load original encoders and meta
    from utils.data_loader import load_encoders, load_feature_meta
    import os
    
    artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")
    original_encoders_path = os.path.join(artifacts_dir, "encoders.pkl")
    original_meta_path = os.path.join(artifacts_dir, "feature_meta.pkl")
    
    import joblib
    encoders = joblib.load(original_encoders_path)
    meta = joblib.load(original_meta_path)
    
    # Build ORIGINAL 9-feature set (no interactions, no bins, no cyclical)
    features = {
        'weather': weather,
        'road_condition': road_condition,
        'accident_cause': accident_cause,
        'traffic_density': traffic_density,
        'vehicles_involved': vehicles_involved,
        'nearby_accidents': nearby_accidents,
        'hour': hour,
        'day_of_week': day_of_week,
        'is_night': is_night
    }
    
    # Encode categorical features
    X_encoded = {}
    for col in meta['categorical_features']:
        le = encoders[col]
        val = str(features.get(col, ""))
        if val not in le.classes_:
            val = le.classes_[0]
        X_encoded[col] = le.transform([val])[0]
    
    # Scale numeric features
    scaler = encoders['__scaler__']
    numeric_values = np.array([[features.get(col, 0) for col in meta['numeric_features']]])
    numeric_scaled = scaler.transform(numeric_values)
    
    for i, col in enumerate(meta['numeric_features']):
        X_encoded[col] = numeric_scaled[0, i]
    
    # Create feature array in correct order
    feature_names = meta['categorical_features'] + meta['numeric_features']
    X_array = np.array([[X_encoded[col] for col in feature_names]])
    
    # Defensive validation
    expected_features = model.n_features_in_
    actual_features = X_array.shape[1]
    if actual_features != expected_features:
        raise ValueError(
            f"Fatality model feature mismatch: expected {expected_features} features, "
            f"got {actual_features}. Schema: {feature_names}"
        )
    
    # Predict
    prediction = model.predict(X_array)[0]
    probability = model.predict_proba(X_array)[0][1]  # Probability of class 1 (fatality)
    
    fatality_risk = bool(prediction == 1)
    
    if probability >= 0.75:
        risk_level = "Critical"
        risk_color = "#ef4444"
    elif probability >= 0.50:
        risk_level = "High"
        risk_color = "#f97316"
    elif probability >= 0.25:
        risk_level = "Medium"
        risk_color = "#f59e0b"
    else:
        risk_level = "Low"
        risk_color = "#10b981"
    
    return {
        'fatality_risk': fatality_risk,
        'probability': float(probability),
        'risk_level': risk_level,
        'risk_color': risk_color
    }

def get_risk_factors(weather, road_condition, accident_cause, hour, is_night):
    """
    Identify and explain main risk factors based on input conditions.
    
    Returns:
        list: List of risk factor descriptions
    """
    factors = []
    
    # Weather risks
    if weather in ["Fog", "Heavy Rain", "Dust Storm"]:
        factors.append(f"⚠️ **{weather}** conditions significantly increase accident severity risk")
    elif weather == "Rain":
        factors.append(f"🌧️ **Rain** increases risk due to reduced visibility and traction")
    
    # Road condition risks
    if road_condition in ["Flooding", "Muddy", "Potholed"]:
        factors.append(f"⚠️ **{road_condition}** road conditions are high-risk factors")
    elif road_condition == "Wet":
        factors.append(f"💧 **Wet** roads increase accident severity potential")
    
    # Cause risks
    if accident_cause in ["Signal Violation", "Weather"]:
        factors.append(f"🚨 **{accident_cause}** as a cause is associated with higher severity")
    elif accident_cause == "Human Error":
        factors.append(f"⚠️ **Human Error** contributes to varied severity outcomes")
    
    # Time risks
    if is_night:
        factors.append(f"🌙 **Night-time** accidents tend to be more severe due to visibility")
    elif 7 <= hour <= 9 or 17 <= hour <= 19:
        factors.append(f"🕐 **Rush hour** conditions may increase accident complexity")
    
    if not factors:
        factors.append("✅ Current conditions suggest moderate risk levels")
    
    return factors
