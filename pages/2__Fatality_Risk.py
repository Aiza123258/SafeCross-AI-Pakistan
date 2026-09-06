"""
SafeCross AI - Fatality Risk Assessment Page
"""

import streamlit as st
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.predictor import predict_fatality_risk, get_risk_factors

st.set_page_config(page_title="Fatality Risk - SafeCross AI", page_icon="", layout="wide")

try:
    from utils.ui_components import inject_global_css, render_page_header, render_footer, render_sidebar_brand, render_sidebar_about, render_sidebar_nav, render_sidebar_footer, render_top_nav, render_detection_settings_panel
    inject_global_css()
    HAS_UI = True
except ImportError:
    HAS_UI = False

if HAS_UI:
    render_top_nav()
    render_page_header("Fatality Risk Assessment", "Evaluate the probability of fatal outcomes based on accident conditions — decision support only")
else:
    st.markdown("## Fatality Risk Assessment")

with st.sidebar:
    if HAS_UI:
        render_sidebar_brand()
        render_sidebar_about()
        render_sidebar_nav()
        render_detection_settings_panel()
        render_sidebar_footer()

st.markdown("""
<div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
    <strong>Note:</strong> This assessment evaluates the probability of fatal outcomes
    based on accident conditions. It is a decision support tool only - always contact
    Rescue 1122 and Police 15 for actual emergencies.
</div>
""", unsafe_allow_html=True)

# Input form
st.markdown("### Input Accident Conditions")

col1, col2 = st.columns(2)

with col1:
    weather = st.selectbox(
        "Weather Condition",
        ["Clear", "Cloudy", "Rain", "Heavy Rain", "Fog", "Dust Storm"],
        key="fat_weather"
    )
    
    road_condition = st.selectbox(
        "Road Condition",
        ["Dry", "Wet", "Muddy", "Potholed", "Flooding", "Construction"],
        key="fat_road"
    )
    
    accident_cause = st.selectbox(
        "Accident Cause",
        ["Human Error", "Signal Violation", "Weather", "Poor Road", 
         "Mechanical Failure", "Animal Crossing"],
        key="fat_cause"
    )

with col2:
    traffic_density = st.selectbox(
        "Traffic Density",
        ["Light", "Moderate", "Heavy"],
        key="fat_traffic"
    )
    
    vehicles_involved = st.number_input(
        "Vehicles Involved",
        min_value=1,
        max_value=20,
        value=2,
        key="fat_vehicles"
    )
    
    nearby_accidents = st.number_input(
        "Nearby Accidents (within 1km)",
        min_value=0,
        max_value=20,
        value=1,
        key="fat_nearby"
    )

col3, col4 = st.columns(2)

with col3:
    accident_date = st.date_input(
        "Accident Date",
        value=pd.Timestamp.now().date(),
        key="fat_date"
    )

with col4:
    accident_time = st.time_input(
        "Accident Time",
        value=pd.Timestamp.now().time(),
        key="fat_time"
    )

# Calculate derived features
hour = accident_time.hour
day_of_week = pd.Timestamp(accident_date).dayofweek
is_night = 1 if (hour >= 20 or hour < 6) else 0

st.markdown("---")

