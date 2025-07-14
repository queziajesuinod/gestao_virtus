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



df_critico_estado["Investimento Ideal p/ Meta"] = df_critico_estado["Matriculados"] /  0.01
df_critico_estado["Diferença de Investimento"] = df_critico_estado["Investimento Ideal p/ Meta"] - df_critico_estado["Investimento"]
df_critico_estado["Alvo Bate Meta"] = df_critico_estado["Diferença de Investimento"].apply(lambda x: "🔺 Precisa aumentar" if x > 0 else "✅ ROI já atinge")

# Renomear colunas antes de usar no restante do código
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


# Gráficos
st.subheader("📊 Investimento x Total de Matriculados por Estado")
fig_inv_vs_mat = px.scatter(
    df_critico_estado,
    x="Investimento Atual",
    y="Total de Matriculados",
    color="Estado",
    size="Total de Matriculados",
    hover_name="Estado",
    text="Estado",
    labels={"Investimento Atual": "Investimento (R$)", "Total de Matriculados": "Matriculados"},
    title="Investimento versus Matriculados"
)
fig_inv_vs_mat.update_traces(textposition='top center')
fig_inv_vs_mat.update_layout(xaxis_tickprefix="R$ ", showlegend=False)
st.plotly_chart(fig_inv_vs_mat, use_container_width=True)

st.subheader("📉 Investimento x Total de Inscritos por Estado")
fig_inv_vs_insc = px.scatter(
    df_critico_estado,
    x="Investimento Atual",
    y="Total de Inscritos",
    color="Estado",
    size="Total de Inscritos",
    hover_name="Estado",
    text="Estado",
    labels={"Investimento Atual": "Investimento (R$)", "Total de Inscritos": "Inscritos"},
    title="Investimento versus Inscritos"
)
fig_inv_vs_insc.update_traces(textposition='top center')
fig_inv_vs_insc.update_layout(xaxis_tickprefix="R$ ", showlegend=False)
st.plotly_chart(fig_inv_vs_insc, use_container_width=True)

st.subheader("📈 Projeção de Inscritos para 6 Meses")
fig_proj = px.bar(
    df_critico_estado,
    x="Estado",
    y="Projeção de Inscritos (6 meses)",
    text="Projeção de Inscritos (6 meses)",
    title="Projeção de Inscrições em 6 Meses",
    labels={"Projeção de Inscritos (6 meses)": "Quantidade"}
)
fig_proj.update_traces(textposition="outside", textfont_size=14)
fig_proj.update_layout(xaxis_tickangle=-45, font=dict(size=14))
st.plotly_chart(fig_proj, use_container_width=True)

# Insights Automáticos
st.subheader("🔎 Insights Automáticos")
estado_mais_ineficiente = df_critico_estado.sort_values("ROI Atual").iloc[0]
estado_melhor_custo = df_critico_estado.sort_values("CPI Médio").iloc[0]
estado_maior_diferenca = df_critico_estado.sort_values("Diferença de Investimento", ascending=False).iloc[0]

st.markdown(f"➡️ O estado **{estado_mais_ineficiente['Estado']}** possui o ROI mais baixo atualmente: **{estado_mais_ineficiente['ROI Atual']:.4f}**.")
st.markdown(f"💸 O menor custo por inscrito médio foi registrado em **{estado_melhor_custo['Estado']}**: **R${estado_melhor_custo['CPI Médio']:.2f}**.")
st.markdown(f"🚨 O maior descompasso entre investimento atual e ideal para bater meta está em **{estado_maior_diferenca['Estado']}**: precisa de **R${estado_maior_diferenca['Diferença de Investimento']:.2f}** a mais.")

# Download dos dados como Excel
st.subheader("📥 Download de Dados")
excel_output = io.BytesIO()
df_critico_estado.to_excel(excel_output, index=False)
st.download_button(
    label="📊 Baixar relatório completo (Excel)",
    data=excel_output.getvalue(),
    file_name="relatorio_critico_estados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Sugestões automáticas
with st.expander("💡 Sugestões Automáticas Baseadas em ROI e CPM"):
    for _, row in df_critico_estado.iterrows():
        if "❗" in row["Alerta"]:
            st.markdown(f"**{row['Estado']}** → {row['Sugerir Ação']} (ROI: {row['ROI Atual']:.4f}, CPM: R${row['CPM Médio']:.2f})")