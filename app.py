"""
app.py — Check-in page. This is the screen the QR code points to.

Mobile-first, one screen, no login. A judge/student scans the QR, picks or
types their name, taps "Check in", and is done in ~3 seconds.
"""
import streamlit as st

import storage
import ui

st.set_page_config(page_title="QR UniPass — Check-in", page_icon="✅", layout="centered")

# Bigger touch targets for phones; keep it minimal.
st.markdown(
    """
    <style>
      .stButton > button { font-size: 1.25rem; padding: 0.9rem 1rem; border-radius: 12px; }
      .block-container { padding-top: 2.5rem; max-width: 32rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

ui.render_header(active="attendance")
st.caption("Xin chào — check in below")

roster = storage.load_roster()
PLACEHOLDER = "— Select your name —"
NOT_LISTED = "My name is not listed"

# Name input (reactive, no form, so the "not listed" field appears instantly).
manual_name = ""
choice = None
if roster:
    choice = st.selectbox("Your name", [PLACEHOLDER] + roster + [NOT_LISTED])
    if choice == NOT_LISTED:
        manual_name = st.text_input("Type your name")
else:
    manual_name = st.text_input("Your name", placeholder="e.g. Nguyen Van A")

student_id = st.text_input("Student ID (optional)")

if st.button("Check in", type="primary", width="stretch"):
    if roster and choice and choice not in (PLACEHOLDER, NOT_LISTED):
        name = choice
    else:
        name = manual_name
    name = (name or "").strip()

    if not name:
        st.warning("Please enter your name.")
    else:
        try:
            rec = storage.add_checkin(name, student_id)
            when = rec["timestamp"].split("T")[-1][:5]
            st.markdown(
                f'<div style="background:#E1F5EE;border:1px solid #9FE1CB;border-radius:12px;'
                f'padding:22px;text-align:center;margin-top:10px;">'
                f'<div style="font-size:46px;line-height:1;">✅</div>'
                f'<div style="font-size:18px;font-weight:600;color:#04342C;margin-top:6px;">'
                f'You\'re checked in!</div>'
                f'<div style="font-size:24px;font-weight:700;color:#04342C;margin-top:4px;">'
                f'{rec["name"]}</div>'
                f'<div style="font-size:13px;color:#0F6E56;margin-top:4px;">{when} · welcome aboard</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.balloons()
        except storage.AlreadyCheckedIn:
            st.info("You're already checked in ✓")
        except Exception:
            st.error("Something went wrong. Please try again.")
