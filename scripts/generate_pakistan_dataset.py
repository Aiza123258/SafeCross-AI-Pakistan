"""
SafeCross AI - Pakistan Accident Dataset Generator
===================================================
Generates a 5,000-row synthetic dataset using the 45-column schema
from data/pakistan_dataset_schema_template.csv.

Severity is assigned via transparent deterministic risk rules computed
from pre-accident features only. Fatalities/injuries/property_damage
are back-filled from severity as outcome reference columns and are
NOT used as input features.

Label noise: ~0% (deterministic mapping from risk score to severity).
"""

import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(ROOT, "data", "pakistan_accidents_5000.csv")

N_ROWS = 5_000
SEED = 42

PROVINCES = ["Punjab", "Sindh", "KPK", "Balochistan", "Islamabad"]
PROVINCE_WEIGHTS = [0.45, 0.25, 0.13, 0.10, 0.07]

DISTRICTS = {
    "Punjab": ["Lahore", "Faisalabad", "Rawalpindi", "Multan", "Gujranwala", "Sialkot", "Bahawalpur", "Sargodha"],
    "Sindh": ["Karachi", "Hyderabad", "Sukkur", "Larkana", "Nawabshah"],
    "KPK": ["Peshawar", "Abbottabad", "Mardan", "Swat", "Dera Ismail Khan"],
    "Balochistan": ["Quetta", "Gwadar", "Khuzdar", "Turbat"],
    "Islamabad": ["Islamabad"],
}

ROAD_TYPES = ["Highway", "Urban", "Rural", "Residential"]
ROAD_TYPE_WEIGHTS = [0.20, 0.35, 0.30, 0.15]

WEATHERS = ["Clear", "Cloudy", "Rain", "Heavy Rain", "Fog", "Dust Storm", "Haze"]
WEATHER_WEIGHTS = [0.30, 0.20, 0.15, 0.08, 0.10, 0.07, 0.10]

LIGHTINGS = ["Daylight", "Street-lit", "Unlit", "Dawn-Dusk", "Tunnel"]
LIGHTING_WEIGHTS = [0.35, 0.25, 0.20, 0.12, 0.08]

ROAD_CONDITIONS = ["Dry", "Wet", "Potholed", "Construction", "Muddy", "Flooding", "Icy"]
ROAD_COND_WEIGHTS = [0.35, 0.20, 0.15, 0.08, 0.10, 0.05, 0.07]

SURFACE_MATERIALS = ["Asphalt", "Concrete", "Gravel", "Dirt"]
SURFACE_WEIGHTS = [0.55, 0.20, 0.15, 0.10]

CURVATURES = ["Straight", "Gentle", "Sharp", "Hairpin"]
CURVATURE_WEIGHTS = [0.45, 0.30, 0.18, 0.07]

GRADIENTS = ["Flat", "Uphill", "Downhill"]
GRADIENT_WEIGHTS = [0.50, 0.25, 0.25]

MEDIANS = ["Physical", "Painted", "None"]
MEDIAN_WEIGHTS = [0.40, 0.35, 0.25]

VEHICLE_TYPES = ["Motorcycle", "Car", "Truck", "Bus", "Auto-rickshaw", "Bicycle"]
VEHICLE_WEIGHTS = [0.35, 0.30, 0.12, 0.08, 0.10, 0.05]

CAUSES = [
    "Signal Violation", "Speeding", "Wrong Side", "Weather",
    "Human Error", "Mechanical Failure", "Animal Crossing",
    "Overloading", "Drunk Driving", "Mobile Phone"
]
CAUSE_WEIGHTS = [0.15, 0.20, 0.10, 0.08, 0.18, 0.08, 0.05, 0.06, 0.03, 0.07]

COLLISION_TYPES = ["Head-on", "Rear-end", "Side-swipe", "Rollover", "Fixed-object", "Pedestrian", "Multi-vehicle pileup"]
COLLISION_WEIGHTS = [0.18, 0.22, 0.20, 0.10, 0.12, 0.08, 0.10]

