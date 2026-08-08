import streamlit as st
import cv2
import numpy as np
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Configuração inicial da página
st.set_page_config(
    page_title="VISIONX360 - Controle de Acesso",
    page_icon="🔒",
    layout="wide"
)

# Carrega variáveis de ambiente (.env)
load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

@st.cache_resource
def init_supabase():
    if URL and KEY:
        return create_client(URL, KEY)
    return None

supabase = init_supabase()

# --- SISTEMA DE AUTENTICAÇÃO ---
def checar_senha():
    """Gerencia o login do sistema."""
    def login_form():
        # Exibe a logo na tela de login se ela existir
        if os.path.exists("logo_visionx360.jpg"):
            col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
            with col_l2:
                st.image("logo_visionx360.jpg", use_container_width=True)

        st.markdown("<h3 style='text-align: center;'>🔒 VISIONX360 - Acesso Restrito</h3>", unsafe_allow_html=True)
        
        col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
        with col_f2:
            with st.form("Credentials"):
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                submit = st.form_submit_button("Entrar", use_container_width=True)

                if submit:
                    if "passwords" in st.secrets and username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                        st.session_state["password_correct"] = True
                        st.session_state["usuario_logado"] = username
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos.")

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        login_form()
        return False
    else:
        return True

# --- INTERFACE PRINCIPAL ---
if checar_senha():
    # BARRA LATERAL (SIDEBAR)
    with st.sidebar:
        if os.path.exists("logo_visionx360.jpg"):
            st.image("logo_visionx360.jpg", use_container_width=True)
        
        st.title("VISIONX360")
        st.write(f"👤 Usuário: **{st.session_state['usuario_logado']}**")
        st.divider()
        
        if st.button("🚪 Sair / Logout", use_container_width=True):
            st.session_state["password_correct"] = False
            st.rerun()

    # PAINEL PRINCIPAL COM ABAS
    st.title("🖥️ VISIONX360 - Painel de Controle")
    st.success("Conectado ao sistema com sucesso!")

    tab_monitor, tab_cadastro, tab_gestao = st.tabs([
        "🎥 Monitoramento e Controle", 
        "👤 Cadastrar Novo Usuário",
        "⚙️ Gerenciar Usuários"
    ])

    # -------------------------------------------------------------
    # ABA 1: MONITORAMENTO E CONTROLE
    # -------------------------------------------------------------
    with tab_monitor:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎥 Feed da Câmera em Tempo Real")
            st.info("O feed da câmera pode ser acionado via script 'main.py' ou streamer integrado.")

        with col2:
            st.subheader("📋 Ações e Comandos")
            if st.button("🔓 Abrir Portão Manualmente", type="primary", use_container_width=True):
                st.warning("⚡ Comando de abertura manual enviado ao relé!")

    # -------------------------------------------------------------
    # ABA 2: CADASTRO DE NOVO USUÁRIO
    # -------------------------------------------------------------
    with tab_cadastro:
        st.subheader("📝 Cadastro de Biometria Facial")
        st.caption("Preencha os dados e tire a foto usando a webcam do navegador.")

        with st.form("form_cadastro_usuario", clear_on_submit=True):
            nome = st.text_input("Nome Completo")
            cpf = st.text_input("CPF (Apenas números)")
            foto_camera = st.camera_input("Tire a foto para a biometria facial")

            cadastrar = st.form_submit_button("Salvar Usuário no Supabase", use_container_width=True)

            if cadastrar:
                if not nome or not cpf:
                    st.error("⚠️ Por favor, preencha o Nome e o CPF!")
                elif foto_camera is None:
                    st.error("⚠️ Tire uma foto antes de salvar!")
                elif not supabase:
                    st.error("❌ Conexão com o Supabase não configurada no arquivo .env!")
                else:
                    try:
                        # Converte a foto tirada pelo Streamlit para o formato do OpenCV / face_recognition
                        bytes_data = foto_camera.getvalue()
                        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                        rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

                        # Detecta os rostos na foto
                        face_locations = face_recognition.face_locations(rgb_img)
                        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

                        if len(face_encodings) == 0:
                            st.error("❌ Nenhum rosto detectado na foto. Tente novamente centralizando o rosto.")
                        elif len(face_encodings) > 1:
                            st.warning("⚠️ Mais de um rosto foi detectado! Certifique-se de estar sozinho(a) na foto.")
                        else:
                            # Converte o vetor numérico do rosto para formato lista/JSON
                            encoding_list = face_encodings[0].tolist()

                            # Insere no Supabase
                            dados_usuario = {
                                "nome": nome.strip(),
                                "cpf": cpf.strip(),
                                "encoding": encoding_list
                            }

                            res = supabase.from_("usuarios").insert(dados_usuario).execute()
                            st.balloons()
                            st.success(f"✅ Usuário **{nome}** cadastrado com sucesso!")

                    except Exception as e:
                        st.error(f"❌ Erro ao salvar cadastro: {e}")

    # -------------------------------------------------------------
    # ABA 3: GESTÃO DE USUÁRIOS (CONSULTAR E EXCLUIR)
    # -------------------------------------------------------------
    with tab_gestao:
        st.subheader("👥 Usuários Cadastrados no Banco de Dados")
        st.caption("Consulte os usuários com acesso facial ativo e remova registros se necessário.")

        if not supabase:
            st.error("❌ Conexão com o Supabase não configurada!")
        else:
            try:
                # Consulta os registros no Supabase
                resposta = supabase.from_("usuarios").select("id, nome, cpf, created_at").execute()
                usuarios = resposta.data

                if not usuarios:
                    st.info("Nenhum usuário cadastrado até o momento.")
                else:
                    st.write(f"**Total de usuários ativos:** {len(usuarios)}")
                    st.divider()

                    # Lista cada usuário com opção de exclusão
                    for usr in usuarios:
                        col_info, col_btn = st.columns([4, 1])

                        with col_info:
                            st.markdown(f"**{usr['nome']}**")
                            st.text(f"CPF: {usr['cpf']} | Cadastrado em: {usr.get('created_at', 'N/A')}")

                        with col_btn:
                            if st.button("🗑️ Excluir", key=f"del_{usr['id']}", type="secondary", use_container_width=True):
                                supabase.from_("usuarios").delete().eq("id", usr['id']).execute()
                                st.success(f"Usuário '{usr['nome']}' excluído!")
                                st.rerun()

                        st.divider()

            except Exception as e:
                st.error(f"❌ Erro ao carregar usuários: {e}")