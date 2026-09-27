import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# Configuração da Página
# ---------------------------------------------------------
st.set_page_config(page_title="Urna Eletrônica 2026", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    
    .urna-tela {
        background-color: #dbe3db;
        border: 4px solid #1a1a1a;
        border-radius: 8px;
        padding: 18px;
        min-height: 380px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.15);
        color: #000;
        font-family: Arial, Helvetica, sans-serif;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .caixa-num {
        display: inline-block;
        width: 34px;
        height: 42px;
        border: 2px solid #000;
        font-size: 26px;
        font-weight: bold;
        text-align: center;
        line-height: 38px;
        margin-right: 3px;
        background-color: #fff;
        color: #000;
    }

    .teclado-painel {
        background-color: #2b2b2b;
        padding: 15px;
        border-radius: 10px;
        border: 3px solid #111;
        box-shadow: 0 6px 12px rgba(0,0,0,0.4);
        margin-top: 10px;
    }

    div.stButton > button {
        width: 100%;
        height: 52px;
        font-weight: bold;
        font-size: 18px;
        border-radius: 6px;
        box-shadow: 0 4px 0px #000;
        transition: all 0.05s ease;
    }

    div.stButton > button:active {
        transform: translateY(3px);
        box-shadow: 0 1px 0px #000;
    }

    .btn-num button {
        background-color: #222222 !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
    }

    .btn-branco button { background-color: #ffffff !important; color: #000000 !important; border: 1px solid #888 !important; font-size: 13px !important; }
    .btn-corrige button { background-color: #e65100 !important; color: #ffffff !important; border: none !important; font-size: 13px !important; }
    .btn-confirma button { background-color: #1b5e20 !important; color: #ffffff !important; border: none !important; font-size: 14px !important; height: 60px !important; }

    @media (max-width: 768px) {
        .urna-tela {
            min-height: 320px;
            padding: 12px;
        }
        .caixa-num {
            width: 28px;
            height: 36px;
            font-size: 20px;
            line-height: 32px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sons da Urna (Simulados em Web Audio/HTML5)
# ---------------------------------------------------------
def tocar_som(tipo="tecla"):
    if tipo == "tecla":
        st.markdown("""
            <audio autoplay style="display:none;">
                <source src="https://www.soundjay.com/buttons/sounds/button-16a.mp3" type="audio/mpeg">
            </audio>
        """, unsafe_allow_html=True)
    elif tipo == "fim":
        st.markdown("""
            <audio autoplay style="display:none;">
                <source src="https://www.soundjay.com/buttons/sounds/button-09.mp3" type="audio/mpeg">
            </audio>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Carregamento e Limpeza da Base de Dados
# ---------------------------------------------------------
@st.cache_data
def carregar_candidatos():
    try:
        df = pd.read_csv("Consulta_cand_2026_BRASIL.csv", sep=None, engine='python', encoding="utf-8", dtype=str)
    except Exception:
        try:
            df = pd.read_csv("Consulta_cand_2026_BRASIL.csv", sep=None, engine='python', encoding="latin1", dtype=str)
        except Exception:
            return pd.DataFrame()
            
    df.columns = df.columns.str.strip()
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()
    return df

df_candidatos = carregar_candidatos()

ufs_disponiveis = sorted(df_candidatos['SG_UF'].unique().tolist()) if not df_candidatos.empty and 'SG_UF' in df_candidatos.columns else ["MT", "RJ", "SP", "PE", "GO", "DF", "MG"]

# Etapas Eleitorais Oficiais de 2026 (2 vagas para Senador)
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
if 'tocar_som_tipo' not in st.session_state:
    st.session_state.tocar_som_tipo = None

if st.session_state.tocar_som_tipo:
    tocar_som(st.session_state.tocar_som_tipo)
    st.session_state.tocar_som_tipo = None

etapa_atual = ETAPAS[st.session_state.etapa_index] if st.session_state.etapa_index < len(ETAPAS) else None

def pressionar_numero(num):
    if etapa_atual and len(st.session_state.digitos) < etapa_atual["digitos"] and st.session_state.tipo_voto == "NOMINATIVO":
        st.session_state.digitos += str(num)
        st.session_state.tocar_som_tipo = "tecla"

def pressionar_branco():
    st.session_state.digitos = ""
    st.session_state.tipo_voto = "BRANCO"
    st.session_state.tocar_som_tipo = "tecla"

def pressionar_corrige():
    st.session_state.digitos = ""
    st.session_state.tipo_voto = "NOMINATIVO"
    st.session_state.tocar_som_tipo = "tecla"

def pressionar_confirma():
    if not etapa_atual:
        return
    qtd_dig = len(st.session_state.digitos)
    if st.session_state.tipo_voto == "BRANCO" or qtd_dig == etapa_atual["digitos"] or (etapa_atual["permite_legenda"] and qtd_dig == 2):
        # Armazena o voto do 1º Senador para evitar repetição no 2º Senador
        if etapa_atual.get("chave") == "senador1":
            st.session_state.voto_senador1 = st.session_state.digitos if st.session_state.tipo_voto == "NOMINATIVO" else "BRANCO"

        st.session_state.etapa_index += 1
        st.session_state.digitos = ""
        st.session_state.tipo_voto = "NOMINATIVO"
        st.session_state.tocar_som_tipo = "fim"

def reiniciar():
    st.session_state.etapa_index = 0
    st.session_state.digitos = ""
    st.session_state.tipo_voto = "NOMINATIVO"
    st.session_state.voto_senador1 = ""

# ---------------------------------------------------------
# Interface Principal
# ---------------------------------------------------------
st.markdown("<h3 style='text-align: center; margin-bottom: 5px;'>Justiça Eleitoral</h3>", unsafe_allow_html=True)

index_uf = ufs_disponiveis.index(st.session_state.uf_selecionada) if st.session_state.uf_selecionada in ufs_disponiveis else 0
uf = st.selectbox("Estado da Votação (UF):", ufs_disponiveis, index=index_uf, key="uf_select")
st.session_state.uf_selecionada = uf

col_tela, col_teclado = st.columns([1.2, 1])

# --- TELA DA URNA ---
with col_tela:
    if st.session_state.etapa_index >= len(ETAPAS):
        st.markdown('''
            <div class="urna-tela" style="justify-content: center; align-items: center; text-align: center;">
                <h1 style="font-size: 90px; margin: 0; letter-spacing: 4px;">FIM</h1>
                <p style="font-size: 22px; color: #1b5e20; font-weight: bold; margin-top: 10px;">VOTOU</p>
            </div>
        ''', unsafe_allow_html=True)
        st.write("")
        if st.button("REINICIAR VOTAÇÃO"):
            reiniciar()
            st.rerun()
    else:
        candidato_encontrado = None
        legenda_encontrada = None
        voto_duplicado_senador = False
        qtd_digitos = etapa_atual["digitos"]
        digitos_atuais = st.session_state.digitos
        
        # Alerta para o 2º Senador igual ao 1º
        if etapa_atual.get("chave") == "senador2" and digitos_atuais != "" and digitos_atuais == st.session_state.voto_senador1:
            voto_duplicado_senador = True

        if not df_candidatos.empty:
            df_filtrado = df_candidatos.copy()

            if 'DS_CARGO' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['DS_CARGO'].isin(etapa_atual["filtro_cargo"])]

            if 'SG_UF' in df_filtrado.columns and etapa_atual["cargo"] != "PRESIDENTE":
                df_filtrado = df_filtrado[df_filtrado['SG_UF'].isin([st.session_state.uf_selecionada, "BR"])]

            if len(digitos_atuais) == qtd_digitos:
                if 'NR_CANDIDATO' in df_filtrado.columns:
                    match = df_filtrado[df_filtrado['NR_CANDIDATO'] == digitos_atuais]
                    if not match.empty:
                        candidato_encontrado = match.iloc[0]

            elif etapa_atual["permite_legenda"] and len(digitos_atuais) == 2:
                col_partido = 'NR_PARTIDO' if 'NR_PARTIDO' in df_filtrado.columns else 'NR_CANDIDATO'
                match_leg = df_filtrado[df_filtrado[col_partido].str[:2] == digitos_atuais]
                if not match_leg.empty:
                    legenda_encontrada = match_leg.iloc[0]

        boxes_html = "".join([f'<span class="caixa-num">{digitos_atuais[i] if i < len(digitos_atuais) else "&nbsp;"}</span>' for i in range(qtd_digitos)])

        info_cand = ""
        if st.session_state.tipo_voto == "BRANCO":
            info_cand = "<h2 style='text-align:center; margin-top:25px;'>VOTO EM BRANCO</h2>"
        else:
            if voto_duplicado_senador:
                detalhes = "<p style='color:#b71c1c; margin-top:10px; font-size:15px;'><b>SENADOR JÁ VOTADO!<br>NÃO É PERMITIDO REPETIR O MESMO CANDIDATO.</b></p>"
            elif candidato_encontrado is not None:
                nome = candidato_encontrado.get('NM_URNA_CANDIDATO', candidato_encontrado.get('NM_CANDIDATO', ''))
                partido = candidato_encontrado.get('SG_PARTIDO', '')
                detalhes = f"<p style='margin-top:10px; font-size:16px;'><b>Nome:</b> {nome}<br><b>Partido:</b> {partido}</p>"
            elif legenda_encontrada is not None:
                partido = legenda_encontrada.get('SG_PARTIDO', '')
                detalhes = f"<p style='margin-top:10px; font-size:16px; color:#0d47a1;'><b>VOTO NA LEGENDA</b><br><b>Partido:</b> {partido}</p>"
            elif len(digitos_atuais) == qtd_digitos or (not etapa_atual["permite_legenda"] and len(digitos_atuais) == 2):
                detalhes = "<p style='color:#b71c1c; margin-top:10px; font-size:16px;'><b>NÚMERO ERRADO / VOTO NULO</b></p>"
            else:
                detalhes = ""
            info_cand = f'<div style="margin: 10px 0;">{boxes_html}</div>' + detalhes

        st.markdown(f'''
            <div class="urna-tela">
                <div>
                    <p style="font-size: 12px; margin-bottom: 2px; font-weight: bold; color: #333;">SEU VOTO VAI PARA</p>
                    <h2 style="margin: 0; text-transform: uppercase; font-size: 22px; letter-spacing: 1px;">{etapa_atual["cargo"]}</h2>
                    {info_cand}
                </div>
                <div>
                    <hr style="border: 0.5px solid #888; margin-bottom: 8px;">
                    <p style="font-size: 10px; line-height: 1.3; margin: 0;">
                        Aperte a tecla:<br>
                        <b>CONFIRMA</b> para CONFIRMAR este voto<br>
                        <b>CORRIGE</b> para REINICIAR este voto
                    </p>
                </div>
            </div>
        ''', unsafe_allow_html=True)

# --- TECLADO NUMÉRICO ---
with col_teclado:
    st.markdown('<div class="teclado-painel">', unsafe_allow_html=True)
    
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

    st.write("")

    col_b, col_c, col_f = st.columns(3)
    
    with col_b:
        st.markdown('<div class="btn-branco">', unsafe_allow_html=True)
        if st.button("BRANCO", key="btn_branco"):
            pressionar_branco()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_c:
        st.markdown('<div class="btn-corrige">', unsafe_allow_html=True)
        if st.button("CORRIGE", key="btn_corrige"):
            pressionar_corrige()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_f:
        st.markdown('<div class="btn-confirma">', unsafe_allow_html=True)
        if st.button("CONFIRMA", key="btn_confirma"):
            pressionar_confirma()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)