import unicodedata
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

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
        df = pd.read_excel("BR_malha_Municipios_2025.xlsx")
        df["nm_municipio"] = df["NM_MUN"].apply(remover_acentos)
        df["sg_uf"] = df["SIGLA_UF"]
        df["municipio_id"] = df["nm_municipio"] + " - " + df["sg_uf"]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data
def carregar_dados_2022():
    try:
        df = pd.read_excel("geral.xlsx")
        df["UF_code"] = df["geocodigo"].astype(str).str[:2].astype(int)
        df["sg_uf"] = df["UF_code"].map(uf_map)
        df["nm_municipio"] = df["nome"].apply(remover_acentos)
        df["sg_partido"] = df["Eleiç_2022"]

        col_votos = next(
            (
                c
                for c in ["Vots_2022", "Votó_2022", "Voto_2022", "Votos_2022"]
                if c in df.columns
            ),
            None,
        )
        df["qt_votos_nom_validos"] = (
            pd.to_numeric(df[col_votos], errors="coerce").fillna(0).astype(int)
            if col_votos
            else 0
        )

        def ext_pct(row):
            partido = str(row.get("Eleiç_2022", "")).strip().upper()
            col = f"{partido}%"
            if col in row.index and pd.notna(row[col]):
                try:
                    v = float(
                        str(row[col])
                        .replace("%", "")
                        .replace(",", ".")
                        .strip()
                    )
                    return v * 100 if 0 < v <= 1.0 else v
                except ValueError:
                    pass
            return None

        df["pct_votos"] = df.apply(ext_pct, axis=1)
        df["coligacao"] = df.get(
            "ds_composicao_coligacao", "Não informada / Partido Isolado"
        ).fillna("Não informada / Partido Isolado")
        df["ds_sit_tot_turno"] = "Mais Votado 2022"
        df["municipio_id"] = df["nm_municipio"] + " - " + df["sg_uf"]
        return df
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
            c_t2 = df2["nm_municipio"] + " - " + df2["sg_uf"]
            df1["mun_id"] = df1["nm_municipio"] + " - " + df1["sg_uf"]
            df1_f = df1[~df1["mun_id"].isin(c_t2)].drop(
                columns=["mun_id"], errors="ignore"
            )
            df = pd.concat([df1_f, df2], ignore_index=True)
        except Exception:
            df = df1
            df["nm_municipio"] = df["nm_municipio"].apply(remover_acentos)

        df["municipio_id"] = df["nm_municipio"] + " - " + df["sg_uf"]
        if "qt_votos_nom_validos" in df.columns:
            tot = (
                df.groupby("municipio_id")["qt_votos_nom_validos"]
                .sum()
                .reset_index(name="total_votos_mun")
            )
            df = df.merge(tot, on="municipio_id", how="left")
            df["pct_votos"] = (
                df["qt_votos_nom_validos"] / df["total_votos_mun"]
            ) * 100
        else:
            df["pct_votos"] = 0.0
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data
def carregar_vereadores_2024():
    try:
        df = pd.read_csv(
            "cand_mais_votado-municipio_vereador_t1_2024.csv",
            sep=";",
            encoding="latin1",
        )
        df["nm_municipio"] = df["nm_municipio"].apply(remover_acentos)
        df["municipio_id"] = df["nm_municipio"] + " - " + df["sg_uf"]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data
def carregar_vagas_2026():
    try:
        return pd.read_csv(
            "consulta_vagas_2026_BRASIL.csv", sep=";", encoding="latin1"
        )
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

tab1, tab2, tab3 = st.tabs(
    ["📊 Visão Geral", "🔍 Consulta por Cidade", "📈 Projeções & Força 2026"]
)

