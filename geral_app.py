import unicodedata
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Painel Eleitoral Brasil",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def remover_acentos(texto):
    if not isinstance(texto, str):
        return texto
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).upper()


cores_partidos = {
    "PT": "#CC0000",
    "PL": "#FFD700",
    "MDB": "#008000",
    "PSD": "#FF8C00",
    "PP": "#00A896",
    "UNIÃO": "#0047AB",
    "REPUBLICANOS": "#FF5722",
    "AVANTE": "#708090",
    "PSDB": "#0000FF",
    "PRD": "#E53935",
    "SOLIDARIEDADE": "#F57C00",
    "PODE": "#03A9F4",
    "PSB": "#D32F2F",
    "PDT": "#1976D2",
    "MOBILIZA": "#FF9800",
    "CIDADANIA": "#00BCD4",
    "NOVO": "#FF6F00",
    "PV": "#4CAF50",
    "REDE": "#8BC34A",
}


@st.cache_data
def carregar_dados_2022_csv():
    """Carrega os dados de 2022 a partir do CSV convertido."""
    try:
        df = pd.read_csv("geral_2022.csv", sep=";", encoding="utf-8", low_memory=False)
        if "geocodigo" in df.columns and "nome" in df.columns:
            df["nm_municipio"] = df["nome"].apply(remover_acentos)
            df["sg_partido"] = df.get("Eleiç_2022", "OUTROS")
            col_votos = next(
                (c for c in ["Vots_2022", "Voto_2022", "Votos_2022"] if c in df.columns),
                None,
            )
            df["qt_votos_nom_validos"] = (
                pd.to_numeric(df[col_votos], errors="coerce").fillna(0).astype(int)
                if col_votos
                else 0
            )
            df["nm_candidato"] = "Presidente mais votado (" + df["sg_partido"] + ")"
            df["ds_sit_tot_turno"] = "Mais Votado 2022"
            df["ds_composicao_coligacao"] = df.get(
                "ds_composicao_coligacao", "Não informada / Partido Isolado"
            ).fillna("Não informada / Partido Isolado")
            
            # Ajuste da UF se disponível ou extração do geocódigo
            if "sg_uf" not in df.columns:
                df["sg_uf"] = df["geocodigo"].astype(str).str[:2]
            
            df["municipio_id"] = df["nm_municipio"] + " - " + df["sg_uf"]
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data
def carregar_dados_prefeitos(ano):
    cols = [
        "sg_uf",
        "nm_municipio",
        "sg_partido",
        "nm_candidato",
        "ds_sit_tot_turno",
        "qt_votos_nom_validos",
        "ds_composicao_coligacao",
    ]
    try:
        df = pd.read_csv(
            f"cand_mais_votado-municipio_prefeito_t1_{ano}.csv",
            sep=";",
            encoding="latin1",
            usecols=lambda c: c in cols,
            low_memory=False,
        )
        df["nm_municipio"] = df["nm_municipio"].apply(remover_acentos)
        df["municipio_id"] = df["nm_municipio"] + " - " + df["sg_uf"]
        return df
    except Exception:
        return pd.DataFrame()


def obter_df_por_ano(ano):
    if "2022" in ano:
        return carregar_dados_2022_csv()
    else:
        return carregar_dados_prefeitos(ano)


st.title("📱 Painel Eleitoral Brasil")

tab1, tab2 = st.tabs(["📊 Visão Geral", "🔍 Consulta por Cidade"])

# --- ABA 1: VISÃO GERAL ---
with tab1:
    ano_sel = st.selectbox(
        "Ano da Eleição (Visão Geral)",
        options=["2024", "2022 (Presidencial)", "2020"],
    )
    df = obter_df_por_ano(ano_sel)

    if df.empty:
        st.warning(f"⚠️ Dados para o ano **{ano_sel}** não encontrados.")
    else:
        ufs = sorted(df["sg_uf"].dropna().unique())
        uf_sel = st.selectbox("Filtrar por Estado (UF):", options=["Todos"] + ufs)

        df_filtered = df if uf_sel == "Todos" else df[df["sg_uf"] == uf_sel]

        m1, m2 = st.columns(2)
        m1.metric("Cidades", df_filtered["municipio_id"].nunique())
        m2.metric(
            "Total Votos",
            f"{df_filtered['qt_votos_nom_validos'].sum():,.0f}".replace(",", "."),
        )

        df_grouped = (
            df_filtered.groupby("sg_partido")["qt_votos_nom_validos"]
            .sum()
            .reset_index()
        )
        fig = px.treemap(
            df_grouped,
            path=["sg_partido"],
            values="qt_votos_nom_validos",
            color="sg_partido",
            color_discrete_map=cores_partidos,
            title=f"Votação por Partido em {ano_sel} ({uf_sel})",
        )
        st.plotly_chart(fig, use_container_width=True)

# --- ABA 2: CONSULTA POR CIDADE ---
with tab2:
    st.subheader("🔍 Consulta por Cidade")

    ano_cidade_sel = st.selectbox(
        "Selecione o Ano para Consultar:",
        options=["2024", "2022 (Presidencial)", "2020"],
        key="sel_ano_cidade",
    )

    df_cidade_ano = obter_df_por_ano(ano_cidade_sel)

    if df_cidade_ano.empty:
        st.warning(f"⚠️ Dados não encontrados para a eleição de **{ano_cidade_sel}**.")
    else:
        cidades = sorted(df_cidade_ano["municipio_id"].dropna().unique())
        cid_sel = st.selectbox("Selecione a Cidade:", options=cidades)

        if cid_sel:
            dados = df_cidade_ano[df_cidade_ano["municipio_id"] == cid_sel]
            st.markdown(f"### 📍 **{cid_sel}** — Eleições **{ano_cidade_sel}**")

            for _, row in dados.iterrows():
                st.info(
                    f"📅 **Ano da Eleição:** {ano_cidade_sel}\n\n"
                    f"👤 **Candidato:** {row.get('nm_candidato', '-')}\n\n"
                    f"🚩 **Partido:** {row.get('sg_partido', '-')} | "
                    f"🗳️ **Votos:** {row.get('qt_votos_nom_validos', 0):,.0f} | "
                    f"📌 **Resultado:** {row.get('ds_sit_tot_turno', '-')}\n\n"
                    f"🤝 **Coligação:** {row.get('ds_composicao_coligacao', '-')}"
                )