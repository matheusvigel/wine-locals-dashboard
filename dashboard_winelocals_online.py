
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title="Wine Locals • Dashboard", layout="wide", initial_sidebar_state="expanded")

# Estilo Google-like e responsivo
st.markdown("""
    <style>
    html, body, .main { background-color: #fefcf9; color: #111111; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3, h4 {
        font-family: 'Google Sans', sans-serif;
        color: #333333;
    }
    .section {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f4f8;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
    }
    .metric-diff {
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🍷 Wine Locals • Dashboard de Vendas")

# Fonte dos dados
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
    return df[df["order_status"] == "aprovado"]

df = load_data()

# Sidebar de filtros
st.sidebar.header("Filtros")
date_type = st.sidebar.radio("Data base", ["DATA DE VENDA", "DATA DA EXPERIÊNCIA"])
date_col = "DATA DE VENDA" if date_type == "DATA DE VENDA" else "DATA DA EXPERIÊNCIA"

min_date = df[date_col].min()
max_date = df[date_col].max()
start_date, end_date = st.sidebar.date_input("Período", [pd.to_datetime('2025-04-01'), pd.to_datetime('2025-04-30')])
start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)

clientes = st.sidebar.multiselect("Clientes", df["client_name"].dropna().unique())
canais = st.sidebar.multiselect("Canais", df["CANAL"].dropna().unique())
campanhas = st.sidebar.multiselect("Campanhas", df["Campanha"].dropna().unique())

# Aplicar filtros
df_filt = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
if clientes: df_filt = df_filt[df_filt["client_name"].isin(clientes)]
if canais: df_filt = df_filt[df_filt["CANAL"].isin(canais)]
if campanhas: df_filt = df_filt[df_filt["Campanha"].isin(campanhas)]

# Comparativos
period_days = (end_date - start_date).days
df_prev = df[(df[date_col] >= start_date - timedelta(days=period_days+1)) & (df[date_col] <= end_date - timedelta(days=period_days+1))]
df_yoy = df[(df[date_col] >= start_date - timedelta(days=365)) & (df[date_col] <= end_date - timedelta(days=365))]

def get_metrics(data):
    return {
        "TPV": data["total"].sum(),
        "Compras": data["partner_order_id"].nunique(),
        "Tickets": data["item_id"].sum(),
        "Ticket Médio": data["total"].sum() / data["item_id"].sum() if data["item_id"].sum() > 0 else 0
    }

def compare(val1, val2):
    if val2 == 0: return "—", ""
    diff = val1 - val2
    pct = (diff / val2) * 100
    cor = "green" if pct > 0 else "red"
    return f"<span style='color:{cor}'>({pct:+.1f}%)</span>", f"<span style='color:{cor}'>R$ {abs(diff):,.0f}</span>"

metrics = get_metrics(df_filt)
metrics_prev = get_metrics(df_prev)
metrics_yoy = get_metrics(df_yoy)

# Seção 1: Visão Geral
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 📊 Visão Geral")
st.markdown(f"Período selecionado: **{start_date.date()}** até **{end_date.date()}**")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='metric-card'><div class='metric-value'>R$ {metrics['TPV']:,.0f}</div>TPV<br>{compare(metrics['TPV'], metrics_prev['TPV'])[0]}</div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card'><div class='metric-value'>{metrics['Compras']}</div>Compras<br>{compare(metrics['Compras'], metrics_prev['Compras'])[0]}</div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card'><div class='metric-value'>{int(metrics['Tickets'])}</div>Tickets<br>{compare(metrics['Tickets'], metrics_prev['Tickets'])[0]}</div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='metric-card'><div class='metric-value'>R$ {metrics['Ticket Médio']:,.2f}</div>Ticket Médio<br>{compare(metrics['Ticket Médio'], metrics_prev['Ticket Médio'])[0]}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Seção 2: Evolução Diária
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 📈 Evolução Diária de TPV")
evol = df_filt.groupby(df_filt[date_col].dt.date)["total"].sum().reset_index()
evol.columns = ["Data", "TPV"]
fig = px.line(evol, x="Data", y="TPV", markers=True)
st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)


# Seção 3: Marketing
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 📣 Distribuição de Canais e Campanhas")
col1, col2 = st.columns(2)

with col1:
    pie_canal = px.pie(df_filt, names="CANAL", title="Por Canal")
    st.plotly_chart(pie_canal, use_container_width=True)

    pie_origem = px.pie(df_filt, names="origin", title="Origem da Venda")
    st.plotly_chart(pie_origem, use_container_width=True)

with col2:
    pie_estado = px.pie(df_filt.dropna(subset=["Estado de Compra"]), names="Estado de Compra", title="Estados")
    st.plotly_chart(pie_estado, use_container_width=True)

st.markdown("### 📋 Tabela de Campanhas")
if "Campanha" in df_filt.columns:
    campanha_tbl = df_filt.dropna(subset=["Campanha"]).groupby("Campanha").agg(
        TPV=("total", "sum"),
        Compras=("partner_order_id", "nunique"),
        Tickets=("item_id", "sum")
    ).reset_index()
    campanha_tbl["Ticket Médio"] = campanha_tbl["TPV"] / campanha_tbl["Tickets"]
    st.dataframe(campanha_tbl.sort_values("TPV", ascending=False), use_container_width=True)
else:
    st.warning("Nenhuma campanha registrada neste filtro.")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 📣 Distribuição de Canais e Campanhas")
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(px.pie(df_filt, names="CANAL", title="Por Canal"), use_container_width=True)
    st.plotly_chart(px.pie(df_filt, names="origin", title="Origem da Venda"), use_container_width=True)
with col2:
    st.plotly_chart(px.pie(df_filt.dropna(subset=["Campanha"]), names="Campanha", title="Campanhas"), use_container_width=True)
    st.plotly_chart(px.pie(df_filt.dropna(subset=["Estado de Compra"]), names="Estado de Compra", title="Estados"), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Seção 4: Tabela
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 📋 Tabela Detalhada")
st.dataframe(df_filt[[
    "partner_order_id", "DATA DE VENDA", "DATA DA EXPERIÊNCIA", "client_name", "experience",
    "item_id", "total", "order_status", "Regiões", "CANAL", "Campanha"
]], use_container_width=True)
st.download_button("📥 Baixar CSV", data=df_filt.to_csv(index=False), file_name="vendas_filtradas.csv", mime="text/csv")
st.markdown("</div>", unsafe_allow_html=True)
