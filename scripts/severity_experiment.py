"""
SafeCross AI - Severity Model Optimization Experiment
======================================================
Investigates whether a genuinely leakage-free severity model can reach
90%+ accuracy, and finds the best (dataset size, model) combination.

LEAKAGE AUDIT (see report for full detail):
  - `lane_utilization` is EXCLUDED. It is a synthetic-generation artifact:
    "Overtaking" maps 100% to High/Critical, "Single Lane" maps 100% to
    Low/Medium. This is not a real causal relationship and the app never
    collects this input (predictor.py hardcodes a constant placeholder),
    so a model trained on it cannot honestly use that signal at inference.
  - `latitude`/`longitude` are EXCLUDED - not collected by the UI, and
    fixed to (0,0) at inference in the previous "honest" model, making
    them uninformative constants anyway.
  - `injuries`/`fatalities` are EXCLUDED - post-accident outcomes.

FEATURE SET (matches what the Severity Predictor UI actually collects):
  Categorical : weather, road_condition, accident_cause, traffic_density
  Numeric     : vehicles_involved, nearby_accidents, hour, day_of_week, is_night
  Engineered  : risk_combo = weather + road_condition + accident_cause
                (a legitimate combination of already-causal pre-accident
                features; not derived from the target)

Usage:
    py scripts/severity_experiment.py
"""

import os
import sys
import time
import json
import warnings
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
ARTIFACTS_DIR = os.path.join(ROOT, "artifacts")
DATASET_PATH = os.path.join(DATA_DIR, "india_traffic_accidents.csv")
RESULTS_PATH = os.path.join(ARTIFACTS_DIR, "severity_experiment_results.csv")

CATEGORICAL_FEATURES = ["weather", "road_condition", "accident_cause", "traffic_density"]
NUMERIC_FEATURES = ["vehicles_involved", "nearby_accidents", "hour", "day_of_week", "is_night"]
SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]
RANDOM_STATE = 42

SAMPLE_SIZES = [50_000, 100_000, 150_000, 200_000, 250_000, 300_000]


def load_full_dataset() -> pd.DataFrame:
    print(f"Loading {DATASET_PATH} ...")
    df = pd.read_csv(DATASET_PATH)
    df["hour"] = pd.to_datetime(df["time"], format="%H:%M", errors="coerce").dt.hour
    df["day_of_week"] = pd.to_datetime(df["date"], errors="coerce").dt.dayofweek
    df["is_night"] = ((df["hour"] >= 20) | (df["hour"] < 6)).astype(int)
    df = df.dropna(subset=["hour", "day_of_week"]).reset_index(drop=True)
    print(f"Full clean shape: {df.shape}")
    return df


def stratified_sample(df: pd.DataFrame, size: int, random_state: int = RANDOM_STATE) -> pd.DataFrame:
    """Stratified sample preserving severity class proportions exactly."""
    if size >= len(df):
        return df.copy()
    frames = []
    for _, group in df.groupby("severity"):
        n = max(1, round(len(group) / len(df) * size))
        frames.append(group.sample(n=n, random_state=random_state))
    return pd.concat(frames).sample(frac=1.0, random_state=random_state).reset_index(drop=True)


def build_features(df: pd.DataFrame, use_interaction: bool) -> tuple[pd.DataFrame, list[str], list[str]]:
    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES].copy()
    cat_cols = list(CATEGORICAL_FEATURES)
    if use_interaction:
        X["risk_combo"] = (
            df["weather"].astype(str) + "|" + df["road_condition"].astype(str) + "|" + df["accident_cause"].astype(str)
        )
        cat_cols = cat_cols + ["risk_combo"]
    return X, cat_cols, list(NUMERIC_FEATURES)


def encode(X: pd.DataFrame, cat_cols: list[str]) -> tuple[np.ndarray, dict, list[str]]:
    X_enc = X.copy()
    encoders = {}
    for col in cat_cols:
        le = LabelEncoder()
        X_enc[col] = le.fit_transform(X_enc[col].astype(str))
        encoders[col] = le
    feature_names = list(X_enc.columns)
    return X_enc.values.astype(float), encoders, feature_names


