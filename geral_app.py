import streamlit as st
import pandas as pd
import os

# 1. Configuração Responsiva para Telemóvel e PC
st.set_page_config(page_title="Urna Eletrônica 2026", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Otimização da tela da urna para telemóveis */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 500px !important;
    }
    
    .urna-tela {
        background-color: #dbe3db;
        border: 3px solid #1a1a1a;
        border-radius: 8px;
        padding: 12px;
        min-height: 220px;
        box-shadow: inset 0 0 8px rgba(0,0,0,0.15);
        color: #000;
        font-family: Arial, sans-serif;
    }

    .caixa-num {
        display: inline-block;
        width: 30px;
        height: 38px;
        border: 2px solid #000;
        font-size: 22px;
        font-weight: bold;
        text-align: center;
        line-height: 34px;
        margin-right: 2px;
        background-color: #fff;
        color: #000;
    }

    /* Ajuste dos botões no teclado tátil */
    div.stButton > button {
        width: 100% !important;
        height: 48px !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border-radius: 6px !important;
        margin-bottom: 2px !important;
    }

    .btn-num button { background-color: #222 !important; color: #fff !important; }
    .btn-branco button { background-color: #ffffff !important; color: #000 !important; font-size: 12px !important; }
    .btn-corrige button { background-color: #e65100 !important; color: #fff !important; font-size: 12px !important; }
    .btn-confirma button { background-color: #1b5e20 !important; color: #fff !important; font-size: 13px !important; height: 54px !important; }
    </style>
""", unsafe_allow_html=True)

# 2. Carregamento ultrarrápido da planilha na nuvem
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_candidatos():
    diretorio = os.path.dirname(os.path.abspath(__file__))
    
    # Procura todas as variações de nomes do CSV na pasta
    ficheiros = [f for f in os.listdir(diretorio) if f.lower().endswith('.csv')]
    caminho = None
    for f in ficheiros:
        if 'cand' in f.lower():
            caminho = os.path.join(diretorio, f)
            break

    if not caminho:
        caminho = os.path.join(diretorio, "Consulta_cand_2026_BRASIL.csv")

    if not os.path.exists(caminho):
        return pd.DataFrame()

    for enc in ['latin1', 'utf-8', 'iso-8859-1']:
        try:
            df = pd.read_csv(caminho, sep=';', encoding=enc, dtype=str, on_bad_lines='skip')
            if len(df.columns) > 1:
                df.columns = df.columns.str.strip().str.upper()
                for col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.upper()
                return df
        except Exception:
            continue
    return pd.DataFrame()

df_candidatos = carregar_candidatos()

col_numero = next((c for c in ['NR_CANDIDATO', 'NR_CAND', 'NUMERO'] if c in df_candidatos.columns), None)
col_cargo = next((c for c in ['DS_CARGO', 'CARGO'] if c in df_candidatos.columns), None)
col_uf = next((c for c in ['SG_UF', 'UF'] if c in df_candidatos.columns), None)
col_nome = next((c for c in ['NM_URNA_CANDIDATO', 'NM_CANDIDATO'] if c in df_candidatos.columns), None)
col_partido = next((c for c in ['SG_PARTIDO', 'PARTIDO'] if c in df_candidatos.columns), None)

ufs_disponiveis = sorted(df_candidatos[col_uf].unique().tolist()) if (col_uf and not df_candidatos.empty) else ["MT", "RJ", "SP", "PE", "GO", "DF", "MG"]

ETAPAS = [
    {"cargo": "DEPUTADO FEDERAL", "digitos": 4, "filtro_cargo": ["DEPUTADO FEDERAL"], "permite_legenda": True},
    {"cargo": "DEPUTADO ESTADUAL", "digitos": 5, "filtro_cargo": ["DEPUTADO ESTADUAL", "DEPUTADO DISTRITAL"], "permite_legenda": True},
    {"cargo": "1º SENADOR", "digitos": 3, "filtro_cargo": ["SENADOR"], "permite_legenda": False, "chave": "senador1"},
    {"cargo": "2º SENADOR", "digitos": 3, "filtro_cargo": ["SENADOR"], "permite_legenda": False, "chave": "senador2"},
    {"cargo": "GOVERNADOR", "digitos": 2, "filtro_cargo": ["GOVERNADOR"], "permite_legenda": False},
    {"cargo": "PRESIDENTE", "digitos": 2, "filtro_cargo": ["PRESIDENTE", "PRESIDENTE DA REPÚBLICA"], "permite_legenda": False}
]

if 'etapa_index' not in st.session_state:
    st.session_state.etapa_index = 0
if 'digitos' not in st.session_state:
    st.session_state.digitos = ""
if 'tipo_voto' not in st.session_state:
    st.session_state.tipo_voto = "NOMINATIVO"
if 'voto_senador1' not in st.session_state:
    st.session_state.voto_senador1 = ""
if 'uf_selecionada' not in st.session_state:
    st.session_state.uf_selecionada = "MT" if "MT" in ufs_disponiveis else ufs_disponiveis[0]

etapa_atual = ETAPAS[st.session_state.etapa_index] if st.session_state.etapa_index < len(ETAPAS) else None

def pressionar_numero(num):
    if etapa_atual and len(st.session_state.digitos) < etapa_atual["digitos"] and st.session_state.tipo_voto == "NOMINATIVO":
        st.session_state.digitos += str(num)

def pressionar_branco():
    st.session_state.digitos = ""
    st.session_state.tipo_voto = "BRANCO"

def pressionar_corrige():
    st.session_state.digitos = ""
    st.session_state.tipo_voto = "NOMINATIVO"

def pressionar_confirma():
    if not etapa_atual:
        return
    qtd_dig = len(st.session_state.digitos)
    if st.session_state.tipo_voto == "BRANCO" or qtd_dig == etapa_atual["digitos"] or (etapa_atual["permite_legenda"] and qtd_dig == 2):
        if etapa_atual.get("chave") == "senador1":
            st.session_state.voto_senador1 = st.session_state.digitos if st.session_state.tipo_voto == "NOMINATIVO" else "BRANCO"

        st.session_state.etapa_index += 1
        st.session_state.digitos = ""
        st.session_state.tipo_voto = "NOMINATIVO"

def reiniciar():
    st.session_state.etapa_index = 0
    st.session_state.digitos = ""
    st.session_state.tipo_voto = "NOMINATIVO"
    st.session_state.voto_senador1 = ""

# --- INTERFACE ---
st.markdown("<h4 style='text-align: center; margin: 0;'>Urna Eletrônica 2026</h4>", unsafe_allow_html=True)

idx_uf = ufs_disponiveis.index(st.session_state.uf_selecionada) if st.session_state.uf_selecionada in ufs_disponiveis else 0
st.session_state.uf_selecionada = st.selectbox("UF:", ufs_disponiveis, index=idx_uf)

if st.session_state.etapa_index >= len(ETAPAS):
    st.markdown('''
        <div class="urna-tela" style="text-align: center; padding-top: 40px;">
            <h1 style="font-size: 60px; margin: 0;">FIM</h1>
            <p style="font-size: 20px; color: #1b5e20; font-weight: bold;">VOTO REGISTRADO</p>
        </div>
    ''', unsafe_allow_html=True)
    st.write("")
    if st.button("NOVA VOTAÇÃO"):
        reiniciar()
        st.rerun()
else:
    candidato_encontrado = None
    legenda_encontrada = None
    voto_duplicado = False
    qtd_digitos = etapa_atual["digitos"]
    digitos_atuais = st.session_state.digitos

    if etapa_atual.get("chave") == "senador2" and digitos_atuais != "" and digitos_atuais == st.session_state.voto_senador1:
        voto_duplicado = True

    if not df_candidatos.empty and col_numero:
        df_f = df_candidatos.copy()
        if col_cargo:
            df_f = df_f[df_f[col_cargo].isin(etapa_atual["filtro_cargo"])]
        if col_uf and etapa_atual["cargo"] != "PRESIDENTE":
            df_f = df_f[df_f[col_uf].isin([st.session_state.uf_selecionada, "BR"])]

        if len(digitos_atuais) == qtd_digitos:
            m = df_f[df_f[col_numero] == digitos_atuais]
            if not m.empty:
                candidato_encontrado = m.iloc[0]
        elif etapa_atual["permite_legenda"] and len(digitos_atuais) == 2:
            m_leg = df_f[df_f[col_numero].str[:2] == digitos_atuais]
            if not m_leg.empty:
                legenda_encontrada = m_leg.iloc[0]

    boxes_html = "".join([f'<span class="caixa-num">{digitos_atuais[i] if i < len(digitos_atuais) else "&nbsp;"}</span>' for i in range(qtd_digitos)])

    if st.session_state.tipo_voto == "BRANCO":
        info_html = "<h3 style='text-align:center; margin-top:15px;'>VOTO EM BRANCO</h3>"
    else:
        if voto_duplicado:
            det = "<p style='color:#b71c1c; margin-top:5px;'><b>SENADOR JÁ VOTADO!</b></p>"
        elif candidato_encontrado is not None:
            n = candidato_encontrado.get(col_nome, '')
            p = candidato_encontrado.get(col_partido, '')
            det = f"<p style='margin-top:5px; font-size:14px;'><b>Nome:</b> {n}<br><b>Partido:</b> {p}</p>"
        elif legenda_encontrada is not None:
            p = legenda_encontrada.get(col_partido, '')
            det = f"<p style='margin-top:5px; font-size:14px; color:#0d47a1;'><b>VOTO NA LEGENDA</b><br><b>Partido:</b> {p}</p>"
        elif len(digitos_atuais) == qtd_digitos or (not etapa_atual["permite_legenda"] and len(digitos_atuais) == 2):
            det = "<p style='color:#b71c1c; margin-top:5px;'><b>VOTO NULO</b></p>"
        else:
            det = ""
        info_html = f'<div style="margin: 5px 0;">{boxes_html}</div>' + det

    st.markdown(f'''
        <div class="urna-tela">
            <p style="font-size: 11px; margin: 0; font-weight: bold; color: #555;">SEU VOTO VAI PARA</p>
            <h3 style="margin: 0; font-size: 18px;">{etapa_atual["cargo"]}</h3>
            {info_html}
        </div>
    ''', unsafe_allow_html=True)

    # Teclado Numérico Adaptado para Touch Screen
    st.write("")
    for r in range(3):
        cols = st.columns(3)
        for c in range(3):
            val = r * 3 + c + 1
            with cols[c]:
                st.markdown('<div class="btn-num">', unsafe_allow_html=True)
                if st.button(str(val), key=f"btn_{val}"):
                    pressionar_numero(val)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    _, col0, _ = st.columns(3)
    with col0:
        st.markdown('<div class="btn-num">', unsafe_allow_html=True)
        if st.button("0", key="btn_0"):
            pressionar_numero(0)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    c_b, c_c, c_f = st.columns(3)
    with c_b:
        st.markdown('<div class="btn-branco">', unsafe_allow_html=True)
        if st.button("BRANCO", key="btn_b"):
            pressionar_branco()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c_c:
        st.markdown('<div class="btn-corrige">', unsafe_allow_html=True)
        if st.button("CORRIGE", key="btn_c"):
            pressionar_corrige()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c_f:
        st.markdown('<div class="btn-confirma">', unsafe_allow_html=True)
        if st.button("CONFIRMA", key="btn_f"):
            pressionar_confirma()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)