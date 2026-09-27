import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Urna Eletrônica 2026", layout="centered")

# --- ESTILO E DESIGN FIEL À URNA ELETRÔNICA DO TSE ---
st.markdown("""
<style>
/* Otimização da tela */
.block-container { padding-top: 0.5rem; max-width: 800px; }

/* Corpo da Urna */
.corpo-urna {
    background-color: #dbdbdb;
    border: 3px solid #888;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.3);
}

/* Visor LCD da Urna */
.visor-urna {
    background-color: #e2ece0;
    border: 3px solid #222;
    border-radius: 6px;
    padding: 20px;
    min-height: 380px;
    font-family: Arial, sans-serif;
    color: #111;
    position: relative;
}

/* Título e Caixas dos Números */
.titulo-cargo { font-size: 18px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
.nome-cargo { font-size: 26px; font-weight: bold; margin-bottom: 20px; }

.caixa-numero {
    display: inline-block;
    width: 42px;
    height: 52px;
    border: 2px solid #000;
    font-size: 32px;
    font-weight: bold;
    text-align: center;
    line-height: 48px;
    margin-right: 6px;
    background-color: #fff;
}

/* Painel de Teclas */
.painel-teclas {
    background-color: #222;
    border-radius: 8px;
    padding: 15px;
}

/* Botões do Teclado */
.stButton > button {
    border-radius: 6px !important;
    font-size: 20px !important;
    font-weight: bold !important;
    height: 55px !important;
}

/* Cores específicas dos botões da urna */
div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #333; color: white; }
</style>
""", unsafe_allow_html=True)

# --- CARREGAMENTO DA PLANILHA ---
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
    st.error("⚠️ Nenhuma base de dados encontrada no servidor.")
    st.stop()

# Mapeamento de colunas da planilha do TSE
col_num = next((c for c in ['NR_CANDIDATO', 'NR_CAND', 'NUMERO'] if c in df_candidatos.columns), None)
col_nome = next((c for c in ['NM_URNA_CANDIDATO', 'NM_CANDIDATO'] if c in df_candidatos.columns), None)
col_partido = next((c for c in ['SG_PARTIDO', 'PARTIDO'] if c in df_candidatos.columns), None)
col_uf = next((c for c in ['SG_UF', 'UF'] if c in df_candidatos.columns), None)
col_cargo = next((c for c in ['DS_CARGO', 'CARGO'] if c in df_candidatos.columns), None)

# --- ETAPAS DA ELEIÇÃO ---
ETAPAS = [
    {"cargo": "DEPUTADO FEDERAL", "digitos": 4, "legenda": True, "filtro": ["DEPUTADO FEDERAL"]},
    {"cargo": "DEPUTADO ESTADUAL", "digitos": 5, "legenda": True, "filtro": ["DEPUTADO ESTADUAL", "DEPUTADO DISTRITAL"]},
    {"cargo": "SENADOR", "digitos": 3, "legenda": False, "filtro": ["SENADOR"]},
    {"cargo": "GOVERNADOR", "digitos": 2, "legenda": False, "filtro": ["GOVERNADOR"]},
    {"cargo": "PRESIDENTE", "digitos": 2, "legenda": False, "filtro": ["PRESIDENTE"]}
]

# Estado da sessão
if "etapa" not in st.session_state:
    st.session_state.etapa = 0
if "digitos" not in st.session_state:
    st.session_state.digitos = ""
if "votos" not in st.session_state:
    st.session_state.votos = {}
if "uf_selecionada" not in st.session_state:
    st.session_state.uf_selecionada = "MT"

# Seleção de Estado (UF) no topo
ufs_br = sorted(df_candidatos[col_uf].dropna().unique().tolist()) if col_uf else ['SP', 'MT', 'RJ']
col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.title("🗳️ Simulação de Urna Eletrônica")
with col_top2:
    st.session_state.uf_selecionada = st.selectbox("UF de Votação:", ufs_br, index=ufs_br.index(st.session_state.uf_selecionada) if st.session_state.uf_selecionada in ufs_br else 0)

