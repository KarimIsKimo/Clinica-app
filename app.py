import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import threading
import queue

# ============================================================
# 1. CONFIGURATION
# ============================================================
# set_page_config must be the very first Streamlit command called —
# touching st.secrets or anything else beforehand can break it in some
# environments (e.g. stlite/pyodide), so it comes before everything else.
st.set_page_config(page_title="Jothen Clinics", layout="centered", page_icon="🏥")

# Prefer storing this in .streamlit/secrets.toml as:
#   GOOGLE_URL = "https://script.google.com/..."
# so it isn't hardcoded in a file you might share or commit.
DEFAULT_GOOGLE_URL = "https://script.google.com/macros/s/AKfycbw0u5gqcy3jsMfiEN1JP7iPJQmwIMbnT5X-dVaIQ40c9l_nkTinIt0F2FbJuO1ND-8k/exec"
try:
    GOOGLE_URL = st.secrets["GOOGLE_URL"]
except Exception:
    # No secrets.toml present (or key missing) — fall back to the hardcoded URL.
    GOOGLE_URL = DEFAULT_GOOGLE_URL

# --- DEMURE & SOPHISTICATED UI (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');

    .stApp { background-color: #FDFDFD; font-family: 'Inter', sans-serif; }

    .main-header {
        font-family: 'Playfair Display', serif;
        font-weight: 700;
        color: #1A1A1A;
        text-align: center;
        margin-top: -30px;
        margin-bottom: 0px;
        letter-spacing: -3px;
        line-height: 1;
        font-size: clamp(2.5rem, 8vw, 5rem);
    }

    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        text-align: center;
        color: #A0A0A0;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    .app-card {
        background: white;
        padding: 18px;
        border-radius: 15px;
        margin-bottom: 12px;
        border: 1px solid #F5F5F5;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }

    .status-pill {
        padding: 5px 15px;
        border-radius: 30px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 10px;
    }

    .bg-Free { background-color: #BDC3C7 !important; color: #1A1A1A !important; }
    .bg-Booked { background-color: #F39C12 !important; color: #FFFFFF !important; }
    .bg-Arrived { background-color: #3498DB !important; color: #FFFFFF !important; }
    .bg-In { background-color: #8E44AD !important; color: #FFFFFF !important; }
    .bg-Done { background-color: #27AE60 !important; color: #FFFFFF !important; }
    .bg-Cancelled { background-color: #E74C3C !important; color: #FFFFFF !important; }

    .stTextInput input {
        border: none !important;
        border-bottom: 1px solid #EEE !important;
        padding: 5px 0px !important;
        font-size: 14px !important;
        background-color: transparent !important;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: transparent !important;
        border: none !important;
        font-size: 14px;
        font-weight: 600;
    }

    .sync-ok { color: #27AE60; font-size: 12px; font-weight: 600; }
    .sync-bad { color: #E74C3C; font-size: 12px; font-weight: 600; }
    .sync-pending { color: #F39C12; font-size: 12px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

slots = ["12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM",
         "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM",
         "06:00 PM", "06:30 PM", "07:00 PM", "07:30 PM", "08:00 PM", "08:30 PM",
         "09:00 PM", "09:30 PM", "10:00 PM"]
status_options = ["Free", "Booked", "Arrived", "In", "Done", "Cancelled"]
EMPTY_ENTRY = {"name": "", "phone": "", "status": "Free", "confirmed": False}


def normalize_phone(value):
    """
    Google Sheets often stores digit-only text as a number, which drops a
    leading zero (e.g. "01026438897" becomes 1026438897). Local mobile
    numbers are 11 digits starting with 0, so restore it when we detect
    this pattern coming back from the cloud.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    if s.isdigit() and len(s) == 10 and not s.startswith("0"):
        s = "0" + s
    return s


def normalize_entries(data):
    """Fix up phone numbers on every entry returned from the cloud."""
    if not isinstance(data, dict):
        return data
    for entry in data.values():
        if isinstance(entry, dict) and "phone" in entry:
            entry["phone"] = normalize_phone(entry.get("phone"))
    return data

# ============================================================
# 2. SAFE DATA LAYER
# ============================================================
def fetch_cloud_data():
    """Fetch data from the cloud. Returns (data, error_message)."""
    try:
        res = requests.get(GOOGLE_URL, timeout=8)
        res.raise_for_status()
        return res.json(), None
    except requests.exceptions.Timeout:
        return None, "Connection timed out. Check your internet and try again."
    except requests.exceptions.RequestException as e:
        return None, f"Couldn't reach the server ({e.__class__.__name__})."
    except ValueError:
        return None, "Server returned an unexpected response."


def push_cloud_data(data):
    """Push data to the cloud. Returns (success, error_message)."""
    try:
        res = requests.post(GOOGLE_URL, json=data, timeout=10)
        res.raise_for_status()
        return True, None
    except requests.exceptions.Timeout:
        return False, "Save timed out. Your changes are kept locally — try syncing again."
    except requests.exceptions.RequestException as e:
        return False, f"Save failed ({e.__class__.__name__}). Your changes are kept locally."


def _background_push(data_snapshot, result_queue):
    ok, err = push_cloud_data(data_snapshot)
    ts = datetime.now().strftime('%H:%M:%S')
    if ok:
        result_queue.put(("ok", f"Synced at {ts}"))
    else:
        result_queue.put(("bad", err))


def autosave():
    """
    Fire-and-forget auto-save: pushes a snapshot of the current local
    state to the cloud on a background thread and returns immediately.
    This is what makes edits feel instant — the UI never waits on the
    network request. The result (success/failure) is picked up from a
    queue and shown in the sync status bar on the next rerun. The full
    merge-safe save (fetch + merge + push) still runs synchronously on
    the manual "SAVE NOW" button and on Refresh.
    """
    snapshot = dict(st.session_state.clinic_data)
    st.session_state.dirty_keys = set()
    st.session_state.sync_status = "pending"
    st.session_state.sync_message = "Saving…"
    threading.Thread(
        target=_background_push,
        args=(snapshot, st.session_state.sync_queue),
        daemon=True,
    ).start()


def save_to_cloud(silent=False):
    """
    Merge-safe save: re-fetches the latest cloud data, overlays only the
    entries we've locally changed (dirty_keys), then pushes the merged
    result. This avoids one device wiping out another device's edits.
    """
    cloud_data, err = fetch_cloud_data()
    if cloud_data is None:
        # Couldn't confirm the latest cloud state — refuse to blind-overwrite it.
        st.session_state.sync_status = "bad"
        st.session_state.sync_message = err or "Couldn't verify cloud data before saving."
        return False
    cloud_data = normalize_entries(cloud_data)

    merged = {**cloud_data}
    for key in st.session_state.dirty_keys:
        if key in st.session_state.clinic_data:
            merged[key] = st.session_state.clinic_data[key]

    ok, push_err = push_cloud_data(merged)
    if ok:
        st.session_state.clinic_data = merged
        st.session_state.dirty_keys = set()
        st.session_state.sync_status = "ok"
        st.session_state.sync_message = f"Synced at {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.data_loaded = True
        if not silent:
            st.toast("Saved", icon="✨")
        return True
    else:
        st.session_state.sync_status = "bad"
        st.session_state.sync_message = push_err
        return False


def load_from_cloud(initial=False):
    data, err = fetch_cloud_data()
    if data is None:
        st.session_state.sync_status = "bad"
        st.session_state.sync_message = err
        if initial:
            # First load failed: start with an empty local cache but mark
            # data as NOT loaded, so we refuse to save until a load succeeds.
            st.session_state.clinic_data = {}
            st.session_state.data_loaded = False
        return False
    st.session_state.clinic_data = normalize_entries(data)
    st.session_state.dirty_keys = set()
    st.session_state.data_loaded = True
    st.session_state.sync_status = "ok"
    st.session_state.sync_message = f"Loaded at {datetime.now().strftime('%H:%M:%S')}"
    return True


# ============================================================
# 3. SESSION STATE INIT
# ============================================================
if "clinic_data" not in st.session_state:
    st.session_state.dirty_keys = set()
    st.session_state.data_loaded = False
    st.session_state.sync_status = "pending"
    st.session_state.sync_message = "Loading..."
    st.session_state.sync_queue = queue.Queue()
    load_from_cloud(initial=True)

# Pick up results from any background auto-saves that finished since the
# last rerun (drain to the latest result if several queued up).
while not st.session_state.sync_queue.empty():
    _status, _message = st.session_state.sync_queue.get()
    st.session_state.sync_status = _status
    st.session_state.sync_message = _message
    if _status == "ok":
        st.session_state.data_loaded = True


def update_entry(s_id):
    st.session_state.clinic_data[s_id] = {
        "name": st.session_state[f"n_{s_id}"],
        "phone": st.session_state[f"p_{s_id}"],
        "status": st.session_state[f"s_{s_id}"],
        "confirmed": st.session_state[f"c_{s_id}"],
    }
    st.session_state.dirty_keys.add(s_id)
    # Fast auto-save so a closed tab or crash never loses an edit, without
    # blocking on a full fetch+merge round trip.
    autosave()


def clear_entry(s_id):
    st.session_state.clinic_data[s_id] = dict(EMPTY_ENTRY)
    st.session_state.dirty_keys.add(s_id)
    autosave()


# ============================================================
# 4. HEADER
# ============================================================
st.markdown("<div class='main-header'>Jothen</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Clinics • Est. 2024</div>", unsafe_allow_html=True)

# Sync status bar
status_class = {"ok": "sync-ok", "bad": "sync-bad", "pending": "sync-pending"}[st.session_state.sync_status]
status_icon = {"ok": "🟢", "bad": "🔴", "pending": "🟡"}[st.session_state.sync_status]
st.markdown(
    f"<div style='text-align:center;margin-bottom:10px' class='{status_class}'>"
    f"{status_icon} {st.session_state.sync_message}</div>",
    unsafe_allow_html=True,
)

if not st.session_state.data_loaded:
    st.error(
        "Couldn't load data from the cloud, so saving is disabled to avoid "
        "overwriting anything. Click **Refresh** below to try again."
    )

top_left, top_mid, top_right = st.columns([2, 1, 1])
with top_left:
    clinic_date = st.date_input("Schedule Date", datetime.now(), label_visibility="collapsed")
with top_mid:
    if st.button("🔄 Refresh", use_container_width=True):
        if load_from_cloud():
            st.toast("Refreshed", icon="🔄")
        st.rerun()
with top_right:
    if st.button("SAVE NOW", use_container_width=True, disabled=not st.session_state.data_loaded):
        save_to_cloud()
        st.rerun()

# Quick counts for the selected day
day_entries = [
    st.session_state.clinic_data.get(f"{slot}_{clinic_date}", EMPTY_ENTRY) for slot in slots
]
counts = pd.Series([e["status"] for e in day_entries]).value_counts()
count_cols = st.columns(len(status_options))
for col, status in zip(count_cols, status_options):
    col.metric(status, int(counts.get(status, 0)))

st.divider()

# ============================================================
# 5. TABS
# ============================================================
tab_manage, tab_summary = st.tabs(["📝 MANAGEMENT", "📋 VIEW SUMMARY"])

# --- TAB 1: MANAGEMENT ---
with tab_manage:
    search = st.text_input(
        "Search", placeholder="🔍 Search by patient name or phone…", label_visibility="collapsed"
    )
    search_lower = search.strip().lower()
    any_match = False

    for slot in slots:
        s_id = f"{slot}_{clinic_date}"
        entry = st.session_state.clinic_data.get(s_id, dict(EMPTY_ENTRY))

        if search_lower and search_lower not in entry["name"].lower() and search_lower not in entry["phone"].lower():
            continue
        any_match = True

        confirmed_badge = " ✅ Confirmed" if entry.get("confirmed") else ""
        st.markdown(f"""
            <div class="app-card">
                <span class="status-pill bg-{entry['status']}">{slot} &nbsp;•&nbsp; {entry['status']}</span>{confirmed_badge}
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 1, 1])
        with c1:
            st.text_input("Name", value=entry["name"], key=f"n_{s_id}", placeholder="Patient Name",
                          label_visibility="collapsed", on_change=update_entry, args=(s_id,),
                          disabled=not st.session_state.data_loaded)
        with c2:
            st.text_input("Phone", value=entry["phone"], key=f"p_{s_id}", placeholder="Contact Number",
                          label_visibility="collapsed", on_change=update_entry, args=(s_id,),
                          disabled=not st.session_state.data_loaded)
        with c3:
            st.selectbox("Status", options=status_options,
                        index=status_options.index(entry["status"]) if entry["status"] in status_options else 0,
                        key=f"s_{s_id}", label_visibility="collapsed", on_change=update_entry, args=(s_id,),
                        disabled=not st.session_state.data_loaded)
        with c4:
            st.checkbox("Confirmed", value=entry.get("confirmed", False), key=f"c_{s_id}",
                       on_change=update_entry, args=(s_id,),
                       disabled=not st.session_state.data_loaded)
        with c5:
            st.button("🗑️", key=f"clear_{s_id}", help="Clear this slot",
                      on_click=clear_entry, args=(s_id,),
                      disabled=not st.session_state.data_loaded)
        st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

    if search_lower and not any_match:
        st.info("No matching patients for this day.")

# --- TAB 2: SUMMARY VIEW ---
with tab_summary:
    summary_list = []
    for slot in slots:
        s_id = f"{slot}_{clinic_date}"
        e = st.session_state.clinic_data.get(s_id, dict(EMPTY_ENTRY))
        summary_list.append({
            "Time": slot,
            "Patient": e["name"] if e["name"] else "—",
            "Contact": e["phone"] if e["phone"] else "—",
            "Status": e["status"],
            "Confirmed": "✅" if e.get("confirmed") else "—",
        })

    df = pd.DataFrame(summary_list)

    def style_rows(val):
        colors = {
            'Free': 'background-color: #BDC3C7; color: black; font-weight: bold;',
            'Booked': 'background-color: #F39C12; color: white; font-weight: bold;',
            'Arrived': 'background-color: #3498DB; color: white; font-weight: bold;',
            'In': 'background-color: #8E44AD; color: white; font-weight: bold;',
            'Done': 'background-color: #27AE60; color: white; font-weight: bold;',
            'Cancelled': 'background-color: #E74C3C; color: white; font-weight: bold;',
        }
        return colors.get(val, '')

    st.markdown("### Daily Overview")
    if hasattr(df.style, 'map'):
        styled_df = df.style.map(style_rows, subset=['Status'])
    else:
        styled_df = df.style.applymap(style_rows, subset=['Status'])

    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=800)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download this day as CSV", data=csv,
        file_name=f"jothen_schedule_{clinic_date}.csv", mime="text/csv",
    )