# --- ABA 1: VISÃO GERAL ---
with tab1:
    col_ano, col_uf = st.columns(2)
    with col_ano:
        ano_sel = st.selectbox(
            "Ano", options=["2024", "2022 (Presidencial)", "2020"]
        )

    df_cand = (
        carregar_dados_2022()
        if "2022" in ano_sel
        else carregar_dados_csv(ano_sel)
    )

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

        df_eleitos = (
            df_filtered.copy()
            if "2022" in ano_sel
            else df_filtered[
                df_filtered["ds_sit_tot_turno"].isin(
                    ["Eleito", "Eleito por QP", "Eleito por média"]
                )
            ]
        )

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
    df_ver_2024 = carregar_vereadores_2024()

    cidades_lista = (
        sorted(df_malha["municipio_id"].dropna().unique())
        if not df_malha.empty
        else (
            sorted(df_2024["municipio_id"].dropna().unique())
            if not df_2024.empty
            else []
        )
    )

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

            # Vereadores 2024
            st.markdown("#### 🗳️ Vereadores Eleitos (2024)")
            if not df_ver_2024.empty:
                v_cid = df_ver_2024[
                    (df_ver_2024["municipio_id"] == cidade_selecionada)
                    & (
                        df_ver_2024["ds_sit_tot_turno"].isin(
                            ["Eleito por QP", "Eleito por média", "Eleito"]
                        )
                    )
                ]

                if not v_cid.empty:
                    v_resumo = (
                        v_cid.groupby("sg_partido")
                        .size()
                        .reset_index(name="Cadeiras")
                        .sort_values(by="Cadeiras", ascending=False)
                    )
                    cols = st.columns(len(v_resumo))
                    for idx, row in v_resumo.reset_index(drop=True).iterrows():
                        if idx < len(cols):
                            cols[idx].metric(
                                row["sg_partido"], f"{row['Cadeiras']} seg."
                            )

                    st.dataframe(
                        v_cid[
                            [
                                "nm_candidato",
                                "sg_partido",
                                "qt_votos_nom_validos",
                                "ds_sit_tot_turno",
                            ]
                        ]
                        .rename(
                            columns={
                                "nm_candidato": "Nome",
                                "sg_partido": "Partido",
                                "qt_votos_nom_validos": "Votos",
                                "ds_sit_tot_turno": "Situação",
                            }
                        )
                        .sort_values(by="Votos", ascending=False),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Sem registro de vereadores eleitos.")

            # Eleições 2022
            st.markdown("#### 🇧🇷 Eleições 2022 (Presidencial)")
            if not e2022.empty:
                cand = e2022.iloc[0]
                votos_2022 = f"{cand.get('qt_votos_nom_validos', 0):,.0f}".replace(
                    ",", "."
                )
                pct_val = cand.get("pct_votos")
                pct_str = (
                    f" ({pct_val:.2f}%)".replace(".", ",")
                    if pct_val is not None and pd.notna(pct_val)
                    else ""
                )
                colig_2022 = cand.get(
                    "coligacao", "Não informada / Partido Isolado"
                )

                st.info(
                    f"**Mais Votado:** Partido {cand.get('sg_partido', '-')}\n\n"
                    f"**Votos Válidos:** {votos_2022}{pct_str}\n\n"
                    f"**Coligação:** {colig_2022}"
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

# --- ABA 3: PROJEÇÕES & FORÇA 2026 ---
with tab3:
    st.subheader("📈 Capilaridade e Força Política para 2026")
    st.markdown(
        "Esta aba cruza o desempenho dos partidos na base municipal (Prefeitos e Vereadores eleitos em 2024) "
        "para medir a estrutura de apoio (cabos eleitorais) com a qual cada partido chega para as Eleições de 2026."
    )

    df_vagas = carregar_vagas_2026()
    ufs_vagas = (
        sorted(df_vagas["SG_UF"].dropna().unique())
        if not df_vagas.empty
        else []
    )
    uf_proj = st.selectbox(
        "Selecione a UF para Análise Projetiva:",
        options=["Brasil (Todos)"] + ufs_vagas,
    )

    # Vagas 2026
    if not df_vagas.empty:
        df_v_filtrado = (
            df_vagas
            if uf_proj == "Brasil (Todos)"
            else df_vagas[df_vagas["SG_UF"] == uf_proj]
        )
        vagas_summary = (
            df_v_filtrado.groupby("DS_CARGO")["QT_VAGA"]
            .sum()
            .reset_index()
            .sort_values(by="QT_VAGA", ascending=False)
        )

        st.markdown(f"**Vagas em Disputa em 2026 ({uf_proj}):**")
        v_cols = st.columns(min(len(vagas_summary), 6))
        for idx, row in vagas_summary.reset_index(drop=True).iterrows():
            if idx < len(v_cols):
                v_cols[idx].metric(row["DS_CARGO"], int(row["QT_VAGA"]))

    st.markdown("---")

    # Comparativo de Prefeituras (2020 vs 2024)
    st.markdown("### 🏛️ Comparativo de Prefeituras (2020 vs 2024)")
    if not df_2020.empty and not df_2024.empty:
        d20 = (
            df_2020
            if uf_proj == "Brasil (Todos)"
            else df_2020[df_2020["sg_uf"] == uf_proj]
        )
        d24 = (
            df_2024
            if uf_proj == "Brasil (Todos)"
            else df_2024[df_2024["sg_uf"] == uf_proj]
        )

        e20 = (
            d20[
                d20["ds_sit_tot_turno"].isin(
                    ["Eleito", "Eleito por QP", "Eleito por média"]
                )
            ]
            .groupby("sg_partido")
            .size()
            .reset_index(name="Prefeituras 2020")
        )
        e24 = (
            d24[
                d24["ds_sit_tot_turno"].isin(
                    ["Eleito", "Eleito por QP", "Eleito por média"]
                )
            ]
            .groupby("sg_partido")
            .size()
            .reset_index(name="Prefeituras 2024")
        )

        df_comp = pd.merge(e20, e24, on="sg_partido", how="outer").fillna(0)
        df_comp["Saldo"] = df_comp["Prefeituras 2024"] - df_comp["Prefeituras 2020"]
        df_comp = df_comp.sort_values(
            by="Prefeituras 2024", ascending=False
        ).head(15)

        fig_comp = go.Figure()
        fig_comp.add_trace(
            go.Bar(
                x=df_comp["sg_partido"],
                y=df_comp["Prefeituras 2020"],
                name="2020",
                marker_color="#90A4AE",
            )
        )
        fig_comp.add_trace(
            go.Bar(
                x=df_comp["sg_partido"],
                y=df_comp["Prefeituras 2024"],
                name="2024",
                marker_color="#1E88E5",
            )
        )
        fig_comp.update_layout(
            barmode="group",
            height=400,
            margin=dict(t=30, l=10, r=10, b=10),
            title="Prefeituras Conquistadas por Partido",
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    # Força dos Vereadores
    st.markdown("### 🗳️ Total de Vereadores Eleitos em 2024 por Partido")
    if not df_ver_2024.empty:
        dver = (
            df_ver_2024
            if uf_proj == "Brasil (Todos)"
            else df_ver_2024[df_ver_2024["sg_uf"] == uf_proj]
        )
        v_eleitos = dver[
            dver["ds_sit_tot_turno"].isin(
                ["Eleito por QP", "Eleito por média", "Eleito"]
            )
        ]

        if not v_eleitos.empty:
            v_partido = (
                v_eleitos.groupby("sg_partido")
                .size()
                .reset_index(name="Vereadores")
                .sort_values(by="Vereadores", ascending=False)
                .head(15)
            )

            fig_v = px.bar(
                v_partido,
                x="sg_partido",
                y="Vereadores",
                color="sg_partido",
                color_discrete_map=cores_partidos,
                text="Vereadores",
                title="Bases de Vereadores (Principais Partidos)",
            )
            fig_v.update_traces(textposition="outside")
            fig_v.update_layout(
                height=400, showlegend=False, margin=dict(t=30, l=10, r=10, b=10)
            )
            st.plotly_chart(fig_v, use_container_width=True)