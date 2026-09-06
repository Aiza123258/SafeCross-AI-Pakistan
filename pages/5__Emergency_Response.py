"""
SafeCross AI - Emergency Response Advisor Page
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Emergency Response - SafeCross AI", page_icon="", layout="wide")

try:
    from utils.ui_components import inject_global_css, render_page_header, render_footer, render_sidebar_brand, render_sidebar_about, render_sidebar_nav, render_sidebar_footer, render_top_nav, render_detection_settings_panel
    inject_global_css()
    HAS_UI = True
except ImportError:
    HAS_UI = False

if HAS_UI:
    render_top_nav()
    render_page_header("Emergency Response Advisor", "Scenario-based emergency guidance, first aid protocols, and contact information for Pakistan")
else:
    st.markdown("## Emergency Response Advisor")

with st.sidebar:
    if HAS_UI:
        render_sidebar_brand()
        render_sidebar_about()
        render_sidebar_nav()
        render_detection_settings_panel()
        render_sidebar_footer()

st.info("""
**Note:** This advisor provides general emergency response
guidance based on accident conditions. It does NOT dispatch emergency services.
Always call official emergency numbers for actual incidents.
""")

# Emergency contacts
st.markdown("### :material_phone: Emergency Contact Numbers - Pakistan")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #ef4444;">
        <h3 style="margin:0; color: #6b7280; font-size: 0.9rem;">Ambulance / Rescue</h3>
        <h1 style="margin:0.5rem 0; color: #ef4444; font-size: 3rem;">1122</h1>
        <p style="margin:0; color: #6b7280; font-size: 0.9rem;">Rescue Service (24/7)</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #f59e0b;">
        <h3 style="margin:0; color: #6b7280; font-size: 0.9rem;">Police</h3>
        <h1 style="margin:0.5rem 0; color: #f59e0b; font-size: 3rem;">15</h1>
        <p style="margin:0; color: #6b7280; font-size: 0.9rem;">Emergency Police</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #10b981;">
        <h3 style="margin:0; color: #6b7280; font-size: 0.9rem;">Traffic Police</h3>
        <h1 style="margin:0.5rem 0; color: #10b981; font-size: 3rem;">1915</h1>
        <p style="margin:0; color: #6b7280; font-size: 0.9rem;">Traffic Helpline</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Scenario-based guidance
st.markdown("### :material_emergency: Scenario-Based Response Guidance")

scenario = st.selectbox(
    "Select Accident Scenario",
    [
        "Select a scenario...",
        "Single vehicle accident - Minor",
        "Single vehicle accident - Major",
        "Multi-vehicle accident - No injuries",
        "Multi-vehicle accident - Injuries reported",
        "Accident with fatalities",
        "Accident in adverse weather (Fog/Heavy Rain)",
        "Accident on poor road conditions",
        "Accident during night time"
    ]
)

if scenario != "Select a scenario...":
    st.markdown("---")
    st.markdown(f"### Response Plan: {scenario}")
    
    if "Minor" in scenario and "Single" in scenario:
        st.info("""
        **Priority Level:** LOW to MEDIUM
        
        **Immediate Actions:**
        1. ✅ Ensure personal safety first
        2. ✅ Move vehicle to safe location if possible
        3. ✅ Turn on hazard lights
        4. ✅ Check for injuries (self and others)
        5. ✅ Take photos of damage and scene
        6. ✅ Exchange information with other parties (if any)
        
        **Contact:**
        - Traffic Police 1915 - For accident report
        - Insurance company - For claim processing
        
        **Do NOT:**
        - ❌ Leave the scene without reporting
        - ❌ Admit fault at the scene
        - ❌ Move vehicles before photos (unless blocking traffic dangerously)
        """)
    
    elif "Major" in scenario and "Single" in scenario:
        st.warning("""
        **Priority Level:** HIGH
        
        **Immediate Actions:**
        1. 🚨 Call Rescue 1122 immediately
        2. 🚨 Call Police 15
        3. ✅ Turn on hazard lights
        4. ✅ Set up warning triangles (if available)
        5. ✅ Do NOT move if injured
        6. ✅ Keep others away from vehicle
        7. ✅ Wait for emergency services
        
        **If Others Are Present:**
        - Direct someone to call emergency services
        - Ask witnesses to stay
        - Note down witness contact information
        """)
    
    elif "Multi-vehicle" in scenario and "No injuries" in scenario:
        st.info("""
        **Priority Level:** MEDIUM
        
        **Immediate Actions:**
        1. ✅ Ensure all parties are safe
        2. ✅ Turn on hazard lights for all vehicles
        3. ✅ Move vehicles to safe location if possible
        4. ✅ Call Traffic Police 1915
        5. ✅ Exchange information with all drivers:
           - Name and contact
           - License number
           - Vehicle registration
           - Insurance details
        6. ✅ Take photos of all vehicles and scene
        7. ✅ Get witness information
        
        **Documentation:**
        - Note down all vehicle details
        - Photograph damage from multiple angles
        - Record road and weather conditions
        - Note time and exact location
        """)
    
    elif "Multi-vehicle" in scenario and "Injuries" in scenario:
        st.error("""
        **Priority Level:** HIGH to CRITICAL
        
        **Immediate Actions:**
        1. 🚨 **Call Rescue 1122 FIRST** - Request multiple ambulances
        2. 🚨 **Call Police 15** - Report accident with injuries
        3. ✅ Do NOT move injured people (unless in immediate danger)
        4. ✅ Turn on hazard lights
        5. ✅ Set up warning triangles
        6. ✅ Provide first aid if trained
        7. ✅ Keep injured people conscious and calm
        8. ✅ Direct emergency services to location
        
        **First Aid Priorities:**
        - Check breathing and pulse
        - Control severe bleeding with direct pressure
        - Keep injured people warm
        - Do NOT give food or water
        - Do NOT remove helmets (motorcycle accidents)
        """)
    
    elif "fatalities" in scenario:
        st.error("""
        **Priority Level:** CRITICAL
        
        **Immediate Actions:**
        1. 🚨 **Call Rescue 1122** - Confirm fatalities
        2. 🚨 **Call Police 15** - Report fatal accident
        3. ✅ Do NOT disturb the scene
        4. ✅ Do NOT move bodies
        5. ✅ Secure the area
        6. ✅ Wait for police and forensic team
        7. ✅ Provide statements to police
        
        **Legal Requirements:**
        - Police must investigate fatal accidents
        - Forensic examination required
        - Post-mortem may be ordered
        - Insurance claims require police report
        
        **Do NOT:**
        - ❌ Move anything at the scene
        - ❌ Leave the location
        - ❌ Make statements about fault
        """)
    
    elif "adverse weather" in scenario:
        st.warning("""
        **Priority Level:** MEDIUM to HIGH (depending on severity)
        
        **Weather-Specific Actions:**
        
        **Fog:**
        - Use fog lights and hazard lights
        - Reduce speed significantly
        - Increase following distance
        - Be extra cautious at intersections
        
        **Heavy Rain:**
        - Watch for hydroplaning
        - Avoid flooded areas
        - Use wipers and lights
        - Brake gently to avoid skidding
        
        **Dust Storm:**
        - Pull over safely if visibility is near zero
        - Turn off lights (to avoid rear-end collisions)
        - Keep windows closed
        - Wait for storm to pass
        """)
    
    elif "poor road" in scenario:
        st.warning("""
        **Priority Level:** MEDIUM
        
        **Road Condition Actions:**
        
        **Potholed Roads:**
        - Reduce speed
        - Maintain safe following distance
        - Watch for sudden swerving by other vehicles
        - Avoid sudden braking
        
        **Muddy Roads:**
        - Use lower gears
        - Avoid sudden acceleration or braking
        - Keep steady speed
        - Watch for skidding
        
        **Flooding:**
        - DO NOT drive through flooded areas
        - Turn around, find alternate route
        - If stuck, abandon vehicle and move to high ground
        - Call Rescue 1122 if trapped
        """)
    
    elif "night time" in scenario:
        st.warning("""
        **Priority Level:** MEDIUM to HIGH
        
        **Night-Time Considerations:**
        - Reduced visibility increases risk
        - Emergency response may be slower
        - Location identification is harder
        - Fatigue may be a factor
        
        **Actions:**
        1. ✅ Use all available lights
        2. ✅ Make yourself highly visible
        3. ✅ Use phone flashlight to signal
        4. ✅ Provide detailed location to emergency services
        5. ✅ Stay in vehicle if on highway (safer than walking)
        6. ✅ Lock doors if in unsafe area
        
        **Location Tips for Emergency Services:**
        - Use GPS coordinates from phone
        - Note nearest landmark or mile marker
        - Describe road name and direction
        - Mention cross streets or intersections
        """)

st.markdown("---")

# General first aid
st.markdown("### :material_medical_services: Basic First Aid Guidelines")

with st.expander("Bleeding Control"):
    st.markdown("""
    **For Severe Bleeding:**
    1. Apply direct pressure with clean cloth
    2. Maintain pressure - do not peek
    3. If blood soaks through, add more cloth on top
    4. Elevate injured limb if possible (not if fractured)
    5. Call Rescue 1122 immediately
    
    **Do NOT:**
    - Remove embedded objects
    - Apply tourniquet unless trained
    - Use dirty materials
    """)

with st.expander("Fracture Management"):
    st.markdown("""
    **For Suspected Fractures:**
    1. Do NOT move the injured person
    2. Do NOT try to straighten the limb
    3. Support the injured area in position found
    4. Apply cold pack if available (wrapped in cloth)
    5. Keep person warm and calm
    6. Call Rescue 1122
    
    **Signs of Fracture:**
    - Deformity or unusual angle
    - Swelling and bruising
    - Severe pain
    - Inability to move limb
    - Grinding sensation
    """)

with st.expander("Shock Management"):
    st.markdown("""
    **Recognizing Shock:**
    - Pale, cold, clammy skin
    - Rapid, weak pulse
    - Rapid breathing
    - Confusion or anxiety
    - Nausea
    
    **Treatment:**
    1. Lay person down
    2. Elevate legs 30cm (if no spinal injury suspected)
    3. Keep warm with blankets/coats
    4. Loosen tight clothing
    5. Do NOT give food or water
    6. Reassure and calm the person
    7. Call Rescue 1122
    8. Monitor breathing continuously
    """)

st.markdown("---")

st.success("""
**Remember:** Your safety comes first. Never put yourself in danger to help others.
Call professional emergency services immediately - they are trained and equipped to handle 
these situations.
""")

st.caption("""
**Disclaimer:** This guidance is for informational purposes only and does not replace 
professional medical advice or emergency services. Always follow instructions from 
emergency dispatchers and first responders.
""")

if HAS_UI:
    render_footer()
