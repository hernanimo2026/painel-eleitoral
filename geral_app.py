import streamlit as st
import pandas as pd

st.set_page_config(page_title="Painel Eleitoral 2026", layout="wide")

st.title("🗳️ Eleições 2026 - Consulta Geral de Candidatos e Coligações")

@st.cache_data
def carregar_dados(caminho):
    encodings = ["latin-1", "iso-8859-1", "cp1252", "utf-8"]
    for enc in encodings:
        try:
            df = pd.read_csv(caminho, sep=";", encoding=enc, low_memory=False)
            return df
        except (UnicodeDecodeError, Exception):
            continue
    return None

st.sidebar.header("📁 Base de Dados 2026")
tipo_base = st.sidebar.radio(
    "Escolha o foco de análise:",
    ["Candidatos 2026", "Coligações e Partidos 2026"]
)

if tipo_base == "Candidatos 2026":
    arquivo = "consulta_cand_2026_BRASIL.csv"
else:
    arquivo = "consulta_coligacao_2026_BRASIL.csv"

df_2026 = carregar_dados(arquivo)

if df_2026 is not None:
    cols = df_2026.columns.tolist()
    
    col_uf = next((c for c in cols if "UF" in c.upper() or "SG_UF" in c.upper()), None)
    col_cargo = next((c for c in cols if "CARGO" in c.upper() or "DS_CARGO" in c.upper()), None)
    col_partido = next((c for c in cols if "PARTIDO" in c.upper() or "SG_PARTIDO" in c.upper()), None)
    col_cand = next((c for c in cols if "NM_CANDIDATO" in c.upper() or "CANDIDATO" in c.upper() or "NM_URNA" in c.upper()), None)

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros de Busca")
    df_filtrado = df_2026.copy()

    # 1. Filtro UF
    if col_uf:
        lista_ufs = ["TODOS"] + sorted([str(x) for x in df_2026[col_uf].dropna().unique()])
        uf_sel = st.sidebar.selectbox("Estado (UF):", lista_ufs)
        if uf_sel != "TODOS":
            df_filtrado = df_filtrado[df_filtrado[col_uf] == uf_sel]

    # 2. Filtro Cargo
    if col_cargo:
        lista_cargos = ["TODOS"] + sorted([str(x) for x in df_filtrado[col_cargo].dropna().unique()])
        cargo_sel = st.sidebar.selectbox("Cargo Disputado:", lista_cargos)
        if cargo_sel != "TODOS":
            df_filtrado = df_filtrado[df_filtrado[col_cargo] == cargo_sel]

    # 3. Filtro Partido
    if col_partido:
        lista_partidos = ["TODOS"] + sorted([str(x) for x in df_filtrado[col_partido].dropna().unique()])
        partido_sel = st.sidebar.selectbox("Partido / Coligação:", lista_partidos)
        if partido_sel != "TODOS":
            df_filtrado = df_filtrado[df_filtrado[col_partido] == partido_sel]

    # 4. Filtro por Lista de Candidatos 2026
    if col_cand:
        lista_candidatos = ["TODOS"] + sorted([str(x) for x in df_filtrado[col_cand].dropna().unique()])
        cand_sel = st.sidebar.selectbox("Selecione o Candidato:", lista_candidatos)
        if cand_sel != "TODOS":
            df_filtrado = df_filtrado[df_filtrado[col_cand] == cand_sel]

    # Métricas da Busca
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Total de Registros Encontrados", f"{len(df_filtrado):,}".replace(",", "."))
    with m2:
        if col_cand and 'cand_sel' in locals() and cand_sel != "TODOS":
            st.metric("Candidato Selecionado", cand_sel)

    st.subheader(f"Tabela de Dados - {tipo_base}")
    st.dataframe(df_filtrado, use_container_width=True)

else:
    st.error("Aguardando carregamento da base de dados...")