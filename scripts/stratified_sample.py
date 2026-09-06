"""
SafeCross AI - Stratified Dataset Sampling & Model Comparison
==============================================================
Creates a stratified sample of the training dataset and compares
model performance with different sample sizes.

Usage:
    py scripts/stratified_sample.py

This script:
1. Loads the full 1M dataset
2. Creates stratified samples (100k, 150k, 200k)
3. Trains models on each sample
4. Compares metrics
5. Saves the best-performing smaller model

HONESTY: This maintains the leakage-free policy - no post-accident
outcomes used as features.
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
import warnings
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, f1_score, classification_report
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
ARTIFACTS_DIR = os.path.join(ROOT, "artifacts")

DATASET_PATH = os.path.join(DATA_DIR, "india_traffic_accidents.csv")

CATEGORICAL_FEATURES = [
    "weather",
    "road_condition",
    "accident_cause",
    "traffic_density",
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


def engineer_time_features(df):
    df = df.copy()
    df["hour"] = pd.to_datetime(df["time"], format="%H:%M", errors="coerce").dt.hour
    df["day_of_week"] = pd.to_datetime(df["date"], errors="coerce").dt.dayofweek
    df["is_night"] = ((df["hour"] >= 20) | (df["hour"] < 6)).astype(int)
    return df


def create_stratified_sample(df, target_col, sample_size, random_state=42):
    """Create a stratified sample maintaining class distribution."""
    sampled_frames = []
    for _, group in df.groupby(target_col):
        n_samples = int(len(group) / len(df) * sample_size)
        sampled_frames.append(group.sample(n=n_samples, random_state=random_state))
    return pd.concat(sampled_frames).reset_index(drop=True)


def prepare_data(df, sample_size=None, random_state=42):
    """Prepare data for training with optional sampling."""
    df = engineer_time_features(df)
    df = df.dropna(subset=["hour", "day_of_week"])

    if sample_size and sample_size < len(df):
        df = create_stratified_sample(df, TARGET, sample_size, random_state)
        print(f"  Stratified sample: {len(df)} rows")

    encoders = {}
    X = df[ALL_FEATURES].copy()

    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        X[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    target_encoder = LabelEncoder()
    target_encoder.classes_ = np.array(SEVERITY_ORDER)
    y = pd.Series(
        target_encoder.transform(df[TARGET].astype(str)),
        name=TARGET,
        index=df.index,
    )

    scaler = StandardScaler()
    X[NUMERIC_FEATURES] = scaler.fit_transform(X[NUMERIC_FEATURES])
    encoders["__scaler__"] = scaler

    return X, y, encoders, target_encoder


def train_and_evaluate(X, y, sample_label):
    """Train XGBoost model and return metrics."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='multi:softprob',
        num_class=4,
        eval_metric='mlogloss',
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    f1_weighted = f1_score(y_test, y_pred, average='weighted')

    print(f"\n  {sample_label} Results:")
    print(f"    Accuracy: {accuracy:.4f}")
    print(f"    F1-macro: {f1_macro:.4f}")
    print(f"    F1-weighted: {f1_weighted:.4f}")

    return {
        "model": model,
        "accuracy": accuracy,
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted,
        "sample_size": len(X),
    }


def main():
    print("=" * 70)
    print("SafeCross AI - Stratified Dataset Sampling & Comparison")
    print("=" * 70)

    if not os.path.exists(DATASET_PATH):
        print(f"\nERROR: Dataset not found at {DATASET_PATH}")
        print("Please ensure the data file exists before running this script.")
        return

    print(f"\nLoading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    print(f"Full dataset: {len(df):,} rows")

    print(f"\nTarget distribution (severity):")
    counts = df[TARGET].value_counts()
    for label in SEVERITY_ORDER:
        n = counts.get(label, 0)
        pct = n / len(df) * 100
        print(f"  {label:<10} {n:>8,}  ({pct:.1f}%)")

    sample_sizes = [100_000, 150_000, 200_000]
    results = {}

    for size in sample_sizes:
        print(f"\n{'='*70}")
        print(f"Training model on {size:,} rows (stratified sample)...")
        print(f"{'='*70}")

        X, y, encoders, target_encoder = prepare_data(df, sample_size=size)
        result = train_and_evaluate(X, y, f"{size//1000}k sample")
        result["encoders"] = encoders
        result["target_encoder"] = target_encoder
        results[size] = result

    print(f"\n{'='*70}")
    print("COMPARISON SUMMARY")
    print(f"{'='*70}")
    print(f"{'Sample Size':<15} {'Accuracy':<12} {'F1-macro':<12} {'F1-weighted':<12}")
    print("-" * 70)
    for size in sample_sizes:
        r = results[size]
        print(f"{size//1000}k{'':<12} {r['accuracy']:<12.4f} {r['f1_macro']:<12.4f} {r['f1_weighted']:<12.4f}")

    best_size = max(results.keys(), key=lambda k: results[k]['f1_macro'])
    best_result = results[best_size]

    print(f"\n{'='*70}")
    print(f"BEST MODEL: {best_size//1000}k sample")
    print(f"  Accuracy: {best_result['accuracy']:.4f}")
    print(f"  F1-macro: {best_result['f1_macro']:.4f}")
    print(f"  F1-weighted: {best_result['f1_weighted']:.4f}")
    print(f"{'='*70}")

    save_path = os.path.join(ARTIFACTS_DIR, f"severity_model_{best_size//1000}k.pkl")
    joblib.dump(best_result["model"], save_path)
    print(f"\nSaved best model to: {save_path}")

    encoders_path = os.path.join(ARTIFACTS_DIR, f"encoders_{best_size//1000}k.pkl")
    joblib.dump(best_result["encoders"], encoders_path)
    print(f"Saved encoders to: {encoders_path}")

    meta = {
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "all_features": ALL_FEATURES,
        "target": TARGET,
        "severity_order": SEVERITY_ORDER,
        "sample_size": best_size,
    }
    meta_path = os.path.join(ARTIFACTS_DIR, f"feature_meta_{best_size//1000}k.pkl")
    joblib.dump(meta, meta_path)
    print(f"Saved feature meta to: {meta_path}")

    print(f"\n[done] Stratified sampling complete.")
    print(f"Note: Existing artifacts (severity_model_honest.pkl) remain unchanged.")
    print(f"To use the new model, rename it to severity_model_honest.pkl")


if __name__ == "__main__":
    main()