IMPACT_POINTS = ["Front", "Side", "Rear", "Roof"]
IMPACT_WEIGHTS = [0.40, 0.30, 0.20, 0.10]

EVASIVE_ACTIONS = ["Braking", "Swerving", "None"]
EVASIVE_WEIGHTS = [0.40, 0.25, 0.35]


def compute_risk_score(row):
    """
    Transparent deterministic risk score from pre-accident features.
    Range: 0 to ~100. Higher = more severe expected outcome.
    """
    score = 0.0

    # 1. Weather (0-10)
    weather_map = {"Clear": 0, "Cloudy": 1, "Haze": 2, "Rain": 4, "Fog": 6, "Heavy Rain": 8, "Dust Storm": 10}
    score += weather_map.get(row["weather"], 0)

    # 2. Road condition (0-10)
    road_map = {"Dry": 0, "Wet": 2, "Construction": 4, "Potholed": 5, "Icy": 5, "Muddy": 7, "Flooding": 10}
    score += road_map.get(row["road_condition"], 0)

    # 3. Speed factor (0-15): based on speed_at_impact
    spd = row["speed_at_impact_kmh"]
    if spd < 30:
        score += 0
    elif spd < 50:
        score += 3
    elif spd < 70:
        score += 6
    elif spd < 90:
        score += 10
    else:
        score += 15

    # 4. Collision type (0-12)
    coll_map = {"Side-swipe": 2, "Rear-end": 4, "Fixed-object": 6, "Pedestrian": 8,
                "Head-on": 10, "Rollover": 11, "Multi-vehicle pileup": 12}
    score += coll_map.get(row["collision_type"], 0)

    # 5. Vehicle risk (0-8): worst vehicle in the incident
    vehicle_risk_map = {"Bicycle": 7, "Motorcycle": 6, "Auto-rickshaw": 3, "Car": 2, "Bus": 4, "Truck": 5}
    vtypes = row["vehicle_types"].split(";")
    max_vrisk = max(vehicle_risk_map.get(v.strip(), 2) for v in vtypes)
    score += max_vrisk

    # 6. Safety equipment (0-6)
    if row["helmet_usage"] == "No":
        score += 3
    elif row["helmet_usage"] == "Partial":
        score += 1
    if row["seatbelt_usage"] == "No":
        score += 3
    elif row["seatbelt_usage"] == "Partial":
        score += 1

    # 7. Visibility (0-5)
    vis = row["visibility_meters"]
    if vis < 100:
        score += 5
    elif vis < 250:
        score += 3
    elif vis < 500:
        score += 1

    # 8. Road type (0-4)
    rtype_map = {"Residential": 1, "Urban": 2, "Rural": 3, "Highway": 4}
    score += rtype_map.get(row["road_type"], 0)

    # 9. Lighting (0-4)
    light_map = {"Daylight": 0, "Tunnel": 1, "Street-lit": 1, "Dawn-Dusk": 2, "Unlit": 4}
    score += light_map.get(row["lighting"], 0)

    # 10. Evasive action (0-3)
    ev_map = {"Braking": 0, "Swerving": 1, "None": 3}
    score += ev_map.get(row["evasive_action"], 0)

    # 11. Overspeeding (0-5)
    overspeed = row["speed_at_impact_kmh"] - row["speed_limit_kmh"]
    if overspeed > 30:
        score += 5
    elif overspeed > 20:
        score += 3
    elif overspeed > 10:
        score += 1

    # 12. Road curvature (0-4)
    curve_map = {"Straight": 0, "Gentle": 1, "Sharp": 3, "Hairpin": 4}
    score += curve_map.get(row["road_curvature"], 0)

    # 13. Overloading (0-3)
    if row["overloading_detected"] == "Yes":
        score += 3

    # 14. Driver age (0-3)
    age = row["driver_age"]
    if age < 20 or age > 65:
        score += 3
    elif age < 25 or age > 55:
        score += 1

    # 15. Distance to hospital (0-3)
    dist = row["distance_to_hospital_km"]
    if dist > 30:
        score += 3
    elif dist > 15:
        score += 2
    elif dist > 5:
        score += 1

    # 16. Number of collisions (0-3)
    n_coll = row["num_collisions"]
    if n_coll >= 3:
        score += 3
    elif n_coll == 2:
        score += 1

    # 17. Wind speed (0-3)
    wind = row["wind_speed_kmh"]
    if wind > 40:
        score += 3
    elif wind > 25:
        score += 2
    elif wind > 15:
        score += 1

    # 18. Cause severity (0-4)
    cause_map = {"Animal Crossing": 1, "Human Error": 1, "Mechanical Failure": 2,
                 "Mobile Phone": 2, "Weather": 2, "Overloading": 3, "Wrong Side": 3,
                 "Signal Violation": 3, "Speeding": 4, "Drunk Driving": 4}
    score += cause_map.get(row["accident_cause"], 0)

    return score


