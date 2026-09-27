import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.assistant import render_assistant_page
from components.dashboard import render_dashboard
from components.history import render_history_page
from components.inspection import render_inspection_page
from components.login import render_auth_view
from components.profile import render_profile_page
from database.database import init_db

st.set_page_config(page_title="AI Product Quality Inspector", page_icon="🧪", layout="wide")


def inject_custom_css():
    st.markdown(
        """
        <style>
        :root {
            --bg-1: #07111f;
            --bg-2: #0d1b2a;
            --panel: rgba(17, 25, 40, 0.78);
            --panel-strong: rgba(20, 32, 48, 0.96);
            --line: rgba(148, 163, 184, 0.2);
            --primary: #6ee7b7;
            --primary-2: #60a5fa;
            --text: #e5eefb;
            --muted: #a5b4c9;
            --success: #34d399;
            --warning: #fbbf24;
            --danger: #f87171;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, var(--bg-1), var(--bg-2));
            color: var(--text);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        [data-testid="stSidebar"] {
            background: rgba(8, 15, 25, 0.9);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] .stMarkdown {
            color: var(--text);
        }

        .stTabs [role="tablist"] {
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .stTabs [role="tab"] {
            background: rgba(148, 163, 184, 0.08);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 0.55rem 1rem;
            color: var(--text);
        }

        .stTabs [role="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(110, 231, 183, 0.18), rgba(96, 165, 250, 0.18));
            border-color: rgba(96, 165, 250, 0.5);
            color: white;
        }

        .stButton > button {
            background: linear-gradient(135deg, var(--primary-2), var(--primary));
            color: #05121a;
            border: none;
            border-radius: 12px;
            font-weight: 700;
            padding: 0.7rem 1.2rem;
            box-shadow: 0 8px 20px rgba(96, 165, 250, 0.2);
        }

        .stButton > button:hover {
            filter: brightness(1.05);
            transform: translateY(-1px);
        }

        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input,
        .stSelectbox > div > div > select,
        .stTextArea > div > textarea {
            background: rgba(15, 23, 35, 0.9);
            color: var(--text);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
        }

        .stMetric {
            background: linear-gradient(180deg, rgba(15, 23, 35, 0.7), rgba(15, 23, 35, 0.9));
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 24px rgba(2, 6, 23, 0.25);
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .hero-panel {
            background: linear-gradient(135deg, rgba(96, 165, 250, 0.14), rgba(110, 231, 183, 0.12));
            border: 1px solid rgba(96, 165, 250, 0.25);
            border-radius: 22px;
            padding: 1.5rem 1.75rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 16px 40px rgba(2, 6, 23, 0.24);
        }

        .hero-badge {
            display: inline-block;
            background: rgba(110, 231, 183, 0.12);
            color: var(--primary);
            border: 1px solid rgba(110, 231, 183, 0.3);
            border-radius: 999px;
            padding: 0.35rem 0.8rem;
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }

        .section-card {
            background: rgba(15, 23, 35, 0.72);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 24px rgba(2, 6, 23, 0.2);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


inject_custom_css()

init_db()

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "pending_user" not in st.session_state:
    st.session_state.pending_user = None
if "pending_verification" not in st.session_state:
    st.session_state.pending_verification = False
if "dev_otp" not in st.session_state:
    st.session_state.dev_otp = None
if "inspect_history" not in st.session_state:
    st.session_state.inspect_history = []
if "current_inspection" not in st.session_state:
    st.session_state.current_inspection = None
if "assistant_history" not in st.session_state:
    st.session_state.assistant_history = []


def logout_user():
    st.session_state.user = None
    st.session_state.page = "login"
    st.session_state.pending_user = None
    st.session_state.pending_verification = False
    st.session_state.dev_otp = None
    st.session_state.current_inspection = None
    st.session_state.assistant_history = []
    st.rerun()


if st.session_state.user is None:
    render_auth_view()
else:
    user = st.session_state.user
    if not user.get("is_verified", False):
        from components.login import render_verification_screen
        render_verification_screen(user)
    else:
        with st.sidebar:
            st.title("AI PRODUCT QUALITY INSPECTOR")
            st.caption(f"Welcome, {user['full_name']}")
            st.markdown("---")
            nav = st.radio(
                "Navigation",
                ["Dashboard", "New Inspection", "Inspection History", "AI Quality Assistant", "Reports", "Profile"],
                index=0,
                label_visibility="collapsed",
            )
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                logout_user()

        if nav == "Dashboard":
            render_dashboard(user)
        elif nav == "New Inspection":
            render_inspection_page(user)
        elif nav == "Inspection History":
            render_history_page(user)
        elif nav == "AI Quality Assistant":
            render_assistant_page(user)
        elif nav == "Reports":
            from components.dashboard import render_reports_page
            render_reports_page(user)
        elif nav == "Profile":
            render_profile_page(user)
