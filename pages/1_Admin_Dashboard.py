"""
pages/1_Admin_Dashboard.py — the presenter's live dashboard (on the projector).

Auto-refreshes every 3 seconds so check-ins from phones appear in near real time.
"""
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import storage
import ui

st.set_page_config(page_title="QR UniPass — Dashboard", page_icon="📊", layout="wide")

# Access logic: the dashboard (count/list/chart) is ALWAYS visible so it can be
# shown on the projector to anyone. Only the "Reset" control is presenter-only —
# the presenter proves it by passing ?key=YOUR_KEY in the URL (matching ADMIN_KEY).
admin_key = storage.get_setting("ADMIN_KEY", "")
is_admin = (not admin_key) or (st.query_params.get("key", "") == admin_key)

# Real-time feel.
st_autorefresh(interval=3000, key="dashboard_refresh")

ui.render_header(active="attendance")
st.markdown("##### Live Attendance Dashboard")

data = storage.get_checkins()
df = pd.DataFrame(data, columns=storage.FIELDS)
roster = storage.load_roster()
count = len(df)

# Big live count — the showstopper. No cap/denominator (that would imply a limit).
st.markdown(
    f'<div style="text-align:center;margin:4px 0 2px;">'
    f'<div style="font-size:88px;font-weight:700;line-height:1;color:#0F6E56;">{count}</div>'
    f'<div style="font-size:15px;color:#5F5E5A;letter-spacing:2px;">CHECKED IN · LIVE</div>'
    f'</div>',
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
c1.metric("Last check-in", df["timestamp"].iloc[-1].split("T")[-1][:5] if count else "—")
if roster:
    c2.metric("Check-in rate", f"{round(100 * count / len(roster))}%")
else:
    c2.metric("Latest", df["name"].iloc[-1] if count else "—")

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

# --- Reset (presenter only; with confirmation) ---
if is_admin:
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
