"""
pages/1_Admin_Dashboard.py — the presenter's live dashboard (on the projector).

Auto-refreshes every 3 seconds so check-ins from phones appear in near real time.
"""
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import storage
import ui

st.set_page_config(page_title="QR UniPass — Dashboard", layout="wide")

# Access logic: the dashboard (count/list/chart) is ALWAYS visible so it can be
# shown on the projector to anyone. Only the "Reset" control is presenter-only —
# the presenter proves it by passing ?key=YOUR_KEY in the URL (matching ADMIN_KEY).
admin_key = storage.get_setting("ADMIN_KEY", "")
is_admin = (not admin_key) or (st.query_params.get("key", "") == admin_key)

ui.render_header(active="attendance")

# Presenter-only: the whole dashboard is locked behind ?key=YOUR_KEY.
if not is_admin:
    st.info("This dashboard is for the presenter. Add ?key=YOUR_KEY to the URL to view it.")
    st.stop()

# Real-time feel.
st_autorefresh(interval=3000, key="dashboard_refresh")
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

# --- Cafeteria (live, secondary section — same dashboard, all campus data) ---
st.divider()
st.markdown("##### Cafeteria")
cafe = storage.get_cafeteria()
pays = [t for t in cafe if t.get("kind") == "pay"]
meals = len(pays)
revenue = sum(int(t.get("amount") or 0) for t in pays)
diners = len({(t.get("student_id") or t.get("name") or "").strip().lower() for t in pays})

m1, m2, m3 = st.columns(3)
m1.metric("Meals sold", meals)
m2.metric("Revenue", storage.fmt_vnd(revenue))
m3.metric("Students served", diners)

if meals:
    cdf = pd.DataFrame(pays)
    cdf["Time"] = cdf["timestamp"].str.split("T").str[-1].str[:5]
    cdf["Amount"] = cdf["amount"].apply(storage.fmt_vnd)
    cdf = cdf.rename(columns={"name": "Name", "item": "Item"})
    cdf = cdf[["Name", "Item", "Amount", "Time"]].iloc[::-1].reset_index(drop=True)
    st.dataframe(cdf, width="stretch", hide_index=True)
else:
    st.caption("No cafeteria payments yet — open the Cafeteria page to try one.")

st.caption(f"Source: {storage.source_label()} · auto-refresh every 3s")

# --- Reset (presenter only; with confirmation) ---
if is_admin:
    with st.expander("Admin controls"):
        b1, b2, b3 = st.columns(3)
        if b1.button("Reset check-ins"):
            st.session_state["confirm_target"] = "checkins"
        if b2.button("Reset cafeteria"):
            st.session_state["confirm_target"] = "cafeteria"
        if b3.button("Reset everything"):
            st.session_state["confirm_target"] = "all"

        pending = st.session_state.get("confirm_target")
        if pending:
            what = {
                "checkins": "all check-ins",
                "cafeteria": "all cafeteria data",
                "all": "ALL data (check-ins + cafeteria)",
            }[pending]
            st.warning(f"This permanently deletes {what}.")
            yes, no = st.columns(2)
            if yes.button("Yes, reset now", type="primary"):
                if pending in ("checkins", "all"):
                    storage.reset()
                if pending in ("cafeteria", "all"):
                    storage.cafe_reset()
                st.session_state["confirm_target"] = None
                st.success("Cleared.")
                st.rerun()
            if no.button("Cancel"):
                st.session_state["confirm_target"] = None
