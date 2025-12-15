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

# Database File (Created by agent.py on your laptop)
DB_FILE = "live_incidents.csv"

# 2. DATA LOADING (The Hybrid Logic)
if 'incident_data' not in st.session_state:
    # A. Check if the Agent is running (Laptop Mode)
    if os.path.exists(DB_FILE):
        try:
            st.session_state.incident_data = pd.read_csv(DB_FILE)
            st.toast("🔌 Connected to Autonomous Agent", icon="🤖")
        except:
            st.session_state.incident_data = pd.DataFrame(columns=["ID", "Type", "Title", "Latitude", "Longitude", "Status", "Location"])
    # B. Fallback to Empty State (Cloud/Judge Mode)
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

# Auto-refresh logic (only if file exists)
if os.path.exists(DB_FILE):
    time.sleep(1)
    st.rerun()

# --- INTELLIGENCE LAYER (For Manual Input) ---
def process_report(raw_text):
    geolocator = Nominatim(user_agent="resqnet_hybrid_v1")
    noise_words = ["reported", "massive", "huge", "severe", "major", "fire", "flood", 
                   "accident", "medical", "near", "at", "in", "hyderabad", "breaking"]
    
    clean_text = raw_text.lower()
    for word in noise_words:
        clean_text = clean_text.replace(word, "")
    clean_text = clean_text.strip().split(" ")[0]
    
    try:
        # Assume Hyderabad for the demo
        location = geolocator.geocode(f"{clean_text}, Hyderabad")
        if location:
            # Simple Type Detection
            dtype = "General"
            if "fire" in raw_text.lower(): dtype = "Fire"
            elif "flood" in raw_text.lower(): dtype = "Flood"
            elif "accident" in raw_text.lower(): dtype = "Accident"
            elif "medical" in raw_text.lower(): dtype = "Medical"
            
            return dtype, location.latitude, location.longitude, clean_text.title()
    except:
        return None, None, None, None
    return None, None, None, None

# --- SIDEBAR (Always Active for Judges) ---
with st.sidebar:
    st.header("📡 Command Center")
    
    # Mode Indicator
    if os.path.exists(DB_FILE):
        st.success("🟢 MODE: Autonomous Agent (Laptop)")
        st.caption("Reading from live
