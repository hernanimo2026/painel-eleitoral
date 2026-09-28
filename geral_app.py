import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Simulador de Votação 2026", layout="centered")

# --- LEITURA DA BASE DE DADOS ---
@st.cache_data
def carregar_dados():
    csvs = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csvs:
        return pd.DataFrame()
    for enc in ['latin1', 'iso-8859-1', 'cp1252', 'utf-8']:
        try:
            df = pd.read_csv(csvs[0], sep=';', encoding=enc, dtype=str, on_bad_lines='skip')
            if len(df.columns) > 1:
                df.columns = df.columns.str.strip().str.upper()
                for c in df.columns:
                    df[c] = df[c].astype(str).str.strip().str.upper()
                return df
        except Exception:
            continue
    return pd.DataFrame()

df_candidatos = carregar_dados()

if df_candidatos.empty:
    st.error("⚠️ Nenhuma base de dados (.csv) encontrada no repositório.")
    st.stop()

# Identificação das Colunas
col_num = next((c for c in ['NR_CANDIDATO', 'NR_CAND', 'NUMERO'] if c in df_candidatos.columns), None)
col_nome = next((c for c in ['NM_URNA_CANDIDATO', 'NM_CANDIDATO'] if c in df_candidatos.columns), None)
col_partido = next((c for c in ['SG_PARTIDO', 'PARTIDO'] if c in df_candidatos.columns), None)
col_uf = next((c for c in ['SG_UF', 'UF'] if c in df_candidatos.columns), None)
col_cargo = next((c for c in ['DS_CARGO', 'CARGO'] if c in df_candidatos.columns), None)

# ETAPAS DA VOTAÇÃO 2026
ETAPAS = [
    {"cargo": "DEPUTADO FEDERAL", "digitos": 4, "filtro": ["DEPUTADO FEDERAL"]},
    {"cargo": "DEPUTADO ESTADUAL", "digitos": 5, "filtro": ["DEPUTADO ESTADUAL", "DEPUTADO DISTRITAL"]},
    {"cargo": "SENADOR (1ª VAGA)", "digitos": 3, "filtro": ["SENADOR"]},
    {"cargo": "SENADOR (2ª VAGA)", "digitos": 3, "filtro": ["SENADOR"]},
    {"cargo": "GOVERNADOR", "digitos": 2, "filtro": ["GOVERNADOR"]},
    {"cargo": "PRESIDENTE", "digitos": 2, "filtro": ["PRESIDENTE"]}
]

if "etapa" not in st.session_state:
    st.session_state.etapa = 0
if "votos" not in st.session_state:
    st.session_state.votos = {}
if "uf_sel" not in st.session_state:
    st.session_state.uf_sel = "MT"

# Cabeçalho
c_tit, c_uf = st.columns([2.5, 1])
with c_tit:
    st.title("🗳️ Simulação Eleições 2026")
with c_uf:
    ufs = sorted(df_candidatos[col_uf].dropna().unique().tolist()) if col_uf else ['MT', 'SP', 'RJ']
    st.session_state.uf_sel = st.selectbox("UF:", ufs, index=ufs.index(st.session_state.uf_sel) if st.session_state.uf_sel in ufs else 0)

# Fim da Votação
if st.session_state.etapa >= len(ETAPAS):
    st.balloons()
    st.success("🎉 VOTAÇÃO CONCLUÍDA COM SUCESSO!")
    st.subheader("Resumo dos seus votos:")
    for cargo, voto in st.session_state.votos.items():
        st.write(f"• **{cargo}:** {voto}")
    
    st.divider()
    if st.button("🔄 Reiniciar Votação", type="primary", use_container_width=True):
        st.session_state.etapa = 0
        st.session_state.votos = {}
        st.rerun()
    st.stop()

etapa = ETAPAS[st.session_state.etapa]

# Filtragem de Dados
df_uf = df_candidatos[df_candidatos[col_uf].isin([st.session_state.uf_sel, 'BR'])] if col_uf else df_candidatos
df_cargo = df_uf[df_uf[col_cargo].isin(etapa["filtro"])] if col_cargo else df_uf

st.subheader(f"Voto para: {etapa['cargo']}")
st.caption(f"Digite o número de {etapa['digitos']} dígitos ou selecione na lista.")

# Entrada do Número pelo Teclado Nativo
numero_digitado = st.text_input(
    f"Número do candidato ({etapa['digitos']} dígitos):",
    max_chars=etapa["digitos"],
    key=f"input_{st.session_state.etapa}"
)

cand_encontrado = None
if len(numero_digitado) == etapa["digitos"]:
    match = df_cargo[df_cargo[col_num] == numero_digitado] if col_num else pd.DataFrame()
    if not match.empty:
        cand_encontrado = match.iloc[0]

if cand_encontrado is not None:
    st.info(f"👤 **Candidato:** {cand_encontrado.get(col_nome, 'N/A')}\n\n🚩 **Partido:** {cand_encontrado.get(col_partido, 'N/A')}")
elif len(numero_digitado) == etapa["digitos"]:
    st.warning("⚠️ Número não encontrado na base (será considerado Voto Nulo).")

st.divider()

# Botões de Ação Nativos do Streamlit
c_branco, c_confirma = st.columns(2)

with c_branco:
    if st.button("⚪ Votar em Branco", use_container_width=True):
        st.session_state.votos[etapa["cargo"]] = "BRANCO"
        st.session_state.etapa += 1
        st.rerun()

with c_confirma:
    if st.button("🟢 Confirmar Voto", type="primary", use_container_width=True):
        if len(numero_digitado) == etapa["digitos"]:
            if cand_encontrado is not None:
                st.session_state.votos[etapa["cargo"]] = f"{numero_digitado} - {cand_encontrado.get(col_nome, '')}"
            else:
                st.session_state.votos[etapa["cargo"]] = f"{numero_digitado} (NULO)"
        else:
            st.session_state.votos[etapa["cargo"]] = "NULO"
            
        st.session_state.etapa += 1
        st.rerun()