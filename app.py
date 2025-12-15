import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import os
import time

# 1. SETUP
st.set_page_config(page_title="ResQ-Net Operations", layout="wide")
st.title("ResQ-Net Live Operations 🚁")

# Database File
DB_FILE = "live_incidents.csv"

# 2. DATA LOADING
if 'incident_data' not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            st.session_state.incident_data = pd.read_csv(DB_FILE)
            st.toast("🔌 Connected to Autonomous Agent", icon="🤖")
        except:
            st.session_state.incident_data = pd.DataFrame(columns=["ID", "Type", "Title", "Latitude", "Longitude", "Status", "Location"])
    else:
        st.session_state.incident_data = pd.DataFrame({
            'ID': [101, 102],
            'Type': ['Fire', 'Medical'],
            'Title': ['Manual Report', 'Manual Report'],
            'Latitude': [17.3850, 17.4000],
            'Longitude': [78.4867, 78.4900],
            'Status': [False, False],
            'Location': ['Charminar', 'Nampally']
        })

# Auto-refresh logic
if os.path.exists(DB_FILE):
    time.sleep(1)
    st.rerun()

# --- INTELLIGENCE LAYER (Improved) ---
def process_report(raw_text):
    # 1. Update User Agent to avoid timeouts
    geolocator = Nominatim(user_agent="resqnet_hybrid_fix_v2")
    
    # 2. Expanded list of noise words to remove
    noise_words = ["reported", "massive", "huge", "severe", "major", "fire", "flood", 
                   "accident", "medical", "near", "at", "in", "hyderabad", "breaking", 
                   "emergency", "help", "please", "located", "area"]
    
    clean_text = raw_text.lower()
    for word in noise_words:
        clean_text = clean_text.replace(word, "")
    
    # 3. FIX: Don't split! Keep the whole string (e.g., "Jubilee Hills")
    clean_text = clean_text.strip().replace("  ", " ")
    
    # Safety check: If text is too short (e.g., just " "), return None
    if len(clean_text) < 3:
        return None, None, None, None
    
    try:
        # Search specifically in Hyderabad
        location = geolocator.geocode(f"{clean_text}, Hyderabad")
        
        if location:
            # Detect Type
            dtype = "General"
            if "fire" in raw_text.lower(): dtype = "Fire"
            elif "flood" in raw_text.lower(): dtype = "Flood"
            elif "accident" in raw_text.lower(): dtype = "Accident"
            elif "medical" in raw_text.lower(): dtype = "Medical"
            
            return dtype, location.latitude, location.longitude, clean_text.title()
    except:
        return None, None, None, None
        
    return None, None, None, None

# --- SIDEBAR ---
with st.sidebar:
    st.header("📡 Command Center")
    
    # Mode Indicator
    if os.path.exists(DB_FILE):
        st.success("🟢 MODE: Autonomous Agent (Laptop)")
        st.caption("Reading from live_incidents.csv")
    else:
        st.info("🔵 MODE: Manual / Cloud (Judges)")
        st.caption("Agent script not detected. Manual entry enabled.")

    st.divider()
    
    # Manual Entry Tool
    st.write("**📝 Manually Report Incident:**")
    report_input = st.text_input("Report:", placeholder="e.g., Fire at Gachibowli")
    
    if st.button("📢 Dispatch Team"):
        if report_input:
            dtype, lat, lon, loc_name = process_report(report_input)
            if lat:
                new_row = pd.DataFrame({
                    "ID": [len(st.session_state.incident_data) + 101],
                    "Type": [dtype],
                    "Title": [report_input],
                    "Latitude": [lat],
                    "Longitude": [lon],
                    "Status": [False],
                    "Location": [loc_name]
                })
                # Update State
                st.session_state.incident_data = pd.concat([st.session_state.incident_data, new_row], ignore_index=True)
                
                # Show Success & Refresh
                st.success(f"✅ Dispatched: {dtype} at {loc_name}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Location not found. Try 'Fire at [Place Name]'.")

# --- MAIN DASHBOARD LAYOUT ---
col1, col2 = st.columns([1, 2], gap="medium")

with col1:
    st.subheader("📝 Incident Log")
    if os.path.exists(DB_FILE):
        try:
            current_df = pd.read_csv(DB_FILE)
            st.dataframe(current_df, use_container_width=True, hide_index=True)
        except:
            st.write("Waiting for data...")
    else:
        edited_df = st.data_editor(
            st.session_state.incident_data,
            column_config={
                "Status": st.column_config.CheckboxColumn("Resolved?", default=False),
                "Latitude": None, "Longitude": None
            },
            disabled=["ID", "Type", "Title", "Location"],
            hide_index=True,
            use_container_width=True
        )
        st.session_state.incident_data = edited_df

with col2:
    st.subheader("📍 Live Map")
    if not st.session_state.incident_data.empty:
        map_data = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else st.session_state.incident_data
        
        if not map_data.empty:
            center_lat = map_data['Latitude'].mean()
            center_lon = map_data['Longitude'].mean()
        else:
            center_lat, center_lon = 17.3850, 78.4867
            
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

        for _, row in map_data.iterrows():
            if row['Type'] == 'Fire': color = 'red'
            elif row['Type'] == 'Flood': color = 'blue'
            elif row['Type'] == 'Medical': color = 'green'
            elif row['Type'] == 'Accident': color = 'orange'
            else: color = 'gray'

            is_resolved = str(row['Status']).lower() == 'true'
            
            if is_resolved:
                folium.CircleMarker(
                    [row['Latitude'], row['Longitude']], radius=5, color='gray', fill_opacity=0.2,
                    popup=f"✅ RESOLVED: {row['Location']}"
                ).add_to(m)
            else:
                folium.Marker(
                    [row['Latitude'], row['Longitude']],
                    popup=f"🚨 {row['Type']}\n📍 {row['Location']}",
                    icon=folium.Icon(color=color, icon="info-sign")
                ).add_to(m)
        
        st_folium(m, use_container_width=True, height=500)
    else:
        st.write("No active incidents.")

