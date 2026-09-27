import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Urna Eletrônica 2026", layout="centered")

# --- LEITURA DA PLANILHA ---
@st.cache_data
def carregar_dados():
    # Busca qualquer arquivo CSV na pasta do projeto
    arquivos_csv = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not arquivos_csv:
        return pd.DataFrame(), "Nenhum arquivo .csv encontrado na pasta!"
    
    caminho = arquivos_csv[0]
    
    for enc in ['latin1', 'iso-8859-1', 'cp1252', 'utf-8']:
        try:
            df = pd.read_csv(caminho, sep=';', encoding=enc, dtype=str, on_bad_lines='skip')
            if len(df.columns) > 1:
                df.columns = df.columns.str.strip().str.upper()
                for col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.upper()
                return df, f"Sucesso! {len(df)} candidatos carregados do arquivo '{caminho}'."
        except Exception as e:
            continue
            
    return pd.DataFrame(), "Erro ao ler o arquivo CSV."

df_candidatos, mensagem_status = carregar_dados()

# Exibe o status do carregamento no topo
if df_candidatos.empty:
    st.error(f"⚠️ {mensagem_status}")
else:
    st.success(f"✅ {mensagem_status}")

# --- IDENTIFICAÇÃO DAS COLUNAS ---
col_num = next((c for c in ['NR_CANDIDATO', 'NR_CAND', 'NUMERO'] if c in df_candidatos.columns), None)
col_nome = next((c for c in ['NM_URNA_CANDIDATO', 'NM_CANDIDATO'] if c in df_candidatos.columns), None)
col_partido = next((c for c in ['SG_PARTIDO', 'PARTIDO'] if c in df_candidatos.columns), None)
col_uf = next((c for c in ['SG_UF', 'UF'] if c in df_candidatos.columns), None)
col_cargo = next((c for c in ['DS_CARGO', 'CARGO'] if c in df_candidatos.columns), None)

st.title("🗳️ Urna Eletrônica 2026")

# Seleção de Estado (UF)
ufs_disponiveis = sorted(df_candidatos[col_uf].dropna().unique().tolist()) if not df_candidatos.empty and col_uf else ['SP', 'RJ', 'MG', 'MT']
uf_selecionada = st.selectbox("UF:", ufs_disponiveis)

# Teste direto de voto/busca
st.subheader("Simulador de Voto")
numero_digitado = st.text_input("Digite o número (2 dígitos para legenda, 4 para Dep. Federal):", max_chars=5)

if numero_digitado:
    num = numero_digitado.strip()
    
    # Filtra por UF se existir
    df_uf = df_candidatos[df_candidatos[col_uf] == uf_selecionada] if not df_candidatos.empty and col_uf else df_candidatos
    
    # Busca Candidato Completo
    cand = df_uf[df_uf[col_num] == num] if not df_uf.empty and col_num else pd.DataFrame()
    
    if not cand.empty:
        item = cand.iloc[0]
        st.markdown(f"### 🟢 CANDIDATO ENCONTRADO")
        st.write(f"**Nome:** {item.get(col_nome, 'N/A')}")
        st.write(f"**Partido:** {item.get(col_partido, 'N/A')}")
        st.write(f"**Cargo:** {item.get(col_cargo, 'N/A')}")
    else:
        # Voto na Legenda (2 dígitos)
        legenda = df_uf[df_uf[col_num].str.startswith(num)] if not df_uf.empty and col_num else pd.DataFrame()
        if len(num) == 2 and not legenda.empty:
            partido = legenda.iloc[0].get(col_partido, 'N/A')
            st.markdown(f"### 🔵 VOTO NA LEGENDA")
            st.write(f"**Partido:** {partido}")
            st.write(f"**UF:** {uf_selecionada}")
        else:
            st.markdown("### 🔴 VOTO NULO")