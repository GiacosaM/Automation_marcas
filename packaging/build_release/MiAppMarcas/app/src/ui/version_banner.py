"""
Muestra la versión en la UI. El texto proviene de version.py (sin duplicar strings).
"""
import streamlit as st


def render_version_banner(app_display: str, *, show_in_sidebar: bool = True) -> None:
    st.markdown(
        f'<div style="text-align:right;color:#9ca3af;font-size:0.85rem;font-weight:500;'
        f'padding:0.25rem 0 0.75rem 0;border-bottom:1px solid rgba(255,255,255,0.06);'
        f'margin-bottom:0.75rem;">{app_display}</div>',
        unsafe_allow_html=True,
    )
    if show_in_sidebar:
        st.sidebar.caption(app_display)
