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
    st.error("⚠️ Nenhuma base de dados (.csv) encontrada no repositório.")
    st.stop()

# Identificação das Colunas
col_num = next((c for c in ['NR_CANDIDATO', 'NR_CAND', 'NUMERO'] if c in df_candidatos.columns), None)
col_nome = next((c for c in ['NM_URNA_CANDIDATO', 'NM_CANDIDATO'] if c in df_candidatos.columns), None)
col_partido = next((c for c in ['SG_PARTIDO', 'PARTIDO'] if c in df_candidatos.columns), None)
col_uf = next((c for c in ['SG_UF', 'UF'] if c in df_candidatos.columns), None)
col_cargo = next((c for c in ['DS_CARGO', 'CARGO'] if c in df_candidatos.columns), None)

# --- ETAPAS DA VOTAÇÃO OFICIAL 2026 (6 VOTOS COM 2 SENADORES) ---
ETAPAS = [
    {"cargo": "DEPUTADO FEDERAL", "digitos": 4, "legenda": True, "filtro": ["DEPUTADO FEDERAL"]},
    {"cargo": "DEPUTADO ESTADUAL", "digitos": 5, "legenda": True, "filtro": ["DEPUTADO ESTADUAL", "DEPUTADO DISTRITAL"]},
    {"cargo": "SENADOR (1ª VAGA)", "digitos": 3, "legenda": False, "filtro": ["SENADOR"]},
    {"cargo": "SENADOR (2ª VAGA)", "digitos": 3, "legenda": False, "filtro": ["SENADOR"]},
    {"cargo": "GOVERNADOR", "digitos": 2, "legenda": False, "filtro": ["GOVERNADOR"]},
    {"cargo": "PRESIDENTE", "digitos": 2, "legenda": False, "filtro": ["PRESIDENTE"]}
]

if "etapa" not in st.session_state:
    st.session_state.etapa = 0
if "digitos" not in st.session_state:
    st.session_state.digitos = ""
if "votos" not in st.session_state:
    st.session_state.votos = {}
if "uf_sel" not in st.session_state:
    st.session_state.uf_sel = "MT"

# ESTILIZAÇÃO CSS
st.markdown("""
<style>
    /* Força botões do teclado lado a lado no telemóvel */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
    }

    div[data-testid="column"] {
        width: 100% !important;
        min-width: 0px !important;
        flex: 1 1 0% !important;
    }

    /* Visor */
    .visor-container {
        background-color: #dbe4db;
        border: 2px solid #222;
        border-radius: 8px;
        padding: 15px;
        min-height: 260px;
        color: #111;
        font-family: Arial, sans-serif;
        margin-bottom: 15px;
    }

    /* Quadrados dos dígitos */
    .digit-box {
        display: inline-block;
        width: 35px;
        height: 45px;
        border: 2px solid #000;
        background-color: #fff;
        color: #000;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        line-height: 40px;
        margin-right: 3px;
    }

    .info-cand {
        margin-top: 12px;
        padding-top: 8px;
        border-top: 1px solid #888;
        font-size: 16px;
    }

    /* Teclas do Teclado */
    div[data-testid="stColumn"] button {
        background-color: #111 !important;
        color: #fff !important;
        font-size: 20px !important;
        font-weight: bold !important;
        height: 50px !important;
        border-radius: 6px !important;
        border: 1px solid #000 !important;
        padding: 2px !important;
    }

    /* Tecla BRANCO */
    div[data-testid="stColumn"]:has(button:contains("BRANCO")) button {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-size: 12px !important;
    }

    /* Tecla CORRIGE */
    div[data-testid="stColumn"]:has(button:contains("CORRIGE")) button {
        background-color: #f37021 !important;
        color: #000000 !important;
        font-size: 12px !important;
    }

    /* Tecla CONFIRMA */
    div[data-testid="stColumn"]:has(button:contains("CONFIRMA")) button {
        background-color: #008000 !important;
        color: #ffffff !important;
        font-size: 11px !important;
        height: 58px !important;
    }
</style>
""", unsafe_allow_html=True)

# Topo
c_tit, c_uf = st.columns([2.5, 1])
with c_tit:
    st.title("🗳️ Urna Eletrônica 2026")
