"""
SafeCross AI - Severity Predictor Page
"""

import streamlit as st
import sys
import os
import requests
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.backend_server import ensure_backend_running

from utils.predictor import predict_severity, predict_severity_v2, get_risk_factors
from utils.data_loader import get_severity_color


st.set_page_config(
    page_title="Severity Predictor - SafeCross AI",
    page_icon="",
    layout="wide"
)


# ============================================================
# UI COMPONENTS
# ============================================================

try:
    from utils.ui_components import (
        inject_global_css,
        render_page_header,
        render_footer,
        render_sidebar_brand,
        render_sidebar_about,
        render_sidebar_nav,
        render_sidebar_footer,
        render_top_nav,
        render_detection_settings_panel
    )

    inject_global_css()
    HAS_UI = True

except ImportError:
    HAS_UI = False


# ============================================================
# HEADER
# ============================================================

if HAS_UI:
    render_top_nav()

    render_page_header(
        "AI Accident Severity Predictor",
        "Input accident conditions and get AI-predicted severity levels from models trained on 1 million accident records"
    )
else:
    st.markdown("## AI Accident Severity Predictor")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    if HAS_UI:
        render_sidebar_brand()
        render_sidebar_about()
        render_sidebar_nav()
        render_detection_settings_panel()
        render_sidebar_footer()


# ============================================================
# INFORMATION BOX
# ============================================================

