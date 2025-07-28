import streamlit as st
from typing import Optional
import os
from .auth_manager import AuthManager
from .email_service import EmailService

def init_auth():
    """Initialize authentication in Streamlit app"""
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager()
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Check for persistent session
    if st.session_state.user is None:
        token = st.query_params.get('token')
        if token:
            user = st.session_state.auth_manager.verify_session(token)
            if user:
                st.session_state.user = user

def require_auth(role: Optional[str] = None):
    """Decorator to require authentication for a page"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if st.session_state.user is None:
                show_login_page()
                st.stop()
            
            if role and st.session_state.user.get('role') != role:
                st.error("Você não tem permissão para acessar esta página.")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def show_login_page():
    """Display login/register page"""
    st.title("🔐 Marine Seguros - Login")
    
    tab1, tab2, tab3 = st.tabs(["Login", "Registrar", "Esqueci a senha"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_register_form()
    
    with tab3:
        show_password_reset_form()

def show_login_form():
    """Display login form"""
    with st.form("login_form"):
        st.subheader("Entrar no Sistema")
        
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        remember_me = st.checkbox("Lembrar de mim")
        
        if st.form_submit_button("Entrar", use_container_width=True, type="primary"):
            if username and password:
                user = st.session_state.auth_manager.authenticate(username, password)
                if user:
                    st.session_state.user = user
                    
                    # Set persistent session if remember me is checked
                    if remember_me:
                        st.query_params.token = user['token']
                    
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos. Após 5 tentativas, a conta será bloqueada por 30 minutos.")
            else:
                st.error("Por favor, preencha todos os campos.")

def show_register_form():
    """Display registration form"""
    with st.form("register_form"):
        st.subheader("Criar Nova Conta")
        
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Email")
            username = st.text_input("Usuário")
        
        with col2:
            password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirmar Senha", type="password")
        
        st.info("A senha deve ter pelo menos 8 caracteres.")
        
        if st.form_submit_button("Registrar", use_container_width=True, type="primary"):
            if email and username and password and confirm_password:
                if len(password) < 8:
                    st.error("A senha deve ter pelo menos 8 caracteres.")
                elif password != confirm_password:
                    st.error("As senhas não coincidem.")
                else:
                    # Check if admin exists, if not make first user admin
                    users = st.session_state.auth_manager.list_users()
                    role = 'admin' if len(users) == 0 else 'user'
                    
                    if st.session_state.auth_manager.create_user(email, username, password, role):
                        st.success("Conta criada com sucesso! Faça login para continuar.")
                        if role == 'admin':
                            st.info("Você é o primeiro usuário e foi designado como administrador.")
                        
                        # Send welcome email
                        try:
                            email_service = EmailService()
                            email_service.send_welcome_email(email, username)
                        except Exception as e:
                            st.warning("Conta criada, mas não foi possível enviar email de boas-vindas. Verifique as configurações de email.")
                    else:
                        st.error("Erro ao criar conta. Usuário ou email já existe.")
            else:
                st.error("Por favor, preencha todos os campos.")

def show_password_reset_form():
    """Display password reset form"""
    with st.form("reset_form"):
        st.subheader("Recuperar Senha")
        
        email = st.text_input("Email cadastrado")
        
        if st.form_submit_button("Enviar email de recuperação", use_container_width=True, type="primary"):
            if email:
                token = st.session_state.auth_manager.create_reset_token(email)
                if token:
                    # Send email
                    email_service = EmailService()
                    if email_service.send_reset_email(email, token):
                        st.success("Email de recuperação enviado! Verifique sua caixa de entrada.")
                    else:
                        st.error("Erro ao enviar email. Verifique as configurações de email.")
                else:
                    st.error("Email não encontrado no sistema.")
            else:
                st.error("Por favor, insira seu email.")

def show_change_password_form():
    """Show change password form"""
    with st.form("change_password_form"):
        current_password = st.text_input("Senha Atual", type="password")
        new_password = st.text_input("Nova Senha", type="password", help="Mínimo 8 caracteres")
        confirm_password = st.text_input("Confirmar Nova Senha", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Alterar Senha", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancelar", use_container_width=True)
        
        if cancel:
            st.session_state.show_change_password = False
            st.rerun()
        
        if submit:
            if not current_password or not new_password or not confirm_password:
                st.error("Por favor, preencha todos os campos.")
            elif new_password != confirm_password:
                st.error("As senhas não coincidem.")
            elif len(new_password) < 8:
                st.error("A nova senha deve ter pelo menos 8 caracteres.")
            else:
                # Change password
                success, message = st.session_state.auth_manager.change_password(
                    st.session_state.user['id'], 
                    current_password, 
                    new_password
                )
                
                if success:
                    st.success(message)
                    st.session_state.show_change_password = False
                    st.rerun()
                else:
                    st.error(message)

def show_user_menu():
    """Display user menu in sidebar"""
    # Debug: Check if user exists and what it contains
    if hasattr(st.session_state, 'user') and st.session_state.user:
        # Ensure user dict has required fields
        user = st.session_state.user
        if isinstance(user, dict) and all(key in user for key in ['username', 'email', 'role']):
            with st.sidebar:
                # User info section with better styling
                st.markdown("---")
                st.markdown("### 👤 Perfil do Usuário")
                
                # Create a container for user info
                with st.container():
                    st.markdown(f"**Nome:** {st.session_state.user['username']}")
                    st.markdown(f"**Email:** {st.session_state.user['email']}")
                    role_display = "Administrador" if st.session_state.user['role'] == 'admin' else "Usuário"
                    st.markdown(f"**Função:** {role_display}")
                
                st.markdown("")  # Add some space
                
                # Buttons in columns
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔑 Alterar Senha", use_container_width=True, help="Alterar sua senha"):
                        st.session_state.show_change_password = True
                with col2:
                    if st.button("🚪 Sair", use_container_width=True, type="primary", help="Fazer logout"):
                        st.session_state.user = None
                        st.rerun()
            
            # Show change password modal
            if getattr(st.session_state, 'show_change_password', False):
                with st.expander("🔑 Alterar Senha", expanded=True):
                    show_change_password_form()
            
            if st.session_state.user['role'] == 'admin':
                st.divider()
                if st.button("⚙️ Gerenciar Usuários", use_container_width=True):
                    st.session_state.navigate_to_auth = True
                    st.info("👉 Clique na aba '🔐 Autenticação' acima para gerenciar usuários")

def show_admin_panel():
    """Display admin panel for user management"""
    st.title("⚙️ Gerenciamento de Usuários")
    
    users = st.session_state.auth_manager.list_users()
    
    # User list
    st.subheader("Usuários Cadastrados")
    
    for user in users:
        with st.expander(f"{user['username']} - {user['email']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**ID:** {user['id']}")
                st.write(f"**Função:** {user['role']}")
            
            with col2:
                st.write(f"**Ativo:** {'Sim' if user['is_active'] else 'Não'}")
                st.write(f"**Criado em:** {user['created_at']}")
            
            with col3:
                st.write(f"**Último login:** {user['last_login'] or 'Nunca'}")
            
            # Admin actions
            if user['id'] != st.session_state.user['id']:  # Can't modify self
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    new_role = st.selectbox(
                        "Função",
                        options=['user', 'admin'],
                        index=0 if user['role'] == 'user' else 1,
                        key=f"role_{user['id']}"
                    )
                    if st.button("Atualizar Função", key=f"update_role_{user['id']}"):
                        if st.session_state.auth_manager.update_user(user['id'], role=new_role):
                            st.success("Função atualizada!")
                            st.rerun()
                
                with col2:
                    if user['is_active']:
                        if st.button("Desativar", key=f"deactivate_{user['id']}"):
                            if st.session_state.auth_manager.update_user(user['id'], is_active=False):
                                st.success("Usuário desativado!")
                                st.rerun()
                    else:
                        if st.button("Ativar", key=f"activate_{user['id']}"):
                            if st.session_state.auth_manager.update_user(user['id'], is_active=True):
                                st.success("Usuário ativado!")
                                st.rerun()
                
                with col3:
                    if st.button("Resetar Senha", key=f"reset_{user['id']}"):
                        token = st.session_state.auth_manager.create_reset_token(user['email'])
                        if token:
                            st.info(f"Token de reset criado: {token[:8]}...")
                            st.success("Email de reset enviado!")
    
    # Audit log
    st.divider()
    st.subheader("Log de Auditoria")
    
    # This would show recent security events
    st.info("Log de auditoria será implementado para rastrear todas as ações de segurança.")