"""
SafeCross AI - Accident Hotspot Map Page
"""

import streamlit as st
import sys
import os
import pandas as pd
import folium
from streamlit_folium import st_folium

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_training_data_sample

st.set_page_config(page_title="Hotspot Map - SafeCross AI", page_icon="", layout="wide")

try:
    from utils.ui_components import inject_global_css, render_page_header, render_footer, render_sidebar_brand, render_sidebar_about, render_sidebar_nav, render_sidebar_footer, render_top_nav, render_detection_settings_panel
    inject_global_css()
    HAS_UI = True
except ImportError:
    HAS_UI = False

if HAS_UI:
    render_top_nav()
    render_page_header("Accident Hotspot Map", "Interactive visualization of accident patterns from model training data")
else:
    st.markdown("## Accident Hotspot Map")

with st.sidebar:
    if HAS_UI:
        render_sidebar_brand()
        render_sidebar_about()
        render_sidebar_nav()
        render_detection_settings_panel()
        render_sidebar_footer()

st.info("""
**Note:** This map displays accident patterns from the model training dataset.
These are **not verified Pakistani accident locations**. The map is for visualization
of model-data patterns only.
""")

# Load data
df = load_training_data_sample()

# Filters
st.markdown("### Map Filters")

col1, col2, col3 = st.columns(3)

with col1:
    severity_filter = st.multiselect(
        "Filter by Severity",
        options=sorted(df['severity'].unique()),
        default=sorted(df['severity'].unique()),
        help="Show accidents of selected severity levels"
    )

with col2:
    weather_filter = st.multiselect(
        "Filter by Weather",
        options=sorted(df['weather'].unique()),
        default=sorted(df['weather'].unique())[:3],
        help="Show accidents in selected weather conditions"
    )

with col3:
    max_points = st.slider(
        "Number of Points to Display",
        min_value=100,
        max_value=5000,
        value=2000,
        step=100,
        help="Limit number of points for performance"
    )

# Filter data
filtered_df = df[
    (df['severity'].isin(severity_filter)) &
    (df['weather'].isin(weather_filter))
].head(max_points)

if len(filtered_df) == 0:
    st.warning("No data available for the selected filters.")
    st.stop()

st.info(f"**Displaying {len(filtered_df):,} accident records**")

# Create map centered on South Asia
m = folium.Map(
    location=[25.0, 75.0],  # Centered on Pakistan/India region
    zoom_start=5,
    tiles='OpenStreetMap'
)

# Color mapping for severity
severity_colors = {
    'Low': 'green',
    'Medium': 'orange',
    'High': 'red',
    'Critical': 'darkred'
}

# Add markers
for idx, row in filtered_df.iterrows():
    color = severity_colors.get(row['severity'], 'blue')
    
    popup_html = f"""
    <div style="font-family: Arial; min-width: 200px;">
        <h4 style="margin: 0 0 10px 0; color: {color};">
            {row['severity']} Severity
        </h4>
        <p style="margin: 5px 0;"><strong>Weather:</strong> {row['weather']}</p>
        <p style="margin: 5px 0;"><strong>Road:</strong> {row['road_condition']}</p>
        <p style="margin: 5px 0;"><strong>Cause:</strong> {row['accident_cause']}</p>
        <p style="margin: 5px 0;"><strong>Injuries:</strong> {row['injuries']}</p>
        <p style="margin: 5px 0;"><strong>Fatalities:</strong> {row['fatalities']}</p>
    </div>
    """
    
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=5,
        popup=folium.Popup(popup_html, max_width=300),
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        weight=1
    ).add_to(m)

# Display map
st_folium(m, width=None, height=600, returned_objects=[])

st.markdown("---")

# Statistics
st.markdown("### Hotspot Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Severity Distribution**")
    severity_counts = filtered_df['severity'].value_counts()
    for severity, count in severity_counts.items():
        st.write(f"**{severity}**: {count:,} ({count/len(filtered_df)*100:.1f}%)")

with col2:
    st.markdown("**Top Weather Conditions**")
    weather_counts = filtered_df['weather'].value_counts().head(5)
    for weather, count in weather_counts.items():
        st.write(f"{weather}: {count:,}")

with col3:
    st.markdown("**Top Road Conditions**")
    road_counts = filtered_df['road_condition'].value_counts().head(5)
    for road, count in road_counts.items():
        st.write(f"{road}: {count:,}")

st.markdown("---")

# Geographic bounds
st.markdown("### Geographic Coverage")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    **Latitude Range:**
    - Min: {filtered_df['latitude'].min():.4f}
    - Max: {filtered_df['latitude'].max():.4f}
    - Mean: {filtered_df['latitude'].mean():.4f}
    """)

with col2:
    st.markdown(f"""
    **Longitude Range:**
    - Min: {filtered_df['longitude'].min():.4f}
    - Max: {filtered_df['longitude'].max():.4f}
    - Mean: {filtered_df['longitude'].mean():.4f}
    """)

st.caption("""
**Disclaimer:** This visualization uses model training data for demonstration purposes.
The coordinates shown are from the general accident pattern dataset and do not represent
verified Pakistani accident locations. For Pakistan-specific data, refer to the 
Pakistan Dashboard page.
""")

if HAS_UI:
    render_footer()
