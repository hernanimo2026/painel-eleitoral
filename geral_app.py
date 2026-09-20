import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração inicial da página
st.set_page_config(page_title="Painel Eleitoral 2026", layout="wide")

st.title("🗳️ Eleições 2026 - Navegação Direta pelo Mapa")

# Função de Leitura do Ficheiro CSV com Cache de Memória
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

# Painel Lateral (Sidebar) - Seleção da Base de Dados
st.sidebar.header("📁 Base de Dados 2026")
tipo_base = st.sidebar.radio(
    "Escolha o foco de análise:",
    ["Candidatos 2026", "Coligações e Partidos 2026"]
)

# Seleção automática do ficheiro CSV
arquivo = "consulta_cand_2026_BRASIL.csv" if tipo_base == "Candidatos 2026" else "consulta_coligacao_2026_BRASIL.csv"
df_2026 = carregar_dados(arquivo)

if df_2026 is not None:
    cols = df_2026.columns.tolist()
    
    # Identificação automática dos nomes das colunas
    col_uf = next((c for c in cols if "SG_UF" in c.upper() or "UF" in c.upper()), None)
    col_cargo = next((c for c in cols if "DS_CARGO" in c.upper() or "CARGO" in c.upper()), None)
    col_partido = next((c for c in cols if "SG_PARTIDO" in c.upper() or "PARTIDO" in c.upper()), None)
    
    col_nome_urna = next((c for c in cols if "NM_URNA_CANDIDATO" in c.upper() or "NM_URNA" in c.upper()), None)
    col_nome_cand = next((c for c in cols if "NM_CANDIDATO" in c.upper()), None)
    col_num_cand = next((c for c in cols if "NR_CANDIDATO" in c.upper()), None)

    col_cand_principal = col_nome_urna if col_nome_urna else col_nome_cand

    # Estado da Sessão (Session State) para armazenar o toque no mapa
    if "uf_mapa" not in st.session_state:
        st.session_state["uf_mapa"] = "TODOS"

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros de Apoio")

    df_filtrado = df_2026.copy()

    # Aplica o filtro de estado (UF) selecionado pelo mapa
    if col_uf and st.session_state["uf_mapa"] != "TODOS":
        df_filtrado = df_filtrado[df_filtrado[col_uf] == st.session_state["uf_mapa"]]

    # Menu 1: Filtro por Cargo
    if col_cargo:
        lista_cargos = ["TODOS"] + sorted([str(x) for x in df_filtrado[col_cargo].dropna().unique()])
        cargo_sel = st.sidebar.selectbox("Cargo Disputado:", lista_cargos)
        if cargo_sel != "TODOS":
            df_filtrado = df_filtrado[df_filtrado[col_cargo] == cargo_sel]

    # Menu 2: Filtro por Partido
    if col_partido:
        lista_partidos = ["TODOS"] + sorted([str(x) for x in df_filtrado[col_partido].dropna().unique()])
        partido_sel = st.sidebar.selectbox("Partido / Coligação:", lista_partidos)
        if partido_sel != "TODOS":
            df_filtrado = df_filtrado[df_filtrado[col_partido] == partido_sel]

    # Menu 3: Filtro por Nome do Candidato
    if col_cand_principal:
        if col_num_cand:
            df_filtrado["CANDIDATO_EXIBICAO"] = df_filtrado[col_cand_principal].astype(str) + " (" + df_filtrado[col_num_cand].astype(str) + ")"
            col_busca_cand = "CANDIDATO_EXIBICAO"
        else:
            col_busca_cand = col_cand_principal

        lista_candidatos = ["TODOS"] + sorted([str(x) for x in df_filtrado[col_busca_cand].dropna().unique()])
        cand_sel = st.sidebar.selectbox("Selecione o Candidato pelo Nome:", lista_candidatos)
        if cand_sel != "TODOS":
            df_filtrado = df_filtrado[df_filtrado[col_busca_cand] == cand_sel]

    # Botão para limpar a seleção do mapa
    if st.session_state["uf_mapa"] != "TODOS":
        if st.sidebar.button("🇧🇷 Ver Brasil Inteiro (Resetar Mapa)"):
            st.session_state["uf_mapa"] = "TODOS"
            st.rerun()

    # Seção de Indicadores
    st.markdown("### 📊 Indicadores Gerais")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total de Registros", f"{len(df_filtrado):,}".replace(",", "."))
    with m2:
        if col_partido:
            st.metric("Partidos na Análise", df_filtrado[col_partido].nunique())
    with m3:
        st.metric("Estado Selecionado no Mapa", st.session_state["uf_mapa"])

    st.markdown("---")

    # Divisão em 2 colunas para Mapa e Gráfico
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("🗺️ Toque em um Estado para Selecionar")
if col_uf:
    df_mapa = df_2026.groupby(col_uf).size().reset_index(name="TOTAL")
    geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

    fig_mapa = px.choropleth(
        df_mapa,
        geojson=geojson_url,
        locations=col_uf,
        featureidkey="properties.sigla",
        color="TOTAL",
        color_continuous_scale="Blues",
        labels={"TOTAL": "Registros", col_uf: "UF"},
        projection="mercator"  # Garante proporção ideal sem caixa retangular solta
    )
    
    # Recalcula o enquadramento exato das fronteiras do Brasil
    fig_mapa.update_geos(
        fitbounds="locations",
        visible=False,
        showframe=False
    )
    
    # Ajusta o tamanho da área do gráfico para encaixar o Brasil de ponta a ponta
    fig_mapa.update_layout(
        margin=dict(t=0, l=0, r=0, b=0),
        height=320,  # Altura proporcional ao formato do Brasil em telas mobile
        dragmode=False,
        coloraxis_showscale=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    event_data = st.plotly_chart(
        fig_mapa,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        config={
            'displayModeBar': False,
            'scrollZoom': False
        }
    )

    if event_data and "selection" in event_data and "points" in event_data["selection"]:
        pontos = event_data["selection"]["points"]
        if pontos:
            uf_clicada = pontos[0].get("location")
            if uf_clicada and uf_clicada != st.session_state["uf_mapa"]:
                st.session_state["uf_mapa"] = uf_clicada
                st.rerun()

st.markdown("---")

# Exibição da Tabela Final (Dataframe)
st.subheader(f"📋 Tabela Completa de Dados - {tipo_base}")

# Fazemos uma cópia leve para formatar os textos
df_exibicao = df_filtrado.copy()

# Dicionário para simplificar os nomes longos de federações e coligações por siglas
substituicoes = {
    "FEDERAÇÃO BRASIL DA ESPERANÇA - FE BRASIL (13-PT / 65-PC do B / 43-PV)": "FE BRASIL (PT/PCdoB/PV)",
    "FEDERAÇÃO BRASIL DA ESPERANÇA - FE BRASIL": "FE BRASIL (PT/PCdoB/PV)",
    "FEDERAÇÃO PSDB CIDADANIA (45-PSDB / 23-CIDADANIA)": "PSDB/CIDADANIA",
    "FEDERAÇÃO PSDB CIDADANIA": "PSDB/CIDADANIA",
    "FEDERAÇÃO RENOVAÇÃO SOLIDÁRIA (25-PRD / 77-SOLIDARIEDADE)": "RENOVAÇÃO (PRD/SOLIDARIEDADE)",
    "FEDERAÇÃO RENOVAÇÃO SOLIDÁRIA": "RENOVAÇÃO (PRD/SOLIDARIEDADE)",
    "FEDERAÇÃO UNIÃO PROGRESSISTA (44-UNIÃO / 11-PP)": "UNIÃO/PP",
    "FEDERAÇÃO UNIÃO PROGRESSISTA": "UNIÃO/PP",
    "FEDERAÇÃO PSOL REDE (50-PSOL / 18-REDE)": "PSOL/REDE",
    "FEDERAÇÃO PSOL REDE": "PSOL/REDE",
}

# Aplica a substituição nas colunas de composição se elas existirem na tabela
for col in ["DS_COMPOSICAO_COLIGACAO", "DS_COMPOSICAO_FEDERACAO"]:
    if col in df_exibicao.columns:
        for nome_longo, sigla_curta in substituicoes.items():
            df_exibicao[col] = df_exibicao[col].astype(str).str.replace(nome_longo, sigla_curta, regex=False)

# Organização das colunas principais
cols_destaque = [c for c in [col_nome_urna, col_nome_cand, col_num_cand, col_cargo, col_partido, col_uf] if c and c in df_exibicao.columns]

# Oculta colunas redundantes
cols_para_esconder = ["CANDIDATO_EXIBICAO", "NM_FEDERACAO", "NM_COLIGACAO"]
cols_outras = [c for c in df_exibicao.columns if c not in cols_destaque and c not in cols_para_esconder]

# Exibe a tabela otimizada
st.dataframe(
    df_exibicao[cols_destaque + cols_outras],
    use_container_width=True
)