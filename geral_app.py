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

# ETAPAS DA VOTAÇÃO
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

# --- CSS COM TECLADO COMPACTO ---
st.markdown("""
<style>
    /* Limita o container principal para centralizar como uma urna */
    .main .block-container {
        max-width: 360px !important;
        padding-left: 8px !important;
        padding-right: 8px !important;
        margin: 0 auto !important;
    }

    /* Força colunas a manterem layout horizontal compacto */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        justify-content: center !important;
    }

    div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }

    /* Visor estilo Urna */
    .visor-box {
        background-color: #dbe4db;
        border: 2px solid #222;
        border-radius: 6px;
        padding: 10px;
        min-height: 180px;
        color: #000;
        font-family: Arial, sans-serif;
        box-shadow: inset 0 0 6px rgba(0,0,0,0.15);
        margin-bottom: 10px;
    }

    /* Quadrados dos dígitos */
    .digit-square {
        display: inline-block;
        width: 26px;
        height: 32px;
        border: 2px solid #000;
        background-color: #fff;
        color: #000;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        line-height: 28px;
        margin-right: 2px;
    }

    /* Botões numéricos menores e compactos */
    div[data-testid="stButton"] button {
        width: 100% !important;
        height: 40px !important;
        border-radius: 5px !important;
        font-weight: bold !important;
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        font-size: 16px !important;
        border: 1px solid #000 !important;
        padding: 0px !important;
    }

    /* Botões de Ação (Ajustados no mesmo padrão compacto) */
    div[data-testid="stElementContainer"]:has(button[key="btn_branco"]) button {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-size: 9px !important;
        height: 42px !important;
    }

    div[data-testid="stElementContainer"]:has(button[key="btn_corrige"]) button {
        background-color: #f37021 !important;
        color: #000000 !important;
        font-size: 9px !important;
        height: 42px !important;
    }

    div[data-testid="stElementContainer"]:has(button[key="btn_confirma"]) button {
        background-color: #008000 !important;
        color: #ffffff !important;
        font-size: 9px !important;
        height: 48px !important;
    }
</style>
""", unsafe_allow_html=True)

# Topo da aplicação
c_tit, c_uf = st.columns([2.5, 1])
with c_tit:
    st.markdown("### 🗳️ Urna Eletrônica")
with c_uf:
    ufs = sorted(df_candidatos[col_uf].dropna().unique().tolist()) if col_uf else ['MT', 'SP', 'RJ']
    st.session_state.uf_sel = st.selectbox("UF:", ufs, index=ufs.index(st.session_state.uf_sel) if st.session_state.uf_sel in ufs else 0)

# TELA DE FIM
if st.session_state.etapa >= len(ETAPAS):
    st.balloons()
    st.markdown("""
    <div class='visor-box' style='text-align: center; padding-top: 30px;'>
        <h1 style='font-size: 50px; margin: 0; color: #000;'>FIM</h1>
        <p style='font-size: 14px; color: #333;'>VOTAÇÃO CONCLUÍDA</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Reiniciar Votação", use_container_width=True):
        st.session_state.etapa = 0
        st.session_state.digitos = ""
        st.session_state.votos = {}
        st.rerun()
    st.stop()

etapa = ETAPAS[st.session_state.etapa]

# Filtragem de candidatos
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
boxes_html = "".join([f"<div class='digit-square'>{dig[i] if i < len(dig) else ''}</div>" for i in range(etapa["digitos"])])

cand_info = ""
if len(dig) == etapa["digitos"] or (len(dig) == 2 and e_legenda):
    if cand is not None:
        if e_legenda:
            cand_info = f"<div style='margin-top: 8px; border-top: 1px solid #777; padding-top: 4px;'><b>VOTO NA LEGENDA</b><br><b>Partido:</b> {cand.get(col_partido, 'N/A')}</div>"
        else:
            cand_info = f"<div style='margin-top: 8px; border-top: 1px solid #777; padding-top: 4px;'><b>Nome:</b> {cand.get(col_nome, 'N/A')}<br><b>Partido:</b> {cand.get(col_partido, 'N/A')}</div>"
    else:
        cand_info = "<div style='margin-top: 8px; border-top: 1px solid #777; padding-top: 4px; color: red;'><b>VOTO NULO</b></div>"

st.markdown(f"""
<div class='visor-box'>
    <p style='font-size: 11px; margin-bottom: 2px; color: #444;'>SEU VOTO VAI PARA</p>
    <h3 style='font-size: 16px; margin-top: 0; color: #000;'>{etapa['cargo']}</h3>
    <div style='margin-top: 6px; margin-bottom: 6px;'>
        <span style='font-size: 12px; margin-right: 4px;'>Número:</span>{boxes_html}
    </div>
    {cand_info}
</div>
""", unsafe_allow_html=True)

# TECLADO NUMÉRICO COMPACTO
def press(n):
    if len(st.session_state.digitos) < etapa["digitos"]:
        st.session_state.digitos += str(n)

# Linhas numéricas (1 a 9)
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("1", key="b1", use_container_width=True): press(1); st.rerun()
with c2:
    if st.button("2", key="b2", use_container_width=True): press(2); st.rerun()
with c3:
    if st.button("3", key="b3", use_container_width=True): press(3); st.rerun()

c4, c5, c6 = st.columns(3)
with c4:
    if st.button("4", key="b4", use_container_width=True): press(4); st.rerun()
with c5:
    if st.button("5", key="b5", use_container_width=True): press(5); st.rerun()
with c6:
    if st.button("6", key="b6", use_container_width=True): press(6); st.rerun()

c7, c8, c9 = st.columns(3)
with c7:
    if st.button("7", key="b7", use_container_width=True): press(7); st.rerun()
with c8:
    if st.button("8", key="b8", use_container_width=True): press(8); st.rerun()
with c9:
    if st.button("9", key="b9", use_container_width=True): press(9); st.rerun()

# Linha do botão 0
_, c0, _ = st.columns(3)
with c0:
    if st.button("0", key="b0", use_container_width=True): press(0); st.rerun()

st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)

# BOTÕES DE AÇÃO (BRANCO, CORRIGE, CONFIRMA)
act1, act2, act3 = st.columns(3)

with act1:
    if st.button("BRANCO", key="btn_branco", use_container_width=True):
        st.session_state.votos[etapa["cargo"]] = "BRANCO"
        st.session_state.etapa += 1
        st.session_state.digitos = ""
        st.rerun()

with act2:
    if st.button("CORRIGE", key="btn_corrige", use_container_width=True):
        st.session_state.digitos = ""
        st.rerun()

with act3:
    if st.button("CONFIRMA", key="btn_confirma", use_container_width=True):
        st.session_state.votos[etapa["cargo"]] = st.session_state.digitos if st.session_state.digitos else "NULO"
        st.session_state.etapa += 1
        st.session_state.digitos = ""
        st.rerun()