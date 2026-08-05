import streamlit as st
from datetime import datetime
import requests

# 1. PASTE YOUR GOOGLE WEB APP URL HERE INSIDE THE QUOTES
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbw0u5gqcy3jsMfiEN1JP7iPJQmwIMbnT5X-dVaIQ40c9l_nkTinIt0F2FbJuO1ND-8k/exec"

st.set_page_config(page_title="Neoderma Cloud Sync", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: white; }
    p, span, label { color: black !important; font-size: 14px !important; font-weight: bold; }
    input { background-color: #ffffff !important; color: black !important; border: 2px solid #d4af37 !important; border-radius: 5px !important; height: 38px !important; }
    .status-indicator { height: 20px; width: 20px; border-radius: 50%; margin-right: 10px; display: inline-block; border: 1px solid #ccc; }
    .color-Free { background-color: #e0e0e0; }
    .color-Booked { background-color: #f1c40f; }
    .color-Arrived { background-color: #3498db; }
    .color-Done { background-color: #2ecc71; }
    .color-Cancelled { background-color: #e74c3c; }
    div[data-testid="stRadio"] > div { flex-direction: row; gap: 10px; }
    div[data-testid="stRadio"] label { background-color: #f0f2f6; padding: 4px 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Function to fetch saved data from Google
def load_cloud_data():
    try:
        res = requests.get(GOOGLE_URL, timeout=5)
        return res.json()
    except:
        return {}

if 'clinic_data' not in st.session_state:
    st.session_state.clinic_data = load_cloud_data()

# Page setup 
c_title, c_sync = st.columns([3, 1])
with c_title:
    st.markdown("<h1 style='color:#1a2a6c; margin:0;'>🏥 Neoderma Cloud Sync</h1>", unsafe_allow_html=True)

# BIG SAVE BUTTON
with c_sync:
    if st.button("💾 SYNC TO GOOGLE SHEETS", use_container_width=True):
        with st.spinner("Uploading to Google..."):
            try:
                requests.post(GOOGLE_URL, json=st.session_state.clinic_data, timeout=8)
                st.toast("Database updated!")
            except:
                st.error("Upload failed")

st.markdown("<div style='background:#f4f4f4; padding:15px; border-radius:10px; border:1px solid #d4af37;'>", unsafe_allow_html=True)
sc1, sc2, sc3 = st.columns([2, 1, 1])
with sc1:
    doc_name = st.text_input("DOCTOR NAME:", value="Dr. Smith")
with sc2:
    clinic_day = st.text_input("DAY:", value=datetime.now().strftime("%A"))
with sc3:
    clinic_date = st.date_input("DATE:", datetime.now())
st.markdown("</div><br>", unsafe_allow_html=True)

slots = ["12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM", "06:00 PM", "06:30 PM", "07:00 PM", "07:30 PM", "08:00 PM", "08:30 PM", "09:00 PM", "09:30 PM", "10:00 PM"]

for slot in slots:
    s_id = f"{slot}_{clinic_date}"
    curr_entry = st.session_state.clinic_data.get(s_id, {"name": "", "phone": "", "status": "Free"})

    r_time, r_name, r_phone, r_status = st.columns([0.6, 2, 1.2, 2.5])
    
    with r_time:
        st.markdown(f'<div style="display: flex; align-items:center; margin-top:10px;"><div class="status-indicator color-{curr_entry["status"]}"></div><span style="color:#d4af37;">{slot}</span></div>', unsafe_allow_html=True)
    with r_name:
        p_name = st.text_input("Name", value=curr_entry["name"], key=f"n_{s_id}", label_visibility="collapsed")
    with r_phone:
        p_phone = st.text_input("Phone", value=curr_entry["phone"], key=f"p_{s_id}", label_visibility="collapsed")
    with r_status:
        p_stat = st.radio("Status", options=["Free", "Booked", "Arrived", "Done", "Cancelled"], index=["Free", "Booked", "Arrived", "Done", "Cancelled"].index(curr_entry["status"]), key=f"s_{s_id}", horizontal=True, label_visibility="collapsed")

    # Keep memory updated as user clicks around
    st.session_state.clinic_data[s_id] = {"name": p_name, "phone": p_phone, "status": p_stat}
    st.markdown('<hr style="margin:5px 0; border:0; border-top:1px solid #eee;">', unsafe_allow_html=True)
