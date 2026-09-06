"""
SafeCross AI - Prediction History Page
"""

import streamlit as st
import requests
from utils.backend_server import ensure_backend_running
import pandas as pd

st.set_page_config(
    page_title="Prediction History - SafeCross AI",
    page_icon="📋",
    layout="wide"
)

# API URL
API_URL = "http://127.0.0.1:8000"

# Load UI components
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


# Top navigation
if HAS_UI:
    render_top_nav()
    render_page_header(
        "Prediction History",
        "View previously generated AI accident severity predictions"
    )
else:
    st.title("📋 Prediction History")


# Sidebar
with st.sidebar:
    if HAS_UI:
        render_sidebar_brand()
        render_sidebar_about()
        render_sidebar_nav()
        render_detection_settings_panel()
        render_sidebar_footer()


st.markdown("---")

st.markdown("### :material/history: Previous Severity Predictions")


# Get predictions from backend
try:
    ensure_backend_running()
    response = requests.get(
        f"{API_URL}/predictions",
        timeout=10
    )

    if response.status_code == 200:

        data = response.json()

        predictions = data.get("predictions", [])

        if predictions:

            st.success(
                f"✅ {len(predictions)} prediction(s) found in database."
            )

            # Convert to DataFrame
            df = pd.DataFrame(predictions)

            # Rename columns
            df = df.rename(columns={
                "id": "Prediction ID",
                "severity": "Severity",
                "confidence": "Confidence",
                "created_at": "Created At"
            })

            # Convert confidence to percentage
            if "Confidence" in df.columns:
                df["Confidence"] = (
                    df["Confidence"] * 100
                ).round(1).astype(str) + "%"

            # Display table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            # Individual prediction cards
            st.markdown("### :material/analytics: Prediction Details")

            for prediction in predictions:

                prediction_id = prediction.get("id")
                severity = prediction.get("severity", "Unknown")
                confidence = prediction.get("confidence", 0) * 100
                created_at = prediction.get("created_at", "")

                if severity == "Critical":
                    icon = "🚨"
                elif severity == "High":
                    icon = "⚠️"
                elif severity == "Medium":
                    icon = "🟡"
                else:
                    icon = "🟢"

                with st.expander(
                    f"{icon} Prediction #{prediction_id} — {severity}"
                ):

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Prediction ID",
                            prediction_id
                        )

                    with col2:
                        st.metric(
                            "Severity",
                            severity
                        )

                    with col3:
                        st.metric(
                            "Confidence",
                            f"{confidence:.1f}%"
                        )

                    st.caption(
                        f"Created: {created_at}"
                    )

        else:

            st.info(
                "No predictions found yet. "
                "Make a prediction from the Severity Predictor page first."
            )

    else:

        st.error(
            f"Backend returned error: {response.status_code}"
        )


except requests.exceptions.ConnectionError:

    st.error(
        "❌ Cannot connect to backend."
    )

    st.info(
        "FastAPI backend is being started automatically on this deployment."
    )

except Exception as e:

    st.error(
        f"❌ Error loading prediction history: {e}"
    )


# Footer
if HAS_UI:
    render_footer()