st.markdown(
    """
    <div class="info-box">
        <strong>How it works:</strong> Input the accident conditions below and our AI model will predict
        the likely severity level. The model was trained on 1 million accident records to learn patterns
        between conditions and outcomes.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# INPUT FORM
# ============================================================

st.markdown("### Input Accident Conditions")

col1, col2, col3 = st.columns(3)


# ------------------------------------------------------------
# COLUMN 1
# ------------------------------------------------------------

with col1:

    weather = st.selectbox(
        "Weather Condition",
        [
            "Clear",
            "Cloudy",
            "Rain",
            "Heavy Rain",
            "Fog",
            "Dust Storm"
        ],
        help="Current weather at time of accident"
    )

    road_condition = st.selectbox(
        "Road Condition",
        [
            "Dry",
            "Wet",
            "Muddy",
            "Potholed",
            "Flooding",
            "Construction"
        ],
        help="State of the road surface"
    )

    accident_cause = st.selectbox(
        "Accident Cause",
        [
            "Human Error",
            "Signal Violation",
            "Weather",
            "Poor Road",
            "Mechanical Failure",
            "Animal Crossing"
        ],
        help="Primary cause of the accident"
    )


# ------------------------------------------------------------
# COLUMN 2
# ------------------------------------------------------------

with col2:

    traffic_density = st.selectbox(
        "Traffic Density",
        [
            "Light",
            "Moderate",
            "Heavy"
        ],
        help="Traffic volume at time of accident"
    )

    vehicles_involved = st.number_input(
        "Vehicles Involved",
        min_value=1,
        max_value=20,
        value=2,
        help="Number of vehicles in the accident"
    )

    nearby_accidents = st.number_input(
        "Nearby Accidents (within 1km)",
        min_value=0,
        max_value=20,
        value=1,
        help="Number of recent accidents in the area"
    )


# ------------------------------------------------------------
# COLUMN 3
# ------------------------------------------------------------

with col3:

    accident_date = st.date_input(
        "Accident Date",
        value=pd.Timestamp.now().date(),
        help="Date of the accident"
    )

    accident_time = st.time_input(
        "Accident Time",
        value=pd.Timestamp.now().time(),
        help="Time of the accident"
    )

    # Derived features
    hour = accident_time.hour

    day_of_week = pd.Timestamp(accident_date).dayofweek

    is_night = 1 if (hour >= 20 or hour < 6) else 0


# ============================================================
# EXTRA INPUTS
# ============================================================

col_a, col_b = st.columns(2)


with col_a:

    speed_at_impact_kmh = st.number_input(
        "Speed at Impact (km/h)",
        min_value=20,
        max_value=160,
        value=60,
        help="Estimated vehicle speed at the moment of impact"
    )


with col_b:

    collision_type = st.selectbox(
        "Collision Type",
        [
            "Head-on",
            "Rear-end",
            "Side-swipe",
            "Fixed-object",
            "Rollover",
            "Pedestrian",
            "Multi-vehicle pileup"
        ],
        help="Type of collision"
    )


st.markdown("---")


# ============================================================
# PREDICT BUTTON
# ============================================================

if st.button(
    "🔮 Predict Severity",
    type="primary",
    use_container_width=True
):

    with st.spinner("Analyzing conditions..."):

        # ----------------------------------------------------
        # Convert frontend value to backend-compatible value
        # ----------------------------------------------------

        api_traffic_density = (
            "Medium"
            if traffic_density == "Moderate"
            else traffic_density
        )

        accident_date_str = str(accident_date)
        accident_time_str = accident_time.strftime("%H:%M")

        # ----------------------------------------------------
        # Call FastAPI Backend
        # ----------------------------------------------------

        try:

            if not ensure_backend_running():
                st.error("❌ FastAPI backend could not be started on port 8000.")
                st.stop()

            response = requests.post(
                "http://127.0.0.1:8000/predict/severity",

                json={
                    "weather": weather,
                    "road_condition": road_condition,
                    "accident_cause": accident_cause,
                    "traffic_density": api_traffic_density,
                    "vehicles_involved": int(vehicles_involved),
                    "nearby_accidents": int(nearby_accidents),
                    "hour": int(hour),
                    "day_of_week": int(day_of_week),
                    "is_night": int(is_night),

                    # Pakistan / Islamabad default coordinates
                    "latitude": 33.6844,
                    "longitude": 73.0479,

                    "month": int(accident_date.month)
                },

                timeout=30
            )

        except requests.exceptions.ConnectionError:

            st.error(
                "❌ Cannot connect to FastAPI backend. "
                "Please make sure the backend is running on port 8000."
            )

            st.code(
                "py -m uvicorn backend.main:app --reload --port 8000"
            )

            st.stop()

        except requests.exceptions.Timeout:

            st.error(
                "❌ Backend request timed out. "
                "Please check that the FastAPI server is running."
            )

            st.stop()

        except requests.exceptions.RequestException as e:

            st.error(
                f"❌ Backend request failed: {str(e)}"
            )

            st.stop()


        # ----------------------------------------------------
        # Process Backend Response
        # ----------------------------------------------------

        if response.status_code == 200:

            try:

                api_data = response.json()

                result = api_data["prediction"]

                prediction_id = api_data["database"]["prediction_id"]

            except (ValueError, KeyError):

                st.error(
                    "❌ Backend returned an invalid response."
                )

                st.stop()


        else:

            st.error(
                f"❌ FastAPI prediction failed. "
                f"Status code: {response.status_code}"
            )

            try:
                st.json(response.json())
            except Exception:
                st.text(response.text)

            st.stop()


        # ====================================================
        # DATABASE SAVE CONFIRMATION
        # ====================================================

        st.success(
            f"✅ Prediction saved successfully! "
            f"Prediction ID: {prediction_id}"
        )


        # ====================================================
        # DISPLAY RESULTS
        # ====================================================

        st.markdown("### Prediction Results")


        # ----------------------------------------------------
        # Main Severity Card
        # ----------------------------------------------------

        severity_color = get_severity_color(
            result["severity"]
        )

        confidence_pct = result["confidence"] * 100


        col1, col2, col3 = st.columns([2, 1, 1])


        with col1:

            st.markdown(
                f"""
                <div class="metric-card"
                     style="border-left: 4px solid {severity_color};">

                    <h3 style="
                        margin:0;
                        color:#6b7280;
                        font-size:0.9rem;
                    ">
                        Predicted Severity
                    </h3>

                    <h1 style="
                        margin:0.5rem 0;
                        color:{severity_color};
                        font-size:2.5rem;
                    ">
                        {result['severity']}
                    </h1>

                    <p style="
                        margin:0;
                        color:#6b7280;
                    ">
                        Risk Score:
                        <strong>
                            {result['risk_score']:.1f}/100
                        </strong>
                    </p>

                    <p style="
                        margin:0.4rem 0 0 0;
                        color:#6b7280;
                        font-size:0.85rem;
                    ">
                        Prediction ID:
                        <strong>
                            #{prediction_id}
                        </strong>
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )


        # ----------------------------------------------------
        # Risk Level
        # ----------------------------------------------------

        with col2:

            risk_color = result["risk_color"]

            st.markdown(
                f"""
                <div class="metric-card"
                     style="border-left: 4px solid {risk_color};">

                    <h3 style="
                        margin:0;
                        color:#6b7280;
                        font-size:0.9rem;
                    ">
                        Risk Level
                    </h3>

                    <h2 style="
                        margin:0.5rem 0;
                        color:{risk_color};
                        font-size:2rem;
                    ">
                        {result['risk_level']}
                    </h2>

                </div>
                """,
                unsafe_allow_html=True
            )


        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        with col3:

            if confidence_pct >= 70:

                conf_color = "#10b981"
                conf_text = "High"

            elif confidence_pct >= 50:

                conf_color = "#f59e0b"
                conf_text = "Medium"

            else:

                conf_color = "#ef4444"
                conf_text = "Low"


            st.markdown(
                f"""
                <div class="metric-card"
                     style="border-left: 4px solid {conf_color};">

                    <h3 style="
                        margin:0;
                        color:#6b7280;
                        font-size:0.9rem;
                    ">
                        Model Confidence
                    </h3>

                    <h2 style="
                        margin:0.5rem 0;
                        color:{conf_color};
                        font-size:2rem;
                    ">
                        {confidence_pct:.1f}%
                    </h2>

                    <p style="
                        margin:0;
                        color:#6b7280;
                        font-size:0.85rem;
                    ">
                        {conf_text}
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )


        st.markdown("---")


        # ====================================================
        # PROBABILITY DISTRIBUTION
        # ====================================================

        st.markdown("### Severity Probability Distribution")


        prob_df = pd.DataFrame(
            {
                "Severity": list(
                    result["probabilities"].keys()
                ),

                "Probability": list(
                    result["probabilities"].values()
                )
            }
        )


        chart_data = prob_df.set_index(
            "Severity"
        )


        st.bar_chart(
            chart_data,
            color="#3b82f6",
            height=300
        )


        # ----------------------------------------------------
        # Exact Probabilities
        # ----------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.metric(
                "Low",
                f"{result['probabilities']['Low'] * 100:.1f}%"
            )


        with col2:

            st.metric(
                "Medium",
                f"{result['probabilities']['Medium'] * 100:.1f}%"
            )


        with col3:

            st.metric(
                "High",
                f"{result['probabilities']['High'] * 100:.1f}%"
            )


        with col4:

            st.metric(
                "Critical",
                f"{result['probabilities']['Critical'] * 100:.1f}%"
            )


        st.markdown("---")


        # ====================================================
        # RISK FACTORS
        # ====================================================

        st.markdown("### Key Risk Factors")


        factors = get_risk_factors(
            weather,
            road_condition,
            accident_cause,
            hour,
            is_night
        )


        for factor in factors:

            st.markdown(factor)


        st.markdown("---")


        # ====================================================
        # EMERGENCY PRIORITY
        # ====================================================

        st.markdown(
            "### Emergency Priority Recommendation"
        )


        if result["risk_level"] == "Critical":

            st.error(
                """
                **🚨 CRITICAL PRIORITY** - Immediate emergency response required

                **Recommended Actions:**
                - Call Rescue 1122 immediately
                - Contact Police 15
                - Alert nearest hospital emergency department
                - Prepare for multiple casualties
                - Coordinate traffic diversion
                """
            )


        elif result["risk_level"] == "High":

            st.warning(
                """
                **⚠️ HIGH PRIORITY** - Urgent response needed

                **Recommended Actions:**
                - Call Rescue 1122
                - Contact Police 15
                - Monitor for escalation
                - Prepare emergency services
                """
            )


        elif result["risk_level"] == "Medium":

            st.info(
                """
                **ℹ️ MEDIUM PRIORITY** - Standard response

                **Recommended Actions:**
                - Contact local emergency services
                - Assess situation on ground
                - Report to traffic police
                - Monitor conditions
                """
            )


        else:

            st.success(
                """
                **✅ LOW PRIORITY** - Minor incident

                **Recommended Actions:**
                - Standard reporting procedures
                - Document incident
                - Clear traffic if possible
                - Monitor for changes
                """
            )


        st.markdown("---")


        # ====================================================
        # DISCLAIMER
        # ====================================================

        st.caption(
            """
            **Disclaimer:** This prediction is based on AI analysis of
            general accident patterns. It is not a substitute for
            professional emergency assessment. Always contact official
            emergency services (Rescue 1122, Police 15) for actual incidents.
            """
        )


# ============================================================
# FOOTER
# ============================================================

if HAS_UI:

    render_footer()