import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração Otimizada para Mobile
st.set_page_config(
    page_title="Painel Eleitoral Brasil", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mapeamento Oficial de Cores dos Partidos
cores_partidos = {
    "PT": "#CC0000", "PL": "#FFD700", "MDB": "#008000", "PSD": "#FF8C00",
    "PP": "#00A896", "UNIÃO": "#0047AB", "REPUBLICANOS": "#FF5722",
    "AVANTE": "#708090", "PSDB": "#0000FF", "PRD": "#E53935",
    "SOLIDARIEDADE": "#F57C00", "PODE": "#03A9F4", "PSB": "#D32F2F",
    "PDT": "#1976D2", "MOBILIZA": "#FF9800", "CIDADANIA": "#00BCD4",
    "PSC": "#009688", "NOVO": "#FF6F00", "PV": "#4CAF50", "REDE": "#8BC34A"
}

uf_map = {
    11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
    21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
    31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
    41: 'PR', 42: 'SC', 43: 'RS',
    50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
}

# Funções de Leitura com Cache
@st.cache_data
def carregar_dados_2022():
    try:
        df_geral = pd.read_excel("geral.xlsx")
        df_geral['UF_code'] = df_geral['geocodigo'].astype(str).str[:2].astype(int)
        df_geral['sg_uf'] = df_geral['UF_code'].map(uf_map)
        df_geral['nm_municipio'] = df_geral['nome']
        df_geral['sg_partido'] = df_geral['Eleiç_2022']
        df_geral['qt_votos_nom_validos'] = df_geral['Vots_2022'].fillna(0)
        df_geral['ds_sit_tot_turno'] = 'Mais Votado 2022'
        df_geral['municipio_id'] = df_geral['nm_municipio'] + ' - ' + df_geral['sg_uf']
        return df_geral
    except Exception:
        return pd.DataFrame()

@st.cache_data
def carregar_dados_csv(ano, turno_sel="Resultado Final (1º+2ºT)"):
    try:
        df1 = pd.read_csv(f'cand_mais_votado-municipio_prefeito_t1_{ano}.csv', sep=';', encoding='latin1')
        try:
            df2 = pd.read_csv(f'cand_mais_votado-municipio_prefeito_t2_{ano}.csv', sep=';', encoding='latin1')
            cidades_t2 = df2['nm_municipio'] + ' - ' + df2['sg_uf']
            df1['mun_id'] = df1['nm_municipio'] + ' - ' + df1['sg_uf']
            df1_filtrado = df1[~df1['mun_id'].isin(cidades_t2)].drop(columns=['mun_id'], errors='ignore')
            df = pd.concat([df1_filtrado, df2], ignore_index=True)
        except Exception:
            df = df1
        df['municipio_id'] = df['nm_municipio'] + ' - ' + df['sg_uf']
        return df
    except Exception:
        return pd.DataFrame()

st.title("📱 Painel Eleitoral Brasil")

# Abas Adaptadas
tab1, tab2 = st.tabs(["📊 Visão Geral", "🔍 Consulta por Cidade"])

# --- ABA 1: VISÃO GERAL ---
with tab1:
    col_ano, col_uf = st.columns(2)

    with col_ano:
        ano_sel = st.selectbox("Ano", options=["2024", "2022 (Presidencial)", "2020"])

    if "2022" in ano_sel:
        df_cand = carregar_dados_2022()
        turno_sel = "2º Turno (Presidencial)"
    else:
        df_cand = carregar_dados_csv(ano_sel)
        turno_sel = "Resultado Final (1º+2ºT)"

    if df_cand.empty:
        st.warning(f"⚠️ Dados para o ano **{ano_sel}** não encontrados.")
    else:
        with col_uf:
            ufs = sorted(df_cand['sg_uf'].dropna().unique())
            uf_sel = st.selectbox("UF", options=["Brasil (Todos)"] + ufs)

        metrica = st.radio("Visualizar por:", options=["Total de Votos Válidos", "Dominância nas Cidades"], horizontal=True)

        df_filtered = df_cand.copy()
        if uf_sel != "Brasil (Todos)":
            df_filtered = df_filtered[df_filtered['sg_uf'] == uf_sel]

        if "2022" in ano_sel:
            df_eleitos = df_filtered.copy()
        else:
            df_eleitos = df_filtered[df_filtered['ds_sit_tot_turno'].isin(['Eleito', 'Eleito por QP', 'Eleito por média'])]

        # Cards 2x2 para telas pequenas
        m1, m2 = st.columns(2)
        m1.metric("Total de Votos", f"{df_filtered['qt_votos_nom_validos'].sum():,.0f}".replace(",", "."))
        m2.metric("Municípios", df_filtered['municipio_id'].nunique())

        m3, m4 = st.columns(2)
        m3.metric("Definidos", df_eleitos['municipio_id'].nunique())
        m4.metric("Partido Líder", df_eleitos['sg_partido'].mode()[0] if not df_eleitos.empty else "-")

        st.markdown("---")

        if metrica == "Dominância nas Cidades":
            df_grouped = df_eleitos.groupby('sg_partido').size().reset_index(name='Valor')
            unidade_label = "Cidades"
        else:
            df_grouped = df_filtered.groupby('sg_partido')['qt_votos_nom_validos'].sum().reset_index(name='Valor')
            unidade_label = "Votos"

        df_grouped = df_grouped.sort_values(by='Valor', ascending=False)

        fig = px.treemap(
            df_grouped, path=['sg_partido'], values='Valor',
            color='sg_partido', color_discrete_map=cores_partidos,
            title=f"Desempenho em {ano_sel} - {uf_sel}"
        )
        fig.update_traces(
            texttemplate="<b>%{label}</b><br>" + unidade_label + ": %{value:,.0f}<br>%{percentEntry:.1%}",
            textfont_size=14
        )
        # Altura otimizada para a tela do celular
        fig.update_layout(height=450, margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

# --- ABA 2: CONSULTA POR CIDADE (Mobile Friendly) ---
with tab2:
    st.subheader("🔍 Histórico por Município")

    df_2020 = carregar_dados_csv("2020")
    df_2022 = carregar_dados_2022()
    df_2024 = carregar_dados_csv("2024")

    if not df_2024.empty:
        cidades_lista = sorted(df_2024['municipio_id'].dropna().unique())
        cidade_selecionada = st.selectbox("Selecione o Município:", options=cidades_lista)

        if cidade_selecionada:
            st.markdown(f"### 📍 **{cidade_selecionada}**")

            e2020 = df_2020[(df_2020['municipio_id'] == cidade_selecionada) & (df_2020['ds_sit_tot_turno'].isin(['Eleito', 'Eleito por QP', 'Eleito por média']))]
            e2022 = df_2022[df_2022['municipio_id'] == cidade_selecionada]
            e2024 = df_2024[(df_2024['municipio_id'] == cidade_selecionada) & (df_2024['ds_sit_tot_turno'].isin(['Eleito', 'Eleito por QP', 'Eleito por média']))]

            # Exibição Empilhada Verticalmente para Celular
            st.markdown("#### 🏛️ Eleições 2024 (Prefeito)")
            if not e2024.empty:
                cand = e2024.iloc[0]
                st.success(f"**Prefeito Eleito:** {cand.get('nm_candidato', 'Não informado')}\n\n**Partido:** {cand.get('sg_partido', '-')} | **Votos:** {cand.get('qt_votos_nom_validos', 0):,.0f}".replace(",", "."))
            else:
                st.info("Sem dados de 2024.")

            st.markdown("#### 🇧🇷 Eleições 2022 (Presidencial)")
            if not e2022.empty:
                cand = e2022.iloc[0]
                st.info(f"**Mais Votado:** Partido {cand.get('sg_partido', '-')}\n\n**Votos Válidos:** {cand.get('qt_votos_nom_validos', 0):,.0f}".replace(",", "."))
            else:
                st.info("Sem dados de 2022.")

            st.markdown("#### 🏛️ Eleições 2020 (Prefeito)")
            if not e2020.empty:
                cand = e2020.iloc[0]
                st.success(f"**Prefeito Eleito:** {cand.get('nm_candidato', 'Não informado')}\n\n**Partido:** {cand.get('sg_partido', '-')} | **Votos:** {cand.get('qt_votos_nom_validos', 0):,.0f}".replace(",", "."))
            else:
                st.info("Sem dados de 2020.")