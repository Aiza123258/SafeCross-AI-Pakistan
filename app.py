"""
SafeCross AI - Home Page
AI-Powered Intelligent Road Safety & Emergency Management Platform.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.ui_components import (
    inject_global_css, render_hero, render_metric_card,
    render_compact_metric_card,
    render_feature_card, render_pipeline_step, render_footer,
    render_section_title, render_sidebar_brand, render_sidebar_about, render_sidebar_nav,
    render_sidebar_footer, render_top_nav, render_detection_settings_panel,
)

st.set_page_config(
    page_title="SafeCross AI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

render_top_nav()

with st.sidebar:
    render_sidebar_brand()
    render_sidebar_about()
    render_sidebar_nav()
    render_detection_settings_panel()
    render_sidebar_footer()


# ── Hero Section ─────────────────────────────────────────────────────────────

render_hero(
    title="SafeCross AI",
    subtitle="Intelligent Road Safety & Emergency Management",
    tagline="Real-time computer vision, pedestrian safety intelligence, emergency prioritization, and smart barrier decision support — from detection to decision.",
)


# ── Pipeline Visualization ───────────────────────────────────────────────────

render_section_title("From Detection to Decision")

st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 0.9rem; margin-bottom: 0.8rem;">
    The complete SafeCross AI pipeline — from camera input to actionable safety recommendations.
</div>
""", unsafe_allow_html=True)

p1, p2, p3, p4, p5, p6, p7 = st.columns(7)
with p1:
    render_pipeline_step("", "Camera / Video")
with p2:
    render_pipeline_step("", "YOLO Detection", active=True)
with p3:
    render_pipeline_step("", "Proximity AI", active=True)
with p4:
    render_pipeline_step("", "Pedestrian Safety", active=True)
with p5:
    render_pipeline_step("", "Emergency Priority", active=True)
with p6:
    render_pipeline_step("", "Smart Barrier", active=True)
with p7:
    render_pipeline_step("", "Action", active=True)


# ── System Status KPIs ───────────────────────────────────────────────────────

render_section_title("System Status")

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    render_compact_metric_card("AI Detection", "ACTIVE", "#10b981", "YOLOv8 Ready")
with k2:
    render_compact_metric_card("Pedestrian Safety", "ACTIVE", "#10b981", "Crossing Zone AI")
with k3:
    render_compact_metric_card("Emergency Priority", "ACTIVE", "#10b981", "State Machine")
with k4:
    render_compact_metric_card("Smart Barrier", "SIMULATION", "#f59e0b", "Decision Engine")
with k5:
    render_compact_metric_card("Model Status", "READY", "#3b82f6", "Severity + Fatality")


# ── Feature Cards ────────────────────────────────────────────────────────────

render_section_title("Platform Features")

f1, f2, f3, f4 = st.columns(4)
with f1:
    render_feature_card(
        "", "Live Traffic Detection",
        "YOLOv8-powered real-time vehicle and pedestrian detection from camera or video input.",
        "ACTIVE", "#10b981",
    )
with f2:
    render_feature_card(
        "", "Pedestrian Safety",
        "Crossing zone analysis, pedestrian-vehicle conflict detection, and safety scoring.",
        "ACTIVE", "#10b981",
    )
with f3:
    render_feature_card(
        "", "Proximity Intelligence",
        "Relative proximity analysis between pedestrians and vehicles with SAFE/WARNING/DANGER zones.",
        "ACTIVE", "#10b981",
    )
with f4:
    render_feature_card(
        "", "Emergency Priority",
        "Situation-aware emergency vehicle passage recommendation with safety checks.",
        "SIMULATION", "#f59e0b",
    )

f5, f6, f7, f8 = st.columns(4)
with f5:
    render_feature_card(
        "", "Smart Barrier",
        "Explainable AI-assisted barrier decision engine with safety-first priority hierarchy.",
        "SIMULATION", "#f59e0b",
    )
with f6:
    render_feature_card(
        "", "Risk Analytics",
        "AI-powered accident severity prediction and fatality risk assessment from trained ML models.",
        "ACTIVE", "#10b981",
    )
