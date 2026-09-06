"""
SafeCross AI - Emergency Vehicle Priority Page
AI-assisted emergency vehicle priority with Smart Barrier Decision Engine.

HONESTY NOTE:
Standard YOLOv8 COCO detection does NOT provide dedicated ambulance recognition.
This page provides an Emergency Scenario Demo Mode for prototype demonstration.
Real-world emergency vehicle recognition requires a dedicated trained model.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.emergency_priority import (
    EmergencyPriorityEngine, DEMO_SCENARIOS,
    log_emergency_event,
)
from utils.smart_barrier import (
    SmartBarrierDecisionEngine, SMART_BARRIER_SCENARIOS,
    log_barrier_event, BARRIER_DISPLAY,
)

st.set_page_config(page_title="Emergency Priority - SafeCross AI", page_icon="", layout="wide")

try:
    from utils.ui_components import inject_global_css, render_page_header, render_footer, render_sidebar_brand, render_sidebar_about, render_sidebar_nav, render_sidebar_footer, render_top_nav, render_detection_settings_panel
    inject_global_css()
    HAS_UI = True
except ImportError:
    HAS_UI = False

if HAS_UI:
    render_top_nav()
    render_page_header("Emergency Vehicle Priority & Smart Barrier", "AI-assisted emergency recognition, safety-aware decision engine, and explainable smart barrier simulation")
else:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%); padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem;">
        <h2 style="margin:0;">Emergency Vehicle Priority & Smart Barrier</h2>
        <p style="margin:0.3rem 0 0 0; opacity:0.85;">AI-assisted emergency recognition and smart barrier simulation</p>
    </div>
    """, unsafe_allow_html=True)


# ── Session State ────────────────────────────────────────────────────────────

if "emergency_engine" not in st.session_state:
    st.session_state.emergency_engine = EmergencyPriorityEngine()
if "barrier_engine" not in st.session_state:
    st.session_state.barrier_engine = SmartBarrierDecisionEngine()
if "emergency_event_log" not in st.session_state:
    st.session_state.emergency_event_log = []

engine: EmergencyPriorityEngine = st.session_state.emergency_engine
barrier_engine: SmartBarrierDecisionEngine = st.session_state.barrier_engine
event_log: list = st.session_state.emergency_event_log


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    if HAS_UI:
        render_sidebar_brand()
        render_sidebar_about()
        render_sidebar_nav()
        render_detection_settings_panel()
        render_sidebar_footer()
    st.markdown("### Emergency Scenario Demo")

    scenario = st.selectbox(
        "Select Scenario",
        options=list(SMART_BARRIER_SCENARIOS.keys()),
        format_func=lambda k: SMART_BARRIER_SCENARIOS[k]["label"],
    )


# ── Process Scenario ─────────────────────────────────────────────────────────

prev_scenario = st.session_state.get("_prev_scenario", None)
if scenario != prev_scenario:
    engine.set_scenario(scenario if scenario in DEMO_SCENARIOS else "no_emergency")
    st.session_state._prev_scenario = scenario

scenario_data = SMART_BARRIER_SCENARIOS[scenario]
inputs = scenario_data["inputs"]

emergency_decision = engine.decide()
barrier_decision = barrier_engine.decide(**inputs)

prev_barrier_state = barrier_decision["previous_state"]
new_barrier_state = barrier_decision["state"]

if prev_barrier_state != new_barrier_state:
    event_log.append(log_barrier_event(barrier_decision))


# ── Status Banner ────────────────────────────────────────────────────────────

state_colors = {
    "NORMAL": "#10b981", "EMERGENCY_DETECTED": "#f59e0b",
    "PRIORITY_REQUESTED": "#ef4444", "PASSAGE_ACTIVE": "#3b82f6",
    "PASSAGE_COMPLETED": "#8b5cf6",
}
color = state_colors.get(engine.state, "#6b7280")
b_disp = barrier_engine.get_display()

