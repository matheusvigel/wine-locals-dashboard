
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Wine Locals • Dashboard", layout="wide")

# Estilo Wine Locals
custom_css = '''
<style>
    body {
        background-color: #faf8f6;
    }
    .main {
        background-color: #faf8f6;
    }
    header, footer {
        visibility: hidden;
    }
    .block-container {
        padding: 2rem;
    }
    .css-10trblm {
        font-size: 28px !important;
        font-weight: 700;
        color: #6a1b1a;
    }
</style>
'''
st.markdown(custom_css, unsafe_allow_html=True)

# Logotipo
st.image("https://i.imgur.com/6Z8cv2m.png", width=180)  # substitua com o logo oficial da Wine Locals se quiser

st.title("Wine Locals • Dashboard de Vendas e Marketing 🍷")

# Carregar planilha do Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1iGN1gCZILFY1ejwz6IBhrOikC_aIMs5xUkEsCE2DW3U/export?format=csv"
df = pd.read_csv(sheet_url)

# Pré-processamento
df["DATA DE VENDA"] = pd.to_datetime(df["DATA DE VENDA"], errors="coerce", dayfirst=True)
df["DATA DA EXPERIÊNCIA"] = pd.to_datetime(df["DATA DA EXPERIÊNCIA"], errors="coerce", dayfirst=True)
df["total"] = pd.to_numeric(df["total"], errors="coerce")
df["item_id"] = pd.to_numeric(df["item_id"], errors="coerce")

aba = st.sidebar.radio("Selecione uma aba", ["Visão Geral de Vendas", "Detalhamento de Vendas", "Marketing e Origem"])

if aba == "Visão Geral de Vendas":
    st.subheader("📈 Evolução diária de Vendas (TPV)")
    vendas_diarias = df.groupby("DATA DE VENDA")["total"].sum().reset_index()
    fig = px.line(vendas_diarias, x="DATA DE VENDA", y="total", title="Total de Vendas por Dia")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 Indicadores de Vendas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("TPV", f'R$ {df["total"].sum():,.2f}')
    with col2:
        st.metric("Total de Compras", df["partner_order_id"].nunique())
    with col3:
        if df["item_id"].sum() > 0:
            st.metric("Ticket Médio", f'R$ {df["total"].sum() / df["item_id"].sum():.2f}')
        else:
            st.metric("Ticket Médio", "N/A")

elif aba == "Detalhamento de Vendas":
    st.subheader("🗃️ Tabela de Vendas Detalhada")
    clientes = st.multiselect("Filtrar por Cliente", df["client_name"].dropna().unique())
    regioes = st.multiselect("Filtrar por Região", df["Regiões"].dropna().unique())
    canais = st.multiselect("Filtrar por Canal", df["CANAL"].dropna().unique())

    df_filt = df.copy()
    if clientes:
        df_filt = df_filt[df_filt["client_name"].isin(clientes)]
    if regioes:
        df_filt = df_filt[df_filt["Regiões"].isin(regioes)]
    if canais:
        df_filt = df_filt[df_filt["CANAL"].isin(canais)]

    st.dataframe(df_filt[[
        "partner_order_id", "partner_order_code", "DATA DE VENDA", "DATA DA EXPERIÊNCIA", 
        "client_name", "experience", "Regiões", "CANAL", "Campanha", 
        "item_id", "total"
    ]])

elif aba == "Marketing e Origem":
    st.subheader("📣 Marketing: Canais, Campanhas e Origens")

    col1, col2 = st.columns(2)

    with col1:
        canal_fig = px.pie(df, names="CANAL", title="Distribuição por Canal")
        st.plotly_chart(canal_fig, use_container_width=True)

        origem_fig = px.pie(df, names="origin", title="Distribuição por Origem")
        st.plotly_chart(origem_fig, use_container_width=True)

    with col2:
        campanha_fig = px.pie(df.dropna(subset=["Campanha"]), names="Campanha", title="Distribuição por Campanha")
        st.plotly_chart(campanha_fig, use_container_width=True)

        estado_fig = px.pie(df.dropna(subset=["Estado de Compra"]), names="Estado de Compra", title="Distribuição por Estado de Compra")
        st.plotly_chart(estado_fig, use_container_width=True)
