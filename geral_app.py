import streamlit as st

# Configuração da página para focar na experiência mobile
st.set_page_config(page_title="Urna Eletrônica", layout="centered")

# CSS personalizado para replicar o visual da urna da imagem
st.markdown("""
    <style>
    /* Estilo do ecrã da urna */
    .urna-screen {
        background-color: #dce2d6;
        border: 2px solid #222;
        border-radius: 8px;
        padding: 15px;
        min-height: 180px;
        font-family: sans-serif;
        color: #111;
        margin-bottom: 20px;
    }
    .sub-title {
        font-size: 11px;
        letter-spacing: 0.5px;
        color: #444;
        margin-bottom: 5px;
    }
    .cargo-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .digits-container {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 14px;
        font-weight: bold;
    }
    .digit-box {
        width: 32px;
        height: 40px;
        border: 2px solid #111;
        background-color: #fff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: bold;
    }
    
    /* Botões numéricos */
    .stButton>button {
        width: 100%;
        height: 52px;
        font-size: 20px;
        font-weight: bold;
        background-color: #262626;
        color: white;
        border-radius: 6px;
        border: none;
    }
    
    /* Cores dos botões de ação */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ccc !important;
        font-size: 13px !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background-color: #f26522 !important;
        color: #ffffff !important;
        font-size: 13px !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {
        background-color: #008000 !important;
        color: #ffffff !important;
        font-size: 13px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Inicialização do estado da sessão
if "numero_digitado" not in st.session_state:
    st.session_state.numero_digitado = ""
if "voto_confirmado" not in st.session_state:
    st.session_state.voto_confirmado = False

# Seletor de UF
uf = st.selectbox("UF:", ["ES", "AC", "AL", "AM", "AP", "BA", "CE", "DF", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"])

# Funções de controlo dos botões
def InserirNumero(num):
    if len(st.session_state.numero_digitado) < 4:
        st.session_state.numero_digitado += str(num)

def Limpar():
    st.session_state.numero_digitado = ""
    st.session_state.voto_confirmado = False

def VotarBranco():
    st.session_state.numero_digitado = "BRANCO"

def Confirmar():
    if st.session_state.numero_digitado:
        st.session_state.voto_confirmado = True

# --- ECRÃ DA URNA ---
num_str = st.session_state.numero_digitado

if st.session_state.voto_confirmado:
    st.markdown("""
        <div class="urna-screen" style="display:flex; justify-content:center; align-items:center;">
            <h1 style="font-size: 60px; color: #111;">FIM</h1>
        </div>
    """, unsafe_allow_html=True)
else:
    # Renderiza as caixinhas dos dígitos (máximo 4 para Deputado Federal)
    caixas_html = ""
    if num_str == "BRANCO":
        caixas_html = "<strong>VOTO EM BRANCO</strong>"
    else:
        for i in range(4):
            val = num_str[i] if i < len(num_str) else ""
            caixas_html += f'<div class="digit-box">{val}</div>'

    st.markdown(f"""
        <div class="urna-screen">
            <div class="sub-title">SEU VOTO VAI PARA</div>
            <div class="cargo-title">DEPUTADO FEDERAL</div>
            <div class="digits-container">
                <span>Número:</span>
                {caixas_html}
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- TECLADO DA URNA ---
col1, col2, col3 = st.columns(3)
with col1:
    st.button("1", on_click=InserirNumero, args=(1,))
    st.button("4", on_click=InserirNumero, args=(4,))
    st.button("7", on_click=InserirNumero, args=(7,))

with col2:
    st.button("2", on_click=InserirNumero, args=(2,))
    st.button("5", on_click=InserirNumero, args=(5,))
    st.button("8", on_click=InserirNumero, args=(8,))

with col3:
    st.button("3", on_click=InserirNumero, args=(3,))
    st.button("6", on_click=InserirNumero, args=(6,))
    st.button("9", on_click=InserirNumero, args=(9,))

# Linha com o botão '0' centrado
c1, c2, c3 = st.columns(3)
with c2:
    st.button("0", on_click=InserirNumero, args=(0,))

# Botões de Ação na parte inferior
btn_col1, btn_col2, btn_col3 = st.columns(3)
with btn_col1:
    st.button("BRANCO", on_click=VotarBranco)
with btn_col2:
    st.button("CORRIGE", on_click=Limpar)
with btn_col3:
    st.button("CONFIRMA", on_click=Confirmar)