def severity_from_score(score):
    """Deterministic severity from risk score. Thresholds chosen for ~balanced classes."""
    if score < 39:
        return "Low"
    elif score < 45:
        return "Medium"
    elif score < 51:
        return "High"
    else:
        return "Critical"


def outcome_from_severity(severity, rng):
    """Back-fill outcome columns from severity. These are reference only."""
    if severity == "Low":
        fatalities = 0
        serious = 0
        minor = rng.choice([0, 1, 1, 2])
        damage = rng.choice(["Minor", "Minor", "None"])
    elif severity == "Medium":
        fatalities = 0
        serious = rng.choice([0, 0, 1, 1, 2])
        minor = rng.choice([1, 2, 2, 3])
        damage = rng.choice(["Minor", "Moderate", "Moderate"])
    elif severity == "High":
        fatalities = rng.choice([0, 0, 0, 1])
        serious = rng.choice([1, 2, 2, 3])
        minor = rng.choice([2, 3, 4])
        damage = rng.choice(["Moderate", "Severe", "Severe"])
    else:  # Critical
        fatalities = rng.choice([1, 1, 2, 3])
        serious = rng.choice([2, 3, 3, 4])
        minor = rng.choice([1, 2, 3])
        damage = rng.choice(["Severe", "Total", "Total"])

    return int(fatalities), int(serious), int(minor), damage


