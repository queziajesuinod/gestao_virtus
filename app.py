import streamlit as st
import plotly.io as pio
from fpdf import FPDF
import datetime
import os
import pandas as pd
import plotly.express as px
import io

# Carregamento dos dados
df = pd.read_excel("Calculo_conversao_Inscritos.xlsx", sheet_name="Calculo")

# Filtro: cidades com 15 inscritos ou menos
df_critico = df[df["Inscritos"] <= 15].copy()

# Agrupar por estado
df_critico_estado = df_critico.groupby("Estado").agg({
    "Cidade": "count",
    "Inscritos": "sum",
    "Matriculados": "sum",
    "Investimento": "sum",
    "CPInsc": "mean",
    "CPMat": "mean"
}).reset_index()

# Projeções
df_critico_estado["Projeção de Inscritos (6 meses)"] = df_critico_estado["Inscritos"] * 6
df_critico_estado["Projeção de Matriculados (6 meses)"] = df_critico_estado["Matriculados"] * 6
df_critico_estado["Investimento Projetado (6 meses)"] = df_critico_estado["Investimento"] * 6
df_critico_estado["Proj. Matriculados Pessimista (6 meses)"] = df_critico_estado["Projeção de Matriculados (6 meses)"] * 0.8

# ROI
df_critico_estado["ROI Atual"] = df_critico_estado["Matriculados"] / df_critico_estado["Investimento"]
df_critico_estado["ROI Proj. (6 meses)"] = df_critico_estado["Projeção de Matriculados (6 meses)"] / df_critico_estado["Investimento Projetado (6 meses)"]
df_critico_estado["ROI Pessimista"] = df_critico_estado["Proj. Matriculados Pessimista (6 meses)"] / df_critico_estado["Investimento Projetado (6 meses)"]

# Eficiência relativa
roi_medio = df_critico_estado["ROI Atual"].mean()
df_critico_estado["Eficiência Relativa"] = df_critico_estado["ROI Atual"] / roi_medio

# Simulação de meta ROI
st.set_page_config("Análise Crítica por Estado", layout="wide")
st.title("🚨 Análise de Estados com Baixo Volume de Inscrições")

meta_roi = st.slider("Defina o ROI desejado:", 0.001, 0.05, 0.01, step=0.001)
df_critico_estado["Investimento Ideal p/ Meta"] = df_critico_estado["Matriculados"] / meta_roi
df_critico_estado["Diferença de Investimento"] = df_critico_estado["Investimento Ideal p/ Meta"] - df_critico_estado["Investimento"]
df_critico_estado["Alvo Bate Meta"] = df_critico_estado["Diferença de Investimento"].apply(lambda x: "🔺 Precisa aumentar" if x > 0 else "✅ ROI já atinge")

# Renomear colunas antes de sugestões para compatibilidade
df_critico_estado = df_critico_estado.rename(columns={
    "Matriculados": "Total de Matriculados",
    "Inscritos": "Total de Inscritos",
    "Investimento": "Investimento Atual",
    "CPInsc": "CPI Médio",
    "CPMat": "CPM Médio"
})

# Sugestões estratégicas
def sugestao(row):
    if row["ROI Atual"] < 0.005:
        return "🔻 Reduzir Investimento"
    elif row["CPM Médio"] > 300:
        return "🔄 Reestruturar Estratégia"
    else:
        return "✅ Manter"
df_critico_estado["Sugerir Ação"] = df_critico_estado.apply(sugestao, axis=1)
df_critico_estado["Alerta"] = df_critico_estado["Sugerir Ação"].apply(lambda x: "❗" if "Reduzir" in x or "Reestruturar" in x else "")

# Rankings
df_critico_estado["Ranking ROI"] = df_critico_estado["ROI Atual"].rank(ascending=False)
df_critico_estado["Ranking Eficiência"] = df_critico_estado["Eficiência Relativa"].rank(ascending=False)

# Conversão por cidade média
df_critico_estado["Conversão %"] = (df_critico_estado["Total de Matriculados"] / df_critico_estado["Total de Inscritos"] * 100).round(2)

# CPCR - Custo por Conversão Real
df_critico_estado["CPCR (R$/matrícula)"] = df_critico_estado["Investimento Atual"] / df_critico_estado["Total de Matriculados"]

# Tabelas importantes
st.subheader("🏙️ Top 5 Cidades Críticas (Inscritos <= 15)")
df_top5_cidades = df_critico.sort_values(by="Inscritos").head(5)
st.dataframe(df_top5_cidades[["Cidade", "Estado", "Inscritos", "Matriculados", "Investimento"]])

