"""
SafeCross AI - Model Training Pipeline
=======================================
Trains two models using the preprocessed accident dataset:

  Model 1 - Severity Classifier
    Target  : severity (Low / Medium / High / Critical)
    Algorithm: XGBoost (multi-class classification)
    Output  : artifacts/severity_model.pkl

  Model 2 - Fatality Risk Classifier
    Target  : fatality_risk  (0 = no fatality, 1 = one or more fatalities)
    Note    : fatalities column used ONLY as the target label here, not as
              an input feature - there is no target leakage.
    Algorithm: XGBoost (binary classification)
    Output  : artifacts/fatality_model.pkl

Evaluation saved to: artifacts/evaluation_report.txt
Confusion matrix plots saved to: artifacts/
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")  # headless - no display required
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, ConfusionMatrixDisplay,
    roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

# -- paths ------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
ARTIFACTS_DIR = os.path.join(ROOT, "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

DATASET_A_PATH = os.path.join(DATA_DIR, "india_traffic_accidents.csv")
REPORT_PATH = os.path.join(ARTIFACTS_DIR, "evaluation_report.txt")

# Training sample size - 300k rows balances training time vs. generalisation.
# Set to None in data_preprocessing.py to use full 1M (takes ~10 min on CPU).
SAMPLE_SIZE = 300_000
RANDOM_STATE = 42
TEST_SIZE = 0.20

SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]

# LEAKAGE AUDIT (synthetic dataset):
#   lane_utilization  DROPPED - Overtaking maps 100% to High/Critical,
#                               Single Lane maps 100% to Low/Medium.
#                               This is a label-encoding artifact of synthetic
#                               generation, not a real causal relationship.
#   weather/road_condition/accident_cause - kept; domain-valid causal features
#                               even though the synthetic generator used them
#                               to influence severity probabilities.
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


# -- helpers ----------------------------------------------------------------

def _log(msg: str, file=None) -> None:
    print(msg)
    if file:
        print(msg, file=file)


def _save_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: list[str],
    title: str,
    filename: str,
) -> None:
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(7, 6))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(ax=ax, colorbar=True, cmap="Blues")
    ax.set_title(title)
    plt.tight_layout()
    path = os.path.join(ARTIFACTS_DIR, filename)
    plt.savefig(path, dpi=120)
    plt.close(fig)
    print(f"  Confusion matrix saved -> {path}")


# -- data loading ------------------------------------------------------------

def load_training_data() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Load the accident CSV, engineer features, and return:
      X  - feature matrix (pre-encoding; encoding handled per-model)
      y_severity - raw severity labels
      y_fatality - binary fatality risk (0/1)
    """
    print(f"Loading {DATASET_A_PATH} ...")
    df = pd.read_csv(DATASET_A_PATH)
    print(f"Raw shape: {df.shape}")

    if SAMPLE_SIZE and SAMPLE_SIZE < len(df):
        df = df.sample(n=SAMPLE_SIZE, random_state=RANDOM_STATE).reset_index(drop=True)
        print(f"Sampled: {len(df):,} rows")

    # Time engineering
    df["hour"] = pd.to_datetime(df["time"], format="%H:%M", errors="coerce").dt.hour
    df["day_of_week"] = pd.to_datetime(df["date"], errors="coerce").dt.dayofweek
    df["is_night"] = ((df["hour"] >= 20) | (df["hour"] < 6)).astype(int)
    df = df.dropna(subset=["hour", "day_of_week"])

    # Fatality risk label (derived from fatalities column; NOT an input feature)
    y_fatality = (df["fatalities"] > 0).astype(int).rename("fatality_risk")

    X = df[ALL_FEATURES].copy()
    y_severity = df["severity"].copy()

    return X, y_severity, y_fatality


# -- encoding ----------------------------------------------------------------

def encode_features(X: pd.DataFrame) -> tuple[np.ndarray, dict]:
    """Label-encode categorical columns. Returns encoded array and encoder dict."""
    from sklearn.preprocessing import StandardScaler

    X_enc = X.copy()
    encoders: dict = {}

    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        X_enc[col] = le.fit_transform(X_enc[col].astype(str))
        encoders[col] = le

    scaler = StandardScaler()
    X_enc[NUMERIC_FEATURES] = scaler.fit_transform(X_enc[NUMERIC_FEATURES])
    encoders["__scaler__"] = scaler

    return X_enc.values, encoders


