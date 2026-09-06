"""
SafeCross AI - Evaluate pakistan_accidents_5000_v2.csv for severity prediction.
Tests whether redesigned scoring logic achieves 90%+ test accuracy.
"""
import time
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, f1_score, confusion_matrix, classification_report
)
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

warnings.filterwarnings("ignore")

SEED = 42
OUTCOME_COLS = ["fatalities", "serious_injuries", "minor_injuries", "property_damage_level"]
TARGET = "severity"
DROP_COLS = OUTCOME_COLS + [TARGET, "incident_id"]

DATA_PATH = "data/pakistan_accidents_5000_v2.csv"

def main():
    print("=" * 70)
    print("SafeCross AI - Pakistan Dataset V2 Severity Evaluation")
    print("=" * 70)

    df = pd.read_csv(DATA_PATH)
    print(f"\nLoaded: {df.shape[0]:,} rows, {df.shape[1]} columns")
    print(f"Severity distribution:\n{df[TARGET].value_counts().sort_index()}")

    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    print(f"\nInput features: {len(feature_cols)}")
    print(f"Excluded (outcome): {OUTCOME_COLS}")
    print(f"Excluded (target):  {TARGET}")
    print(f"Excluded (id):      incident_id")

    X = df[feature_cols].copy()
    y = df[TARGET].copy()

    cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
    num_cols = X.select_dtypes(exclude=["object"]).columns.tolist()
    print(f"\nCategorical features: {len(cat_cols)}")
    print(f"Numerical features:   {len(num_cols)}")

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
    print(f"\nSplit sizes:")
    print(f"  Train: {len(X_train):,}  Val: {len(X_val):,}  Test: {len(X_test):,}")
    print(f"  Train severity dist: {dict(y_train.value_counts(normalize=True).sort_index())}")
    print(f"  Val   severity dist: {dict(y_val.value_counts(normalize=True).sort_index())}")
    print(f"  Test  severity dist: {dict(y_test.value_counts(normalize=True).sort_index())}")

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
    class_names = list(sev_le.classes_)

    models = {
        "CatBoost": CatBoostClassifier(
            iterations=300, depth=6, learning_rate=0.1,
            random_seed=SEED, verbose=False,
            auto_class_weights="Balanced"
        ),
        "XGBoost": XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            random_state=SEED, eval_metric="mlogloss",
            verbosity=0
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=300, max_depth=6, learning_rate=0.1,
            random_state=SEED
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, max_depth=None, min_samples_leaf=2,
            random_state=SEED, n_jobs=-1, class_weight="balanced"
        ),
    }

    results = []

    print("\n" + "=" * 70)
    print("TRAINING & EVALUATION")
    print("=" * 70)

    for name, model in models.items():
        print(f"\n{'-' * 50}")
        print(f"  {name}")
        print(f"{'-' * 50}")

        t0 = time.time()
        model.fit(X_train_arr, y_train_arr)
        train_time = time.time() - t0

        y_val_pred = model.predict(X_val_arr)
        y_test_pred = model.predict(X_test_arr)

        val_acc = accuracy_score(y_val_arr, y_val_pred)
        test_acc = accuracy_score(y_test_arr, y_test_pred)
        val_f1w = f1_score(y_val_arr, y_val_pred, average="weighted")
        test_f1w = f1_score(y_test_arr, y_test_pred, average="weighted")
        val_f1m = f1_score(y_val_arr, y_val_pred, average="macro")
        test_f1m = f1_score(y_test_arr, y_test_pred, average="macro")

        print(f"  Train time: {train_time:.2f}s")
        print(f"  Val  accuracy:  {val_acc:.4f}  F1-w: {val_f1w:.4f}  F1-m: {val_f1m:.4f}")
        print(f"  Test accuracy:  {test_acc:.4f}  F1-w: {test_f1w:.4f}  F1-m: {test_f1m:.4f}")

        print(f"\n  TEST Confusion Matrix:")
        cm = confusion_matrix(y_test_arr, y_test_pred, labels=list(range(len(class_names))))
        header = "  " + "  ".join(f"{c:>8}" for c in class_names)
        print(f"  {'':>10} {header}")
        for i, cls in enumerate(class_names):
            row = "  ".join(f"{cm[i][j]:>8}" for j in range(len(class_names)))
            print(f"  {cls:>10} {row}")

        print(f"\n  TEST Classification Report:")
        print(classification_report(y_test_arr, y_test_pred, labels=list(range(len(class_names))), target_names=class_names))

        if hasattr(model, "feature_importances_"):
            importances = np.nan_to_num(model.feature_importances_, nan=0.0)
        else:
            importances = np.zeros(len(feature_cols))

        results.append({
            "model": name,
            "train_time": train_time,
            "val_accuracy": val_acc,
            "test_accuracy": test_acc,
            "val_f1_weighted": val_f1w,
            "test_f1_weighted": test_f1w,
            "val_f1_macro": val_f1m,
            "test_f1_macro": test_f1m,
            "importances": importances,
        })

    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    print(f"\n{'Model':<25} {'Val Acc':>8} {'Test Acc':>9} {'Val F1w':>8} {'Test F1w':>9} {'Val F1m':>8} {'Test F1m':>9} {'Time':>6}")
    print("-" * 90)
    for r in sorted(results, key=lambda x: x["test_accuracy"], reverse=True):
        print(f"{r['model']:<25} {r['val_accuracy']:>8.4f} {r['test_accuracy']:>9.4f} "
              f"{r['val_f1_weighted']:>8.4f} {r['test_f1_weighted']:>9.4f} "
              f"{r['val_f1_macro']:>8.4f} {r['test_f1_macro']:>9.4f} {r['train_time']:>5.1f}s")

    best = max(results, key=lambda x: x["test_accuracy"])
    print(f"\n{'=' * 70}")
    print(f"BEST MODEL: {best['model']}")
    print(f"  Test Accuracy:      {best['test_accuracy']:.4f}")
    print(f"  Test F1 (weighted): {best['test_f1_weighted']:.4f}")
    print(f"  Test F1 (macro):    {best['test_f1_macro']:.4f}")
    print(f"  90%+ achievable:    {'YES' if best['test_accuracy'] >= 0.90 else 'NO'}")
    print(f"{'=' * 70}")

    print(f"\nTOP 15 FEATURES (by {best['model']} importance):")
    imp_sorted = sorted(
        zip(feature_cols, best["importances"]),
        key=lambda x: x[1], reverse=True
    )
    max_imp = imp_sorted[0][1] if imp_sorted[0][1] > 0 else None
    if max_imp is None:
        print(f"  ({best['model']} does not expose usable feature importances)")
    else:
        for i, (feat, imp) in enumerate(imp_sorted[:15]):
            bar = "#" * int(imp / max_imp * 30)
            print(f"  {i+1:>2}. {feat:<30} {imp:.4f} {bar}")

    print(f"\nALL MODELS - Feature Importance (top 5 each):")
    for r in sorted(results, key=lambda x: x["test_accuracy"], reverse=True):
        print(f"\n  {r['model']}:")
        imp_sorted_r = sorted(
            zip(feature_cols, r["importances"]),
            key=lambda x: x[1], reverse=True
        )
        max_imp_r = imp_sorted_r[0][1] if imp_sorted_r[0][1] > 0 else None
        if max_imp_r is None:
            print(f"    (no usable feature importances)")
        else:
            for feat, imp in imp_sorted_r[:5]:
                print(f"    {feat:<30} {imp:.4f}")

    summary_rows = []
    for r in results:
        summary_rows.append({
            "model": r["model"],
            "train_time_sec": round(r["train_time"], 2),
            "val_accuracy": round(r["val_accuracy"], 4),
            "test_accuracy": round(r["test_accuracy"], 4),
            "val_f1_weighted": round(r["val_f1_weighted"], 4),
            "test_f1_weighted": round(r["test_f1_weighted"], 4),
            "val_f1_macro": round(r["val_f1_macro"], 4),
            "test_f1_macro": round(r["test_f1_macro"], 4),
        })
    pd.DataFrame(summary_rows).to_csv(
        "artifacts/pakistan_5000_v2_evaluation.csv", index=False
    )
    print(f"\n[done] Results saved to artifacts/pakistan_5000_v2_evaluation.csv")


if __name__ == "__main__":
    main()
