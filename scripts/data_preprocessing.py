"""
SafeCross AI - Data Preprocessing Pipeline
==========================================
Prepares two datasets for downstream use:

  Dataset A (ML training)  : data/india_traffic_accidents.csv
    - General accident-pattern dataset used ONLY to train the AI severity
      predictor. It is NOT Pakistani data and is never presented as such.
    - Outputs: processed feature matrix + target, fitted encoders/scaler.

  Dataset B (Pakistan stats): data/traffic-accidents-annual-.csv
    - Official Pakistan provincial accident statistics (2008-09 to 2018-19).
    - Outputs: clean, typed DataFrame saved to artifacts/.

Original CSV files are read-only and are never modified.
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ── paths ──────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
ARTIFACTS_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

DATASET_A_PATH = os.path.join(DATA_DIR, "india_traffic_accidents.csv")
DATASET_B_PATH = os.path.join(DATA_DIR, "traffic-accidents-annual-.csv")


# ── Dataset B: Pakistan provincial statistics ───────────────────────────────

def preprocess_pakistan_stats() -> pd.DataFrame:
    """
    Clean and type the Pakistan annual accident statistics dataset.
    The raw CSV has a malformed header (footnote in row 0, real header in row 1).
    Returns a clean DataFrame and saves it as artifacts/pakistan_stats.csv.

    If the raw data file is not available (e.g. on Streamlit Cloud), returns
    the pre-computed artifact directly or an empty DataFrame.
    """
    if not os.path.exists(DATASET_B_PATH):
        precomputed = os.path.join(ARTIFACTS_DIR, "pakistan_stats.csv")
        if os.path.exists(precomputed):
            print(f"[pakistan_stats] Raw data not found. Using pre-computed artifact: {precomputed}")
            return pd.read_csv(precomputed)
        print(f"[pakistan_stats] WARNING: Neither raw data ({DATASET_B_PATH}) nor pre-computed artifact found.")
        return pd.DataFrame()

    raw = pd.read_csv(DATASET_B_PATH)

    # Row 0 holds the real column names; rows 1+ are data
    real_columns = raw.iloc[0].tolist()
    df = raw.iloc[1:].copy()
    df.columns = real_columns
    df = df.reset_index(drop=True)

    # Rename columns for usability
    df = df.rename(columns={
        real_columns[0]: "province",
        real_columns[1]: "fiscal_year",
        real_columns[2]: "total_accidents",
        real_columns[3]: "fatal_accidents",
        real_columns[4]: "non_fatal_accidents",
        real_columns[5]: "killed",
        real_columns[6]: "injured",
        real_columns[7]: "vehicles_involved",
    })

    # Strip whitespace from fiscal_year and remove footnote markers (* chars)
    df["fiscal_year"] = df["fiscal_year"].str.strip().str.replace(r"\s*\*\s*", "", regex=True)
    df["province"] = df["province"].str.strip()

    # Cast numeric columns
    numeric_cols = ["total_accidents", "fatal_accidents", "non_fatal_accidents",
                    "killed", "injured", "vehicles_involved"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derived ratios (useful for dashboard)
    df["fatality_rate"] = (df["killed"] / df["total_accidents"]).round(4)
    df["injury_rate"] = (df["injured"] / df["total_accidents"]).round(4)
    df["fatal_accident_pct"] = (df["fatal_accidents"] / df["total_accidents"] * 100).round(2)

    out_path = os.path.join(ARTIFACTS_DIR, "pakistan_stats.csv")
    df.to_csv(out_path, index=False)
    print(f"[pakistan_stats] Saved {len(df)} rows -> {out_path}")
    return df


# ── Dataset A: accident pattern data for ML training ───────────────────────

# Features selected after leakage audit:
#   EXCLUDED (post-accident outcomes / consequences of severity):
#     - injuries      → consequence, not cause
#     - fatalities    → consequence, not cause
#     - id            → meaningless identifier
#     - date/time     → replaced by engineered hour/day_of_week/is_night
#     - latitude/longitude → too specific; not available at prediction time
#     - nearby_accidents  → post-incident aggregation, mild leakage risk;
#                           kept because it reflects local road hazard density
#                           (a pre-existing condition), not the outcome itself.
#
#   INCLUDED causal/contextual features:
#     weather, road_condition, accident_cause, traffic_density,
#     lane_utilization, vehicles_involved, nearby_accidents,
#     hour, day_of_week, is_night

CATEGORICAL_FEATURES = [
    "weather",
    "road_condition",
    "accident_cause",
    "traffic_density",
    "lane_utilization",
]
NUMERIC_FEATURES = [
    "vehicles_involved",
    "nearby_accidents",
    "hour",
    "day_of_week",
    "is_night",
]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "severity"
SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]


def _engineer_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract hour, day_of_week, and is_night from date/time columns."""
    df = df.copy()
    df["hour"] = pd.to_datetime(df["time"], format="%H:%M", errors="coerce").dt.hour
    df["day_of_week"] = pd.to_datetime(df["date"], errors="coerce").dt.dayofweek  # 0=Mon
    df["is_night"] = ((df["hour"] >= 20) | (df["hour"] < 6)).astype(int)
    return df


