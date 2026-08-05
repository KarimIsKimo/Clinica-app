import streamlit as st
from datetime import datetime
import pandas as pd
import requests

# 1. DATABASE CONFIGURATION
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbw0u5gqcy3jsMfiEN1JP7iPJQmwIMbnT5X-dVaIQ40c9l_nkTinIt0F2FbJuO1ND-8k/exec"

st.set_page_config(page_title="Jothen Clinics", layout="centered", page_icon="🏥")

# --- DEMURE & SOPHISTICATED UI (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');

    /* Background and Global Font */
    .stApp { background-color: #FDFDFD; font-family: 'Inter', sans-serif; }

    /* Massive Elegant Header */
    .main-header {
        font-family: 'Playfair Display', serif;
        font-size: 5rem !important;
        font-weight: 700;
        color: #1A1A1A;
        text-align: center;
        margin-top: -30px;
        margin-bottom: 0px;
        letter-spacing: -3px;
        line-height: 1;
    }
    
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        text-align: center;
        color: #A0A0A0;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-bottom: 40px;
    }

    /* Appointment Card Styling */
    .app-card {
        background: white;
        padding: 18px;
        border-radius: 15px;
        margin-bottom: 12px;
        border: 1px solid #F5F5F5;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }

    /* High-Contrast Status Badges */
    .status-pill {
        padding: 5px 15px;
        border-radius: 30px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 10px;
    }

    /* Background Colors & Text Contrast Fix */
    .bg-Free { background-color: #BDC3C7 !important; color: #1A1A1A !important; }      /* Dark Gray Text */
    .bg-Booked { background-color: #F1C40F !important; color: #1A1A1A !important; }    /* Dark Gray Text */
    .bg-Arrived { background-color: #3498DB !important; color: #FFFFFF !important; }   /* White Text */
    .bg-Done { background-color: #27AE60 !important; color: #FFFFFF !important; }      /* White Text */
    .bg-Cancelled { background-color: #E74C3C !important; color: #FFFFFF !important; } /* White Text */

    /* Minimalist Inputs */
    .stTextInput input {
        border: none !important;
        border-bottom: 1px solid #EEE !important;
        padding: 5px 0px !important;
        font-size: 15px !important;
        background-color: transparent !important;
    }
    
    /* Clean Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 40px; 
        background-color: transparent !important; 
        border: none !important; 
        font-size: 14px;
        font-weight: 600;
    }
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

# --- HEADER SECTION ---
st.markdown("<div class='main-header'>Jothen</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Clinics • Est. 2024</div>", unsafe_allow_html=True)

# Actions Row
top_left, top_right = st.columns([2, 1])
with top_left:
    clinic_date = st.date_input("Schedule Date", datetime.now(), label_visibility="collapsed")
with top_right:
    if st.button("SAVE TO CLOUD", use_container_width=True):
        try:
            requests.post(GOOGLE_URL, json=st.session_state.clinic_data, timeout=8)
            st.toast("Sync Complete", icon="✨")
        except: st.error("Connection lost")

# --- MAIN INTERFACE (TABS) ---
tab_manage, tab_summary = st.tabs(["📝 MANAGEMENT", "📋 VIEW SUMMARY"])

slots = ["12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM", "06:00 PM", "06:30 PM", "07:00 PM", "07:30 PM", "08:00 PM", "08:30 PM", "09:00 PM", "09:30 PM", "10:00 PM"]

# --- TAB 1: MANAGEMENT ---
with tab_manage:
    for slot in slots:
        s_id = f"{slot}_{clinic_date}"
        entry = st.session_state.clinic_data.get(s_id, {"name": "", "phone": "", "status": "Free"})
        
        # Display Card with Status Color
        st.markdown(f"""
            <div class="app-card">
                <span class="status-pill bg-{entry['status']}">{slot} &nbsp;•&nbsp; {entry['status']}</span>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([3, 3, 2])
        with c1:
            st.text_input("Name", value=entry["name"], key=f"n_{s_id}", placeholder="Patient Name", label_visibility="collapsed", on_change=update_entry, args=(s_id,))
        with c2:
            st.text_input("Phone", value=entry["phone"], key=f"p_{s_id}", placeholder="Contact Number", label_visibility="collapsed", on_change=update_entry, args=(s_id,))
        with c3:
            st.selectbox("Status", options=["Free", "Booked", "Arrived", "Done", "Cancelled"], 
                        index=["Free", "Booked", "Arrived", "Done", "Cancelled"].index(entry["status"]),
                        key=f"s_{s_id}", label_visibility="collapsed", on_change=update_entry, args=(s_id,))
        st.markdown("<div style='margin-bottom:20px'></div>", unsafe_allow_html=True)

# --- TAB 2: SUMMARY VIEW (FIXED) ---
with tab_summary:
    summary_list = []
    for slot in slots:
        s_id = f"{slot}_{clinic_date}"
        e = st.session_state.clinic_data.get(s_id, {"name": "", "phone": "", "status": "Free"})
        summary_list.append({
            "Time": slot,
            "Patient": e["name"] if e["name"] else "—",
            "Contact": e["phone"] if e["phone"] else "—",
            "Status": e["status"]
        })
    
    df = pd.DataFrame(summary_list)

    # Styling function for the table
    def style_rows(val):
        colors = {
            'Free': 'background-color: #BDC3C7; color: black; font-weight: bold;',
            'Booked': 'background-color: #F1C40F; color: black; font-weight: bold;',
            'Arrived': 'background-color: #3498DB; color: white; font-weight: bold;',
            'Done': 'background-color: #27AE60; color: white; font-weight: bold;',
            'Cancelled': 'background-color: #E74C3C; color: white; font-weight: bold;'
        }
        return colors.get(val, '')

    st.markdown("### Daily Overview")
    
    # FIXED: Using a compatibility check for applymap/map
    if hasattr(df.style, 'map'):
        styled_df = df.style.map(style_rows, subset=['Status'])
    else:
        styled_df = df.style.applymap(style_rows, subset=['Status'])
        
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=800)
