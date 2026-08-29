import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io

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
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            color: #f8fafc;
        }
        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(16px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.125) !important;
            border-radius: 20px !important;
            padding: 2.5rem !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4) !important;
            max-width: 450px;
            margin: 2rem auto;
        }
        div[data-testid="stForm"] input {
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
        }
        div[data-testid="stForm"] button {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 0.6rem 1rem !important;
            width: 100%;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 18px 22px;
            border-radius: 14px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        }
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

with st.sidebar:
    st.markdown("### 👤 Account Control")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    st.markdown("---")

    st.header("⚙️ Data Settings")
    use_manual_upload = st.checkbox("Override with manual file upload")

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

st.title("📊 Executive Ticket & CHG Analytics")
st.caption("Real-time Operational Performance & Team Recognition Leaderboard")

if df is not None:
    df.columns = df.columns.str.strip()

    # Column mappings
    opened_col = next((col for col in df.columns if 'open' in col.lower()), None)
    assigned_col = next((col for col in df.columns if 'assigned to' in col.lower() or 'assignee' in col.lower()), None)
    sla_col = next((col for col in df.columns if 'sla' in col.lower() and 'made' in col.lower()), None)

    if opened_col:
        df[opened_col] = pd.to_datetime(df[opened_col], errors='coerce')
        now = pd.Timestamp.now()
        df['Age_Days'] = (now - df[opened_col]).dt.days
        df['Age_Weeks'] = df['Age_Days'] / 7

        bins = [-np.inf, 1, 2, 4, 8, np.inf]
        labels = ['0-1 Wks', '1-2 Wks', '2-4 Wks', '4-8 Wks', '>8 Wks']
        df['Ageing_Bucket'] = pd.cut(df['Age_Weeks'], bins=bins, labels=labels)

    # Sidebar Global Filters
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

    sla_breaches = len(df[df[sla_col] == False]) if sla_col else 0
    col4.metric("SLA Breaches", f"{sla_breaches:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Main Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Executive Summary", 
        "🏆 Top Performers & Recognition", 
        "📊 Breakdown Analytics", 
        "📑 Sheet & Export Data"
    ])

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
            st.subheader("⏰ SLA Performance Summary")
            if sla_col:
                sla_df = df[sla_col].value_counts().reset_index()
                sla_df.columns = ['Made SLA Status', 'Incident Count']
                st.dataframe(sla_df, use_container_width=True)
            else:
                st.info("SLA Status column not available.")

    with tab2:
        st.subheader("🏆 Team Leaderboard & Appreciation Matrix")
        st.caption("Highlighting top resolution speeds and workload completion.")

        if assigned_col:
            perf_df = df.groupby(assigned_col).agg(
                Total_Resolved=('Age_Days', 'count'),
                Avg_Resolution_Days=('Age_Days', 'mean')
            ).reset_index()

            if sla_col:
                sla_stats = df.groupby(assigned_col)[sla_col].apply(lambda x: (x == True).mean() * 100).reset_index()
                sla_stats.columns = [assigned_col, 'SLA_Compliance_%']
                perf_df = perf_df.merge(sla_stats, on=assigned_col)

            # Sort by fastest average resolution
            perf_df['Avg_Resolution_Days'] = perf_df['Avg_Resolution_Days'].round(1)
            perf_df = perf_df.sort_values(by=['Total_Resolved', 'Avg_Resolution_Days'], ascending=[False, True])

            # Top Performers Highlight Cards
            top_col1, top_col2 = st.columns(2)
            with top_col1:
                top_resolver = perf_df.iloc[0][assigned_col] if len(perf_df) > 0 else "N/A"
                st.success(f"🌟 **Most Tickets Closed:** {top_resolver}")
            with top_col2:
                fastest = perf_df.sort_values(by='Avg_Resolution_Days', ascending=True).iloc[0][assigned_col] if len(perf_df) > 0 else "N/A"
                st.info(f"⚡ **Fastest Avg Turnaround:** {fastest}")

            st.dataframe(
                perf_df.rename(columns={
                    assigned_col: "Assignee Name",
                    "Total_Resolved": "Tickets Handled",
                    "Avg_Resolution_Days": "Avg Resolution (Days)",
                    "SLA_Compliance_%": "SLA Compliance %"
                }),
                use_container_width=True
            )
        else:
            st.info("Column for 'Assigned To' not found in dataset.")

    with tab3:
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
            if 'Ageing_Bucket' in df.columns:
                st.bar_chart(df['Ageing_Bucket'].value_counts())

    with tab4:
        st.subheader("📑 Interactive Data Sheet & Export Center")
        
        # Download Action Button
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Filtered_Incidents')
        
        st.download_button(
            label="📥 Download Current Sheet (.xlsx)",
            data=buffer.getvalue(),
            file_name="Incident_Report_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.dataframe(df, use_container_width=True, height=400)

else:
    st.error("Dataset missing. Verify configuration or upload manually via sidebar.")
