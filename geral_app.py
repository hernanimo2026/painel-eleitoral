import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Eleições", layout="wide")

st.title("🗳️ Painel de Acompanhamento - Eleições")
st.write("Filtros combinados: O Estado funciona em conjunto com o Partido ou com a Coligação.")

# 1. Carregar os dados CSV
@st.cache_data
def carregar_dados():
    caminho_csv = "consulta_cand_2026_BRASIL.csv"
    try:
        df = pd.read_csv(caminho_csv, sep=";", encoding="latin-1")
    except FileNotFoundError:
        caminho_csv = "cand_mais_votado-2024_com_ibge.csv"
        df = pd.read_csv(caminho_csv, sep=";", encoding="utf-8")
    return df

df = carregar_dados()

# Mapeamento de colunas do TSE
col_partido = "SG_PARTIDO" if "SG_PARTIDO" in df.columns else "Partido"
col_coligacao = "DS_COMPOSICAO_COLIGACAO" if "DS_COMPOSICAO_COLIGACAO" in df.columns else "DS_COMPOSICAO_FEDERACAO"
col_cargo = "DS_CARGO" if "DS_CARGO" in df.columns else "Cargo Pretendido"
col_uf = "SG_UF" if "SG_UF" in df.columns else "UF"

# Busca dinâmica pela coluna do Nome do Candidato
colunas_nome_possiveis = ["NM_URNA_CANDIDATO", "NM_CANDIDATO", "NM_SOCIAL_CANDIDATO"]
col_nome = None
for col in colunas_nome_possiveis:
    if col in df.columns:
        col_nome = col
        break

# Listas de opções para os filtros
partidos_unicos = sorted([str(p) for p in df[col_partido].dropna().unique()]) if col_partido in df.columns else []
colig_unicas = sorted([str(c) for c in df[col_coligacao].dropna().unique()]) if col_coligacao in df.columns else []
ufs_unicas = sorted([str(u) for u in df[col_uf].dropna().unique()]) if col_uf in df.columns else []

# 2. INICIALIZAÇÃO DO SESSION STATE
if "filtro_partido" not in st.session_state:
    st.session_state["filtro_partido"] = "Todos"
if "filtro_coligacao" not in st.session_state:
    st.session_state["filtro_coligacao"] = "Todos"
if "filtro_uf" not in st.session_state:
    st.session_state["filtro_uf"] = "BR" if "BR" in ufs_unicas else "Todos"

# Callbacks: Partido e Coligação limpam um ao outro
def ao_mudar_partido():
    if st.session_state["filtro_partido"] != "Todos":
        st.session_state["filtro_coligacao"] = "Todos"

def ao_mudar_coligacao():
    if st.session_state["filtro_coligacao"] != "Todos":
        st.session_state["filtro_partido"] = "Todos"

# 3. SELETORES NO TOPO
st.subheader("🔍 Filtros Dinâmicos")
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    st.selectbox(
        "1. Estado (UF):",
        options=["Todos"] + ufs_unicas,
        key="filtro_uf"
    )

with col_f2:
    st.selectbox(
        "2. Partido (Exclusivo com Coligação):",
        options=["Todos"] + partidos_unicos,
        key="filtro_partido",
        on_change=ao_mudar_partido
    )

with col_f3:
    st.selectbox(
        "3. Coligação (Exclusiva com Partido):",
        options=["Todos"] + colig_unicas,
        key="filtro_coligacao",
        on_change=ao_mudar_coligacao
    )

# 4. APLICAÇÃO DOS FILTROS COMBINADOS
df_filtrado = df.copy()

uf_ativa = st.session_state["filtro_uf"]
if uf_ativa != "Todos":
    df_filtrado = df_filtrado[df_filtrado[col_uf] == uf_ativa]

partido_ativo = st.session_state["filtro_partido"]
coligacao_ativa = st.session_state["filtro_coligacao"]

if partido_ativo != "Todos":
    df_filtrado = df_filtrado[df_filtrado[col_partido] == partido_ativo]
elif coligacao_ativa != "Todos":
    df_filtrado = df_filtrado[df_filtrado[col_coligacao] == coligacao_ativa]

st.divider()

# 5. ABAS DE VISUALIZAÇÃO
aba1, aba2 = st.tabs(["📊 Visão Geral", "📋 Lista de Candidatos"])

with aba1:
    st.subheader("Indicadores da Seleção")
    c1, c2, c3 = st.columns(3)
    c1.metric("Candidatos Exibidos", f"{len(df_filtrado):,}")
    c2.metric("Estado Filtrado", uf_ativa)
    
    grupo_ativo = partido_ativo if partido_ativo != "Todos" else coligacao_ativa
    c3.metric("Grupo Político Ativo", grupo_ativo[:20] + "..." if len(grupo_ativo) > 20 else grupo_ativo)

    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.write("### Candidatos por Cargo")
        if col_cargo in df_filtrado.columns and not df_filtrado.empty:
            st.bar_chart(df_filtrado[col_cargo].value_counts())
            
    with col_g2:
        st.write("### Candidatos por Partido")
        if col_partido in df_filtrado.columns and not df_filtrado.empty:
            st.bar_chart(df_filtrado[col_partido].value_counts())

with aba2:
    st.subheader(f"Lista de Candidatos ({len(df_filtrado):,} registos)")
    
    # Campo de busca individual por nome
    termo_busca = st.text_input("🔍 Buscar candidato pelo nome:", "")
    
    df_exibicao = df_filtrado.copy()
    
    if termo_busca and col_nome in df_exibicao.columns:
        df_exibicao = df_exibicao[df_exibicao[col_nome].astype(str).str.contains(termo_busca, case=False, na=False)]
    
    # Montagem explícita das colunas da tabela
    colunas_desejadas = [col_nome, col_cargo, col_partido, col_coligacao, col_uf]
    colunas_finais = [c for c in colunas_desejadas if c and c in df_exibicao.columns]
    
    st.dataframe(
        df_exibicao[colunas_finais],
        use_container_width=True,
        column_config={
            col_nome: "Nome na Urna",
            col_cargo: "Cargo Pretendido",
            col_partido: "Partido",
            col_coligacao: "Coligação / Federação",
            col_uf: "Estado (UF)"
        }
    )