# SafeCross AI - ML Pipeline

Pakistan-focused road safety prediction system. This README covers the
data preprocessing and model training pipeline only. UI documentation is
separate.

---

## Dataset Roles

| Dataset | File | Role |
|---|---|---|
| Accident patterns | `data/india_traffic_accidents.csv` | ML training only - NOT presented as Pakistani data |
| Pakistan statistics | `data/traffic-accidents-annual-.csv` | Pakistan-specific dashboards and analysis |

**The original CSV files are never modified.** All outputs go to `artifacts/`.

---

## Dataset A: Accident Pattern Data (ML training)

1,000,000 synthetic accident records with 15 columns covering weather,
road conditions, cause, severity, injuries, and fatalities.

### Leakage Audit

Before selecting features, every column was cross-tabbed against the
severity target to identify synthetic-generation artifacts:

| Column | Decision | Reason |
|---|---|---|
| `injuries` | **EXCLUDED** | Post-accident outcome - consequence of severity, not cause |
| `fatalities` | **EXCLUDED as feature** | Post-accident outcome (used only as fatality model *target*) |
| `lane_utilization` | **EXCLUDED** | Hard leakage: `Overtaking` = 100% High/Critical, `Single Lane` = 100% Low/Medium |
| `id` | **EXCLUDED** | Identifier with no predictive value |
| `date`, `time` | **EXCLUDED** | Replaced by engineered features: `hour`, `day_of_week`, `is_night` |
| `latitude`, `longitude` | **EXCLUDED** | Not available at prediction time in the Streamlit UI |
| `weather` | **KEPT** | Domain-valid causal feature (Dust Storm/Heavy Rain legitimately raise risk) |
| `road_condition` | **KEPT** | Domain-valid causal feature |
| `accident_cause` | **KEPT** | Domain-valid causal feature |
| `traffic_density` | **KEPT** | Legitimate contextual feature (uniform distribution is harmless) |
| `vehicles_involved` | **KEPT** | Pre-accident context |
| `nearby_accidents` | **KEPT** | Local hazard density - pre-existing condition |

### Final Features Used

```
Categorical: weather, road_condition, accident_cause, traffic_density
Numeric:     vehicles_involved, nearby_accidents, hour, day_of_week, is_night
```

---

## Dataset B: Pakistan Annual Statistics

Official accident statistics from Pakistan's provincial road safety
records, covering 2008-09 to 2018-19 across 5 provinces + national total.

The raw CSV has a malformed header (footnote in row 0, real column names
in row 1). `data_preprocessing.py` fixes this automatically and adds
derived ratios: `fatality_rate`, `injury_rate`, `fatal_accident_pct`.

Output: `artifacts/pakistan_stats.csv`

---

## Models Trained

### Model 1: Severity Classifier

- **Target**: `severity` - 4 classes: Low / Medium / High / Critical
- **Algorithm**: XGBoost (multi-class, `mlogloss`)
- **Training set**: 240,000 rows (80% of 300k sample)
- **Test set**: 60,000 rows (20%, stratified split)
- **Output**: `artifacts/severity_model.pkl`

### Model 2: Fatality Risk Classifier

- **Target**: `fatality_risk` (0 = no fatalities, 1 = one or more fatalities)
- **Note**: The `fatalities` column is used only to construct this binary label.
  It is NOT an input feature - there is no target leakage.
- **Algorithm**: XGBoost (binary, `logloss`, with `scale_pos_weight` for imbalance)
- **Class balance**: ~73% no fatality / 27% fatality risk
- **Output**: `artifacts/fatality_model.pkl`

---

## Performance Results

### Severity Classifier

| Metric | Value |
|---|---|
| Accuracy | 0.4732 |
| Weighted Precision | 0.5075 |
| Weighted Recall | 0.4732 |
| Weighted F1 | 0.4164 |
| ROC-AUC (OvR) | 0.7269 |

