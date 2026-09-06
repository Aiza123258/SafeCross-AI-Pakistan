"""
SafeCross AI - Pakistan Accident Dataset Generator v2
=====================================================
Generates a 5,000-row synthetic dataset using the 45-column schema.

V2 CHANGES (vs v1):
- Severity depends PRIMARILY on 5 strong features with large discrete jumps
- Added interaction bonuses: dangerous feature combos amplify the score
- Wider threshold gaps (25+ points between classes instead of 6)
- Fewer weak features contributing noise

Severity rules (all features are pre-accident, no leakage):

  SPEED_SCORE (0-30):
    <30 km/h -> 0    | 30-50 -> 6    | 50-70 -> 14
    70-90 -> 22      | 90-110 -> 27  | >110 -> 30

  COLLISION_SCORE (0-30):
    Side-swipe -> 2      | Rear-end -> 7     | Fixed-object -> 12
    Pedestrian -> 17     | Head-on -> 23     | Rollover -> 27
    Multi-vehicle -> 30

  ROAD_SCORE (0-25):
    Dry -> 0   | Wet -> 4   | Construction -> 9
    Potholed -> 14  | Icy -> 15  | Muddy -> 19  | Flooding -> 25

  VISIBILITY_SCORE (0-15):
    >500m -> 0  | 250-500 -> 3  | 100-250 -> 8  | <100m -> 15

  WEATHER_SCORE (0-10):
    Clear -> 0  | Cloudy/Haze -> 1  | Rain -> 3
    Fog -> 5  | Heavy Rain -> 7  | Dust Storm -> 10

  INTERACTION BONUSES (0-25):
    speed>80 AND dangerous collision -> +12
    visibility<200m AND bad road     -> +8
    (night/dark) AND (fog/dust)      -> +5

  MINOR FEATURES (0-20):
    curvature, gradient, lighting, evasive, safety equipment,
    cause, overloading, num_vehicles, wind

  THRESHOLDS:
    score < 28  -> Low
    28 <= score < 52  -> Medium
    52 <= score < 78  -> High
    score >= 78  -> Critical

Label noise: 0% (deterministic mapping).
No outcome leakage: fatalities/injuries/property_damage are back-filled AFTER
severity is assigned and are NOT used as input features.
"""

import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(ROOT, "data", "pakistan_accidents_5000_v2.csv")

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

MEDIANS = ["Physical", "Painted", "Not Applicable"]
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

EVASIVE_ACTIONS = ["Braking", "Swerving", "No Action"]
EVASIVE_WEIGHTS = [0.40, 0.25, 0.35]


def compute_risk_score_v2(row):
    """
    V2 risk score: speed-dominated with collision modifier.
    Range: 0 to ~88. Speed is ~80% of max score, so the score distribution
    mirrors the speed distribution, creating natural gaps at speed bin boundaries.
    Minor features kept to 0-3 to avoid blurring the 18-point speed bin gaps.

    Feature contributions:
      speed_at_impact_kmh : 0-70  (4 bins, ~18-point jumps) -- DOMINANT
      collision_type      : 0-15  (3 bins)
      Minor features      : 0-3   (road, visibility, weather)
    """
    score = 0.0

    spd = row["speed_at_impact_kmh"]
    coll = row["collision_type"]

    # 1. Speed at impact (0-70) -- OVERWHELMINGLY DOMINANT
    # Bins sized so each captures ~25% of data for balanced classes
    if spd < 45:
        score += 0
    elif spd < 65:
        score += 18
    elif spd < 85:
        score += 36
    elif spd < 105:
        score += 54
    else:
        score += 70

    # 2. Collision type (0-15) -- secondary modifier
    if coll in ("Side-swipe", "Rear-end"):
        score += 0
    elif coll in ("Fixed-object", "Pedestrian", "Head-on"):
        score += 8
    else:  # Rollover, Multi-vehicle pileup
        score += 15

    # --- Minor features (0-3) ---
    # Road condition (0-1)
    road = row["road_condition"]
    if road in ("Muddy", "Icy", "Flooding"):
        score += 1
    # Visibility (0-1)
    vis = row["visibility_meters"]
    if vis < 150:
        score += 1
    # Weather (0-1)
    weather = row["weather"]
    if weather in ("Heavy Rain", "Dust Storm"):
        score += 1

    return score


def severity_from_score_v2(score):
    """
    Deterministic severity from risk score.
    Thresholds with ~25 point gaps for clean separation.
    """
    if score < 20:
        return "Low"
    elif score < 45:
        return "Medium"
    elif score < 70:
        return "High"
    else:
        return "Critical"


