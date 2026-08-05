import streamlit as st
from datetime import datetime
import pandas as pd
import requests

# 1. DATABASE CONFIGURATION
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbw0u5gqcy3jsMfiEN1JP7iPJQmwIMbnT5X-dVaIQ40c9l_nkTinIt0F2FbJuO1ND-8k/exec"

st.set_page_config(page_title="Jothen Clinics", layout="centered", page_icon="🏥")

# --- DEMURE & CLEAN UI (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');

    /* Global Body */
    .stApp { background-color: #FDFDFD; font-family: 'Inter', sans-serif; }

    /* Elegant Big Header */
    .main-header {
        font-family: 'Playfair Display', serif;
        font-size: 4.5rem !important;
        font-weight: 700;
        color: #1A1A1A;
        text-align: center;
        margin-bottom: 0px;
        letter-spacing: -2px;
        line-height: 1;
    }
    
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        text-align: center;
        color: #999;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 30px;
    }

    /* Appointment Card Styling */
    .app-card {
        background: white;
        padding: 15px 20px;
        border-radius: 12px;
        margin-bottom: 10px;
        border: 1px solid #F0F0F0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }

    /* Specific Status Colors - HIGH VISIBILITY */
    .bg-Free { background-color: #BDC3C7 !important; color: #1A1A1A !important; }      /* Gray */
    .bg-Booked { background-color: #F1C40F !important; color: #1A1A1A !important; }    /* Yellow */
    .bg-Arrived { background-color: #3498DB !important; color: #FFFFFF !important; }   /* Blue */
    .bg-Done { background-color: #27AE60 !important; color: #FFFFFF !important; }      /* Green */
    .bg-Cancelled { background-color: #E74C3C !important; color: #FFFFFF !important; } /* Red */

    .status-pill {
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }

    /* Minimalist Inputs */
    .stTextInput input {
        border: none !important;
        border-bottom: 1px solid #EEE !important;
        padding: 5px 0px !important;
        font-size: 15px !important;
    }

    /* Hide redundant UI elements */
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    </style>
    """, unsafe_allow_html=True)

# --- DATA HELPERS ---
def load_data():
    try:
        res = requests.get(GOOGLE_URL, timeout=5)
        return res.json()
    except: return {}

if 'clinic_data' not in st.session_state:
    st.session_state.clinic_data = load_data()

def update_entry(s_id):
    st.session_state.clinic_data[s_id] = {
        "name": st.session_state[f"n_{s_id}"],
        "phone": st.session_state[f"p_{s_id}"],
        "status": st.session_state[f"s_{s_id}"]
    }

# --- HEADER ---
st.markdown("<div class='main-header'>Jothen</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Clinics • Patient Management</div>", unsafe_allow_html=True)

# Top Bar
c1, c2 = st.columns([2, 1])
with c1:
    clinic_date = st.date_input("Date", datetime.now(), label_visibility="collapsed")
with c2:
    if st.button("SYNC TO CLOUD", use_container_width=True):
        try:
            requests.post(GOOGLE_URL, json=st.session_state.clinic_data, timeout=8)
            st.toast("Database Synced", icon="☁️")
        except: st.error("Sync Error")

# --- NAVIGATION TABS ---
tab_edit, tab_summary = st.tabs(["📝 MANAGEMENT", "📋 DAILY SUMMARY"])

slots = ["12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM", "06:00 PM", "06:30 PM", "07:00 PM", "07:30 PM", "08:00 PM", "08:30 PM", "09:00 PM", "09:30 PM", "10:00 PM"]

# --- TAB 1: EDIT SLOTS ---
with tab_edit:
    for slot in slots:
        s_id = f"{slot}_{clinic_date}"
        entry = st.session_state.clinic_data.get(s_id, {"name": "", "phone": "", "status": "Free"})
        
        st.markdown(f"""
            <div class="app-card">
                <span class="status-pill bg-{entry['status']}">{slot} • {entry['status']}</span>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 3, 2])
        with col1:
            st.text_input("Name", value=entry["name"], key=f"n_{s_id}", placeholder="Patient Name", label_visibility="collapsed", on_change=update_entry, args=(s_id,))
        with col2:
            st.text_input("Phone", value=entry["phone"], key=f"p_{s_id}", placeholder="Phone", label_visibility="collapsed", on_change=update_entry, args=(s_id,))
        with col3:
            st.selectbox("Status", options=["Free", "Booked", "Arrived", "Done", "Cancelled"], 
                        index=["Free", "Booked", "Arrived", "Done", "Cancelled"].index(entry["status"]),
                        key=f"s_{s_id}", label_visibility="collapsed", on_change=update_entry, args=(s_id,))
        st.markdown("<div style='margin-bottom:15px'></div>", unsafe_allow_html=True)

# --- TAB 2: SUMMARY VIEW ---
with tab_summary:
    summary_list = []
    for slot in slots:
        s_id = f"{slot}_{clinic_date}"
        e = st.session_state.clinic_data.get(s_id, {"name": "", "phone": "", "status": "Free"})
        summary_list.append({
            "Time": slot,
            "Patient Name": e["name"] if e["name"] else "—",
            "Contact": e["phone"] if e["phone"] else "—",
            "Status": e["status"]
        })
    
    df = pd.DataFrame(summary_list)

    def color_status(val):
        colors = {
            'Free': 'background-color: #BDC3C7; color: black;',
            'Booked': 'background-color: #F1C40F; color: black;',
            'Arrived': 'background-color: #3498DB; color: white;',
            'Done': 'background-color: #27AE60; color: white;',
            'Cancelled': 'background-color: #E74C3C; color: white;'
        }
        return colors.get(val, '')

    st.markdown("### Daily Overview")
    st.table(df.style.applymap(color_status, subset=['Status']))
