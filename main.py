import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# Page Configuration
st.set_page_config(
    page_title="Executive Ticket & CHG Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Custom Modern UI Styling
# ---------------------------------------------------------
def apply_custom_css():
    st.markdown("""
        <style>
        /* Modern Background & Fonts */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            color: #f8fafc;
        }

        /* Glassmorphic Login Form */
        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(16px) saturate(180%);
            -webkit-backdrop-filter: blur(16px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.125) !important;
            border-radius: 20px !important;
            padding: 2.5rem !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4) !important;
            max-width: 450px;
            margin: 2rem auto;
            animation: fadeIn 0.8s ease-in-out;
        }

        /* Login Inputs */
        div[data-testid="stForm"] input {
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
        }
        div[data-testid="stForm"] input:focus {
            border-color: #6366f1 !important;
            box-shadow: 0 0 12px rgba(99, 102, 241, 0.4) !important;
        }

        /* Gradient Login Button */
        div[data-testid="stForm"] button {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 0.6rem 1rem !important;
            width: 100%;
        }

        /* Metric Cards Clean Container */
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 18px 22px;
            border-radius: 14px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        }

        /* Tab Navigation Enhancements */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 8px 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .stTabs [aria-selected="true"] {
            background: #6366f1 !important;
            color: white !important;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Authentication System
# ---------------------------------------------------------
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    apply_custom_css()

    _, center_col, _ = st.columns([1, 2.5, 1])

    with center_col:
        st.markdown("<h2 style='text-align: center; font-weight: 700; margin-bottom: 0;'>🔐 Executive Portal</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem;'>Enter credentials to access dashboard</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit_button = st.form_submit_button("Sign In →")

            if submit_button:
                if username == "admin" and password == "ticket123":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

    return False

if not check_password():
    st.stop()

# ---------------------------------------------------------
# Dashboard Application Structure
# ---------------------------------------------------------

# Sidebar Configuration
with st.sidebar:
    st.markdown("### 👤 Account Control")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    st.markdown("---")

    st.header("⚙️ Data Settings")
    use_manual_upload = st.checkbox("Override with manual file upload")

# File & Data Logic
DATA_FILE = Path("INCIDENT_YTD_DUMP.xlsx")
FALLBACK_DATA_FILE = Path("INCIDENT_YTD_DUMP.csv")

@st.cache_data(ttl=300)
def load_local_data(path):
    try:
        return pd.read_excel(path, engine="openpyxl")
    except Exception:
        return None

df = None

if use_manual_upload:
    uploaded_file = st.sidebar.file_uploader("Upload INCIDENT_YTD_DUMP file", type=["xlsx", "csv"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
else:
    st.sidebar.info(f"📁 Source: `{DATA_FILE.name}`")
    source_file = DATA_FILE if DATA_FILE.exists() else FALLBACK_DATA_FILE
    df = load_local_data(source_file) if source_file.exists() else None

# Header Banner
st.title("📊 Executive Ticket & CHG Analytics")
st.caption("Real-time Operational Performance & Incident Tracking")

if df is not None:
    df.columns = df.columns.str.strip()

    # Data Processing Logic
    opened_col = next((col for col in df.columns if 'open' in col.lower()), None)
    if opened_col:
        df[opened_col] = pd.to_datetime(df[opened_col], errors='coerce')
        now = pd.Timestamp.now()
        df['Age_Days'] = (now - df[opened_col]).dt.days
        df['Age_Weeks'] = df['Age_Days'] / 7

        bins = [-np.inf, 1, 2, 4, 8, np.inf]
        labels = ['0-1 Wks', '1-2 Wks', '2-4 Wks', '4-8 Wks', '>8 Wks']
        df['Ageing_Bucket'] = pd.cut(df['Age_Weeks'], bins=bins, labels=labels)

    # Sidebar Dynamic Filters
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Global Filters")

    service_col = next((col for col in df.columns if 'service offering' in col.lower()), None)
    if service_col and df[service_col].notna().any():
        selected_services = st.sidebar.multiselect(
            "Service Offering",
            options=df[service_col].dropna().unique()
        )
        if selected_services:
            df = df[df[service_col].isin(selected_services)]

    assigned_col = next((col for col in df.columns if 'assigned to' in col.lower()), None)
    if assigned_col and df[assigned_col].notna().any():
        selected_assignees = st.sidebar.multiselect(
            "Assigned To",
            options=df[assigned_col].dropna().unique()
        )
        if selected_assignees:
            df = df[df[assigned_col].isin(selected_assignees)]

    # 1. KPI Top Bar Metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Incidents", f"{len(df):,}")

    priority_col = next((col for col in df.columns if 'priority' in col.lower()), None)
    high_prio_count = len(df[df[priority_col].astype(str).str.contains('1|2|High', case=False, na=False)]) if priority_col else 0
    col2.metric("High / Critical Prio", f"{high_prio_count:,}")

    aging_count = len(df[df['Age_Weeks'] > 4]) if 'Age_Weeks' in df.columns else 0
    col3.metric("Ageing (> 4 Weeks)", f"{aging_count:,}")

    sla_col = next((col for col in df.columns if 'sla' in col.lower() and 'made' in col.lower()), None)
    sla_breaches = len(df[df[sla_col] == False]) if sla_col else 0
    col4.metric("SLA Breaches", f"{sla_breaches:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Tab Layout to De-Clutter Interface
    tab1, tab2, tab3 = st.tabs(["📈 Executive Summary", "📊 Breakdown Analytics", "📝 Notes & Raw Data"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📌 Active Incident Ageing Matrix")
            if 'Ageing_Bucket' in df.columns and service_col:
                ageing_table = pd.crosstab(
                    df['Ageing_Bucket'],
                    df[service_col],
                    margins=True,
                    margins_name="Total"
                )
                st.dataframe(ageing_table, use_container_width=True)
            else:
                st.info("Missing required columns for Ageing Matrix calculation.")

        with c2:
            st.subheader("⏰ SLA SLA Performance Summary")
            if sla_col:
                sla_df = df[sla_col].value_counts().reset_index()
                sla_df.columns = ['Made SLA Status', 'Incident Count']
                st.dataframe(sla_df, use_container_width=True)
            else:
                st.info("SLA Status column not available.")

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📋 Priority Volume Breakdown")
            if priority_col:
                priority_summary = df.groupby(priority_col).size().reset_index(name='Ticket Count')
                st.dataframe(priority_summary, use_container_width=True)
            else:
                st.info("Priority column not available.")
        
        with c2:
            st.subheader("📊 Age Distribution Summary")
            if 'Age_Days' in df.columns:
                st.bar_chart(df['Ageing_Bucket'].value_counts())

    with tab3:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("📝 Lead Status Notes")
            st.text_area(
                "TL Status Highlights",
                value="• Operations: Ticket queue cleanup ongoing.\n• PBI R&S Team fix planned for release.\n• Ageing items under daily review.",
                height=220
            )
        with c2:
            st.subheader("🔍 Complete Raw Data Access")
            st.dataframe(df, use_container_width=True, height=220)

else:
    st.error("Dataset missing. Verify configuration or upload manually via sidebar.")