def encode_target(y: pd.Series, classes: list[str]) -> tuple[np.ndarray, LabelEncoder]:
    le = LabelEncoder()
    le.classes_ = np.array(classes)
    return le.transform(y.astype(str)), le


# -- model 1: severity classifier --------------------------------------------

def train_severity_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label_names: list[str],
    report_file,
) -> XGBClassifier:

    _log("\n" + "=" * 60, report_file)
    _log("MODEL 1: Severity Classifier (XGBoost multi-class)", report_file)
    _log("=" * 60, report_file)
    _log(f"Features: {ALL_FEATURES}", report_file)
    _log(f"Target classes: {label_names}", report_file)
    _log(f"Train size: {len(X_train):,}  |  Test size: {len(X_test):,}", report_file)

    # Class distribution
    unique, counts = np.unique(y_train, return_counts=True)
    _log("\nTraining target distribution:", report_file)
    for u, c in zip(unique, counts):
        _log(f"  {label_names[u]:<10} {c:>8,}  ({c/len(y_train)*100:.1f}%)", report_file)

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        tree_method="hist",  # fast histogram method
    )

    _log("\nTraining ...", report_file)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    try:
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted")
        auc_str = f"{auc:.4f}"
    except Exception:
        auc_str = "N/A"

    _log(f"\nTest Metrics:", report_file)
    _log(f"  Accuracy          : {acc:.4f}", report_file)
    _log(f"  Precision (wtd)   : {prec:.4f}", report_file)
    _log(f"  Recall (wtd)      : {rec:.4f}", report_file)
    _log(f"  F1-score (wtd)    : {f1:.4f}", report_file)
    _log(f"  ROC-AUC (OvR wtd) : {auc_str}", report_file)

    _log("\nClassification Report:", report_file)
    cr = classification_report(y_test, y_pred, target_names=label_names, zero_division=0)
    _log(cr, report_file)

    # Feature importance
    importances = model.feature_importances_
    feat_imp = sorted(zip(ALL_FEATURES, importances), key=lambda x: x[1], reverse=True)
    _log("Top-10 Feature Importances:", report_file)
    for fname, fimp in feat_imp[:10]:
        _log(f"  {fname:<25} {fimp:.4f}", report_file)

    # Confusion matrix plot
    _save_confusion_matrix(
        y_test, y_pred, label_names,
        "Severity Classifier - Confusion Matrix",
        "confusion_matrix_severity.png",
    )

    return model


# -- model 2: fatality risk classifier ---------------------------------------

def train_fatality_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    report_file,
) -> XGBClassifier:

    _log("\n" + "=" * 60, report_file)
    _log("MODEL 2: Fatality Risk Classifier (XGBoost binary)", report_file)
    _log("=" * 60, report_file)
    _log("Target: fatality_risk  (0 = no fatalities, 1 = one or more fatalities)", report_file)
    _log(f"Features: {ALL_FEATURES}", report_file)
    _log(f"Train size: {len(X_train):,}  |  Test size: {len(X_test):,}", report_file)

    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    _log(f"\nClass balance - 0: {neg:,} ({neg/len(y_train)*100:.1f}%)  "
         f"1: {pos:,} ({pos/len(y_train)*100:.1f}%)", report_file)

    # Handle imbalance with scale_pos_weight
    scale_pos = neg / pos if pos > 0 else 1.0

    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        tree_method="hist",
    )

    _log("\nTraining ...", report_file)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_proba)

    _log(f"\nTest Metrics:", report_file)
    _log(f"  Accuracy          : {acc:.4f}", report_file)
    _log(f"  Precision         : {prec:.4f}", report_file)
    _log(f"  Recall            : {rec:.4f}", report_file)
    _log(f"  F1-score          : {f1:.4f}", report_file)
    _log(f"  ROC-AUC           : {auc:.4f}", report_file)

    _log("\nClassification Report:", report_file)
    cr = classification_report(y_test, y_pred,
                               target_names=["No Fatality", "Fatality Risk"],
                               zero_division=0)
    _log(cr, report_file)

    # Feature importance
    importances = model.feature_importances_
    feat_imp = sorted(zip(ALL_FEATURES, importances), key=lambda x: x[1], reverse=True)
    _log("Top-10 Feature Importances:", report_file)
    for fname, fimp in feat_imp[:10]:
        _log(f"  {fname:<25} {fimp:.4f}", report_file)

    _save_confusion_matrix(
        y_test, y_pred, ["No Fatality", "Fatality Risk"],
        "Fatality Risk Classifier - Confusion Matrix",
        "confusion_matrix_fatality.png",
    )

    return model


