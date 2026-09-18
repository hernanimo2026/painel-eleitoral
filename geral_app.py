import streamlit as st
import pandas as pd

# Configuração da página para ocupar a tela inteira e carregar leve
st.set_page_config(page_title="Painel Eleitoral Brasil", layout="wide")

st.title("🗳️ Painel Eleitoral Brasil")

# Função com cache para não recarregar o arquivo a todo momento na memória
@st.cache_data
def carregar_dados(caminho_arquivo):
    try:
        # Lê apenas colunas essenciais ou trata separadores padrão de dados eleitorais
        df = pd.read_csv(caminho_arquivo, sep=";", low_memory=False)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo {caminho_arquivo}: {e}")
        return None

# Menu de seleção para carregar apenas o dataset necessário (Lazy Loading)
opcao_eleicao = st.sidebar.selectbox(
    "Selecione o Dataset Eleitoral",
    [
        "Selecione...",
        "Prefeito 2020 - 1º Turno",
        "Prefeito 2024 - 1º Turno",
        "Presidente 2020 - 1º Turno",
        "Presidente 2020 - 2º Turno",
        "Cand. 2024 com IBGE",
        "Coligações 2026"
    ]
)

# Mapeamento dos arquivos CSV exatamente como estão no seu repositório
arquivos_map = {
    "Prefeito 2020 - 1º Turno": "cand_mais_votado-municipio_prefeito_t1_2020.csv",
    "Prefeito 2024 - 1º Turno": "cand_mais_votado-municipio_prefeito_t1_2024.csv",
    "Presidente 2020 - 1º Turno": "cand_mais_votado-municipio_presidente_t1_2020.csv",
    "Presidente 2020 - 2º Turno": "cand_mais_votado-municipio_presidente_t2_2020.csv",
    "Cand. 2024 com IBGE": "cand_mais_votado-2024_com_ibge.csv",
    "Coligações 2026": "consulta_coligacao_2026_BRASIL.csv"
}

if opcao_eleicao != "Selecione...":
    arquivo = arquivos_map[opcao_eleicao]
    st.info(f"Carregando dados de: {opcao_eleicao}...")
    
    df = carregar_dados(arquivo)
    
    if df is not None:
        st.success("Dados carregados com sucesso!")
        st.metric("Total de Registros", len(df))
        
        # Exibe uma amostra dos dados para o usuário sem sobrecarregar a tela
        st.subheader("Pré-visualização dos Dados")
        st.dataframe(df.head(100), use_container_width=True)
else:
    st.write("👈 Escolha uma das opções no menu lateral para visualizar os dados eleitorais.")