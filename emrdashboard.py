import streamlit as st
import pandas as pd
import plotly.express as px

# Page settings
st.set_page_config(page_title="EMR Dashboard", layout="wide")
st.title("📊 Ogun EMR Weekly Facility Dashboard")

# Load Excel data directly (no uploader)
@st.cache_data
def load_data():
    return pd.read_excel("EMR_NDR CONC_120725.xlsx", sheet_name="Conc", engine="openpyxl")

# Load the data
try:
    df = load_data()
    df = df.dropna(subset=['FacilityName'])

    # Sidebar filters
    with st.sidebar:
        st.header("📌 Filters")

        # State filter
        state_options = df['State'].dropna().unique()
        states = st.multiselect("State(s)", state_options)

        # Apply state filter to get LGA options
        df_lga = df[df['State'].isin(states)] if states else df.copy()
        lga_options = df_lga['LGA'].dropna().unique()
        lgas = st.multiselect("LGA(s)", lga_options)

        # Apply LGA filter to get Facility options
        df_fac = df_lga[df_lga['LGA'].isin(lgas)] if lgas else df_lga.copy()
        fac_options = df_fac['FacilityName'].dropna().unique()
        facilities = st.multiselect("Facility(s)", fac_options)

        # Apply Filters Button
        apply_filter = st.button("✅ Apply Filters")

    # Wait for user to click "Apply Filters"
    if apply_filter:
        filtered_df = df.copy()
        if states:
            filtered_df = filtered_df[filtered_df['State'].isin(states)]
        if lgas:
            filtered_df = filtered_df[filtered_df['LGA'].isin(lgas)]
        if facilities:
            filtered_df = filtered_df[filtered_df['FacilityName'].isin(facilities)]

        # Core indicators
        tx_curr = filtered_df['TX_Curr_EMR'].sum()
        tx_new = filtered_df['TX_New_EMR'].sum()
        vl_eligible = filtered_df['VL Eligible EMR'].sum()
        tx_pvls_d = filtered_df['TX_PVLS_D_EMR'].sum()
        tx_pvls_n = filtered_df['TX_PVLS_N_EMR'].sum()

        # New indicators
        pbs = filtered_df['PBS_EMR'].sum()
        pbs_recaptured = filtered_df['PBS Recaptured_EMR'].sum()
        iit_cases = filtered_df['IIT Quarter'].sum()
        fingerprints = filtered_df['PBS_NDR'].sum()

        # Calculated ratios
        vl_coverage = (tx_pvls_d / vl_eligible * 100) if vl_eligible > 0 else 0
        vl_suppression = (tx_pvls_n / tx_pvls_d * 100) if tx_pvls_d > 0 else 0

        # KPIs Display
        st.subheader("📊 Key Program Indicators (KPIs)")
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("TX_CURR", f"{tx_curr:,}")
        kpi2.metric("TX_NEW", f"{tx_new:,}")
        kpi3.metric("VL Eligible", f"{vl_eligible:,}")
        kpi4.metric("VL Coverage (%)", f"{vl_coverage:.1f}%")
        kpi5.metric("VL Suppression (%)", f"{vl_suppression:.1f}%")

        kpi6, kpi7, kpi8, kpi9 = st.columns(4)
        kpi6.metric("PBS Enrolled", f"{pbs:,}")
        kpi7.metric("PBS Recaptured", f"{pbs_recaptured:,}")
        kpi8.metric("IIT Cases", f"{iit_cases:,}")
        kpi9.metric("Fingerprint Enrolled", f"{fingerprints:,}")

        st.divider()

        # TX_CURR by Facility
        st.subheader("🏥 TX_CURR by Facility")
        tx_curr_chart = filtered_df.groupby('FacilityName')['TX_Curr_EMR'].sum().reset_index()
        fig1 = px.bar(tx_curr_chart, x='FacilityName', y='TX_Curr_EMR', title="TX_CURR Distribution", height=400)
        st.plotly_chart(fig1, use_container_width=True)

        # VL Suppression by LGA
        st.subheader("🧪 VL Suppression Rate by LGA")
        vl_chart = filtered_df.groupby('LGA').agg({
            'TX_PVLS_D_EMR': 'sum',
            'TX_PVLS_N_EMR': 'sum'
        }).reset_index()
        vl_chart['VL Suppression (%)'] = vl_chart['TX_PVLS_N_EMR'] / vl_chart['TX_PVLS_D_EMR'] * 100
        fig2 = px.bar(vl_chart, x='LGA', y='VL Suppression (%)', color='LGA', title="VL Suppression by LGA", height=400)
        st.plotly_chart(fig2, use_container_width=True)

        # VL Coverage by LGA
        st.subheader("🧪 VL Coverage by LGA")
        vl_chart = filtered_df.groupby('LGA').agg({
            'VL Eligible EMR': 'sum',
            'TX_PVLS_D_EMR': 'sum'
        }).reset_index()
        vl_chart['VL Coverage (%)'] = vl_chart['TX_PVLS_D_EMR'] / vl_chart['VL Eligible EMR'] * 100
        fig3 = px.bar(vl_chart, x='LGA', y='VL Coverage (%)', color='LGA', title="VL Coverage by LGA", height=400)
        st.plotly_chart(fig3, use_container_width=True)

        # Filtered data table
        st.subheader("📄 Filtered Data Preview")
        st.dataframe(filtered_df.head(100))

        # Download as CSV
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        st.download_button("📅 Download Filtered Data as CSV",
                           data=convert_df(filtered_df),
                           file_name="filtered_data.csv",
                           mime="text/csv")
    else:
        st.info("👈 Select your filters and click '✅ Apply Filters' to load dashboard.")

except FileNotFoundError:
    st.error("⚠️ The data file was not found. Please make sure 'data/emr_dashboard.xlsx' exists.")
