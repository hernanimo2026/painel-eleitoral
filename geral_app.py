import unicodedata
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração Otimizada para Mobile
st.set_page_config(
    page_title="Painel Eleitoral Brasil",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Função para remover acentos e 'Ç'
def remover_acentos(texto):
    if not isinstance(texto, str):
        return texto
    nfkd = unicodedata.normalize("NFKD", texto)
    texto_sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return texto_sem_acento.upper()


# Mapeamento Oficial de Cores dos Partidos
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
    "PSC": "#009688",
    "NOVO": "#FF6F00",
    "PV": "#4CAF50",
    "REDE": "#8BC34A",
}

uf_map = {
    11: "RO",
    12: "AC",
    13: "AM",
    14: "RR",
    15: "PA",
    16: "AP",
    17: "TO",
    21: "MA",
    22: "PI",
    23: "CE",
    24: "RN",
    25: "PB",
    26: "PE",
    27: "AL",
    28: "SE",
    29: "BA",
    31: "MG",
    32: "ES",
    33: "RJ",
    35: "SP",
    41: "PR",
    42: "SC",
    43: "RS",
    50: "MS",
    51: "MT",
    52: "GO",
    53: "DF",
}


@st.cache_data
def carregar_malha_2025():
    try:
        df_malha = pd.read_excel("BR_malha_Municipios_2025.xlsx")
        df_malha["nm_municipio"] = df_malha["NM_MUN"].apply(remover_acentos)
        df_malha["sg_uf"] = df_malha["SIGLA_UF"]
        df_malha["municipio_id"] = (
            df_malha["nm_municipio"] + " - " + df_malha["sg_uf"]
        )
        return df_malha
    except Exception:
        return pd.DataFrame()


@st.cache_data
def carregar_dados_2022():
    try:
        df_geral = pd.read_excel("geral.xlsx")
        df_geral["UF_code"] = (
            df_geral["geocodigo"].astype(str).str[:2].astype(int)
        )
        df_geral["sg_uf"] = df_geral["UF_code"].map(uf_map)
        df_geral["nm_municipio"] = df_geral["nome"].apply(remover_acentos)
        df_geral["sg_partido"] = df_geral["Eleiç_2022"]

        # Busca coluna de votos
        col_votos = None
        for col in ["Vots_2022", "Votó_2022", "Voto_2022", "Votos_2022"]:
            if col in df_geral.columns:
                col_votos = col
                break

        if col_votos:
            votos = pd.to_numeric(df_geral[col_votos], errors="coerce").fillna(0)
            df_geral["qt_votos_nom_validos"] = votos.astype(int)
        else:
            df_geral["qt_votos_nom_validos"] = 0

        # Lógica para ler diretamente as colunas PT% e PL% do Excel
        def extrair_porcentagem_2022(row):
            partido = str(row.get("Eleiç_2022", "")).strip().upper()
            col_alvo = f"{partido}%"  # Procura por 'PT%' ou 'PL%'

            if col_alvo in row.index and pd.notna(row[col_alvo]):
                val_raw = row[col_alvo]
                val_clean = (
                    str(val_raw).replace("%", "").replace(",", ".").strip()
                )
                try:
                    val = float(val_clean)
                    return val * 100 if 0 < val <= 1.0 else val
                except ValueError:
                    pass
            return None

        df_geral["pct_votos"] = df_geral.apply(
            extrair_porcentagem_2022, axis=1
        )

        df_geral["ds_sit_tot_turno"] = "Mais Votado 2022"
        df_geral["municipio_id"] = (
            df_geral["nm_municipio"] + " - " + df_geral["sg_uf"]
        )
        return df_geral
    except Exception:
        return pd.DataFrame()


