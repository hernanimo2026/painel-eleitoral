import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Urna Eletrônica 2026", layout="centered")

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
    st.error("⚠️ Nenhuma base de dados encontrada no repositório.")
    st.stop()

# Colunas do TSE
col_num = next((c for c in ['NR_CANDIDATO', 'NR_CAND', 'NUMERO'] if c in df_candidatos.columns), None)
col_nome = next((c for c in ['NM_URNA_CANDIDATO', 'NM_CANDIDATO'] if c in df_candidatos.columns), None)
col_partido = next((c for c in ['SG_PARTIDO', 'PARTIDO'] if c in df_candidatos.columns), None)
col_uf = next((c for c in ['SG_UF', 'UF'] if c in df_candidatos.columns), None)
col_cargo = next((c for c in ['DS_CARGO', 'CARGO'] if c in df_candidatos.columns), None)

# --- ETAPAS DA VOTAÇÃO ---
ETAPAS = [
    {"cargo": "DEPUTADO FEDERAL", "digitos": 4, "legenda": True, "filtro": ["DEPUTADO FEDERAL"]},
    {"cargo": "DEPUTADO ESTADUAL", "digitos": 5, "legenda": True, "filtro": ["DEPUTADO ESTADUAL", "DEPUTADO DISTRITAL"]},
    {"cargo": "SENADOR", "digitos": 3, "legenda": False, "filtro": ["SENADOR"]},
    {"cargo": "GOVERNADOR", "digitos": 2, "legenda": False, "filtro": ["GOVERNADOR"]},
    {"cargo": "PRESIDENTE", "digitos": 2, "legenda": False, "filtro": ["PRESIDENTE"]}
]

# Sessão da Urna
if "etapa" not in st.session_state:
    st.session_state.etapa = 0
if "digitos" not in st.session_state:
    st.session_state.digitos = ""
if "votos" not in st.session_state:
    st.session_state.votos = {}
if "uf_sel" not in st.session_state:
    st.session_state.uf_sel = "MT"

# Topo: Título e Filtro UF
c_tit, c_uf = st.columns([3, 1])
with c_tit:
    st.title("🗳️ Urna Eletrônica 2026")
with c_uf:
    ufs = sorted(df_candidatos[col_uf].dropna().unique().tolist()) if col_uf else ['MT', 'SP', 'RJ']
    st.session_state.uf_sel = st.selectbox("UF:", ufs, index=ufs.index(st.session_state.uf_sel) if st.session_state.uf_sel in ufs else 0)

# FIM DA VOTAÇÃO
if st.session_state.etapa >= len(ETAPAS):
    st.balloons()
    st.success(" VOTAÇÃO CONCLUÍDA COM SUCESSO!")
    st.markdown("<h1 style='text-align: center; font-size: 80px;'>FIM</h1>", unsafe_allow_html=True)
    if st.button("🔄 Nova Votação", use_container_width=True):
        st.session_state.etapa = 0
        st.session_state.digitos = ""
        st.session_state.votos = {}
        st.rerun()
    st.stop()

etapa = ETAPAS[st.session_state.etapa]

# Filtragem de candidatos por UF e Cargo
df_uf = df_candidatos[df_candidatos[col_uf].isin([st.session_state.uf_sel, 'BR'])] if col_uf else df_candidatos
df_cargo = df_uf[df_uf[col_cargo].isin(etapa["filtro"])] if col_cargo else df_uf

dig = st.session_state.digitos
cand = None
e_legenda = False

if len(dig) == etapa["digitos"]:
    m = df_cargo[df_cargo[col_num] == dig] if col_num else pd.DataFrame()
    if not m.empty:
        cand = m.iloc[0]
elif len(dig) == 2 and etapa["legenda"]:
    m_leg = df_cargo[df_cargo[col_num].str.startswith(dig)] if col_num else pd.DataFrame()
    if not m_leg.empty:
        cand = m_leg.iloc[0]
        e_legenda = True

# --- MOSTRAR A TELA E TECLADO LADO A LADO ---
col_visor, col_teclado = st.columns([1.2, 1])

with col_visor:
    st.subheader(f"SEU VOTO VAI PARA:")
    st.header(f"👉 {etapa['cargo']}")
    
    # Exibe caixas dos dígitos
    caixas = " ".join([f"[{dig[i]}]" if i < len(dig) else "[  ]" for i in range(etapa["digitos"])])
    st.markdown(f"### Número: `{caixas}`")
    st.markdown("---")
    
    # Informações do Candidato / Legenda / Nulo
    if len(dig) == etapa["digitos"] or (len(dig) == 2 and e_legenda):
        if cand is not None:
            if e_legenda:
                st.info(f"🔵 **VOTO NA LEGENDA**\n\n**Partido:** {cand.get(col_partido, 'N/A')}")
            else:
                st.success(f"🟢 **CANDIDATO:** {cand.get(col_nome, 'N/A')}\n\n**Partido:** {cand.get(col_partido, 'N/A')}")
        else:
            st.error("🔴 **VOTO NULO**")

with col_teclado:
    st.write("**Teclado da Urna:**")
    
    def press(n):
        if len(st.session_state.digitos) < etapa["digitos"]:
            st.session_state.digitos += str(n)

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("1", use_container_width=True): press(1); st.rerun()
        if st.button("4", use_container_width=True): press(4); st.rerun()
        if st.button("7", use_container_width=True): press(7); st.rerun()
    with b2:
        if st.button("2", use_container_width=True): press(2); st.rerun()
        if st.button("5", use_container_width=True): press(5); st.rerun()
        if st.button("8", use_container_width=True): press(8); st.rerun()
        if st.button("0", use_container_width=True): press(0); st.rerun()
    with t3 if 't3' in locals() else b3:
        if st.button("3", use_container_width=True): press(3); st.rerun()
        if st.button("6", use_container_width=True): press(6); st.rerun()
        if st.button("9", use_container_width=True): press(9); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    cb1, cb2, cb3 = st.columns(3)
    with cb1:
        if st.button("⚪ BRANCO", use_container_width=True):
            st.session_state.votos[etapa["cargo"]] = "BRANCO"
            st.session_state.etapa += 1
            st.session_state.digitos = ""
            st.rerun()
    with cb2:
        if st.button("🟠 CORRIGE", use_container_width=True):
            st.session_state.digitos = ""
            st.rerun()
    with cb3:
        if st.button("🟢 CONFIRMA", use_container_width=True):
            st.session_state.votos[etapa["cargo"]] = st.session_state.digitos if st.session_state.digitos else "NULO"
            st.session_state.etapa += 1
            st.session_state.digitos = ""
            st.rerun()