# -- main --------------------------------------------------------------------

def main() -> None:
    # Ensure UTF-8 output on Windows terminals
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 60)
    print("SafeCross AI - Model Training Pipeline")
    print("=" * 60)

    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        _log("SafeCross AI - Model Evaluation Report", report_file)
        _log("=" * 60, report_file)
        _log(f"Sample size : {SAMPLE_SIZE:,}", report_file)
        _log(f"Test split  : {TEST_SIZE*100:.0f}%", report_file)
        _log(f"Random seed : {RANDOM_STATE}", report_file)

        # 0. Pakistan stats (Dataset B) - clean and save
        print("\n--- Pakistan Statistics (Dataset B) ---")
        from data_preprocessing import preprocess_pakistan_stats
        preprocess_pakistan_stats()

        # 1. Load data
        X_raw, y_severity, y_fatality = load_training_data()

        # 2. Encode features (shared encoders for both models)
        print("\nEncoding features...")
        X_enc, encoders = encode_features(X_raw)
        y_sev_enc, target_encoder = encode_target(y_severity, SEVERITY_ORDER)
        y_fat = y_fatality.values

        # 3. Train/test split (stratified on severity to preserve class balance)
        X_tr, X_te, ys_tr, ys_te, yf_tr, yf_te = train_test_split(
            X_enc, y_sev_enc, y_fat,
            test_size=TEST_SIZE,
            random_state=RANDOM_STATE,
            stratify=y_sev_enc,
        )

        # 4. Train severity model
        sev_model = train_severity_model(
            X_tr, ys_tr, X_te, ys_te, SEVERITY_ORDER, report_file
        )

        # 5. Train fatality model
        fat_model = train_fatality_model(
            X_tr, yf_tr, X_te, yf_te, report_file
        )

        _log("\n" + "=" * 60, report_file)
        _log("Artifact Summary", report_file)
        _log("=" * 60, report_file)

        # 6. Save models
        sev_path = os.path.join(ARTIFACTS_DIR, "severity_model.pkl")
        fat_path = os.path.join(ARTIFACTS_DIR, "fatality_model.pkl")
        enc_path = os.path.join(ARTIFACTS_DIR, "encoders.pkl")
        te_path = os.path.join(ARTIFACTS_DIR, "target_encoder.pkl")

        joblib.dump(sev_model, sev_path)
        joblib.dump(fat_model, fat_path)
        joblib.dump(encoders, enc_path)
        joblib.dump(target_encoder, te_path)

        meta = {
            "categorical_features": CATEGORICAL_FEATURES,
            "numeric_features": NUMERIC_FEATURES,
            "all_features": ALL_FEATURES,
            "target": "severity",
            "severity_order": SEVERITY_ORDER,
        }
        joblib.dump(meta, os.path.join(ARTIFACTS_DIR, "feature_meta.pkl"))

        for path in [sev_path, fat_path, enc_path, te_path,
                     os.path.join(ARTIFACTS_DIR, "feature_meta.pkl"),
                     os.path.join(ARTIFACTS_DIR, "pakistan_stats.csv"),
                     os.path.join(ARTIFACTS_DIR, "confusion_matrix_severity.png"),
                     os.path.join(ARTIFACTS_DIR, "confusion_matrix_fatality.png"),
                     REPORT_PATH]:
            exists = "[ok]" if os.path.exists(path) else "[missing]"
            _log(f"  {exists} {path}", report_file)

    print(f"\n[done] Training complete. Report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