def generate_dataset(n=N_ROWS, seed=SEED):
    rng = np.random.default_rng(seed)

    records = []
    for i in range(n):
        province = rng.choice(PROVINCES, p=PROVINCE_WEIGHTS)
        district = rng.choice(DISTRICTS[province])
        road_type = rng.choice(ROAD_TYPES, p=ROAD_TYPE_WEIGHTS)

        date = f"2024-{rng.integers(1,13):02d}-{rng.integers(1,29):02d}"
        hour = rng.integers(0, 24)
        minute = rng.integers(0, 60)
        time_str = f"{hour:02d}:{minute:02d}"

        weather = rng.choice(WEATHERS, p=WEATHER_WEIGHTS)
        lighting = rng.choice(LIGHTINGS, p=LIGHTING_WEIGHTS)
        road_condition = rng.choice(ROAD_CONDITIONS, p=ROAD_COND_WEIGHTS)
        surface = rng.choice(SURFACE_MATERIALS, p=SURFACE_WEIGHTS)
        curvature = rng.choice(CURVATURES, p=CURVATURE_WEIGHTS)
        gradient = rng.choice(GRADIENTS, p=GRADIENT_WEIGHTS)
        median = rng.choice(MEDIANS, p=MEDIAN_WEIGHTS)
        shoulder = rng.choice(["Yes", "No"], p=[0.6, 0.4])

        n_lanes = int(rng.choice([1, 2, 2, 3, 4, 4, 6], p=[0.10, 0.25, 0.20, 0.15, 0.15, 0.10, 0.05]))
        speed_limit = int(rng.choice([30, 40, 50, 60, 80, 100, 110, 120],
                                     p=[0.08, 0.12, 0.20, 0.20, 0.15, 0.10, 0.10, 0.05]))

        n_vehicles = int(rng.choice([1, 2, 2, 3, 3, 4, 5], p=[0.10, 0.25, 0.20, 0.18, 0.12, 0.10, 0.05]))
        veh_types_list = [rng.choice(VEHICLE_TYPES, p=VEHICLE_WEIGHTS) for _ in range(n_vehicles)]
        vehicle_types_str = ";".join(veh_types_list)
        vehicle_avg_age = float(rng.uniform(2, 20))
        overloading = rng.choice(["Yes", "No"], p=[0.15, 0.85])

        driver_age = int(np.clip(rng.normal(35, 12), 16, 75))
        helmet = rng.choice(["Yes", "No", "Partial"], p=[0.40, 0.45, 0.15])
        seatbelt = rng.choice(["Yes", "No", "Partial", "Not Applicable"], p=[0.35, 0.30, 0.10, 0.25])
        mobile = rng.choice(["Yes", "No"], p=[0.12, 0.88])
        alcohol = rng.choice(["Yes", "No", "Unknown"], p=[0.03, 0.87, 0.10])

        overspeed_delta = rng.choice([-10, -5, 0, 5, 10, 15, 20, 30, 40],
                                      p=[0.05, 0.10, 0.20, 0.15, 0.15, 0.13, 0.10, 0.07, 0.05])
        speed_at_impact = int(np.clip(speed_limit + overspeed_delta, 15, 160))

        evasive = rng.choice(EVASIVE_ACTIONS, p=EVASIVE_WEIGHTS)
        cause = rng.choice(CAUSES, p=CAUSE_WEIGHTS)
        collision = rng.choice(COLLISION_TYPES, p=COLLISION_WEIGHTS)
        impact = rng.choice(IMPACT_POINTS, p=IMPACT_WEIGHTS)
        n_collisions = int(rng.choice([1, 1, 2, 2, 3], p=[0.35, 0.25, 0.20, 0.12, 0.08]))

        traffic_vol = int(rng.uniform(50, 2000))
        peak = rng.choice(["Peak", "Off-peak"], p=[0.45, 0.55])

        vis_meters = int(np.clip(rng.exponential(400), 20, 1500))
        temp = float(np.clip(rng.normal(30, 8), 5, 50))
        wind = float(np.clip(rng.exponential(12), 0, 80))

        dist_hosp = float(np.clip(rng.exponential(12), 0.5, 80))
        resp_time = float(np.clip(dist_hosp * 1.2 + rng.normal(5, 3), 3, 90))

        lat_base = {"Punjab": 31.0, "Sindh": 25.5, "KPK": 33.5, "Balochistan": 29.0, "Islamabad": 33.7}
        lat = round(lat_base[province] + rng.uniform(-1.5, 1.5), 4)
        lon_base = {"Punjab": 73.5, "Sindh": 68.0, "KPK": 71.5, "Balochistan": 66.5, "Islamabad": 73.0}
        lon = round(lon_base[province] + rng.uniform(-1.5, 1.5), 4)

        row = {
            "incident_id": f"PK-2024-{i+1:05d}",
            "date": date,
            "time": time_str,
            "province": province,
            "district": district,
            "road_type": road_type,
            "latitude": lat,
            "longitude": lon,
            "weather": weather,
            "visibility_meters": vis_meters,
            "temperature_c": round(temp, 1),
            "wind_speed_kmh": round(wind, 1),
            "lighting": lighting,
            "road_condition": road_condition,
            "surface_material": surface,
            "number_of_lanes": n_lanes,
            "speed_limit_kmh": speed_limit,
            "road_curvature": curvature,
            "road_gradient": gradient,
            "median_type": median,
            "shoulder_available": shoulder,
            "num_vehicles": n_vehicles,
            "vehicle_types": vehicle_types_str,
            "vehicle_avg_age_years": round(vehicle_avg_age, 1),
            "overloading_detected": overloading,
            "driver_age": driver_age,
            "helmet_usage": helmet,
            "seatbelt_usage": seatbelt,
            "mobile_phone_suspected": mobile,
            "alcohol_drug_suspected": alcohol,
            "speed_at_impact_kmh": speed_at_impact,
            "evasive_action": evasive,
            "accident_cause": cause,
            "collision_type": collision,
            "impact_point": impact,
            "num_collisions": n_collisions,
            "traffic_volume_per_hour": traffic_vol,
            "peak_off_peak": peak,
            "distance_to_hospital_km": round(dist_hosp, 1),
            "expected_response_min": round(resp_time, 1),
        }

        records.append(row)

    df = pd.DataFrame(records)

    # Compute risk score and assign severity (deterministic)
    scores = df.apply(compute_risk_score, axis=1)
    df["risk_score"] = scores
    df["severity"] = scores.apply(severity_from_score)

    # Back-fill outcome columns from severity (reference only)
    fatalities_list, serious_list, minor_list, damage_list = [], [], [], []
    for _, row in df.iterrows():
        f, s, m, d = outcome_from_severity(row["severity"], rng)
        fatalities_list.append(f)
        serious_list.append(s)
        minor_list.append(m)
        damage_list.append(d)

    df["fatalities"] = fatalities_list
    df["serious_injuries"] = serious_list
    df["minor_injuries"] = minor_list
    df["property_damage_level"] = damage_list

    # Print risk score stats before dropping the column
    print(f"\nRisk score statistics:")
    print(f"  Min:    {df['risk_score'].min():.1f}")
    print(f"  Q25:    {df['risk_score'].quantile(0.25):.1f}")
    print(f"  Median: {df['risk_score'].median():.1f}")
    print(f"  Q75:    {df['risk_score'].quantile(0.75):.1f}")
    print(f"  Max:    {df['risk_score'].max():.1f}")
    print(f"  Q10:    {df['risk_score'].quantile(0.10):.1f}")
    print(f"  Q90:    {df['risk_score'].quantile(0.90):.1f}")

    # Reorder columns to match template schema (drops risk_score)
    template_cols = [
        "incident_id", "date", "time", "province", "district", "road_type",
        "latitude", "longitude", "weather", "visibility_meters", "temperature_c",
        "wind_speed_kmh", "lighting", "road_condition", "surface_material",
        "number_of_lanes", "speed_limit_kmh", "road_curvature", "road_gradient",
        "median_type", "shoulder_available", "num_vehicles", "vehicle_types",
        "vehicle_avg_age_years", "overloading_detected", "driver_age", "helmet_usage",
        "seatbelt_usage", "mobile_phone_suspected", "alcohol_drug_suspected",
        "speed_at_impact_kmh", "evasive_action", "accident_cause", "collision_type",
        "impact_point", "num_collisions", "traffic_volume_per_hour", "peak_off_peak",
        "distance_to_hospital_km", "expected_response_min", "fatalities",
        "serious_injuries", "minor_injuries", "property_damage_level", "severity"
    ]
    df = df[template_cols]

    return df


if __name__ == "__main__":
    print("=" * 60)
    print("SafeCross AI - Pakistan Accident Dataset Generator")
    print("=" * 60)

    df = generate_dataset()

    print(f"\nShape: {df.shape}")
    print(f"\nSeverity distribution:")
    counts = df["severity"].value_counts()
    for label in ["Low", "Medium", "High", "Critical"]:
        n = counts.get(label, 0)
        pct = n / len(df) * 100
        print(f"  {label:<10} {n:>6,}  ({pct:.1f}%)")

    print(f"\nMissing values per column:")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("  None")
    else:
        for col, cnt in missing.items():
            if cnt > 0:
                print(f"  {col}: {cnt}")

    dupes = df.duplicated().sum()
    print(f"\nDuplicate rows: {dupes}")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(df)} rows -> {OUTPUT_PATH}")
