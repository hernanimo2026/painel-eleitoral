import streamlit as st
import streamlit.components.v1 as components
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

# Ajustar margens nativas
st.markdown("""
<style>
    .main .block-container {
        max-width: 380px !important;
        padding: 8px !important;
        margin: 0 auto !important;
    }
    .visor-box {
        background-color: #dbe4db;
        border: 2px solid #222;
        border-radius: 6px;
        padding: 12px;
        min-height: 160px;
        color: #000;
        font-family: Arial, sans-serif;
        box-shadow: inset 0 0 6px rgba(0,0,0,0.15);
        margin-bottom: 12px;
    }
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
        margin-right: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Topo
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

# PROCESSAMENTO DE CLIQUES DO COMPONENTE HTML
if "last_action" in st.query_params:
    act = st.query_params["last_action"]
    st.query_params.clear()
    
    if act in [str(i) for i in range(10)]:
        if len(st.session_state.digitos) < etapa["digitos"]:
            st.session_state.digitos += act
    elif act == "BRANCO":
        st.session_state.votos[etapa["cargo"]] = "BRANCO"
        st.session_state.etapa += 1
        st.session_state.digitos = ""
    elif act == "CORRIGE":
        st.session_state.digitos = ""
    elif act == "CONFIRMA":
        st.session_state.votos[etapa["cargo"]] = st.session_state.digitos if st.session_state.digitos else "NULO"
        st.session_state.etapa += 1
        st.session_state.digitos = ""
    st.rerun()

# TECLADO HTML PERFEITO E RESPONSIVO
html_teclado = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: Arial, sans-serif; }
  .keypad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; width: 100%; padding: 4px; }
  button {
    background-color: #1a1a1a; color: white; border: none; border-radius: 5px;
    font-size: 18px; font-weight: bold; height: 44px; cursor: pointer;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3); width: 100%;
  }
  button:active { background-color: #444; }
  .btn-empty { background: transparent; box-shadow: none; cursor: default; }
  .actions { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; width: 100%; padding: 4px; margin-top: 6px; }
  .btn-branco { background-color: #ffffff; color: #000000; font-size: 10px; border: 1px solid #ccc; height: 44px; }
  .btn-corrige { background-color: #f37021; color: #000000; font-size: 10px; height: 44px; }
  .btn-confirma { background-color: #008000; color: #ffffff; font-size: 10px; height: 50px; }
</style>
</head>
<body>
  <div class="keypad">
    <button onclick="send('1')">1</button>
    <button onclick="send('2')">2</button>
    <button onclick="send('3')">3</button>
    <button onclick="send('4')">4</button>
    <button onclick="send('5')">5</button>
    <button onclick="send('6')">6</button>
    <button onclick="send('7')">7</button>
    <button onclick="send('8')">8</button>
    <button onclick="send('9')">9</button>
    <div class="btn-empty"></div>
    <button onclick="send('0')">0</button>
    <div class="btn-empty"></div>
  </div>
  <div class="actions">
    <button class="btn-branco" onclick="send('BRANCO')">BRANCO</button>
    <button class="btn-corrige" onclick="send('CORRIGE')">CORRIGE</button>
    <button class="btn-confirma" onclick="send('CONFIRMA')">CONFIRMA</button>
  </div>
  <script>
    function send(val) {
      window.parent.postMessage({
        type: 'streamlit:setQueryParams',
        queryParams: { last_action: val }
      }, '*');
    }
  </script>
</body>
</html>
"""

components.html(html_teclado, height=270)