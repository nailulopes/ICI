"""ICI Dashboard — Login + Router"""
import streamlit as st

st.set_page_config(
    page_title="ICI Dashboard",
    page_icon="🤱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load secrets ──────────────────────────────────────────────────────────────
try:
    PASSWORDS = {
        "facility_a": st.secrets["facility_a_password"],
        "facility_b": st.secrets["facility_b_password"],
        "admin":      st.secrets["admin_password"],
    }
except Exception:
    st.error("⚠ Secrets not configured. Add facility_a_password, facility_b_password, admin_password to Streamlit Secrets.")
    st.stop()

FACILITY_NAMES = {
    "facility_a": "Facility A",
    "facility_b": "Facility B",
}

# ── Login gate ────────────────────────────────────────────────────────────────
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    # Show login screen
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&family=DM+Serif+Display&display=swap');
    html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
    </style>
    <div style="max-width:420px;margin:80px auto 0 auto;padding:44px;background:white;
         border-radius:24px;box-shadow:0 4px 40px rgba(0,0,0,0.10);text-align:center;">
        <div style="font-family:'DM Serif Display',serif;font-size:1.8rem;color:#005f46;margin-bottom:4px;">
            ICI Dashboard
        </div>
        <div style="font-size:0.8rem;color:#888;margin-bottom:32px;">
            International Childbirth Initiative
        </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        pwd = st.text_input("Password", type="password", placeholder="Enter your password…")
        if st.button("Enter", use_container_width=True, type="primary"):
            matched = None
            for role, password in PASSWORDS.items():
                if pwd == password:
                    matched = role
                    break
            if matched:
                st.session_state.role = matched
                st.rerun()
            else:
                st.error("Incorrect password.")
    st.stop()

# ── Route to correct pages based on role ─────────────────────────────────────
role = st.session_state.role

if role == "admin":
    pages = [
        st.Page("pages/women.py",    title="Women's Experience", icon="👩"),
        st.Page("pages/companion.py",title="Companion Experience", icon="🤝"),
        st.Page("pages/compare.py",  title="Facility Comparison", icon="📊"),
    ]
else:
    pages = [
        st.Page("pages/women.py",    title="Women's Experience", icon="👩"),
        st.Page("pages/companion.py",title="Companion Experience", icon="🤝"),
    ]

pg = st.navigation(pages)
pg.run()
