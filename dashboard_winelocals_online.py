
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Wine Locals • Dashboard", layout="wide")

# Estilo personalizado
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

# Carregar dados do Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1iGN1gCZILFY1ejwz6IBhrOikC_aIMs5xUkEsCE2DW3U/export?format=csv"
df = pd.read_csv(sheet_url)

# Pré-processamento
df["DATA DE VENDA"] = pd.to_datetime(df["DATA DE VENDA"], errors="coerce", dayfirst=True)
df["DATA DA EXPERIÊNCIA"] = pd.to_datetime(df["DATA DA EXPERIÊNCIA"], errors="coerce", dayfirst=True)
df["total"] = pd.to_numeric(df["total"], errors="coerce")
df["item_id"] = pd.to_numeric(df["item_id"], errors="coerce")

# Sidebar com filtros gerais
aba = st.sidebar.radio("Navegue entre as abas", ["📈 Visão Geral", "📋 Detalhamento", "📣 Marketing"])
clientes = st.sidebar.multiselect("Filtrar por Cliente", df["client_name"].dropna().unique())
regioes = st.sidebar.multiselect("Filtrar por Região", df["Regiões"].dropna().unique())
canais = st.sidebar.multiselect("Filtrar por Canal", df["CANAL"].dropna().unique())

# Aplicar filtros
df_filt = df.copy()
if clientes:
    df_filt = df_filt[df_filt["client_name"].isin(clientes)]
if regioes:
    df_filt = df_filt[df_filt["Regiões"].isin(regioes)]
if canais:
    df_filt = df_filt[df_filt["CANAL"].isin(canais)]

if aba == "📈 Visão Geral":
    st.subheader("Evolução diária de vendas (TPV)")
    vendas_diarias = df_filt.groupby("DATA DE VENDA")["total"].sum().reset_index()
    fig = px.line(vendas_diarias, x="DATA DE VENDA", y="total", title="Total de Vendas por Dia")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Indicadores Gerais")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("TPV", f'R$ {df_filt["total"].sum():,.2f}')
    with col2:
        st.metric("Compras Únicas", df_filt["partner_order_id"].nunique())
    with col3:
        tm = df_filt["total"].sum() / df_filt["item_id"].sum() if df_filt["item_id"].sum() > 0 else 0
        st.metric("Ticket Médio", f'R$ {tm:,.2f}')

elif aba == "📋 Detalhamento":
    st.subheader("Tabela de Vendas Filtradas")
    st.dataframe(df_filt[[
        "partner_order_id", "DATA DE VENDA", "DATA DA EXPERIÊNCIA", "client_name", "experience",
        "item_id", "total", "order_status", "Regiões", "CANAL", "Campanha"
    ]])
    
    st.download_button("📥 Baixar CSV", data=df_filt.to_csv(index=False), file_name="vendas_filtradas.csv", mime="text/csv")

elif aba == "📣 Marketing":
    st.subheader("Distribuição de Canais e Campanhas")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(df_filt, names="CANAL", title="Canais de Venda"), use_container_width=True)
        st.plotly_chart(px.pie(df_filt, names="origin", title="Origem da Venda"), use_container_width=True)
    with col2:
        st.plotly_chart(px.pie(df_filt.dropna(subset=["Campanha"]), names="Campanha", title="Campanhas"), use_container_width=True)
        st.plotly_chart(px.pie(df_filt.dropna(subset=["Estado de Compra"]), names="Estado de Compra", title="Estados"), use_container_width=True)
