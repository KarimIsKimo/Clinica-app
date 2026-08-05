import streamlit as st
from datetime import datetime
import requests

# 1. GOOGLE WEB APP URL
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbw0u5gqcy3jsMfiEN1JP7iPJQmwIMbnT5X-dVaIQ40c9l_nkTinIt0F2FbJuO1ND-8k/exec"

st.set_page_config(page_title="Neoderma Cloud Sync", layout="wide")

# CSS for appropriate colors
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    p, span, label { color: #2c3e50 !important; font-size: 14px !important; font-weight: bold; }
    input { background-color: #ffffff !important; color: black !important; border: 1px solid #d4af37 !important; border-radius: 5px !important; }
    
    .status-indicator { 
        height: 18px; width: 18px; border-radius: 50%; 
        display: inline-block; margin-right: 8px; 
        border: 2px solid #ffffff; box-shadow: 0px 0px 3px rgba(0,0,0,0.3);
    }
    
    /* Requested Colors */
    .color-Free { background-color: #BDC3C7; }      /* Gray */
    .color-Booked { background-color: #F1C40F; }    /* Yellow */
    .color-Arrived { background-color: #3498DB; }   /* Blue */
    .color-Done { background-color: #27AE60; }      /* Green */
    .color-Cancelled { background-color: #E74C3C; } /* Red */

    div[data-testid="stRadio"] > div { flex-direction: row; gap: 5px; }
    div[data-testid="stRadio"] label { background-color: #ffffff; padding: 2px 8px; border-radius: 4px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOGIC ---

def load_cloud_data():
    try:
        res = requests.get(GOOGLE_URL, timeout=5)
        return res.json()
    except:
        return {}

# Initialize session state
if 'clinic_data' not in st.session_state:
    st.session_state.clinic_data = load_cloud_data()

# Callback function to handle updates instantly (Fixes the double-click issue)
def update_entry(s_id, key_prefix):
    name = st.session_state[f"n_{s_id}"]
    phone = st.session_state[f"p_{s_id}"]
    status = st.session_state[f"s_{s_id}"]
    st.session_state.clinic_data[s_id] = {"name": name, "phone": phone, "status": status}

# --- UI LAYOUT ---

c_title, c_sync = st.columns([3, 1])
with c_title:
    st.markdown("<h1 style='color:#1a2a6c; margin:0;'>🏥 Neoderma Cloud Sync</h1>", unsafe_allow_html=True)

with c_sync:
    if st.button("💾 SYNC TO GOOGLE SHEETS", use_container_width=True):
        with st.spinner("Syncing..."):
            try:
                requests.post(GOOGLE_URL, json=st.session_state.clinic_data, timeout=8)
                st.toast("✅ Saved to Google Sheets!")
            except:
                st.error("Upload failed")

# Top Bar
st.markdown("<div style='background:#ffffff; padding:15px; border-radius:10px; border:1px solid #d4af37; margin-bottom:20px;'>", unsafe_allow_html=True)
sc1, sc2, sc3 = st.columns([2, 1, 1])
with sc1: doc_name = st.text_input("DOCTOR NAME:", value="Dr. Smith")
with sc2: clinic_day = st.text_input("DAY:", value=datetime.now().strftime("%A"))
with sc3: clinic_date = st.date_input("DATE:", datetime.now())
st.markdown("</div>", unsafe_allow_html=True)

slots = ["12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM", "06:00 PM", "06:30 PM", "07:00 PM", "07:30 PM", "08:00 PM", "08:30 PM", "09:00 PM", "09:30 PM", "10:00 PM"]

# Table Headers
h_time, h_name, h_phone, h_status = st.columns([0.8, 2, 1.2, 3])
with h_time: st.markdown("**TIME**")
with h_name: st.markdown("**PATIENT NAME**")
with h_phone: st.markdown("**PHONE**")
with h_status: st.markdown("**STATUS**")
st.markdown("---")

# Render Slots
for slot in slots:
    s_id = f"{slot}_{clinic_date}"
    
    # Get current data for this slot
    entry = st.session_state.clinic_data.get(s_id, {"name": "", "phone": "", "status": "Free"})
    
    col_time, col_name, col_phone, col_status = st.columns([0.8, 2, 1.2, 3])
    
    # We use st.session_state to look up the LIVE value for the color indicator
    # If the widget hasn't rendered yet, use the 'entry' value
    current_status_val = st.session_state.get(f"s_{s_id}", entry["status"])

    with col_time:
        st.markdown(f'''
            <div style="display: flex; align-items:center; margin-top:8px;">
                <div class="status-indicator color-{current_status_val}"></div>
                <span style="color:#d4af37; font-size:15px;">{slot}</span>
            </div>
        ''', unsafe_allow_html=True)

    with col_name:
        st.text_input("Name", value=entry["name"], key=f"n_{s_id}", 
                     label_visibility="collapsed", on_change=update_entry, args=(s_id, "n"))
    
    with col_phone:
        st.text_input("Phone", value=entry["phone"], key=f"p_{s_id}", 
                     label_visibility="collapsed", on_change=update_entry, args=(s_id, "p"))

    with col_status:
        st.radio("Status", options=["Free", "Booked", "Arrived", "Done", "Cancelled"], 
                 index=["Free", "Booked", "Arrived", "Done", "Cancelled"].index(entry["status"]),
                 key=f"s_{s_id}", horizontal=True, label_visibility="collapsed",
                 on_change=update_entry, args=(s_id, "s"))

    st.markdown('<hr style="margin:2px 0; border:0; border-top:1px solid #eee;">', unsafe_allow_html=True)