@st.cache_data
def carregar_dados_csv(ano):
    try:
        df1 = pd.read_csv(
            f"cand_mais_votado-municipio_prefeito_t1_{ano}.csv",
            sep=";",
            encoding="latin1",
        )
        try:
            df2 = pd.read_csv(
                f"cand_mais_votado-municipio_prefeito_t2_{ano}.csv",
                sep=";",
                encoding="latin1",
            )
            df1["nm_municipio"] = df1["nm_municipio"].apply(remover_acentos)
            df2["nm_municipio"] = df2["nm_municipio"].apply(remover_acentos)
            cidades_t2 = df2["nm_municipio"] + " - " + df2["sg_uf"]
            df1["mun_id"] = df1["nm_municipio"] + " - " + df1["sg_uf"]
            df1_filtrado = df1[~df1["mun_id"].isin(cidades_t2)].drop(
                columns=["mun_id"], errors="ignore"
            )
            df = pd.concat([df1_filtrado, df2], ignore_index=True)
        except Exception:
            df = df1
            df["nm_municipio"] = df["nm_municipio"].apply(remover_acentos)

        df["municipio_id"] = df["nm_municipio"] + " - " + df["sg_uf"]

        if "qt_votos_nom_validos" in df.columns:
            totais = (
                df.groupby("municipio_id")["qt_votos_nom_validos"]
                .sum()
                .reset_index(name="total_votos_mun")
            )
            df = df.merge(totais, on="municipio_id", how="left")
            df["pct_votos"] = (
                df["qt_votos_nom_validos"] / df["total_votos_mun"]
            ) * 100
        else:
            df["pct_votos"] = 0.0

        return df
    except Exception:
        return pd.DataFrame()


def obter_coligacao(cand):
    for col in [
        "ds_coligacao",
        "coligacao",
        "ds_composicao_coligacao",
        "composicao_coligacao",
        "DS_COMPOSICAO_COLIGACAO",
    ]:
        if col in cand and pd.notna(cand[col]):
            return str(cand[col])
    return "Não informada / Partido Isolado"


st.title("📱 Painel Eleitoral Brasil")

tab1, tab2 = st.tabs(["📊 Visão Geral", "🔍 Consulta por Cidade"])