st.subheader("❌ Cidades com ROI igual a 0 (Sem Matrículas)")
df_sem_retorno = df_critico[(df_critico["Matriculados"] == 0) & (df_critico["Investimento"] > 0)]
st.dataframe(df_sem_retorno[["Cidade", "Estado", "Inscritos", "Matriculados", "Investimento"]])

st.subheader("📉 Investimento x Total de Matriculados por Estado")
fig_mat = px.bar(df_critico_estado, x="Estado", y="Total de Matriculados", color="Estado",
                 text="Total de Matriculados", title="Total de Matriculados por Estado")
fig_mat.update_traces(textposition='outside')
st.plotly_chart(fig_mat, use_container_width=True)

fig_inv = px.bar(df_critico_estado, x="Estado", y="Investimento Atual", color="Estado",
                 text="Investimento Atual", title="Investimento Atual por Estado")
fig_inv.update_traces(textposition='outside')
st.plotly_chart(fig_inv, use_container_width=True)

st.subheader("📈 Projeção de Inscritos para 6 Meses")
fig_proj = px.bar(df_critico_estado, x="Estado", y="Projeção de Inscritos (6 meses)", color="Estado",
                  text="Projeção de Inscritos (6 meses)", title="Projeção de Inscritos para 6 meses")
fig_proj.update_traces(textposition='outside')
st.plotly_chart(fig_proj, use_container_width=True)

# Insights automáticos
estado_menor_roi = df_critico_estado.loc[df_critico_estado["ROI Atual"].idxmin(), "Estado"]
menor_cpi = df_critico_estado.loc[df_critico_estado["CPI Médio"].idxmin()]
descompasso = df_critico_estado.loc[df_critico_estado["Diferença de Investimento"].idxmax()]

st.subheader("🔍 Insights Automáticos")
st.markdown(f"➡️ O estado **{estado_menor_roi}** possui o ROI mais baixo atualmente: **{df_critico_estado['ROI Atual'].min():.4f}**.")
st.markdown(f"💸 O menor custo por inscrito médio foi registrado em **{menor_cpi['Estado']}**: R$**{menor_cpi['CPI Médio']:.2f}**.")
st.markdown(f"🚨 O maior descompasso entre investimento atual e ideal para bater meta está em **{descompasso['Estado']}**: precisa de R$**{descompasso['Diferença de Investimento']:.2f}** a mais.")

# 🔎 Pior cidade por estado
st.subheader("📉 Pior Cidade em ROI por Estado")
df_city_roi = df_critico.copy()
df_city_roi["ROI Cidade"] = df_city_roi["Matriculados"] / df_city_roi["Investimento"]
df_city_roi = df_city_roi[df_city_roi["Investimento"] > 0]
df_worst_city_by_state = df_city_roi.sort_values("ROI Cidade").groupby("Estado").first().reset_index()
st.dataframe(df_worst_city_by_state[["Estado", "Cidade", "Inscritos", "Matriculados", "Investimento", "ROI Cidade"]])

fig_worst = px.bar(
    df_worst_city_by_state,
    x="Cidade",
    y="ROI Cidade",
    color="Estado",
    text="ROI Cidade",
    title="Pior Cidade por Estado em ROI"
)
fig_worst.update_traces(texttemplate='%{text:.4f}', textposition='outside')
fig_worst.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_worst, use_container_width=True)

# 🚦 Análise visual de conversão
st.subheader("⚠️ Cidades com Conversão Inferior a 20%")
df_critico["Conversão %"] = (df_critico["Matriculados"] / df_critico["Inscritos"] * 100).round(2)
df_baixa_conversao = df_critico[df_critico["Conversão %"] < 20]
st.dataframe(df_baixa_conversao[["Cidade", "Estado", "Inscritos", "Matriculados", "Conversão %"]])

# 🔝 Ranking de Eficiência Relativa
st.subheader("📊 Ranking de Eficiência Relativa")
col1, col2 = st.columns(2)
with col1:
    st.markdown("### 🥇 Top 3 Estados mais eficientes")
    st.dataframe(df_critico_estado.sort_values("Eficiência Relativa", ascending=False).head(3)[["Estado", "Eficiência Relativa"]])
with col2:
    st.markdown("### 🥵 Top 3 Estados menos eficientes")
    st.dataframe(df_critico_estado.sort_values("Eficiência Relativa").head(3)[["Estado", "Eficiência Relativa"]])

st.markdown(f"📊 **Média Nacional de Eficiência**: {roi_medio:.4f}")
