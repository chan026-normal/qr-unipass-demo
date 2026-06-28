"""Shared UI bits — branded header, line icons, and chrome hiding.

The module nav uses Streamlit's native st.page_link / st.button so navigation
is instant (no full page reload, no badge flicker). Built modules link to their
page; unbuilt ones are disabled with a "Coming soon" tooltip.
"""
import json

import streamlit as st
import streamlit.components.v1 as components

NAVY = "#14294C"

# Chrome we hide so the audience sees a clean product (Fork/GitHub badge, etc.).
_PERSIST_CSS = (
    "header[data-testid='stHeader']{display:none!important;}"
    "[data-testid='stToolbar']{display:none!important;}"
    "[data-testid='stToolbarActions']{display:none!important;}"
    "[data-testid='manage-app-button']{display:none!important;}"
    "[data-testid='stStatusWidget']{display:none!important;}"
    "a[href*='github.com']{display:none!important;}"
    "a[href*='streamlit.io']{display:none!important;}"
    "[class*='viewerBadge']{display:none!important;}"
    "#MainMenu{display:none!important;}footer{display:none!important;}"
)

# Inline SVG icon used by the check-in success card (no font, no emoji).
_ICON_PATHS = {
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
}

# (key, label, page-or-None, material-icon, coming_soon)
_NAV = [
    ("attendance", "Attendance", "app.py", ":material/fact_check:", False),
    ("cafeteria", "Cafeteria", "pages/2_Cafeteria.py", ":material/restaurant:", False),
    ("library", "Library", None, ":material/menu_book:", True),
    ("dormitory", "Dormitory", None, ":material/apartment:", True),
]


def icon_svg(name: str, size: int = 20, color: str = "currentColor", stroke: float = 1.8) -> str:
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" style="vertical-align:middle;">{_ICON_PATHS[name]}</svg>'
    )


def _hide_chrome() -> None:
    """Hide Streamlit's dev toolbar, the page nav, and (best effort) the badges."""
    st.markdown(
        '<style>'
        '[data-testid="stToolbar"]{display:none!important;}'
        '[data-testid="stToolbarActions"]{display:none!important;}'
        '[data-testid="stDecoration"]{display:none!important;}'
        '[data-testid="stSidebarNav"]{display:none!important;}'
        '[data-testid="stStatusWidget"]{display:none!important;}'
        '[data-testid="manage-app-button"]{display:none!important;}'
        '.stAppDeployButton{display:none!important;}'
        'header[data-testid="stHeader"] a[href*="github.com"]{display:none!important;}'
        'a[href*="streamlit.io"]{display:none!important;}'
        '[class*="viewerBadge"]{display:none!important;}'
        '#MainMenu{display:none!important;}footer{display:none!important;}'
        # Remove the empty top header bar and trim the big top gap
        'header[data-testid="stHeader"]{display:none!important;}'
        '.block-container{padding-top:1rem!important;}'
        # Make the module nav look like compact chips
        '[data-testid="stPageLink"] a{justify-content:center;border:1px solid rgba(20,41,76,.18);'
        'border-radius:8px;padding:8px 2px;}'
        '[data-testid="stPageLink"] a span,[data-testid="stPageLink"] a p{white-space:nowrap;font-size:12px;}'
        '[data-testid="stPageLink"] a:hover{background:rgba(29,158,117,.10);border-color:#1D9E75;}'
        '[class*="st-key-nav_"] button p{white-space:nowrap;font-size:12px;}'
        '[class*="st-key-nav_"] button{padding-left:2px;padding-right:2px;}'
        # Pull the 0-height helper component out of flow so it adds no gap
        '[data-testid="stElementContainer"]:has(> iframe[data-testid="stIFrame"])'
        '{position:absolute!important;height:0!important;width:0!important;overflow:hidden!important;}'
        '</style>',
        unsafe_allow_html=True,
    )


def _persist_chrome_hide() -> None:
    """Inject the chrome-hiding CSS into the PARENT document <head> so it stays
    applied across page navigations — prevents the brief Fork-badge flash."""
    components.html(
        "<script>(function(){try{var d=window.parent.document;"
        "var s=d.getElementById('qrunipass-hide');"
        "if(!s){s=d.createElement('style');s.id='qrunipass-hide';d.head.appendChild(s);}"
        "s.textContent=" + json.dumps(_PERSIST_CSS) + ";}catch(e){}})();</script>",
        height=0,
    )


def render_header(active: str = "") -> None:
    """Navy brand bar + tagline + the four campus-module nav chips.

    Built modules (Attendance, Cafeteria) navigate instantly; Library and
    Dormitory are disabled with a "Coming soon" tooltip.
    """
    _persist_chrome_hide()
    _hide_chrome()
    st.markdown(
        f'<div style="background:{NAVY};border-radius:12px;padding:14px 16px;margin-bottom:10px;">'
        f'<div style="font-size:19px;font-weight:600;color:#fff;">QR UniPass</div>'
        f'<div style="font-size:12px;color:rgba(255,255,255,0.78);margin-top:1px;">'
        f'One QR for the whole campus</div></div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for col, (key, label, page, icon, soon) in zip(cols, _NAV):
        with col:
            if soon:
                st.button(f"{label} · Soon", icon=icon, disabled=True, help="Coming soon",
                          width="stretch", key=f"nav_{key}")
            elif key == active:
                # Current page — filled (teal) so you can tell where you are.
                st.button(label, icon=icon, type="primary", width="stretch", key=f"nav_{key}")
            else:
                st.page_link(page, label=label, icon=icon, width="stretch")