# --- ABA 1: VISÃO GERAL ---
with tab1:
    col_ano, col_uf = st.columns(2)

    with col_ano:
        ano_sel = st.selectbox(
            "Ano", options=["2024", "2022 (Presidencial)", "2020"]
        )

    if "2022" in ano_sel:
        df_cand = carregar_dados_2022()
    else:
        df_cand = carregar_dados_csv(ano_sel)

    if df_cand.empty:
        st.warning(f"⚠️ Dados para o ano **{ano_sel}** não encontrados.")
    else:
        with col_uf:
            ufs = sorted(df_cand["sg_uf"].dropna().unique())
            uf_sel = st.selectbox("UF", options=["Brasil (Todos)"] + ufs)

        metrica = st.radio(
            "Visualizar por:",
            options=["Total de Votos Válidos", "Dominância nas Cidades"],
            horizontal=True,
        )

        df_filtered = df_cand.copy()
        if uf_sel != "Brasil (Todos)":
            df_filtered = df_filtered[df_filtered["sg_uf"] == uf_sel]

        if "2022" in ano_sel:
            df_eleitos = df_filtered.copy()
        else:
            df_eleitos = df_filtered[
                df_filtered["ds_sit_tot_turno"].isin(
                    ["Eleito", "Eleito por QP", "Eleito por média"]
                )
            ]

        m1, m2 = st.columns(2)
        m1.metric(
            "Total de Votos",
            f"{df_filtered['qt_votos_nom_validos'].sum():,.0f}".replace(
                ",", "."
            ),
        )
        m2.metric("Municípios", df_filtered["municipio_id"].nunique())

        m3, m4 = st.columns(2)
        m3.metric("Definidos", df_eleitos["municipio_id"].nunique())
        m4.metric(
            "Partido Líder",
            (
                df_eleitos["sg_partido"].mode()[0]
                if not df_eleitos.empty
                else "-"
            ),
        )

        st.markdown("---")

        if metrica == "Dominância nas Cidades":
            df_grouped = (
                df_eleitos.groupby("sg_partido")
                .size()
                .reset_index(name="Valor")
            )
            unidade_label = "Cidades"
        else:
            df_grouped = (
                df_filtered.groupby("sg_partido")["qt_votos_nom_validos"]
                .sum()
                .reset_index(name="Valor")
            )
            unidade_label = "Votos"

        df_grouped = df_grouped.sort_values(by="Valor", ascending=False)

        fig = px.treemap(
            df_grouped,
            path=["sg_partido"],
            values="Valor",
            color="sg_partido",
            color_discrete_map=cores_partidos,
            title=f"Desempenho em {ano_sel} - {uf_sel}",
        )
        fig.update_traces(
            texttemplate="<b>%{label}</b><br>"
            + unidade_label
            + ": %{value:,.0f}<br>%{percentEntry:.1%}",
            textfont_size=14,
        )
        fig.update_layout(height=450, margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

# --- ABA 2: CONSULTA POR CIDADE ---
with tab2:
    st.subheader("🔍 Histórico por Município")

    df_malha = carregar_malha_2025()
    df_2020 = carregar_dados_csv("2020")
    df_2022 = carregar_dados_2022()
    df_2024 = carregar_dados_csv("2024")

    if not df_malha.empty:
        cidades_lista = sorted(df_malha["municipio_id"].dropna().unique())
    elif not df_2024.empty:
        cidades_lista = sorted(df_2024["municipio_id"].dropna().unique())
    else:
        cidades_lista = []

    if cidades_lista:
        cidade_selecionada = st.selectbox(
            "Selecione o Município:", options=cidades_lista
        )

        if cidade_selecionada:
            st.markdown(f"### 📍 **{cidade_selecionada}**")

            e2020 = df_2020[
                (df_2020["municipio_id"] == cidade_selecionada)
                & (
                    df_2020["ds_sit_tot_turno"].isin(
                        ["Eleito", "Eleito por QP", "Eleito por média"]
                    )
                )
            ]
            e2022 = df_2022[df_2022["municipio_id"] == cidade_selecionada]
            e2024 = df_2024[
                (df_2024["municipio_id"] == cidade_selecionada)
                & (
                    df_2024["ds_sit_tot_turno"].isin(
                        ["Eleito", "Eleito por QP", "Eleito por média"]
                    )
                )
            ]

            # Eleições 2024
            st.markdown("#### 🏛️ Eleições 2024 (Prefeito)")
            if not e2024.empty:
                cand = e2024.iloc[0]
                colig_2024 = obter_coligacao(cand)
                votos_2024 = f"{cand.get('qt_votos_nom_validos', 0):,.0f}".replace(
                    ",", "."
                )
                pct_2024 = f"{cand.get('pct_votos', 0):.2f}%".replace(".", ",")
                st.success(
                    f"**Prefeito Eleito:** {cand.get('nm_candidato', 'Não informado')}\n\n"
                    f"**Partido:** {cand.get('sg_partido', '-')} | **Votos:** {votos_2024} ({pct_2024})\n\n"
                    f"**Coligação:** {colig_2024}"
                )
            else:
                st.info("Sem dados de 2024.")

            # Eleições 2022
            st.markdown("#### 🇧🇷 Eleições 2022 (Presidencial)")
            if not e2022.empty:
                cand = e2022.iloc[0]
                votos_2022 = f"{cand.get('qt_votos_nom_validos', 0):,.0f}".replace(
                    ",", "."
                )
                pct_val = cand.get("pct_votos")

                if pct_val is not None and pd.notna(pct_val):
                    pct_str = f" ({pct_val:.2f}%)".replace(".", ",")
                else:
                    pct_str = ""

                st.info(
                    f"**Mais Votado:** Partido {cand.get('sg_partido', '-')}\n\n"
                    f"**Votos Válidos:** {votos_2022}{pct_str}"
                )
            else:
                st.info("Sem dados de 2022.")

            # Eleições 2020
            st.markdown("#### 🏛️ Eleições 2020 (Prefeito)")
            if not e2020.empty:
                cand = e2020.iloc[0]
                colig_2020 = obter_coligacao(cand)
                votos_2020 = f"{cand.get('qt_votos_nom_validos', 0):,.0f}".replace(
                    ",", "."
                )
                pct_2020 = f"{cand.get('pct_votos', 0):.2f}%".replace(".", ",")
                st.success(
                    f"**Prefeito Eleito:** {cand.get('nm_candidato', 'Não informado')}\n\n"
                    f"**Partido:** {cand.get('sg_partido', '-')} | **Votos:** {votos_2020} ({pct_2020})\n\n"
                    f"**Coligação:** {colig_2020}"
                )
            else:
                st.info("Sem dados de 2020.")