with c_uf:
    ufs = sorted(df_candidatos[col_uf].dropna().unique().tolist()) if col_uf else ['MT', 'SP', 'RJ']
    st.session_state.uf_sel = st.selectbox("UF:", ufs, index=ufs.index(st.session_state.uf_sel) if st.session_state.uf_sel in ufs else 0)

# FIM DA VOTAÇÃO
if st.session_state.etapa >= len(ETAPAS):
    st.balloons()
    st.markdown("""
    <div class='visor-container' style='text-align: center; padding-top: 60px;'>
        <h1 style='font-size: 80px; margin: 0; color: #000;'>FIM</h1>
        <p style='font-size: 20px; color: #333;'>VOTAÇÃO CONCLUÍDA</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reiniciar Votação", use_container_width=True):
        st.session_state.etapa = 0
        st.session_state.digitos = ""
        st.session_state.votos = {}
        st.rerun()
    st.stop()

etapa = ETAPAS[st.session_state.etapa]

# Filtrar dados por UF e Cargo
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

# VISOR
boxes_html = "".join([f"<div class='digit-box'>{dig[i] if i < len(dig) else ''}</div>" for i in range(etapa["digitos"])])

cand_info = ""
if len(dig) == etapa["digitos"] or (len(dig) == 2 and e_legenda):
    if cand is not None:
        if e_legenda:
            cand_info = f"<div class='info-cand'><b>VOTO NA LEGENDA</b><br><b>Partido:</b> {cand.get(col_partido, 'N/A')}</div>"
        else:
            cand_info = f"<div class='info-cand'><b>Nome:</b> {cand.get(col_nome, 'N/A')}<br><b>Partido:</b> {cand.get(col_partido, 'N/A')}</div>"
    else:
        cand_info = "<div class='info-cand' style='color: red;'><b>VOTO NULO</b></div>"

st.markdown(f"""
<div class='visor-container'>
    <p style='font-size: 13px; margin-bottom: 2px; color: #444;'>SEU VOTO VAI PARA</p>
    <h3 style='font-size: 20px; margin-top: 0; color: #000;'>{etapa['cargo']}</h3>
    <div style='margin-top: 15px; margin-bottom: 15px;'>
        <span style='font-size: 15px; margin-right: 5px;'>Número:</span>{boxes_html}
    </div>
    {cand_info}
</div>
""", unsafe_allow_html=True)

# TECLADO
def press(n):
    if len(st.session_state.digitos) < etapa["digitos"]:
        st.session_state.digitos += str(n)

k1, k2, k3 = st.columns(3)
with k1:
    if st.button("1", key="btn_1", use_container_width=True): press(1); st.rerun()
    if st.button("4", key="btn_4", use_container_width=True): press(4); st.rerun()
    if st.button("7", key="btn_7", use_container_width=True): press(7); st.rerun()
with k2:
    if st.button("2", key="btn_2", use_container_width=True): press(2); st.rerun()
    if st.button("5", key="btn_5", use_container_width=True): press(5); st.rerun()
    if st.button("8", key="btn_8", use_container_width=True): press(8); st.rerun()
    if st.button("0", key="btn_0", use_container_width=True): press(0); st.rerun()
with k3:
    if st.button("3", key="btn_3", use_container_width=True): press(3); st.rerun()
    if st.button("6", key="btn_6", use_container_width=True): press(6); st.rerun()
    if st.button("9", key="btn_9", use_container_width=True): press(9); st.rerun()

st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

# BOTOES DE AÇÃO
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("BRANCO", key="btn_branco", use_container_width=True):
        st.session_state.votos[etapa["cargo"]] = "BRANCO"
        st.session_state.etapa += 1
        st.session_state.digitos = ""
        st.rerun()
with b2:
    if st.button("CORRIGE", key="btn_corrige", use_container_width=True):
        st.session_state.digitos = ""
        st.rerun()
with b3:
    if st.button("CONFIRMA", key="btn_confirma", use_container_width=True):
        st.session_state.votos[etapa["cargo"]] = st.session_state.digitos if st.session_state.digitos else "NULO"
        st.session_state.etapa += 1
        st.session_state.digitos = ""
        st.rerun()