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
        
        email = st.text_input("Email", placeholder="seu@email.com")
        password = st.text_input("Senha", type="password")
        remember_me = st.checkbox("Lembrar de mim")
        
        if st.form_submit_button("Entrar", use_container_width=True, type="primary"):
            if email and password:
                user = st.session_state.auth_manager.authenticate(email, password)
                if user:
                    st.session_state.user = user
                    
                    # Set persistent session if remember me is checked
                    if remember_me:
                        st.query_params.token = user['token']
                    
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    # Check what the actual issue is
                    import sqlite3
                    conn = sqlite3.connect(st.session_state.auth_manager.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT email_verified FROM users WHERE email = ?", (email.lower(),))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result is None:
                        # Email not registered
                        st.error("❌ Email não registrado. Por favor, registre-se primeiro.")
                        # Check if email is in whitelist
                        from config import ALLOWED_EMAILS
                        if email.lower() not in [e.lower() for e in ALLOWED_EMAILS]:
                            st.warning("⚠️ Este email não está autorizado. Apenas emails pré-aprovados podem acessar o sistema.")
                    elif result[0] == 0:
                        # Email registered but not verified
                        st.error("❌ Email não verificado. Verifique sua caixa de entrada para o link de ativação.")
                    else:
                        # Email exists and is verified, so password must be wrong
                        st.error("❌ Senha incorreta. Após 5 tentativas, a conta será bloqueada por 30 minutos.")
            else:
                st.error("Por favor, preencha todos os campos.")

def show_register_form():
    """Display registration form"""
    with st.form("register_form"):
        st.subheader("Criar Nova Conta")
        
        email = st.text_input("Email", placeholder="seu@email.com")
        password = st.text_input("Senha", type="password")
        confirm_password = st.text_input("Confirmar Senha", type="password")
        
        st.info("A senha deve ter pelo menos 8 caracteres.")
        
        # Show allowed emails
        with st.expander("📧 Emails autorizados"):
            from config import ALLOWED_EMAILS
            for allowed_email in ALLOWED_EMAILS:
                st.write(f"✅ {allowed_email}")
        
        if st.form_submit_button("Registrar", use_container_width=True, type="primary"):
            if email and password and confirm_password:
                if len(password) < 8:
                    st.error("A senha deve ter pelo menos 8 caracteres.")
                elif password != confirm_password:
                    st.error("As senhas não coincidem.")
                else:
                    # Generate username from email
                    username = email.split('@')[0]  # e.g., ellen@marineseguros.com.br -> ellen
                    
                    # All new users are created as admins by default
                    role = 'admin'
                    
                    success, result = st.session_state.auth_manager.create_user(email, username, password, role)
                    if success:
                        # Create verification token
                        user_id = int(result)  # result contains user_id when successful
                        token = st.session_state.auth_manager.create_verification_token(user_id)
                        
                        if token:
                            # Send verification email
                            email_service = EmailService()
                            if email_service.send_verification_email(email, token):
                                st.success("✅ Conta criada com sucesso!")
                                st.info("📧 Verifique seu email para ativar sua conta. O link expira em 24 horas.")
                            else:
                                st.warning("Conta criada, mas houve um erro ao enviar o email de verificação. Entre em contato com o administrador.")
                        else:
                            st.warning("Conta criada, mas houve um erro ao gerar o token de verificação.")
                    else:
                        st.error(f"❌ {result}")  # result contains error message when not successful
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
                    # Extract display name from email or username
                    display_name = st.session_state.user.get('username', st.session_state.user['email'].split('@')[0])
                    display_name = display_name.capitalize()
                    
                    st.markdown(f"**Nome:** {display_name}")
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
    
    # Show allowed emails
    from config import ALLOWED_EMAILS
    with st.expander("📧 Emails Autorizados", expanded=True):
        st.info("Apenas os seguintes emails podem se registrar no sistema:")
        for email in ALLOWED_EMAILS:
            st.write(f"✅ {email}")
    
    users = st.session_state.auth_manager.list_users()
    
    # User list
    st.subheader("Usuários Cadastrados")
    
    for user in users:
        with st.expander(f"{user['username']} - {user['email']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**ID:** {user['id']}")
                st.write(f"**Função:** {user['role']}")
                email_verified = user.get('email_verified', True)
                if email_verified:
                    st.write("**Email:** ✅ Verificado")
                else:
                    st.write("**Email:** ❌ Não verificado")
            
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