MODEL_FACTORY = {
    "XGBoost": lambda: XGBClassifier(
        n_estimators=250, max_depth=6, learning_rate=0.08,
        subsample=0.85, colsample_bytree=0.85,
        reg_lambda=1.0, eval_metric="mlogloss",
        random_state=RANDOM_STATE, n_jobs=-1, tree_method="hist",
    ),
    "LightGBM": lambda: LGBMClassifier(
        n_estimators=300, max_depth=-1, num_leaves=63, learning_rate=0.08,
        subsample=0.85, colsample_bytree=0.85,
        random_state=RANDOM_STATE, n_jobs=-1, verbosity=-1,
    ),
    "HistGradientBoosting": lambda: HistGradientBoostingClassifier(
        max_iter=300, max_depth=8, learning_rate=0.08,
        random_state=RANDOM_STATE,
    ),
    "RandomForest": lambda: RandomForestClassifier(
        n_estimators=300, max_depth=14, min_samples_leaf=20,
        random_state=RANDOM_STATE, n_jobs=-1,
    ),
}


def model_size_kb(model) -> float:
    import io
    buf = io.BytesIO()
    joblib.dump(model, buf)
    return len(buf.getvalue()) / 1024.0


def run_experiment(df_full: pd.DataFrame, size: int, model_name: str, use_interaction: bool) -> dict:
    df_s = stratified_sample(df_full, size)
    X_raw, cat_cols, num_cols = build_features(df_s, use_interaction)

    target_encoder = LabelEncoder()
    target_encoder.classes_ = np.array(SEVERITY_ORDER)
    y = target_encoder.transform(df_s["severity"].astype(str))

    X_enc, encoders, feature_names = encode(X_raw, cat_cols)

    # 70 / 15 / 15 stratified split
    X_train, X_temp, y_train, y_temp = train_test_split(
        X_enc, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp
    )

    model = MODEL_FACTORY[model_name]()

    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1_w = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    f1_m = f1_score(y_test, y_pred, average="macro", zero_division=0)
    try:
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted")
    except Exception:
        auc = float("nan")

    size_kb = model_size_kb(model)

    result = {
        "dataset_size": len(df_s),
        "model": model_name,
        "interaction_feature": use_interaction,
        "accuracy": round(acc, 4),
        "f1_weighted": round(f1_w, 4),
        "f1_macro": round(f1_m, 4),
        "roc_auc": round(auc, 4) if not np.isnan(auc) else None,
        "train_time_sec": round(train_time, 2),
        "model_size_kb": round(size_kb, 1),
        "train_n": len(X_train), "val_n": len(X_val), "test_n": len(X_test),
    }
    print(f"  [{model_name:<22}] n={len(df_s):>7,} interaction={use_interaction!s:<5} "
          f"acc={acc:.4f} f1_w={f1_w:.4f} f1_m={f1_m:.4f} auc={auc:.4f} "
          f"time={train_time:.1f}s size={size_kb:.0f}KB")
    return result


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("SafeCross AI - Severity Model Optimization Experiment")
    print("=" * 80)

    df_full = load_full_dataset()

    print("\nSeverity distribution (full dataset):")
    print(df_full["severity"].value_counts(normalize=True).round(4))

    results = []
    for size in SAMPLE_SIZES:
        print(f"\n--- Dataset size: {size:,} ---")
        for model_name in MODEL_FACTORY:
            for use_interaction in [False, True]:
                r = run_experiment(df_full, size, model_name, use_interaction)
                results.append(r)

    results_df = pd.DataFrame(results)
    results_df.to_csv(RESULTS_PATH, index=False)
    print(f"\n[done] Saved {len(results_df)} experiment rows -> {RESULTS_PATH}")

    print("\n" + "=" * 80)
    print("TOP 10 BY ACCURACY")
    print("=" * 80)
    print(results_df.sort_values("accuracy", ascending=False).head(10).to_string(index=False))

    print("\n" + "=" * 80)
    print("TOP 10 BY MACRO F1")
    print("=" * 80)
    print(results_df.sort_values("f1_macro", ascending=False).head(10).to_string(index=False))


if __name__ == "__main__":
    main()
