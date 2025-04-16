
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title="Wine Locals • Dashboard", layout="wide")

# CSS personalizado
custom_css = '''
<style>
    body, .main, .block-container {
        background-color: #faf8f6;
    }
    .css-10trblm, .css-1v0mbdj {
        color: #5f0f40 !important;
        font-weight: 700;
    }
    h1, h2, h3 {
        color: #6a1b1a;
    }
    .stButton>button {
        background-color: #6a1b1a;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
</style>
'''
st.markdown(custom_css, unsafe_allow_html=True)

# Logotipo
st.image("logo_winelocals.png", width=160)

st.title("Wine Locals • Dashboard de Vendas e Marketing 🍷")

# Leitura do Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1iGN1gCZILFY1ejwz6IBhrOikC_aIMs5xUkEsCE2DW3U/export?format=csv"
df = pd.read_csv(sheet_url)

# Pré-processamento
df["DATA DE VENDA"] = pd.to_datetime(df["DATA DE VENDA"], errors="coerce", dayfirst=True)
df["DATA DA EXPERIÊNCIA"] = pd.to_datetime(df["DATA DA EXPERIÊNCIA"], errors="coerce", dayfirst=True)
df["total"] = pd.to_numeric(df["total"], errors="coerce")
df["item_id"] = pd.to_numeric(df["item_id"], errors="coerce")

# Sidebar
data_tipo = st.sidebar.radio("Filtrar por", ["DATA DE VENDA", "DATA DA EXPERIÊNCIA"])
date_col = "DATA DE VENDA" if data_tipo == "DATA DE VENDA" else "DATA DA EXPERIÊNCIA"

# Filtro de datas
min_date = df[date_col].min()
max_date = df[date_col].max()
start_date, end_date = st.sidebar.date_input("Selecione o intervalo de datas", [min_date, max_date])
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filtros adicionais
aba = st.sidebar.radio("Navegue entre as abas", ["📈 Visão Geral", "📋 Detalhamento", "📣 Marketing"])
clientes = st.sidebar.multiselect("Cliente", df["client_name"].dropna().unique())
regioes = st.sidebar.multiselect("Região", df["Regiões"].dropna().unique())
canais = st.sidebar.multiselect("Canal", df["CANAL"].dropna().unique())

# Aplicar filtros
df_filt = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
if clientes:
    df_filt = df_filt[df_filt["client_name"].isin(clientes)]
if regioes:
    df_filt = df_filt[df_filt["Regiões"].isin(regioes)]
if canais:
    df_filt = df_filt[df_filt["CANAL"].isin(canais)]

# Comparativos
period_days = (end_date - start_date).days
previous_start = start_date - timedelta(days=period_days + 1)
previous_end = end_date - timedelta(days=period_days + 1)
last_year_start = start_date - timedelta(days=365)
last_year_end = end_date - timedelta(days=365)

df_previous = df[(df[date_col] >= previous_start) & (df[date_col] <= previous_end)]
df_last_year = df[(df[date_col] >= last_year_start) & (df[date_col] <= last_year_end)]

def calc_metrics(df_sel):
    return {
        "TPV": df_sel["total"].sum(),
        "Compras": df_sel["partner_order_id"].nunique(),
        "Tickets": df_sel["item_id"].sum(),
        "Ticket Médio": df_sel["total"].sum() / df_sel["item_id"].sum() if df_sel["item_id"].sum() > 0 else 0
    }

atual = calc_metrics(df_filt)
anterior = calc_metrics(df_previous)
ano_passado = calc_metrics(df_last_year)

def diff(current, previous):
    if previous == 0:
        return "—", "—"
    perc = ((current - previous) / previous) * 100
    return f"{perc:.2f}%", f"R$ {abs(current - previous):,.2f}"

if aba == "📈 Visão Geral":
    st.subheader(f"Período: {start_date.date()} até {end_date.date()}")

    st.markdown("### 📊 Indicadores de Venda")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("TPV", f'R$ {atual["TPV"]:,.2f}',
                  help=f"Anterior: {diff(atual['TPV'], anterior['TPV'])[0]} ({diff(atual['TPV'], anterior['TPV'])[1]}) | Ano anterior: {diff(atual['TPV'], ano_passado['TPV'])[0]}")

    with col2:
        st.metric("Compras", atual["Compras"],
                  help=f"Anterior: {diff(atual['Compras'], anterior['Compras'])[0]} | Ano anterior: {diff(atual['Compras'], ano_passado['Compras'])[0]}")

    with col3:
        st.metric("Tickets", int(atual["Tickets"]),
                  help=f"Anterior: {diff(atual['Tickets'], anterior['Tickets'])[0]} | Ano anterior: {diff(atual['Tickets'], ano_passado['Tickets'])[0]}")

    with col4:
        st.metric("Ticket Médio", f'R$ {atual["Ticket Médio"]:,.2f}',
                  help=f"Anterior: {diff(atual['Ticket Médio'], anterior['Ticket Médio'])[0]} | Ano anterior: {diff(atual['Ticket Médio'], ano_passado['Ticket Médio'])[0]}")

    st.markdown("### 📈 Evolução Diária")
    vendas_diarias = df_filt.groupby(df_filt[date_col].dt.date)["total"].sum().reset_index()
    vendas_diarias.columns = ["Data", "TPV"]
    fig = px.line(vendas_diarias, x="Data", y="TPV", title="Vendas por Dia")
    st.plotly_chart(fig, use_container_width=True)

elif aba == "📋 Detalhamento":
    st.subheader("📋 Tabela de Vendas Filtradas")
    st.dataframe(df_filt[[
        "partner_order_id", "DATA DE VENDA", "DATA DA EXPERIÊNCIA", "client_name", "experience",
        "item_id", "total", "order_status", "Regiões", "CANAL", "Campanha"
    ]])
    st.download_button("📥 Baixar CSV", data=df_filt.to_csv(index=False), file_name="vendas_filtradas.csv", mime="text/csv")

elif aba == "📣 Marketing":
    st.subheader("📣 Distribuição de Canais e Campanhas")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(df_filt, names="CANAL", title="Canais de Venda"), use_container_width=True)
        st.plotly_chart(px.pie(df_filt, names="origin", title="Origem da Venda"), use_container_width=True)
    with col2:
        st.plotly_chart(px.pie(df_filt.dropna(subset=["Campanha"]), names="Campanha", title="Campanhas"), use_container_width=True)
        st.plotly_chart(px.pie(df_filt.dropna(subset=["Estado de Compra"]), names="Estado de Compra", title="Estados"), use_container_width=True)
