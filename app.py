import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import re

# 1. SETUP: Wide layout
st.set_page_config(page_title="ResQ-Net Operations", layout="wide")
st.title("ResQ-Net Live Operations 🚁")

# 2. DATA: Initialize Session State
if 'incident_data' not in st.session_state:
    st.session_state.incident_data = pd.DataFrame({
        'ID': [101, 102],
        'Type': ['Fire', 'Medical'],
        'Latitude': [17.3616, 17.3900], # Charminar Coords
        'Longitude': [78.4747, 78.4750],
        'Status': [False, False], # False = Active
        'Location': ['Charminar', 'Nampally']
    })

# --- INTELLIGENCE LAYER (Now with Noise Removal) ---
def process_report(raw_text):
    """
    1. Detects Disaster Type.
    2. Cleans text to find just the Location name.
    3. Geocodes the clean location.
    """
    raw_text_lower = raw_text.lower()
    
    # A. Keyword Detection
    detected_type = "General"
    if "fire" in raw_text_lower or "flame" in raw_text_lower: detected_type = "Fire"
    elif "flood" in raw_text_lower or "water" in raw_text_lower: detected_type = "Flood"
    elif "medical" in raw_text_lower or "injured" in raw_text_lower: detected_type = "Medical"
    elif "accident" in raw_text_lower or "crash" in raw_text_lower: detected_type = "Accident"
    elif "collapse" in raw_text_lower: detected_type = "Collapse"

    # B. Smart Text Cleaning (The FIX)
    # Remove common "noise" words to isolate the location
    noise_words = [
        "massive", "reported", "near", "at", "huge", "severe", "major", 
        "fire", "flood", "accident", "medical", "emergency", "help", "please"
    ]
    
    clean_text = raw_text_lower
    for word in noise_words:
        clean_text = clean_text.replace(word, "")
    
    # Remove extra spaces and special chars
    clean_text = clean_text.strip().replace("  ", " ")
    
    # C. Geocoding
    geolocator = Nominatim(user_agent="resqnet_hackathon_agent_v2") # Updated User Agent
    
    try:
        # Try finding the specific location + City
        # We assume the user is in Hyderabad for the hackathon context
        search_query = f"{clean_text}, Hyderabad"
        location = geolocator.geocode(search_query)
        
        if location:
            return detected_type, location.latitude, location.longitude, location.address
        else:
            return None, None, None, None
    except:
        return None, None, None, None

# --- SIDEBAR: LIVE MONITORING CHANNEL ---
with st.sidebar:
    st.header("📡 Live Monitoring Channel")
    st.info("💡 Tip: You can now type full sentences!")
    
    # The Input for the Agent
    report_input = st.text_area(
        "Incoming Message:", 
        placeholder="e.g., 'Massive fire reported near Golconda Fort'"
    )
    
    if st.button("📢 ANALYZE & DISPATCH", type="primary"):
        if report_input:
            with st.spinner("🤖 AI Agent analyzing text..."):
                # Run the AI logic
                d_type, lat, lon, address = process_report(report_input)
                
                if lat and lon:
                    # Add to database
                    new_id = st.session_state.incident_data['ID'].max() + 1
                    new_row = pd.DataFrame({
                        'ID': [new_id],
                        'Type': [d_type],
                        'Latitude': [lat],
                        'Longitude': [lon],
                        'Status': [False],
                        'Location': [address.split(",")[0]]
                    })
                    st.session_state.incident_data = pd.concat(
                        [st.session_state.incident_data, new_row], ignore_index=True
                    )
                    st.success(f"✅ DISPATCHED: {d_type} team to {address.split(',')[0]}")
                else:
                    st.error(f"❌ Could not find location in: '{report_input}'. Try typing just the place name.")

# 3. LAYOUT: Columns
col1, col2 = st.columns([1, 2], gap="medium")

# --- LEFT: INCIDENT LIST ---
with col1:
    st.subheader("📝 Incident Log")
    edited_df = st.data_editor(
        st.session_state.incident_data,
        column_config={
            "Status": st.column_config.CheckboxColumn("Done?", default=False),
            "Latitude": None, "Longitude": None,
            "ID": st.column_config.NumberColumn("ID", width="small")
        },
        disabled=["ID", "Type", "Location"],
        hide_index=True,
        use_container_width=True
    )
    st.session_state.incident_data = edited_df

    # Statistics
    active_incidents = edited_df[edited_df['Status'] == False]
    st.metric("⚠️ Active Emergencies", len(active_incidents))

# --- RIGHT: MAP ---
with col2:
    st.subheader("📍 Live Geospatial View")
    
    # Dynamic Map Center
    if not active_incidents.empty:
        center_lat = active_incidents['Latitude'].mean()
        center_lon = active_incidents['Longitude'].mean()
        zoom = 12
    else:
        center_lat, center_lon, zoom = 17.3850, 78.4867, 12

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)

    # Plot Markers
    for index, row in edited_df.iterrows():
        # Icons & Colors
        if row['Type'] == 'Fire': color, icon = 'red', 'fire'
        elif row['Type'] == 'Flood': color, icon = 'blue', 'water'
        elif row['Type'] == 'Medical': color, icon = 'green', 'heart'
        elif row['Type'] == 'Accident': color, icon = 'orange', 'car'
        else: color, icon = 'gray', 'info-sign'

        if row['Status']:
            # Resolved Style
            folium.CircleMarker(
                [row['Latitude'], row['Longitude']], radius=5, color='gray', fill=True, fill_opacity=0.2,
                popup=f"✅ RESOLVED: {row['Location']}"
            ).add_to(m)
        else:
            # Active Style
            folium.Marker(
                [row['Latitude'], row['Longitude']],
                popup=f"🚨 {row['Type']}\n📍 {row['Location']}",
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(m)

    st_folium(m, use_container_width=True, height=550)