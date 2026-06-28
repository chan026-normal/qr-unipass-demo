"""
pages/2_Cafeteria.py — Cafeteria payment (virtual balance demo).

Same scan-and-tap pattern as check-in, but for paying for a meal with a virtual
balance. This is a SIMULATION — no real money moves. Kept fully separate so it
never touches the attendance demo used in the scripted pitch.

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
      .block-container { padding-top: 2.5rem; max-width: 32rem; }
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

manual_name = ""
choice = None
if roster:
    choice = st.selectbox("Your name", [PLACEHOLDER] + roster + [NOT_LISTED])
    if choice == NOT_LISTED:
        manual_name = st.text_input("Type your name")
else:
    manual_name = st.text_input("Your name", placeholder="e.g. Nguyen Van A")

if roster and choice and choice not in (PLACEHOLDER, NOT_LISTED):
    name = choice
else:
    name = manual_name
name = (name or "").strip()

# Show a one-time message from the previous action (so the balance below is fresh).
flash = st.session_state.pop("cafe_flash", None)
if flash:
    getattr(st, flash[0])(flash[1])

# Balance shows once a name is entered.
st.metric("Balance", storage.fmt_vnd(storage.cafe_balance(name)) if name else "—")

# Meal + Pay are always visible (like the check-in button) — no Enter needed.
labels = [f"{item} — {storage.fmt_vnd(price)}" for item, price in MENU]
pick = st.selectbox("Choose your meal", labels)
item, price = MENU[labels.index(pick)]

if st.button(f"Pay {storage.fmt_vnd(price)}", type="primary", width="stretch"):
    if not name:
        st.session_state["cafe_flash"] = ("warning", "Please enter your name first.")
    else:
        try:
            new_bal = storage.cafe_pay(name, item, price)
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
    if not name:
        st.session_state["cafe_flash"] = ("warning", "Enter a name first.")
    else:
        new_bal = storage.cafe_topup(name, TOPUP)
        st.session_state["cafe_flash"] = ("info", f"Topped up. New balance: {storage.fmt_vnd(new_bal)}")
    st.rerun()

# Small "data" line — supports the pitch's data-driven story.
txns = storage.get_cafeteria()
pays = [t for t in txns if t.get("kind") == "pay"]
revenue = sum(int(t.get("amount") or 0) for t in pays)
st.caption(f"Today: {len(pays)} meals · {storage.fmt_vnd(revenue)} revenue · {storage.source_label()}")

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
                st.success("Cleared.")
                st.rerun()
            if b.button("Cancel"):
                st.session_state["confirm_cafe_reset"] = False