# FIM DA VOTAÇÃO
if st.session_state.etapa >= len(ETAPAS):
    st.balloons()
    st.markdown("""
        <div class='visor-urna' style='display:flex; align-items:center; justify-content:center; height:350px;'>
            <h1 style='font-size: 90px; letter-spacing: 10px; color:#000;'>FIM</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 REINICIAR VOTAÇÃO", use_container_width=True):
        st.session_state.etapa = 0
        st.session_state.digitos = ""
        st.session_state.votos = {}
        st.rerun()
    st.stop()

etapa_atual = ETAPAS[st.session_state.etapa]

# --- BUSCA DE CANDIDATOS / LEGENDA ---
df_uf = df_candidatos[df_candidatos[col_uf].isin([st.session_state.uf_selecionada, 'BR'])] if col_uf else df_candidatos
df_cargo = df_uf[df_uf[col_cargo].isin(etapa_atual["filtro"])] if col_cargo else df_uf

digitos = st.session_state.digitos
candidato = None
e_legenda = False

if len(digitos) == etapa_atual["digitos"]:
    match = df_cargo[df_cargo[col_num] == digitos] if col_num else pd.DataFrame()
    if not match.empty:
        candidato = match.iloc[0]
elif len(digitos) == 2 and etapa_atual["legenda"]:
    match_leg = df_cargo[df_cargo[col_num].str.startswith(digitos)] if col_num else pd.DataFrame()
    if not match_leg.empty:
        candidato = match_leg.iloc[0]
        e_legenda = True

# --- INTERFACE VISUAL DA URNA (VISOR) ---
col_visor, col_teclado = st.columns([1.2, 1])

with col_visor:
    caixas_num = "".join([f"<div class='caixa-numero'>{digitos[i] if i < len(digitos) else ''}</div>" for i in range(etapa_atual["digitos"])])
    
    info_html = ""
    if len(digitos) == etapa_atual["digitos"] or (len(digitos) == 2 and e_legenda):
        if candidato is not None:
            if e_legenda:
                info_html = f"""
                <hr style='border:1px solid #aaa;'>
                <p style='color:#003399; font-weight:bold; font-size:18px;'>VOTO NA LEGENDA</p>
                <p><b>Partido:</b> {candidato.get(col_partido, 'N/A')}</p>
                """
            else:
                info_html = f"""
                <hr style='border:1px solid #aaa;'>
                <p><b>Nome:</b> {candidato.get(col_nome, 'N/A')}</p>
                <p><b>Partido:</b> {candidato.get(col_partido, 'N/A')}</p>
                """
        else:
            info_html = "<hr style='border:1px solid #aaa;'><h2 style='color:red;'>VOTO NULO</h2>"

    st.markdown(f"""
    <div class='visor-urna'>
        <div class='titulo-cargo'>SEU VOTO VAI PARA</div>
        <div class='nome-cargo'>{etapa_atual['cargo']}</div>
        <div style='margin-top:10px;'>Número: {caixas_num}</div>
        {info_html}
    </div>
    """, unsafe_allow_html=True)

# --- INTERFACE VISUAL DO TECLADO ---
with col_teclado:
    st.markdown("<div class='painel-teclas'>", unsafe_allow_html=True)
    
    def pressionar(num):
        if len(st.session_state.digitos) < etapa_atual["digitos"]:
            st.session_state.digitos += str(num)

    t1, t2, t3 = st.columns(3)
    with t1:
        if st.button("1"): pressionar(1); st.rerun()
        if st.button("4"): pressionar(4); st.rerun()
        if st.button("7"): pressionar(7); st.rerun()
    with t2:
        if st.button("2"): pressionar(2); st.rerun()
        if st.button("5"): pressionar(5); st.rerun()
        if st.button("8"): pressionar(8); st.rerun()
        if st.button("0"): pressionar(0); st.rerun()
    with t3:
        if st.button("3"): pressionar(3); st.rerun()
        if st.button("6"): pressionar(6); st.rerun()
        if st.button("9"): pressionar(9); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    b_branco, b_corrige, b_confirma = st.columns(3)
    
    with b_branco:
        if st.button("BRANCO"):
            st.session_state.votos[etapa_atual["cargo"]] = "BRANCO"
            st.session_state.etapa += 1
            st.session_state.digitos = ""
            st.rerun()
            
    with b_corrige:
        if st.button("CORRIGE"):
            st.session_state.digitos = ""
            st.rerun()
            
    with b_confirma:
        if st.button("CONFIRMA"):
            st.session_state.votos[etapa_atual["cargo"]] = st.session_state.digitos if st.session_state.digitos else "NULO"
            st.session_state.etapa += 1
            st.session_state.digitos = ""
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)