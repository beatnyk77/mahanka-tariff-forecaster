import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import base64
from utils.api_functions import get_tariff_data, get_trade_flow_data, calculate_duty
from samples.demo_data import get_demo_scenario

# --- Config ---
st.set_page_config(
    page_title="Mahanka Trade Uncertainty & Tariff Impact Forecaster",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Styling ---
st.markdown("""
<style>
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #FF4B4B; }
    .savings-card { background-color: #e8fdf5; padding: 20px; border-radius: 10px; border-left: 5px solid #2ecc71; }
    .main-header { font-size: 2.5rem; color: #1e1e1e; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    .sub-header { font-size: 1.2rem; color: #555; margin-bottom: 2rem; }
    .upsell-card { background-color: #fff9c4; padding: 20px; border-radius: 10px; border: 1px solid #fbc02d; margin-top: 30px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.image("https://placehold.co/200x60/d32f2f/FFFFFF?text=Mahanka", use_container_width=True) 
st.sidebar.title("Configuration")

use_sample = st.sidebar.button("Load Sample Data (Smartphones)")

if use_sample:
    sample = get_demo_scenario()
    st.session_state.update({k: sample[k] for k in ['hs_code', 'current_supplier', 'market', 'annual_value', 'base_margin']})
    # Map old keys if needed
    st.session_state['supplier'] = st.session_state.get('current_supplier') 
    st.session_state['value'] = st.session_state.get('annual_value')
    st.session_state['margin'] = st.session_state.get('base_margin')

hs_code = st.sidebar.text_input("Product HS Code", value=st.session_state.get('hs_code', '851713'))
supplier = st.sidebar.selectbox("Current Supplier Country", ["China", "Vietnam", "India", "Mexico", "Germany"], 
                                index=0 if st.session_state.get('supplier') == 'China' else 2) 
market = st.sidebar.selectbox("Target Market", ["USA", "EU", "India"], index=0 if st.session_state.get('market') == 'USA' else 0)
annual_value = st.sidebar.number_input("Annual Import Value (USD)", min_value=0, value=int(st.session_state.get('value', 1000000)))
current_margin = st.sidebar.slider("Current Net Margin (%)", 0.0, 50.0, float(st.session_state.get('margin', 15.0)))

st.sidebar.markdown("---")
st.sidebar.header("Scenario Simulation")
shock_tariff = st.sidebar.slider("Additional Tariff Shock (%)", 0, 100, 25)

# --- Header ---
st.markdown('<div class="main-header">Mahanka Trade Uncertainty & Tariff Impact Forecaster</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Model 2025 Tariff Risks & Discover Cheaper Suppliers – Free Tool for Indian Businesses</div>', unsafe_allow_html=True)

# --- Logic ---
tariff_info = get_tariff_data(hs_code, market, supplier)
base_tariff_rate = tariff_info['mf_rate']
total_scenario_rate = base_tariff_rate + shock_tariff

current_duty = calculate_duty(annual_value, base_tariff_rate)
scenario_duty = calculate_duty(annual_value, total_scenario_rate)
duty_increase = scenario_duty - current_duty

current_profit = annual_value * (current_margin/100.0)
scenario_profit = current_profit - duty_increase
scenario_margin = (scenario_profit / annual_value) * 100.0
profit_impact_pct = ((scenario_profit - current_profit) / current_profit) * 100 if current_profit != 0 else -100

# --- Metrics ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Current Duty (USD)", f"${current_duty:,.0f}", f"{base_tariff_rate}% Rate")
c2.metric("Projected Duty (+Shock)", f"${scenario_duty:,.0f}", f"{total_scenario_rate}% Eff. Rate", delta_color="inverse")
c3.metric("Profit Impact", f"{profit_impact_pct:.1f}%", f"${duty_increase:,.0f} Cost", delta_color="inverse")
c4.metric("New Net Margin", f"{scenario_margin:.1f}%", f"{scenario_margin - current_margin:.1f}%", delta_color="normal" if (scenario_margin - current_margin) > 0 else "inverse")

if scenario_margin < 0:
    st.error(f"⚠️ **Critical Warning:** Margin becomes negative ({scenario_margin:.1f}%) under this shock scenario.")

# --- Tabs ---
tab1, tab2 = st.tabs(["Impact Analytics", "Diversification Map"])

with tab1:
    col_chart, col_waterfall = st.columns(2)
    
    with col_chart:
        st.subheader("Duty Sensitivity Analysis")
        shocks = [0, 25, 50, 100]
        costs = [calculate_duty(annual_value, base_tariff_rate + s) for s in shocks]
        fig_bar = px.bar(x=[f"+{s}%" for s in shocks], y=costs, 
                         labels={'x': 'Shock Scenario', 'y': 'Duty Cost (USD)'},
                         title="Duty Liability at Different Shock Levels",
                         color=costs, color_continuous_scale='Reds')
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_waterfall:
        st.subheader("Cost Structure Walk")
        fig_waterfall = go.Figure(go.Waterfall(
            name = "20", orientation = "v",
            measure = ["relative", "relative", "total", "relative", "total"],
            x = ["Base Cost", "Curr. Duty", "Total Now", "Tariff Shock", "Projected"],
            y = [annual_value, current_duty, annual_value + current_duty, duty_increase, annual_value + scenario_duty],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        st.plotly_chart(fig_waterfall, use_container_width=True)

with tab2:
    st.subheader("Global Alternative Suppliers")
    trade_df = get_trade_flow_data(hs_code, market)
    
    # Simple logic for potential savings
    def calc_potential_savings(row):
        # Mock logic: Vietnam/India/Mexico often cheaper than China
        est_rate = 0.0 if row['partner'] in ['Vietnam', 'India', 'Mexico'] else 5.0
        proj_duty = calculate_duty(annual_value, est_rate)
        return scenario_duty - proj_duty, est_rate

    trade_df[['potential_savings', 'est_tariff']] = trade_df.apply(lambda x: pd.Series(calc_potential_savings(x)), axis=1)
    trade_df = trade_df.sort_values('potential_savings', ascending=False)
    
    fig_map = px.choropleth(
        trade_df, locations="partner", locationmode='country names',
        color="est_tariff", hover_name="partner", hover_data=["potential_savings", "risk_level"],
        color_continuous_scale="RdYlGn_r", title="Tariff Rate Heatmap (Lower is Better)"
    )
    st.plotly_chart(fig_map, use_container_width=True)
    
    best_alt = trade_df.iloc[0]
    st.success(f"**Recommendation:** Sourcing from **{best_alt['partner']}** could save **${best_alt['potential_savings']:,.0f}** annually.")

# --- PDF Report ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(40, 10, f"Mahanka Tariff Forecast: HS {hs_code}")
    pdf.ln(20)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.cell(0, 10, f"Scenario: {supplier} -> {market}", ln=True)
    pdf.cell(0, 10, f"Annual Value: ${annual_value:,.0f}", ln=True)
    pdf.cell(0, 10, f"Base Tariff: {base_tariff_rate}% | Shock: +{shock_tariff}%", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Financial Impact", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Current Duty: ${current_duty:,.0f}", ln=True)
    pdf.cell(0, 10, f"Projected Duty: ${scenario_duty:,.0f}", ln=True)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(0, 10, f"Increase: ${duty_increase:,.0f}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.cell(0, 10, f"Recommended Alternative: {best_alt['partner']} (Save ${best_alt['potential_savings']:,.0f})", ln=True)
    return pdf.output(dest='S').encode('latin-1')

st.markdown("### Export Report")
if st.button("Generate PDF Report"):
    pdf_bytes = create_pdf()
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="mahanka_report.pdf">Download PDF Report</a>'
    st.markdown(href, unsafe_allow_html=True)

# --- Upsell ---
st.markdown("""
<div class="upsell-card">
    <h3>📉 Tariff Risks are Real. Is Your Supply Chain Ready?</h3>
    <p>Mahanka helps Indian businesses hedge forex risks, finance supply chains, and navigate trade compliance.</p>
    <a href="https://mahanka.com/consultation" target="_blank" style="background-color: #d32f2f; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Book Free CFO Consultation</a>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption("Disclaimer: Live data via WITS/Comtrade (2023-2024). 2025 scenarios are simulations. Consult trade counsel.")
