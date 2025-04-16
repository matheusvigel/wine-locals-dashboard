
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title="Wine Locals • Dashboard", layout="wide")
st.title("Wine Locals • Dashboard de Vendas e Marketing 🍷")

# Fonte de dados do Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1iGN1gCZILFY1ejwz6IBhrOikC_aIMs5xUkEsCE2DW3U/export?format=csv"

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(sheet_url)
    df["DATA DE VENDA"] = pd.to_datetime(df["DATA DE VENDA"], errors="coerce", dayfirst=True)
    df["DATA DA EXPERIÊNCIA"] = pd.to_datetime(df["DATA DA EXPERIÊNCIA"], errors="coerce", dayfirst=True)
    df["total"] = pd.to_numeric(df["total"], errors="coerce")
    df["item_id"] = pd.to_numeric(df["item_id"], errors="coerce")
    df["order_status"] = df["order_status"].astype(str).str.lower()
    return df

df = load_data()

# Filtrar apenas vendas aprovadas
df = df[df["order_status"] == "aprovado"]

# Seletor por data de venda ou de experiência
date_type = st.sidebar.radio("Filtrar por", ["DATA DE VENDA", "DATA DA EXPERIÊNCIA"])
date_col = "DATA DE VENDA" if date_type == "DATA DE VENDA" else "DATA DA EXPERIÊNCIA"

# Filtro de intervalo de datas
min_date = df[date_col].min()
max_date = df[date_col].max()
start_date, end_date = st.sidebar.date_input("Período", [min_date, max_date])
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Aplicar filtro por período
df_filt = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]

# Comparativos
period_days = (end_date - start_date).days
previous_start = start_date - timedelta(days=period_days + 1)
previous_end = end_date - timedelta(days=period_days + 1)
last_year_start = start_date - timedelta(days=365)
last_year_end = end_date - timedelta(days=365)

df_previous = df[(df[date_col] >= previous_start) & (df[date_col] <= previous_end)]
df_last_year = df[(df[date_col] >= last_year_start) & (df[date_col] <= last_year_end)]

def calc_metrics(data):
    return {
        "TPV": data["total"].sum(),
        "Compras": data["partner_order_id"].nunique(),
        "Tickets": data["item_id"].sum(),
        "Ticket Médio": data["total"].sum() / data["item_id"].sum() if data["item_id"].sum() > 0 else 0
    }

atual = calc_metrics(df_filt)
anterior = calc_metrics(df_previous)
ano_passado = calc_metrics(df_last_year)

def diff(current, previous):
    if previous == 0:
        return "—", "—"
    perc = ((current - previous) / previous) * 100
    return f"{perc:.2f}%", f"R$ {abs(current - previous):,.2f}"

st.markdown(f"### Período: {start_date.date()} até {end_date.date()}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("TPV", f'R$ {atual["TPV"]:,.2f}',
              help=f"Anterior: {diff(atual['TPV'], anterior['TPV'])[0]} ({diff(atual['TPV'], anterior['TPV'])[1]})\nAno anterior: {diff(atual['TPV'], ano_passado['TPV'])[0]}")
with col2:
    st.metric("Compras", atual["Compras"],
              help=f"Anterior: {diff(atual['Compras'], anterior['Compras'])[0]}\nAno anterior: {diff(atual['Compras'], ano_passado['Compras'])[0]}")
with col3:
    st.metric("Tickets", int(atual["Tickets"]),
              help=f"Anterior: {diff(atual['Tickets'], anterior['Tickets'])[0]}\nAno anterior: {diff(atual['Tickets'], ano_passado['Tickets'])[0]}")
with col4:
    st.metric("Ticket Médio", f'R$ {atual["Ticket Médio"]:,.2f}',
              help=f"Anterior: {diff(atual['Ticket Médio'], anterior['Ticket Médio'])[0]}\nAno anterior: {diff(atual['Ticket Médio'], ano_passado['Ticket Médio'])[0]}")

# Gráfico
vendas_diarias = df_filt.groupby(df_filt[date_col].dt.date)["total"].sum().reset_index()
vendas_diarias.columns = ["Data", "TPV"]
fig = px.line(vendas_diarias, x="Data", y="TPV", title="Vendas por Dia")
st.plotly_chart(fig, use_container_width=True)

# Tabela de dados
st.subheader("📋 Tabela de Vendas Filtradas")
st.dataframe(df_filt[[
    "partner_order_id", "DATA DE VENDA", "DATA DA EXPERIÊNCIA", "client_name", "experience",
    "item_id", "total", "order_status", "Regiões", "CANAL", "Campanha"
]])
st.download_button("📥 Baixar CSV", data=df_filt.to_csv(index=False), file_name="vendas_filtradas.csv", mime="text/csv")