**Why ~47% accuracy is the honest ceiling:**
After removing the leaked `lane_utilization` feature, the remaining
features only provide a theoretical accuracy ceiling of ~53% on this
synthetic dataset. The label was generated with additional hidden
randomness not encoded in the remaining columns. On a 4-class problem
with a 29% majority-class baseline, 47% accuracy and 0.73 ROC-AUC
represent genuine learned discrimination, not a failed model.

The model correctly learns that `Dust Storm + Muddy road + Weather cause`
is more likely Critical, while `Clear + Dry + Animal Crossing` is more
likely Low/Medium - which is domain-valid behavior.

### Fatality Risk Classifier

| Metric | Value |
|---|---|
| Accuracy | 0.6822 |
| Precision | 0.4472 |
| Recall | 0.8074 |
| F1-score | 0.5756 |
| ROC-AUC | 0.7604 |

High recall (0.81) is the right trade-off for an emergency safety system:
the model errs on the side of flagging potential fatalities rather than
missing them.

---

## Artifacts

All outputs are saved to `artifacts/`. **Do not delete these before
running the Streamlit app** - the app loads them at startup.

```
artifacts/
  severity_model.pkl          XGBoost severity classifier
  fatality_model.pkl          XGBoost fatality risk classifier
  encoders.pkl                LabelEncoders + StandardScaler for all features
  target_encoder.pkl          LabelEncoder for severity classes
  feature_meta.pkl            Feature name lists and ordering
  pakistan_stats.csv          Cleaned Pakistan provincial statistics
  confusion_matrix_severity.png
  confusion_matrix_fatality.png
  evaluation_report.txt       Full metrics report
```

---

## How to Run

### One-time setup

```bash
pip install -r requirements.txt
```

### Run the full pipeline

```bash
py model_training.py
```

This single command:
1. Cleans and saves `pakistan_stats.csv`
2. Loads and samples 300,000 rows from the accident dataset
3. Engineers time features, encodes all features
4. Trains the severity classifier + fatality risk classifier
5. Evaluates both models and saves metrics to `evaluation_report.txt`
6. Saves all model + encoder artifacts to `artifacts/`

Expected runtime: 3-7 minutes on a modern CPU.

### Run preprocessing only (no model training)

```bash
py data_preprocessing.py
```

Useful for inspecting the cleaned datasets without retraining.

### Run the Streamlit web application

```bash
py -m streamlit run app.py
```

This launches the SafeCross AI web interface with 5 pages:
- **Home** - Overview and navigation
- **Severity Predictor** - AI-powered accident severity prediction
- **Fatality Risk** - Fatality probability assessment
- **Pakistan Dashboard** - Provincial statistics and trends (2008-2019)
- **Hotspot Map** - Interactive accident hotspot visualization
- **Emergency Response** - Decision support guidance

The app loads pre-trained models from `artifacts/` - no retraining required.
Open the URL shown in the terminal (typically http://localhost:8501) in your browser.

---

## File Structure

```
SafeCross AI/
  data/
    india_traffic_accidents.csv     (read-only, 1M rows, ML training source)
    traffic-accidents-annual-.csv   (read-only, Pakistan stats)
  artifacts/                        (generated - gitignore this if large)
  pages/                            (Streamlit multi-page app)
    1_🎯_Severity_Predictor.py
    2_⚠️_Fatality_Risk.py
    3_📊_Pakistan_Dashboard.py
    4_🗺️_Hotspot_Map.py
    5_🚨_Emergency_Response.py
  utils/                            (shared utilities)
    data_loader.py                  (cached model/data loading)
    predictor.py                    (prediction logic)
  app.py                            (Streamlit home page)
  data_preprocessing.py             (Dataset B cleaning + Dataset A feature engineering)
  model_training.py                 (Training pipeline - run this)
  requirements.txt
  PIPELINE_README.md                (this file)
```

---

## Notes for Streamlit App Development

- Load `encoders.pkl` with `joblib.load()` to transform user inputs
- Load `feature_meta.pkl` to get the exact feature order the models expect
- The `target_encoder.pkl` maps integer predictions back to severity labels
- `pakistan_stats.csv` is ready for direct use in Plotly charts
- All encoder `.transform()` calls must use the same category strings as in
  the training data (see `feature_meta.pkl` for valid values per column)