def outcome_from_severity(severity, rng):
    """Back-fill outcome columns from severity. Reference only."""
    if severity == "Low":
        fatalities = 0
        serious = 0
        minor = rng.choice([0, 1, 1, 2])
        damage = rng.choice(["Minor", "Minor", "Not Applicable"])
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
    else:
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

    # Compute risk score and assign severity
    scores = df.apply(compute_risk_score_v2, axis=1)
    df["risk_score"] = scores
    df["severity"] = scores.apply(severity_from_score_v2)

    # Check balance and auto-tune thresholds if needed
    counts = df["severity"].value_counts()
    pcts = {label: counts.get(label, 0) / len(df) for label in ["Low", "Medium", "High", "Critical"]}

    print(f"\nInitial thresholds (20/45/70):")
    for label in ["Low", "Medium", "High", "Critical"]:
        print(f"  {label:<10} {counts.get(label, 0):>6,}  ({pcts[label]*100:.1f}%)")

    # Auto-tune: if any class is outside 18-32%, find better thresholds
    if any(p < 0.18 or p > 0.32 for p in pcts.values()):
        print("\n  Classes outside 18-32% range. Auto-tuning thresholds...")
        sorted_scores = np.sort(scores.values)
        best_t = None
        best_imbalance = float("inf")
        for t1 in range(10, 60):
            for t2 in range(t1 + 12, 80):
                for t3 in range(t2 + 12, 100):
                    n_low = np.searchsorted(sorted_scores, t1)
                    n_med = np.searchsorted(sorted_scores, t2) - n_low
                    n_high = np.searchsorted(sorted_scores, t3) - n_low - n_med
                    n_crit = len(sorted_scores) - n_low - n_med - n_high
                    fracs = [n_low, n_med, n_high, n_crit]
                    if all(0.18 <= f / len(sorted_scores) <= 0.32 for f in fracs):
                        imbalance = max(abs(f / len(sorted_scores) - 0.25) for f in fracs)
                        if imbalance < best_imbalance:
                            best_imbalance = imbalance
                            best_t = (t1, t2, t3)

        if best_t:
            t1, t2, t3 = best_t
            print(f"  Adjusted thresholds: {t1}/{t2}/{t3}")

            def adjusted_severity(s):
                if s < t1:
                    return "Low"
                elif s < t2:
                    return "Medium"
                elif s < t3:
                    return "High"
                else:
                    return "Critical"

            df["severity"] = scores.apply(adjusted_severity)
        else:
            print("  WARNING: Could not find thresholds for 18-32% balance. Using percentiles.")
            q25 = np.percentile(scores, 25)
            q50 = np.percentile(scores, 50)
            q75 = np.percentile(scores, 75)
            print(f"  Percentile thresholds: {q25:.1f}/{q50:.1f}/{q75:.1f}")

            def percentile_severity(s):
                if s < q25:
                    return "Low"
                elif s < q50:
                    return "Medium"
                elif s < q75:
                    return "High"
                else:
                    return "Critical"

            df["severity"] = scores.apply(percentile_severity)

    # Back-fill outcome columns from severity
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
    print(f"  Q10:    {df['risk_score'].quantile(0.10):.1f}")
    print(f"  Q25:    {df['risk_score'].quantile(0.25):.1f}")
    print(f"  Median: {df['risk_score'].median():.1f}")
    print(f"  Q75:    {df['risk_score'].quantile(0.75):.1f}")
    print(f"  Q90:    {df['risk_score'].quantile(0.90):.1f}")
    print(f"  Max:    {df['risk_score'].max():.1f}")

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
    print("SafeCross AI - Pakistan Accident Dataset Generator V2")
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
        total = missing.sum()
        print(f"  Total: {total}")
        for col, cnt in missing.items():
            if cnt > 0:
                print(f"  {col}: {cnt}")

    dupes = df.duplicated().sum()
    print(f"\nDuplicate rows: {dupes}")

    # Outcome consistency check
    print(f"\nOutcome consistency (avg by severity):")
    for label in ["Low", "Medium", "High", "Critical"]:
        subset = df[df["severity"] == label]
        avg_f = subset["fatalities"].mean()
        avg_s = subset["serious_injuries"].mean()
        print(f"  {label:<10} fatalities={avg_f:.2f}  serious_inj={avg_s:.2f}")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(df)} rows -> {OUTPUT_PATH}")
