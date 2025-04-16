
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title="Wine Locals • Dashboard", layout="wide")

# Título e identidade
st.markdown("""
    <style>
    .main { background-color: #faf8f6; }
    .block-container { padding-top: 2rem; }
    .metric-label { font-size: 14px !important; color: #5f0f40; }
    .metric-value { font-size: 24px !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🍷 Wine Locals • Dashboard de Vendas")

# Carregar dados do Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1iGN1gCZILFY1ejwz6IBhrOikC_aIMs5xUkEsCE2DW3U/export?format=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(sheet_url)
    df["DATA DE VENDA"] = pd.to_datetime(df["DATA DE VENDA"], errors="coerce", dayfirst=True)
    df["DATA DA EXPERIÊNCIA"] = pd.to_datetime(df["DATA DA EXPERIÊNCIA"], errors="coerce", dayfirst=True)
    df["total"] = df["total"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    df["total"] = pd.to_numeric(df["total"], errors="coerce")
    df["item_id"] = pd.to_numeric(df["item_id"], errors="coerce")
    df["order_status"] = df["order_status"].astype(str).str.lower()
    return df

df = load_data()
df = df[df["order_status"] == "aprovado"]

# Filtros globais
st.sidebar.header("Filtros")
date_type = st.sidebar.radio("Data Base", ["DATA DE VENDA", "DATA DA EXPERIÊNCIA"])
date_col = "DATA DE VENDA" if date_type == "DATA DE VENDA" else "DATA DA EXPERIÊNCIA"

min_date = df[date_col].min()
max_date = df[date_col].max()
start_date, end_date = st.sidebar.date_input("Período", [min_date, max_date])
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

clientes = st.sidebar.multiselect("Clientes", df["client_name"].dropna().unique())
canais = st.sidebar.multiselect("Canais", df["CANAL"].dropna().unique())
campanhas = st.sidebar.multiselect("Campanhas", df["Campanha"].dropna().unique())

# Filtro aplicado
df_filt = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
if clientes:
    df_filt = df_filt[df_filt["client_name"].isin(clientes)]
if canais:
    df_filt = df_filt[df_filt["CANAL"].isin(canais)]
if campanhas:
    df_filt = df_filt[df_filt["Campanha"].isin(campanhas)]

# Comparativos
period_days = (end_date - start_date).days
previous_start = start_date - timedelta(days=period_days + 1)
previous_end = end_date - timedelta(days=period_days + 1)
last_year_start = start_date - timedelta(days=365)
last_year_end = end_date - timedelta(days=365)

df_prev = df[(df[date_col] >= previous_start) & (df[date_col] <= previous_end)]
df_yoy = df[(df[date_col] >= last_year_start) & (df[date_col] <= last_year_end)]

def get_metrics(data):
    return {
        "TPV": data["total"].sum(),
        "Compras": data["partner_order_id"].nunique(),
        "Tickets": data["item_id"].sum(),
        "Ticket Médio": data["total"].sum() / data["item_id"].sum() if data["item_id"].sum() > 0 else 0
    }

def compare(val1, val2):
    if val2 == 0: return "—", "—"
    diff = val1 - val2
    pct = (diff / val2) * 100
    return f"{pct:+.1f}%", f"R$ {abs(diff):,.0f}"

# Abas principais
aba = st.tabs(["📊 Visão Geral", "📈 Marketing & Canais", "📋 Tabela Detalhada"])[0]

metrics = get_metrics(df_filt)
metrics_prev = get_metrics(df_prev)
metrics_yoy = get_metrics(df_yoy)

# VISÃO GERAL
with st.tabs(["📊 Visão Geral", "📈 Marketing & Canais", "📋 Tabela Detalhada"])[0]:
    st.markdown(f"### Período selecionado: `{start_date.date()}` até `{end_date.date()}`")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TPV", f'R$ {metrics["TPV"]:,.0f}', f'{compare(metrics["TPV"], metrics_prev["TPV"])[0]} vs mês anterior')
    col2.metric("Compras", metrics["Compras"], f'{compare(metrics["Compras"], metrics_prev["Compras"])[0]} vs mês anterior')
    col3.metric("Tickets", int(metrics["Tickets"]), f'{compare(metrics["Tickets"], metrics_prev["Tickets"])[0]} vs mês anterior')
    col4.metric("Ticket Médio", f'R$ {metrics["Ticket Médio"]:,.2f}', f'{compare(metrics["Ticket Médio"], metrics_prev["Ticket Médio"])[0]} vs mês anterior')

    st.markdown("#### 📈 Evolução diária de TPV")
    df_evol = df_filt.groupby(df_filt[date_col].dt.date)["total"].sum().reset_index()
    df_evol.columns = ["Data", "TPV"]
    fig = px.line(df_evol, x="Data", y="TPV")
    st.plotly_chart(fig, use_container_width=True)

# MARKETING
with st.tabs(["📊 Visão Geral", "📈 Marketing & Canais", "📋 Tabela Detalhada"])[1]:
    st.subheader("🎯 Distribuição de canais e campanhas")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(df_filt, names="CANAL", title="Por Canal"), use_container_width=True)
        st.plotly_chart(px.pie(df_filt, names="origin", title="Origem da Venda"), use_container_width=True)
    with col2:
        st.plotly_chart(px.pie(df_filt.dropna(subset=["Campanha"]), names="Campanha", title="Campanhas"), use_container_width=True)
        st.plotly_chart(px.pie(df_filt.dropna(subset=["Estado de Compra"]), names="Estado de Compra", title="Estados"), use_container_width=True)

# TABELA
with st.tabs(["📊 Visão Geral", "📈 Marketing & Canais", "📋 Tabela Detalhada"])[2]:
    st.subheader("📋 Tabela detalhada")
    st.dataframe(df_filt[[
        "partner_order_id", "DATA DE VENDA", "DATA DA EXPERIÊNCIA", "client_name", "experience",
        "item_id", "total", "order_status", "Regiões", "CANAL", "Campanha"
    ]], use_container_width=True)
    st.download_button("📥 Baixar CSV", data=df_filt.to_csv(index=False), file_name="vendas_filtradas.csv", mime="text/csv")
