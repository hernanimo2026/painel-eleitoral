import unicodedata
import pandas as pd
import streamlit as st


# Função para remover acentos e padronizar texto em maiúsculas
def remover_acentos(texto):
  if not isinstance(texto, str):
    return ""
  texto_nfkd = unicodedata.normalize("NFKD", texto)
  return "".join([c for c in texto_nfkd if not unicodedata.combining(c)]).upper()


# 1. Carregamento e Limpeza
df_candidatos = pd.read_csv(
    "consulta_cand_2026_BRASIL.csv", encoding="latin-1", sep=";"
)
df_limpo = df_candidatos.drop(
    columns=["ANO_ELEICAO", "NM_FEDERACAO"], errors="ignore"
)

# Garante que preenchemos valores nulos nas colunas de alianças políticas
df_limpo["DS_COMPOSICAO_COLIGACAO"] = df_limpo[
    "DS_COMPOSICAO_COLIGACAO"
].fillna("PARTIDO ISOLADO")
if "DS_COMPOSICAO_FEDERACAO" in df_limpo.columns:
  df_limpo["DS_COMPOSICAO_FEDERACAO"] = df_limpo[
      "DS_COMPOSICAO_FEDERACAO"
  ].fillna("SEM FEDERAÇÃO")

st.title("Painel de Eleições 2026")

# --- FILTROS DINÂMICOS NO TOPO ---
with st.expander("🔍 Filtros de Pesquisa (Clique para recolher)", expanded=True):

  # Passo 1: Listas base
  lista_cargos = sorted(df_limpo["DS_CARGO"].dropna().unique())
  lista_ufs = sorted(df_limpo["SG_UF"].dropna().unique())

  col1, col2 = st.columns(2)

  with col1:
    cargos_selecionados = st.multiselect(
        "1. Cargo:",
        options=lista_cargos,
        default=["PRESIDENTE", "GOVERNO", "SENADOR", "DEPUTADO FEDERAL"],
    )
    ufs_selecionadas = st.multiselect("2. Estado (UF):", options=lista_ufs)

  # Pré-filtragem da base para atualizar as opções de partidos e coligações com base no Estado/Cargo escolhidos
  df_opcoes = df_limpo.copy()
  if cargos_selecionados:
    df_opcoes = df_opcoes.loc[df_opcoes["DS_CARGO"].isin(cargos_selecionados)]
  if ufs_selecionadas:
    df_opcoes = df_opcoes.loc[df_opcoes["SG_UF"].isin(ufs_selecionadas)]

  # Puxa apenas os partidos e coligações válidos para as seleções acima
  lista_partidos = sorted(df_opcoes["SG_PARTIDO"].dropna().unique())
  lista_coligacoes = sorted(
      df_opcoes["DS_COMPOSICAO_COLIGACAO"].dropna().unique()
  )

  with col2:
    modo_politico = st.radio(
        "3. Como deseja filtrar os partidos/coligações?",
        options=["Filtrar por Partido", "Filtrar por Coligação"],
        horizontal=True,
    )

    if modo_politico == "Filtrar por Partido":
      partidos_selecionados = st.multiselect(
          "Selecione o Partido:", options=lista_partidos
      )
      coligacoes_selecionadas = []
    else:
      coligacoes_selecionadas = st.multiselect(
          "Selecione a Coligação/Federação:", options=lista_coligacoes
      )
      partidos_selecionados = []

  nome_pesquisa = st.text_input(
      "4. Buscar pelo Nome do Candidato (ou deixe em branco para todos):"
  )

# --- APLICANDO A FILTRAGEM FINAL ---
condicao = pd.Series([True] * len(df_limpo))

if cargos_selecionados:
  condicao = condicao & df_limpo["DS_CARGO"].isin(cargos_selecionados)

if ufs_selecionadas:
  condicao = condicao & df_limpo["SG_UF"].isin(ufs_selecionadas)

if modo_politico == "Filtrar por Partido" and partidos_selecionados:
  condicao = condicao & df_limpo["SG_PARTIDO"].isin(partidos_selecionados)

elif modo_politico == "Filtrar por Coligação" and coligacoes_selecionadas:
  condicao = condicao & df_limpo["DS_COMPOSICAO_COLIGACAO"].isin(
      coligacoes_selecionadas
  )

if nome_pesquisa.strip():
  termo_busca = remover_acentos(nome_pesquisa)
  nomes_sem_acento = df_limpo["NM_URNA_CANDIDATO"].apply(remover_acentos)
  condicao = condicao & nomes_sem_acento.str.contains(
      termo_busca, regex=False
  )

candidatos_filtrados = df_limpo.loc[condicao]

# --- RESULTADOS ---
st.subheader("Candidatos Encontrados")
st.dataframe(candidatos_filtrados.head(50))

total_por_partido = (
    candidatos_filtrados.groupby(["SG_UF", "SG_PARTIDO", "DS_CARGO"])[
        "NR_CANDIDATO"
    ]
    .count()
    .reset_index(name="TOTAL_CANDIDATOS")
)

st.subheader("Resumo por Estado e Partido")
st.dataframe(total_por_partido)