st.markdown(f"""
<div style="background: linear-gradient(135deg, {color}15, {color}30);
            padding: 1.5rem; border-radius: 10px;
            border: 2px solid {color}; margin-bottom: 1.5rem;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h3 style="margin:0; color: {color};">
                Emergency State: {engine.state.replace('_', ' ')}
            </h3>
            <p style="margin:0.3rem 0 0 0; color: #374151;">
                Priority: <strong>{barrier_decision['priority']}</strong> |
                Emergency: <strong>{'YES' if barrier_decision['emergency_detected'] else 'NO'}</strong> |
                Mode: <strong>SIMULATION</strong>
            </p>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.85rem; color: #6b7280;">Smart Barrier</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {b_disp['color']};">
                {b_disp['emoji']} {b_disp['label']}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

sc = SMART_BARRIER_SCENARIOS[scenario]
info_col1, info_col2 = st.columns([3, 1])
with info_col1:
    st.info(f"**{sc['label']}** — {sc['description']}\n\n**Expected Decision:** {sc['expected_decision']}")
with info_col2:
    st.warning("SIMULATION MODE — Standard YOLOv8 COCO does not include an ambulance class. Scenarios use simulated inputs.")


# ── Traffic Conditions ───────────────────────────────────────────────────────

st.markdown("### Traffic Conditions")

tc1, tc2, tc3, tc4, tc5, tc6 = st.columns(6)

with tc1:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid #f59e0b;">
        <div style="color: #6b7280; font-size: 0.85rem;">Vehicles</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #f59e0b;">{inputs['vehicle_count']}</div>
    </div>
    """, unsafe_allow_html=True)
with tc2:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid #0ea5e9;">
        <div style="color: #6b7280; font-size: 0.85rem;">Pedestrians</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #0ea5e9;">{inputs['pedestrian_count']}</div>
    </div>
    """, unsafe_allow_html=True)
with tc3:
    pz_color = "#ef4444" if inputs["pedestrians_in_crossing"] > 0 else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid {pz_color};">
        <div style="color: #6b7280; font-size: 0.85rem;">In Crossing</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: {pz_color};">{inputs['pedestrians_in_crossing']}</div>
    </div>
    """, unsafe_allow_html=True)
with tc4:
    cf_color = "#ef4444" if inputs["potential_conflicts"] > 0 else "#10b981"
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid {cf_color};">
        <div style="color: #6b7280; font-size: 0.85rem;">Conflicts</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: {cf_color};">{inputs['potential_conflicts']}</div>
    </div>
    """, unsafe_allow_html=True)
with tc5:
    ss_color = {"DANGER": "#ef4444", "CAUTION": "#f59e0b", "SAFE": "#10b981", "CLEAR": "#6b7280"}.get(inputs["safety_status"], "#6b7280")
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid {ss_color};">
        <div style="color: #6b7280; font-size: 0.85rem;">Safety Status</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: {ss_color};">{inputs['safety_status']}</div>
    </div>
    """, unsafe_allow_html=True)
