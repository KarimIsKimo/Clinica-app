import streamlit as st
from datetime import datetime
import pandas as pd
import requests

# 1. DATABASE CONFIGURATION
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbw0u5gqcy3jsMfiEN1JP7iPJQmwIMbnT5X-dVaIQ40c9l_nkTinIt0F2FbJuO1ND-8k/exec"

st.set_page_config(page_title="Jothen Clinics Sync", layout="centered", page_icon="🏥")

# --- PROFESSIONAL UI CLEANUP (CSS) ---
st.markdown("""
    <style>
    /* Overall Background and Font */
    .stApp { background-color: #F8F9FA; font-family: 'Inter', sans-serif; }
    
    /* Global Text Color */
    p, span, label { color: #2D3436 !important; font-size: 14px; }

    /* Header Styling */
    .main-header {
        text-align: center;
        color: #2C3E50;
        padding: 10px;
        font-weight: 800;
        letter-spacing: -1px;
    }

    /* Card Styling */
    .appointment-row {
        background: white;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #EDF2F7;
    }

    /* Smart Contrast Badges */
    .badge {
        padding: 5px 12px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
        font-size: 13px !important;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    /* Exact Color Logic with High-Contrast Text */
    .bg-Free { background-color: #BDC3C7; color: #2D3436 !important; }      /* Gray - Black Text */
    .bg-Booked { background-color: #F1C40F; color: #2D3436 !important; }    /* Yellow - Black Text */
    .bg-Arrived { background-color: #3498DB; color: #FFFFFF !important; }   /* Blue - White Text */
    .bg-Done { background-color: #27AE60; color: #FFFFFF !important; }      /* Green - White Text */
    .bg-Cancelled { background-color: #E74C3C; color: #FFFFFF !important; } /* Red - White Text */

    /* Clean Input Fields */
    .stTextInput input {
        border-radius: 8px !important;
        border: 1px solid #D1D5DB !important;
        background: #FFFFFF !important;
    }

    /* Compact Radio Buttons */
    div[data-testid="stRadio"] > div { gap: 6px; }
    div[data-testid="stRadio"] label { 
        background-color: #FFFFFF; 
        border: 1px solid #E2E8F0; 
        padding: 4px 10px !important; 
        border-radius: 20px !important; 
        font-size: 11px !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA HELPERS ---
def load_cloud_data():
    try:
        res = requests.get(GOOGLE_URL, timeout=5)
        return res.json()
    except: return {}

if 'clinic_data' not in st.session_state:
    st.session_state.clinic_data = load_cloud_data()

def update_entry(s_id):
    st.session_state.clinic_data[s_id] = {
        "name": st.session_state[f"n_{s_id}"],
        "phone": st.session_state[f"p_{s_id}"],
        "status": st.session_state[f"s_{s_id}"]
    }

# --- HEADER SECTION ---
st.markdown("<h1 class='main-header'>🏥 Jothen Clinics</h1>", unsafe_allow_html=True)

# Action Bar
top_c1, top_c2 = st.columns([1, 1])
with top_c1:
    view_mode = st.radio("Display View:", ["📝 Edit Slots", "📋 Quick Summary"], horizontal=True, label_visibility="collapsed")
with top_c2:
    if st.button("💾 SYNC TO CLOUD", use_container_width=True):
        try:
            requests.post(GOOGLE_URL, json=st.session_state.clinic_data, timeout=8)
            st.toast("✅ Cloud Update Successful")
        except: st.error("⚠️ Connection Error")

clinic_date = st.date_input("Date Selection", datetime.now())
slots = ["12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM", "06:00 PM", "06:30 PM", "07:00 PM", "07:30 PM", "08:00 PM", "08:30 PM", "09:00 PM", "09:30 PM", "10:00 PM"]

# --- VIEW 1: QUICK SUMMARY (EASY ALL-IN-ONE VIEW) ---
if "Quick Summary" in view_mode:
    summary_data = []
    for slot in slots:
        s_id = f"{slot}_{clinic_date}"
        entry = st.session_state.clinic_data.get(s_id, {"name": "", "phone": "", "status": "Free"})
        summary_data.append({
            "Time": slot,
            "Patient": entry["name"] if entry["name"] else "—",
            "Contact": entry["phone"] if entry["phone"] else "—",
            "Status": entry["status"]
        })
    
    df = pd.DataFrame(summary_data)

    def style_table(val):
        colors = {
            'Free': 'background-color: #BDC3C7; color: black; font-weight: bold',
            'Booked': 'background-color: #F1C40F; color: black; font-weight: bold',
            'Arrived': 'background-color: #3498DB; color: white; font-weight: bold',
            'Done': 'background-color: #27AE60; color: white; font-weight: bold',
            'Cancelled': 'background-color: #E74C3C; color: white; font-weight: bold'
        }
        return colors.get(val, '')

    try:
        styled_df = df.style.map(style_table, subset=['Status'])
    except AttributeError:
        styled_df = df.style.applymap(style_table, subset=['Status'])

    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=750)

# --- VIEW 2: EDIT SLOTS (MANAGEMENT VIEW) ---
else:
    for slot in slots:
        s_id = f"{slot}_{clinic_date}"
        entry = st.session_state.clinic_data.get(s_id, {"name": "", "phone": "", "status": "Free"})
        cur_status = st.session_state.get(f"s_{s_id}", entry["status"])

        # Row Wrapper
        st.markdown(f'''
            <div class="appointment-row">
                <div class="badge bg-{cur_status}">{slot} | {cur_status}</div>
            </div>
        ''', unsafe_allow_html=True)

        # Inputs
        n_col, p_col = st.columns(2)
        with n_col:
            st.text_input("Name", value=entry["name"], key=f"n_{s_id}", 
                         placeholder="Patient Name", label_visibility="collapsed", 
                         on_change=update_entry, args=(s_id,))
        with p_col:
            st.text_input("Phone", value=entry["phone"], key=f"p_{s_id}", 
                         placeholder="Phone Number", label_visibility="collapsed", 
                         on_change=update_entry, args=(s_id,))
        
        # Status Picker
        st.radio(f"rad_{s_id}", options=["Free", "Booked", "Arrived", "Done", "Cancelled"], 
                 index=["Free", "Booked", "Arrived", "Done", "Cancelled"].index(entry["status"]),
                 key=f"s_{s_id}", horizontal=True, label_visibility="collapsed", 
                 on_change=update_entry, args=(s_id,))
        
        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