def preprocess_accident_data(
    sample_size: int | None = None,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.Series, dict, LabelEncoder]:
    """
    Load, clean, and encode the accident dataset for ML training.

    Parameters
    ----------
    sample_size : int | None
        If set, randomly sample this many rows (useful for fast iteration).
        Pass None to use the full 1M-row dataset.
    random_state : int
        Seed for reproducible sampling and encoding.

    Returns
    -------
    X : pd.DataFrame          Encoded feature matrix (all numeric)
    y : pd.Series             Integer-encoded severity labels (0–3)
    encoders : dict           Fitted LabelEncoders keyed by column name
    target_encoder : LabelEncoder  Maps severity string ↔ integer
    """
    print(f"[accident_data] Loading {DATASET_A_PATH} ...")
    if not os.path.exists(DATASET_A_PATH):
        print(f"[accident_data] WARNING: Dataset not found at {DATASET_A_PATH}. Returning empty data.")
        empty_df = pd.DataFrame(columns=ALL_FEATURES + [TARGET])
        empty_y = pd.Series(dtype=str, name=TARGET)
        return empty_df, empty_y, {}, LabelEncoder()

    df = pd.read_csv(DATASET_A_PATH)
    print(f"[accident_data] Raw shape: {df.shape}")

    # --- time features ---
    df = _engineer_time_features(df)

    # --- drop rows where time parsing failed (should be zero) ---
    df = df.dropna(subset=["hour", "day_of_week"])

    # --- optional sampling ---
    if sample_size is not None and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=random_state)
        print(f"[accident_data] Sampled {sample_size} rows")

    # --- target distribution ---
    print("\n[accident_data] Target distribution (severity):")
    counts = df[TARGET].value_counts()
    for label in SEVERITY_ORDER:
        n = counts.get(label, 0)
        pct = n / len(df) * 100
        print(f"  {label:<10} {n:>8,}  ({pct:.1f}%)")

    # --- encode categorical features ---
    encoders: dict[str, LabelEncoder] = {}
    X = df[ALL_FEATURES].copy()

    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        X[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    # --- encode target ---
    target_encoder = LabelEncoder()
    target_encoder.classes_ = np.array(SEVERITY_ORDER)
    y = pd.Series(
        target_encoder.transform(df[TARGET].astype(str)),
        name=TARGET,
        index=df.index,
    )

    # --- scale numeric features ---
    scaler = StandardScaler()
    X[NUMERIC_FEATURES] = scaler.fit_transform(X[NUMERIC_FEATURES])
    encoders["__scaler__"] = scaler

    print(f"\n[accident_data] Final feature matrix shape: {X.shape}")
    print(f"[accident_data] Features: {ALL_FEATURES}")

    return X, y, encoders, target_encoder


def save_preprocessors(encoders: dict, target_encoder: LabelEncoder) -> None:
    """Persist all preprocessing objects so the Streamlit app uses identical transforms."""
    joblib.dump(encoders, os.path.join(ARTIFACTS_DIR, "encoders.pkl"))
    joblib.dump(target_encoder, os.path.join(ARTIFACTS_DIR, "target_encoder.pkl"))
    # Also save the feature name lists so the app can reconstruct inputs correctly
    meta = {
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "all_features": ALL_FEATURES,
        "target": TARGET,
        "severity_order": SEVERITY_ORDER,
    }
    joblib.dump(meta, os.path.join(ARTIFACTS_DIR, "feature_meta.pkl"))
    print(f"[preprocessors] Saved encoders, target_encoder, feature_meta -> {ARTIFACTS_DIR}/")


# ── main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("SafeCross AI — Data Preprocessing")
    print("=" * 60)

    print("\n--- Pakistan Statistics (Dataset B) ---")
    pak_df = preprocess_pakistan_stats()
    print(pak_df.head(3).to_string())

    print("\n--- Accident Pattern Data (Dataset A, sample=200k for speed) ---")
    X, y, encoders, target_encoder = preprocess_accident_data(sample_size=200_000)

    print("\n--- Saving preprocessors ---")
    save_preprocessors(encoders, target_encoder)

    print("\n[done] Preprocessing complete. Artifacts saved to ./artifacts/")
