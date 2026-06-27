"""
pages/1_Admin_Dashboard.py — the presenter's live dashboard (on the projector).

Auto-refreshes every 3 seconds so check-ins from phones appear in near real time.
"""
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import storage

st.set_page_config(page_title="QR UniPass — Dashboard", page_icon="📊", layout="wide")

# Optional light access gate: if ADMIN_KEY is set, require ?key=... in the URL.
admin_key = storage.get_setting("ADMIN_KEY", "")
if admin_key:
    provided = st.query_params.get("key", "")
    if provided != admin_key:
        st.title("QR UniPass — Live Attendance Dashboard")
        st.warning("Append ?key=YOUR_KEY to the URL to view this dashboard.")
        st.stop()

# Real-time feel.
st_autorefresh(interval=3000, key="dashboard_refresh")

st.title("QR UniPass — Live Attendance Dashboard")

data = storage.get_checkins()
df = pd.DataFrame(data, columns=storage.FIELDS)
roster = storage.load_roster()
count = len(df)

# --- KPI cards ---
c1, c2, c3 = st.columns(3)
c1.metric("Checked-in", count)
c2.metric("Last check-in", df["timestamp"].iloc[-1].split("T")[-1] if count else "—")
if roster:
    c3.metric("Check-in rate", f"{round(100 * count / len(roster))}%")
else:
    c3.metric("Check-in rate", "—")

st.divider()

# --- Live roster table (newest first) ---
if count:
    show = df.copy()
    show["Time"] = show["timestamp"].str.split("T").str[-1]
    show = show.rename(columns={"name": "Name", "student_id": "Student ID"})
    show = show[["Name", "Student ID", "Time"]].iloc[::-1].reset_index(drop=True)
    st.dataframe(show, width="stretch", hide_index=True)

    # --- Cumulative check-ins over time (per minute) ---
    ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
    if not ts.empty:
        per_minute = ts.dt.floor("min").value_counts().sort_index().cumsum()
        st.line_chart(pd.DataFrame({"Checked-in": per_minute.values}, index=per_minute.index))
else:
    st.info("No check-ins yet. Show the QR and ask the audience to scan.")

st.caption(f"Source: {storage.source_label()} · auto-refresh every 3s")

# --- Reset (with confirmation) ---
with st.expander("⚙️ Admin controls"):
    if st.button("Reset all check-ins"):
        st.session_state["confirm_reset"] = True
    if st.session_state.get("confirm_reset"):
        st.warning("This permanently deletes all current check-ins.")
        col_a, col_b = st.columns(2)
        if col_a.button("Yes, reset now", type="primary"):
            storage.reset()
            st.session_state["confirm_reset"] = False
            st.success("Cleared.")
            st.rerun()
        if col_b.button("Cancel"):
            st.session_state["confirm_reset"] = False