# Predict button
if st.button("⚠️ Assess Fatality Risk", type="primary", use_container_width=True):
    with st.spinner("Assessing risk..."):
        # Make prediction
        result = predict_fatality_risk(
            weather=weather,
            road_condition=road_condition,
            accident_cause=accident_cause,
            traffic_density=traffic_density,
            vehicles_involved=vehicles_involved,
            nearby_accidents=nearby_accidents,
            hour=hour,
            day_of_week=day_of_week,
            is_night=is_night
        )
        
        # Display results
        st.markdown("### Risk Assessment Results")
        
        # Main risk card
        risk_color = result['risk_color']
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if result['fatality_risk']:
                st.markdown(f"""
                <div class="metric-card critical">
                    <h3 style="margin:0; color: #6b7280; font-size: 0.9rem;">Fatality Risk</h3>
                    <h1 style="margin:0.5rem 0; color: {risk_color}; font-size: 2.5rem;">
                        HIGH RISK
                    </h1>
                    <p style="margin:0; color: #6b7280;">
                        Probability: <strong>{result['probability']*100:.1f}%</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card success">
                    <h3 style="margin:0; color: #6b7280; font-size: 0.9rem;">Fatality Risk</h3>
                    <h1 style="margin:0.5rem 0; color: {risk_color}; font-size: 2.5rem;">
                        LOW RISK
                    </h1>
                    <p style="margin:0; color: #6b7280;">
                        Probability: <strong>{result['probability']*100:.1f}%</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid {risk_color};">
                <h3 style="margin:0; color: #6b7280; font-size: 0.9rem;">Risk Level</h3>
                <h2 style="margin:0.5rem 0; color: {risk_color}; font-size: 2rem;">
                    {result['risk_level']}
                </h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Probability gauge
        st.markdown("### Fatality Probability")
        
        prob_pct = result['probability'] * 100
        
        st.markdown(f"""
        <div style="background: #e5e7eb; border-radius: 10px; padding: 3px; margin: 1rem 0;">
            <div style="background: {risk_color}; width: {prob_pct}%; height: 30px; 
                        border-radius: 8px; display: flex; align-items: center; 
                        justify-content: center; color: white; font-weight: bold;">
                {prob_pct:.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Risk interpretation
        st.markdown("### Risk Interpretation")
        
        if result['probability'] >= 0.75:
            st.error("""
            **Critical Risk Zone** - Very high probability of fatal outcome
            
            The conditions indicate a severe accident scenario with significant 
            risk to life. Immediate emergency response is critical.
            """)
        elif result['probability'] >= 0.50:
            st.warning("""
            **High Risk Zone** - Elevated probability of fatal outcome
            
            The conditions suggest a dangerous accident scenario. Urgent medical 
            attention and emergency response are strongly recommended.
            """)
        elif result['probability'] >= 0.25:
            st.info("""
            **Moderate Risk Zone** - Notable probability of serious outcome
            
            While not immediately critical, the conditions warrant careful monitoring 
            and preparedness for escalation.
            """)
        else:
            st.success("""
            **Low Risk Zone** - Low probability of fatal outcome
            
            The conditions suggest a less severe scenario, though standard emergency 
            protocols should still be followed.
            """)
        
        st.markdown("---")
        
        # Risk factors
        st.markdown("### Contributing Risk Factors")
        factors = get_risk_factors(weather, road_condition, accident_cause, hour, is_night)
        for factor in factors:
            st.markdown(factor)
        
        st.markdown("---")
        
        # Emergency guidance
        st.markdown("### Emergency Response Guidance")
        
        if result['fatality_risk']:
            st.error(f"""
            **🚨 IMMEDIATE ACTION REQUIRED**
            
            1. **Call Rescue 1122** - Request ambulance with trauma team
            2. **Call Police 15** - Report accident with injuries
            3. **Provide first aid** - If trained and safe to do so
            4. **Do not move injured** - Unless in immediate danger
            5. **Secure the scene** - Prevent further accidents
            6. **Guide emergency services** - Provide clear location details
            
            **Critical Information for Emergency Services:**
            - Number of vehicles involved: {vehicles_involved}
            - Weather conditions: {weather}
            - Road conditions: {road_condition}
            - Time of accident: {accident_time}
            """)
        else:
            st.info(f"""
            **Standard Response Recommended**
            
            1. **Assess injuries** - Check all parties involved
            2. **Call for help if needed** - Rescue 1122 or local hospital
            3. **Report to police** - File accident report
            4. **Document the scene** - Take photos for insurance
            5. **Exchange information** - With other parties involved
            
            **Accident Details:**
            - Vehicles involved: {vehicles_involved}
            - Conditions: {weather} / {road_condition}
            - Time: {accident_time}
            """)
        
        st.markdown("---")
        st.caption("""
        **Disclaimer:** This assessment is based on AI analysis of accident patterns. 
        It cannot predict individual outcomes with certainty. Always prioritize human 
        judgment and official emergency services in real situations.
        """)

if HAS_UI:
    render_footer()