with f7:
    render_feature_card(
        "", "Pakistan Dashboard",
        "Provincial accident statistics, trend analysis, and regional risk patterns (2008-2019).",
        "ACTIVE", "#10b981",
    )
with f8:
    render_feature_card(
        "", "Emergency Response",
        "Scenario-based emergency guidance, first aid protocols, and contact information.",
        "ACTIVE", "#10b981",
    )


# ── Quick Start Guide ────────────────────────────────────────────────────────

render_section_title("Quick Start")

st.markdown("""
<div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem;">
    <strong style="font-size: 1.05rem;">Recommended Demo Path</strong>
    <div style="margin-top: 0.5rem; line-height: 1.5; color: #374151;">
        <strong>1.</strong> Start here to understand the platform<br>
        <strong>2.</strong> <strong>Live Detection</strong> — Upload an image to see AI detection, proximity analysis, pedestrian safety, and barrier recommendation<br>
        <strong>3.</strong> <strong>Emergency Priority</strong> — Try different emergency scenarios and watch the smart barrier decision engine respond<br>
        <strong>4.</strong> <strong>Pakistan Dashboard</strong> — Explore real provincial accident statistics<br>
        <strong>5.</strong> <strong>Severity Predictor</strong> — Input accident conditions and get AI-predicted severity
    </div>
</div>
""", unsafe_allow_html=True)


# ── Technology Stack ─────────────────────────────────────────────────────────

render_section_title("Technology")

t1, t2, t3, t4 = st.columns(4)
with t1:
    st.markdown("""
    <div class="sc-card" style="text-align: center;">
        <div style="font-size: 0.8rem; color: #6b7280; font-weight: 500;">OBJECT DETECTION</div>
        <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937; margin: 0.3rem 0;">YOLOv8</div>
        <div style="font-size: 0.75rem; color: #6b7280;">Ultralytics</div>
    </div>
    """, unsafe_allow_html=True)
with t2:
    st.markdown("""
    <div class="sc-card" style="text-align: center;">
        <div style="font-size: 0.8rem; color: #6b7280; font-weight: 500;">SEVERITY MODEL</div>
        <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937; margin: 0.3rem 0;">XGBoost</div>
        <div style="font-size: 0.75rem; color: #6b7280;">Multi-class Classification</div>
    </div>
    """, unsafe_allow_html=True)
with t3:
    st.markdown("""
    <div class="sc-card" style="text-align: center;">
        <div style="font-size: 0.8rem; color: #6b7280; font-weight: 500;">PLATFORM</div>
        <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937; margin: 0.3rem 0;">Streamlit</div>
        <div style="font-size: 0.75rem; color: #6b7280;">Python Web App</div>
    </div>
    """, unsafe_allow_html=True)
with t4:
    st.markdown("""
    <div class="sc-card" style="text-align: center;">
        <div style="font-size: 0.8rem; color: #6b7280; font-weight: 500;">VISUALIZATION</div>
        <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937; margin: 0.3rem 0;">Plotly</div>
        <div style="font-size: 0.75rem; color: #6b7280;">Interactive Charts</div>
    </div>
    """, unsafe_allow_html=True)


# ── Prototype Disclaimer ─────────────────────────────────────────────────────

with st.expander("Prototype & Model Limitations", expanded=False):
    st.markdown("""
    - Proximity analysis uses pixel-based relative distance estimates, not calibrated physical measurements
    - Ambulance recognition currently uses simulation mode (standard YOLOv8 COCO has no ambulance class)
    - Smart barrier is a simulation — does not control real-world infrastructure
    - AI recommendations are decision support, not certified traffic-control commands
    - Severity and fatality models are trained on synthetic data — accuracy represents honest performance
    - Hotspot map uses prototype coordinates, not verified Pakistan accident locations
    - Pakistan statistics are from official provincial records (2008-2019)
    """)


# ── Footer ───────────────────────────────────────────────────────────────────

render_footer()
