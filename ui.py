"""Shared UI bits — the branded header shown across every page."""
import streamlit as st

NAVY = "#14294C"

_MODULES = [
    ("📍", "Attendance", "attendance"),
    ("🍱", "Cafeteria", "cafeteria"),
    ("📚", "Library", "library"),
    ("🏠", "Dormitory", "dormitory"),
]


def render_header(active: str = "") -> None:
    """Navy brand bar + tagline + the four campus-module icons.

    `active` highlights one module chip (e.g. "attendance" / "cafeteria").
    """
    chips = ""
    for emoji, label, key in _MODULES:
        on = key == active
        bg = "rgba(29,158,117,0.22)" if on else "rgba(255,255,255,0.07)"
        fg = "#9FE1CB" if on else "rgba(255,255,255,0.72)"
        chips += (
            f'<div style="flex:1;text-align:center;background:{bg};border-radius:8px;padding:7px 2px;">'
            f'<div style="font-size:18px;line-height:1.1;">{emoji}</div>'
            f'<div style="font-size:11px;color:{fg};margin-top:2px;">{label}</div></div>'
        )
    st.markdown(
        f'<div style="background:{NAVY};border-radius:12px;padding:14px 16px;margin-bottom:14px;">'
        f'<div style="font-size:19px;font-weight:600;color:#fff;">QR UniPass</div>'
        f'<div style="font-size:12px;color:rgba(255,255,255,0.78);margin-top:1px;">'
        f'One QR for the whole campus</div>'
        f'<div style="display:flex;gap:6px;margin-top:12px;">{chips}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
