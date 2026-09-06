"""
SafeCross AI - Train and save the Pakistan V2 severity model.
Reproduces the exact HistGradientBoosting model that achieved 98.53% test accuracy.
Saves: model, encoders, feature metadata.
"""
import os
import warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score

warnings.filterwarnings("ignore")

SEED = 42
OUTCOME_COLS = ["fatalities", "serious_injuries", "minor_injuries", "property_damage_level"]
TARGET = "severity"
DROP_COLS = OUTCOME_COLS + [TARGET, "incident_id"]

DATA_PATH = "data/pakistan_accidents_5000_v2.csv"
ARTIFACTS_DIR = "artifacts"


def main():
    print("=" * 70)
    print("SafeCross AI - Train & Save Pakistan V2 Severity Model")
    print("=" * 70)

    df = pd.read_csv(DATA_PATH)
    print(f"\nLoaded: {df.shape[0]:,} rows, {df.shape[1]} columns")

    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    print(f"Input features: {len(feature_cols)}")

    X = df[feature_cols].copy()
    y = df[TARGET].copy()

    cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
    num_cols = X.select_dtypes(exclude=["object"]).columns.tolist()
    print(f"Categorical: {len(cat_cols)}, Numeric: {len(num_cols)}")

    for col in cat_cols:
        X[col] = X[col].fillna("Unknown").astype(str)
    for col in num_cols:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median())

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=SEED, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=SEED, stratify=y_temp
    )
    print(f"Split: Train={len(X_train):,}  Val={len(X_val):,}  Test={len(X_test):,}")

    encoders = {}
    X_train_enc = X_train.copy()
    X_val_enc = X_val.copy()
    X_test_enc = X_test.copy()

    for col in cat_cols:
        le = LabelEncoder()
        all_vals = pd.concat([X_train[col], X_val[col], X_test[col]]).unique()
        le.fit(all_vals)
        X_train_enc[col] = le.transform(X_train_enc[col])
        X_val_enc[col] = le.transform(X_val_enc[col])
        X_test_enc[col] = le.transform(
            X_test_enc[col].map(lambda x: x if x in le.classes_ else "Unknown")
        )
        encoders[col] = le

    X_train_arr = X_train_enc.values
    X_val_arr = X_val_enc.values
    X_test_arr = X_test_enc.values

    classes = sorted(y.unique())
    sev_le = LabelEncoder()
    sev_le.fit(classes)
    y_train_arr = sev_le.transform(y_train.values)
    y_val_arr = sev_le.transform(y_val.values)
    y_test_arr = sev_le.transform(y_test.values)

    print(f"\nTraining HistGradientBoosting (max_iter=300, max_depth=6, lr=0.1)...")
    model = HistGradientBoostingClassifier(
        max_iter=300, max_depth=6, learning_rate=0.1,
        random_state=SEED
    )
    model.fit(X_train_arr, y_train_arr)

    y_val_pred = model.predict(X_val_arr)
    y_test_pred = model.predict(X_test_arr)
    val_acc = accuracy_score(y_val_arr, y_val_pred)
    test_acc = accuracy_score(y_test_arr, y_test_pred)
    test_f1w = f1_score(y_test_arr, y_test_pred, average="weighted")
    test_f1m = f1_score(y_test_arr, y_test_pred, average="macro")

    print(f"\n  Val  accuracy: {val_acc:.4f}")
    print(f"  Test accuracy: {test_acc:.4f}")
    print(f"  Test F1-w:     {test_f1w:.4f}")
    print(f"  Test F1-m:     {test_f1m:.4f}")

    assert test_acc >= 0.98, f"Expected ~98.53% but got {test_acc:.4f} — preprocessing mismatch!"

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    model_path = os.path.join(ARTIFACTS_DIR, "severity_model_v2.pkl")
    joblib.dump(model, model_path)
    print(f"\n  Saved model:        {model_path}")

    encoders_data = {
        "feature_encoders": encoders,
        "y_encoder": sev_le,
        "cat_cols": cat_cols,
        "num_cols": num_cols,
    }
    encoders_path = os.path.join(ARTIFACTS_DIR, "encoders_v2.pkl")
    joblib.dump(encoders_data, encoders_path)
    print(f"  Saved encoders:     {encoders_path}")

    feature_meta = {
        "features": feature_cols,
        "cat_cols": cat_cols,
        "num_cols": num_cols,
        "class_names": list(sev_le.classes_),
        "n_features": len(feature_cols),
        "model_name": "HistGradientBoosting",
        "dataset": "pakistan_accidents_5000_v2.csv",
        "dataset_rows": len(df),
        "test_accuracy": round(test_acc, 4),
        "test_f1_weighted": round(test_f1w, 4),
        "test_f1_macro": round(test_f1m, 4),
        "seed": SEED,
    }
    meta_path = os.path.join(ARTIFACTS_DIR, "feature_meta_v2.pkl")
    joblib.dump(feature_meta, meta_path)
    print(f"  Saved feature meta: {meta_path}")

    print(f"\n{'=' * 70}")
    print("VERIFICATION - loading saved artifacts back")
    print(f"{'=' * 70}")

    loaded_model = joblib.load(model_path)
    loaded_enc = joblib.load(encoders_path)
    loaded_meta = joblib.load(meta_path)

    verify_pred = loaded_model.predict(X_test_arr)
    verify_acc = accuracy_score(y_test_arr, verify_pred)
    print(f"  Loaded model test accuracy: {verify_acc:.4f}")
    assert verify_acc == test_acc, "Verification failed!"

    print(f"  Feature columns ({loaded_meta['n_features']}): {loaded_meta['features'][:5]}...")
    print(f"  Classes: {loaded_meta['class_names']}")
    print(f"  Cat cols: {len(loaded_meta['cat_cols'])}, Num cols: {len(loaded_meta['num_cols'])}")
    print(f"\n[done] All v2 artifacts saved and verified.")


if __name__ == "__main__":
    main()
