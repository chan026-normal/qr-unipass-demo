"""
app.py — Check-in page. This is the screen the QR code points to.

Mobile-first, one screen, no login. A judge/student scans the QR, picks or
types their name, taps "Check in", and is done in ~3 seconds.
"""
import streamlit as st

import storage

st.set_page_config(page_title="QR UniPass — Check-in", page_icon="✅", layout="centered")

# Bigger touch targets for phones; keep it minimal.
st.markdown(
    """
    <style>
      .stButton > button { font-size: 1.25rem; padding: 0.9rem 1rem; border-radius: 12px; }
      .block-container { padding-top: 2.5rem; max-width: 32rem; }
      h1 { margin-bottom: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("QR UniPass")
st.caption("Classroom Check-in")

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
            when = rec["timestamp"].split("T")[-1]
            st.success(f"✅ You're checked in! — {rec['name']}, {when}")
        except storage.AlreadyCheckedIn:
            st.info("You're already checked in ✓")
        except Exception:
            st.error("Something went wrong. Please try again.")
