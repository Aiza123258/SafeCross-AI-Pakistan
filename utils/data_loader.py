"""
SafeCross AI - Data and Model Loading Utilities
Cached loading to ensure fast app startup.
"""

import streamlit as st
import joblib
import pandas as pd
import os

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")

@st.cache_resource
def load_severity_model():
    """Load the trained severity prediction model."""
    # Priority: honest model (53.5%, leakage-free) > advanced > original
    honest_path = os.path.join(ARTIFACTS_DIR, "severity_model_honest.pkl")
    advanced_path = os.path.join(ARTIFACTS_DIR, "severity_model_advanced.pkl")
    original_path = os.path.join(ARTIFACTS_DIR, "severity_model.pkl")
    
    if os.path.exists(honest_path):
        return joblib.load(honest_path)
    if os.path.exists(advanced_path):
        return joblib.load(advanced_path)
    if os.path.exists(original_path):
        return joblib.load(original_path)
    return None

@st.cache_resource
def load_fatality_model():
    """Load the trained fatality risk model."""
    model_path = os.path.join(ARTIFACTS_DIR, "fatality_model.pkl")
    if not os.path.exists(model_path):
        return None
    return joblib.load(model_path)

@st.cache_resource
def load_encoders():
    """Load the feature encoders."""
    # Priority: honest encoders > advanced > original
    honest_path = os.path.join(ARTIFACTS_DIR, "encoders_honest.pkl")
    advanced_path = os.path.join(ARTIFACTS_DIR, "encoders_advanced.pkl")
    original_path = os.path.join(ARTIFACTS_DIR, "encoders.pkl")
    
    if os.path.exists(honest_path):
        return joblib.load(honest_path)
    if os.path.exists(advanced_path):
        return joblib.load(advanced_path)
    if os.path.exists(original_path):
        return joblib.load(original_path)
    return None

@st.cache_resource
def load_target_encoder():
    """Load the target label encoder."""
    encoder_path = os.path.join(ARTIFACTS_DIR, "target_encoder.pkl")
    if not os.path.exists(encoder_path):
        return None
    return joblib.load(encoder_path)

@st.cache_resource
def load_feature_meta():
    """Load feature metadata."""
    # Priority: honest meta > advanced > original
    honest_path = os.path.join(ARTIFACTS_DIR, "feature_meta_honest.pkl")
    advanced_path = os.path.join(ARTIFACTS_DIR, "feature_meta_advanced.pkl")
    original_path = os.path.join(ARTIFACTS_DIR, "feature_meta.pkl")
    
    if os.path.exists(honest_path):
        return joblib.load(honest_path)
    if os.path.exists(advanced_path):
        return joblib.load(advanced_path)
    if os.path.exists(original_path):
        return joblib.load(original_path)
    return None

@st.cache_resource
def load_severity_model_v2():
    """Load the Pakistan V2 severity model (HistGradientBoosting, 98.5% accuracy)."""
    path = os.path.join(ARTIFACTS_DIR, "severity_model_v2.pkl")
    if not os.path.exists(path):
        return None
    return joblib.load(path)

@st.cache_resource
def load_encoders_v2():
    """Load the Pakistan V2 feature encoders."""
    path = os.path.join(ARTIFACTS_DIR, "encoders_v2.pkl")
    if not os.path.exists(path):
        return None
    return joblib.load(path)

@st.cache_resource
def load_feature_meta_v2():
    """Load the Pakistan V2 feature metadata."""
    path = os.path.join(ARTIFACTS_DIR, "feature_meta_v2.pkl")
    if not os.path.exists(path):
        return None
    return joblib.load(path)

@st.cache_data
def load_pakistan_stats():
    """Load cleaned Pakistan statistics."""
    stats_path = os.path.join(ARTIFACTS_DIR, "pakistan_stats.csv")
    if not os.path.exists(stats_path):
        return pd.DataFrame()
    return pd.read_csv(stats_path)

@st.cache_data
def load_training_data_sample():
    """Load a sample of training data for hotspot visualization."""
    data_path = os.path.join(os.path.dirname(ARTIFACTS_DIR), "data", "india_traffic_accidents.csv")
    if not os.path.exists(data_path):
        return pd.DataFrame()
    df = pd.read_csv(data_path, nrows=10000)
    return df

def get_severity_color(severity):
    """Return color code for severity level."""
    colors = {
        "Low": "#10b981",      # Green
        "Medium": "#f59e0b",   # Yellow/Orange
        "High": "#f97316",     # Orange
        "Critical": "#ef4444"  # Red
    }
    return colors.get(severity, "#6b7280")

def get_risk_level(score):
    """Categorize risk score into levels."""
    if score >= 75:
        return "Critical", "#ef4444"
    elif score >= 50:
        return "High", "#f97316"
    elif score >= 25:
        return "Medium", "#f59e0b"
    else:
        return "Low", "#10b981"
