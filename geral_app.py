import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Painel Eleitoral 2026", layout="wide")

st.title("🗳️ Eleições 2026 - Consulta de Coligações")

# Função para carregar os dados de 2026 com suporte a acentuação e cache de memória
@st.cache_data
def carregar_dados_2026():
    caminho = "consulta_coligacao_2026_BRASIL.csv"
    encodings = ["latin-1", "iso-8859-1", "cp1252", "utf-8"]
    
    for enc in encodings:
        try:
            df = pd.read_csv(caminho, sep=";", encoding=enc, low_memory=False)
            return df
        except (UnicodeDecodeError, Exception):
            continue
            
    st.error("Não foi possível ler o arquivo das Coligações 2026.")
    return None

st.info("Carregando dados das Coligações de 2026...")

df_2026 = carregar_dados_2026()

if df_2026 is not None:
    st.success("Dados de 2026 carregados com sucesso!")
    
    # Métrica do total de registros
    st.metric("Total de Coligações / Registros", f"{len(df_2026):,}".replace(",", "."))
    
    # Filtro opcional por Estado (UF) se a coluna existir no arquivo
    colunas = [str(col).upper() for col in df_2026.columns]
    col_uf = next((col for col in df_2026.columns if "UF" in col.upper() or "SG_UF" in col.upper()), None)
    
    if col_uf:
        ufs = ["TODOS"] + sorted(list(df_2026[col_uf].dropna().unique()))
        uf_selecionada = st.selectbox("Filtrar por Estado (UF):", ufs)
        
        if uf_selecionada != "TODOS":
            df_exibir = df_2026[df_2026[col_uf] == uf_selecionada]
        else:
            df_exibir = df_2026
    else:
        df_exibir = df_2026

    # Exibição dos dados
    st.subheader("Visualização dos Dados de 2026")
    st.dataframe(df_exibir.head(500), use_container_width=True)