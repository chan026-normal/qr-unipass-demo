"""Shared UI bits — branded header, line icons, and chrome hiding.

Icons are inline SVG (no external font / no emoji) so they always render,
even on a flaky venue network.
"""
import streamlit as st

NAVY = "#14294C"

# Simple outline icons drawn as SVG primitives (24x24, stroke = currentColor).
_ICON_PATHS = {
    "attendance": '<rect x="5" y="4" width="14" height="17" rx="2"/>'
                  '<rect x="9" y="2.5" width="6" height="3" rx="1"/>'
                  '<path d="M9 13l2 2 4-4"/>',
    # fork + knife (utensils)
    "cafeteria": '<path d="M8 3v4.5a1.7 1.7 0 0 0 3.4 0V3"/><path d="M9.7 7.5V21"/>'
                 '<path d="M16 3c-1.7 .5-2.8 2.7-2.8 5 0 1.6 1.2 2.6 2.8 2.6V21"/>',
    "library": '<path d="M12 6c-2.2-1.4-5.2-1.4-8 0v12c2.8-1.4 5.8-1.4 8 0 '
               '2.2-1.4 5.2-1.4 8 0V6c-2.8-1.4-5.8-1.4-8 0z"/><path d="M12 6v12"/>',
    "dormitory": '<rect x="5" y="3" width="14" height="18" rx="1"/>'
                 '<path d="M9 7h2M13 7h2M9 11h2M13 11h2"/><path d="M10 21v-4h4v4"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/>',
}

# (key, label, coming_soon)
_MODULES = [
    ("attendance", "Attendance", False),
    ("cafeteria", "Cafeteria", False),
    ("library", "Library", True),
    ("dormitory", "Dormitory", True),
]


def icon_svg(name: str, size: int = 20, color: str = "currentColor", stroke: float = 1.8) -> str:
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" style="vertical-align:middle;">{_ICON_PATHS[name]}</svg>'
    )


def _hide_chrome() -> None:
    """Hide Streamlit's dev toolbar, the GitHub/Fork badge, and the page nav."""
    st.markdown(
        '<style>'
        '[data-testid="stToolbar"]{display:none!important;}'
        '[data-testid="stToolbarActions"]{display:none!important;}'
        '[data-testid="stDecoration"]{display:none!important;}'
        '[data-testid="stSidebarNav"]{display:none!important;}'
        'header[data-testid="stHeader"] a[href*="github.com"]{display:none!important;}'
        '[class*="viewerBadge"]{display:none!important;}'
        '#MainMenu{display:none!important;}footer{display:none!important;}'
        '</style>',
        unsafe_allow_html=True,
    )


def render_header(active: str = "") -> None:
    """Navy brand bar + tagline + the four campus-module icons (info only).

    `active` highlights one available module; the unbuilt ones show a "Soon" tag.
    """
    _hide_chrome()
    chips = ""
    for key, label, soon in _MODULES:
        on = key == active
        if soon:
            bg, fg = "rgba(255,255,255,0.05)", "rgba(255,255,255,0.45)"
        elif on:
            bg, fg = "rgba(29,158,117,0.22)", "#9FE1CB"
        else:
            bg, fg = "rgba(255,255,255,0.07)", "rgba(255,255,255,0.78)"
        badge = (
            '<div style="font-size:9px;color:#9FE1CB;background:rgba(29,158,117,0.18);'
            'border-radius:6px;display:inline-block;padding:0 5px;margin-top:3px;">Soon</div>'
            if soon else ''
        )
        chips += (
            f'<div style="flex:1;text-align:center;background:{bg};border-radius:8px;padding:7px 2px;">'
            f'<div style="line-height:1;color:{fg};">{icon_svg(key, size=20, color=fg)}</div>'
            f'<div style="font-size:11px;color:{fg};margin-top:3px;">{label}</div>'
            f'{badge}'
            f'</div>'
        )
    st.markdown(
        f'<div style="background:{NAVY};border-radius:12px;padding:14px 16px;margin-bottom:14px;">'
        f'<div style="font-size:19px;font-weight:600;color:#fff;">QR UniPass</div>'
        f'<div style="font-size:12px;color:rgba(255,255,255,0.78);margin-top:1px;">'
        f'One QR for the whole campus</div>'
        f'<div style="display:flex;gap:6px;margin-top:12px;align-items:flex-start;">{chips}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
