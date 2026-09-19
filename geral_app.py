import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Painel Eleitoral 2026", layout="wide")

st.title("🗳️ Eleições 2026 - Navegação Direta pelo Mapa")

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

arquivo = "consulta_cand_2026_BRASIL.csv" if tipo_base == "Candidatos 2026" else "consulta_coligacao_2026_BRASIL.csv"
df_2026 = carregar_dados(arquivo)

if df_2026 is not None:
    cols = df_2026.columns.tolist()
    
    col_uf = next((c for c in cols if "SG_UF" in c.upper() or "UF" in c.upper()), None)
    col_cargo = next((c for c in cols if "DS_CARGO" in c.upper() or "CARGO" in c.upper()), None)
    col_partido = next((c for c in cols if "SG_PARTIDO" in c.upper() or "PARTIDO" in c.upper()), None)
    
    col_nome_urna = next((c for c in cols if "NM_URNA_CANDIDATO" in c.upper() or "NM_URNA" in c.upper()), None)
    col_nome_cand = next((c for c in cols if "NM_CANDIDATO" in c.upper()), None)
    col_num_cand = next((c for c in cols if "NR_CANDIDATO" in c.upper()), None)

    col_cand_principal = col_nome_urna if col_nome_urna else col_nome_cand

    # Estado selecionado exclusivo do Mapa
    if "uf_mapa" not in st.session_state:
        st.session_state["uf_mapa"] = "TODOS"

    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros de Apoio")

    df_filtrado = df_2026.copy()

    # Aplica o filtro da UF vindo unicamente do toque no mapa
    if col_uf and st.session_state["uf_mapa"] != "TODOS":
        df_filtrado = df_filtrado[df_filtrado[col_uf] == st.session_state["uf_mapa"]]

    # 1. Filtro por Cargo
    if col_cargo:
        lista_cargos = ["TODOS"] + sorted([str(x) for x in df_filtrado[col_cargo].dropna().unique()])
        cargo_sel = st.sidebar.selectbox("Cargo Disputado:", lista_cargos)
        if cargo_sel != "TODOS":
            df_filtrado = df_filtrado[df_filtrado[col_cargo] == cargo_sel]

    # 2. Filtro por Partido
    if col_partido:
        lista_partidos = ["TODOS"] + sorted([str(x) for x in df_filtrado[col_partido].dropna().unique()])
        partido_sel = st.sidebar.selectbox("Partido / Coligação:", lista_partidos)
        if partido_sel != "TODOS":
            df_filtrado = df_filtrado[df_filtrado[col_partido] == partido_sel]

    # 3. Filtro por Nome do Candidato
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

    # Botão para resetar o mapa de forma simples
    if st.session_state["uf_mapa"] != "TODOS":
        if st.sidebar.button("🇧🇷 Ver Brasil Inteiro (Resetar Mapa)"):
            st.session_state["uf_mapa"] = "TODOS"
            st.rerun()

    # Indicadores
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
            )
            fig_mapa.update_geos(fitbounds="locations", visible=False)
            fig_mapa.update_layout(
                margin=dict(t=10, l=0, r=0, b=0),
                height=420,
                clickmode="event+select"
            )
            
            # Captura simples de clique/toque
            event_data = st.plotly_chart(
                fig_mapa,
                use_container_width=True,
                on_select="rerun",
                selection_mode="points"
            )

            # Atualiza o filtro apenas quando há um toque confirmado no mapa
            if event_data and "selection" in event_data and "points" in event_data["selection"]:
                pontos = event_data["selection"]["points"]
                if pontos:
                    uf_clicada = pontos[0].get("location")
                    if uf_clicada and uf_clicada != st.session_state["uf_mapa"]:
                        st.session_state["uf_mapa"] = uf_clicada
                        st.rerun()

    with col_right:
        st.subheader("📈 Ranking de Partidos")
        if col_partido:
            df_partidos = df_filtrado[col_partido].value_counts().head(10).reset_index()
            df_partidos.columns = [col_partido, "QTD"]
            fig_bar = px.bar(
                df_partidos,
                x="QTD",
                y=col_partido,
                orientation="h",
                text="QTD",
                color="QTD",
                color_continuous_scale="Blues"
            )
            fig_bar.update_layout(
                yaxis=dict(autorange="reversed"),
                showlegend=False,
                height=420,
                margin=dict(t=10, l=0, r=0, b=0)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader(f"📋 Tabela Completa de Dados - {tipo_base}")

    cols_destaque = [c for c in [col_nome_urna, col_nome_cand, col_num_cand, col_cargo, col_partido, col_uf] if c and c in df_filtrado.columns]
    cols_outras = [c for c in df_filtrado.columns if c not in cols_destaque and c != "CANDIDATO_EXIBICAO"]
    
    st.dataframe(df_filtrado[cols_destaque + cols_outras], use_container_width=True)

else:
    st.error("Aguardando carregamento da base de dados...")