with tc6:
    sc_color = "#ef4444" if inputs["safety_score"] < 40 else ("#f59e0b" if inputs["safety_score"] < 70 else "#10b981")
    st.markdown(f"""
    <div class="metric-card" style="border-left: 4px solid {sc_color};">
        <div style="color: #6b7280; font-size: 0.85rem;">Safety Score</div>
        <div style="font-size: 1.8rem; font-weight: 700; color: {sc_color};">{inputs['safety_score']}/100</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")


# ── Smart Barrier Decision Card ──────────────────────────────────────────────

st.markdown("### Smart Barrier Decision")

d_color = {
    "CLOSE": "#10b981", "PREPARE": "#f59e0b",
    "OPEN": "#3b82f6", "HOLD": "#ef4444",
}.get(barrier_decision["decision"], "#6b7280")

d_icons = {"CLOSE": "\u26aa", "PREPARE": "\U0001f7e1", "OPEN": "\U0001f535", "HOLD": "\U0001f534"}
d_icon = d_icons.get(barrier_decision["decision"], "")

st.markdown(f"""
<div style="background: linear-gradient(135deg, {d_color}10, {d_color}25);
            padding: 1.5rem; border-radius: 10px;
            border: 2px solid {d_color}; margin-bottom: 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 2.5rem; font-weight: 700; color: {d_color};">
                {d_icon} {barrier_decision['decision']}
            </div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 0.85rem; color: #6b7280;">Decision Confidence</div>
            <div style="font-size: 2rem; font-weight: 700; color: {d_color};">
                {barrier_decision['confidence']}%
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.85rem; color: #6b7280;">Priority</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {d_color};">
                {barrier_decision['priority']}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

reason_col, action_col = st.columns(2)
with reason_col:
    st.markdown(f"**Reason:**\n\n{barrier_decision['reason']}")
with action_col:
    st.markdown(f"**Recommended Action:**\n\n{barrier_decision['recommended_action']}")

st.markdown(f"**Safety Consideration:** {barrier_decision['safety_consideration']}")

if barrier_decision["factors"]:
    st.markdown("**Decision Factors:**")
    for f in barrier_decision["factors"]:
        st.markdown(f"- {f}")

st.markdown("---")


# ── Barrier State Visualization ──────────────────────────────────────────────

st.markdown("### Barrier State Machine")

b_cols = st.columns(6)
barrier_flow = [
    ("CLOSED", "Normal - barrier closed"),
    ("PREPARING", "Emergency detected"),
    ("OPEN", "Priority granted"),
    ("HOLD", "Safety hold"),
    ("PASSAGE_ACTIVE", "Vehicle passing"),
    ("RESETTING", "Returning to normal"),
]

for i, (bstate, desc) in enumerate(barrier_flow):
    with b_cols[i]:
        is_active = barrier_engine.state == bstate
        disp = BARRIER_DISPLAY[bstate]
        border = f"3px solid {disp['color']}" if is_active else "1px solid #e5e7eb"
        bg = f"{disp['color']}15" if is_active else "white"
        st.markdown(f"""
        <div style="text-align: center; padding: 0.8rem; border-radius: 8px;
                    border: {border}; background: {bg};">
            <div style="font-size: 1.8rem;">{disp['emoji']}</div>
            <div style="font-size: 0.9rem; font-weight: {'700' if is_active else '400'};
                         color: {disp['color'] if is_active else '#6b7280'};">
                {disp['label']}
            </div>
            <div style="font-size: 0.7rem; color: #6b7280; margin-top: 0.2rem;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")


# ── Event Log ────────────────────────────────────────────────────────────────

log_header, log_action = st.columns([4, 1])
with log_header:
    st.markdown("### Emergency Event Log")
with log_action:
    if st.button("Clear Log", use_container_width=True):
        st.session_state.emergency_event_log = []
        st.rerun()

if event_log:
    log_rows = []
    for evt in event_log[-25:]:
        log_rows.append({
            "Time": evt["timestamp"],
            "Transition": f"{evt['previous_state']} -> {evt['new_state']}",
            "Decision": evt["decision"],
            "Priority": evt["priority"],
            "Confidence": f"{evt['confidence']}%",
            "Peds": evt["pedestrian_count"],
            "Vehicles": evt["vehicle_count"],
            "Conflicts": evt["conflict_count"],
        })
    st.dataframe(log_rows, use_container_width=True, hide_index=True)
else:
    st.info("No events recorded yet. Select a scenario to begin.")


# ── Disclaimer & Footer ──────────────────────────────────────────────────────

with st.expander("Prototype & Model Limitations", expanded=False):
    st.markdown("""
    - Smart Barrier is a prototype AI-assisted decision simulation — does not control real-world infrastructure
    - Decision confidence represents confidence in the rule-based decision, not a certified probability
    - Standard YOLOv8 COCO detection does not provide dedicated ambulance recognition
    - Emergency Scenario Demo Mode is provided for prototype demonstration
    - Real deployment requires validated models, calibrated sensors, and safety certification
    """)

if HAS_UI:
    render_footer()
