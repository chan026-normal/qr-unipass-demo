"""
pages/2_Cafeteria.py — Cafeteria payment (virtual balance demo).

Two-step flow: enter your name -> Continue -> see balance, pick a meal, Pay.
This is a SIMULATION — no real money moves. Kept fully separate so it never
touches the attendance demo used in the scripted pitch.

Great for Q&A: "you mentioned cafeteria payment — can you show it?" → here it is.
"""
import streamlit as st

import storage
import ui

st.set_page_config(page_title="QR UniPass — Cafeteria", layout="centered")

st.markdown(
    """
    <style>
      .stButton > button { font-size: 1.2rem; padding: 0.8rem 1rem; border-radius: 12px; }
      .block-container { max-width: 32rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

ui.render_header(active="cafeteria")
st.caption("Cafeteria Payment")

admin_key = storage.get_setting("ADMIN_KEY", "")
is_admin = (not admin_key) or (st.query_params.get("key", "") == admin_key)

# Vietnamese campus menu; prices in VND. (UI labels stay English.)
MENU = [
    ("Cơm tấm (Broken rice)", 35000),
    ("Phở", 40000),
    ("Bún chả", 45000),
    ("Bánh mì", 20000),
    ("Cà phê (Coffee)", 15000),
]
TOPUP = 100000

roster = storage.load_roster()
PLACEHOLDER = "— Select your name —"
NOT_LISTED = "My name is not listed"

# One-time message from the previous action.
flash = st.session_state.pop("cafe_flash", None)
if flash:
    getattr(st, flash[0])(flash[1])

confirmed = st.session_state.get("cafe_user") or None

if not confirmed:
    # Step 1 — identify yourself (Student ID or name). The menu appears after this.
    st.caption("Enter your Student ID, or your name if you don't have one.")
    sid_in = st.text_input("Student ID")

    manual_name = ""
    choice = None
    if roster:
        choice = st.selectbox("Name", [PLACEHOLDER] + roster + [NOT_LISTED])
        if choice == NOT_LISTED:
            manual_name = st.text_input("Type your name")
    else:
        manual_name = st.text_input("Name", placeholder="e.g. Nguyen Van A")

    if roster and choice and choice not in (PLACEHOLDER, NOT_LISTED):
        name = choice
    else:
        name = manual_name
    name = (name or "").strip()
    sid = (sid_in or "").strip()

    if st.button("Continue", type="primary", width="stretch"):
        if not name and not sid:
            st.session_state["cafe_flash"] = ("warning", "Please enter your name or Student ID.")
        else:
            st.session_state["cafe_user"] = {"name": name, "student_id": sid}
        st.rerun()
else:
    # Step 2 — balance, menu, pay (keyed by Student ID if given, else name).
    cname = confirmed.get("name", "")
    csid = confirmed.get("student_id", "")
    st.caption(f"Paying as {cname or ('ID ' + csid)}")
    st.metric("Balance", storage.fmt_vnd(storage.cafe_balance(cname, csid)))

    labels = [f"{item} — {storage.fmt_vnd(price)}" for item, price in MENU]
    pick = st.selectbox("Choose your meal", labels)
    item, price = MENU[labels.index(pick)]

    if st.button(f"Pay {storage.fmt_vnd(price)}", type="primary", width="stretch"):
        try:
            new_bal = storage.cafe_pay(cname, item, price, csid)
            st.session_state["cafe_flash"] = (
                "success",
                f"Paid {storage.fmt_vnd(price)} for {item}. New balance: {storage.fmt_vnd(new_bal)}",
            )
        except storage.InsufficientBalance:
            st.session_state["cafe_flash"] = ("warning", "Not enough balance. Please top up.")
        except Exception:
            st.session_state["cafe_flash"] = ("error", "Something went wrong. Please try again.")
        st.rerun()

    # Top-up is presenter-only (admin), so the student screen stays clean.
    if is_admin and st.button(f"Top up {storage.fmt_vnd(TOPUP)} (admin)", width="stretch"):
        new_bal = storage.cafe_topup(cname, TOPUP, csid)
        st.session_state["cafe_flash"] = ("info", f"Topped up. New balance: {storage.fmt_vnd(new_bal)}")
        st.rerun()

    if st.button("Start over"):
        st.session_state["cafe_user"] = None
        st.rerun()

# Admin-only reset (same key as the dashboard; others never see this).
if is_admin:
    with st.expander("Admin controls"):
        if st.button("Reset cafeteria data"):
            st.session_state["confirm_cafe_reset"] = True
        if st.session_state.get("confirm_cafe_reset"):
            st.warning("This permanently deletes all cafeteria transactions and balances.")
            a, b = st.columns(2)
            if a.button("Yes, reset now", type="primary"):
                storage.cafe_reset()
                st.session_state["confirm_cafe_reset"] = False
                st.session_state["cafe_user"] = ""
                st.success("Cleared.")
                st.rerun()
            if b.button("Cancel"):
                st.session_state["confirm_cafe_reset"] = False
