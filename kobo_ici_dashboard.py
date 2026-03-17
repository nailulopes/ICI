"""ICI Dashboard — Multi-page entrypoint"""
import streamlit as st

st.set_page_config(
    page_title="ICI Dashboard",
    page_icon="🤱",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/women.py",     title="Women's Experience",    icon="👩"),
    st.Page("pages/companion.py", title="Companion Experience",  icon="🤝"),
    st.Page("pages/debug.py",     title="Debug",                 icon="🔍"),
])
pg.run()
