"""
Authentication Management Tab
Allows users to manage their account and admins to manage all users
"""

import streamlit as st
import hashlib
import json
import os


def hash_password(password):
    """Hash a password"""
    return hashlib.sha256(password.encode()).hexdigest()


def save_users(users):
    """Save users to file"""
    users_file = "data/users.json"
    os.makedirs("data", exist_ok=True)
    
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)


def render_auth_management_tab():
    """Render the authentication management tab"""
    
    # Initialize auth manager if not exists
    if 'auth_manager' not in st.session_state:
        from auth.auth_manager import AuthManager
        st.session_state.auth_manager = AuthManager()
    
    st.header("🔐 Gerenciamento de Autenticação")
    
    # Debug info
    # st.write("Debug - session state user:", st.session_state.get('user', 'Not found'))
    
    # Check if user is authenticated
    if not hasattr(st.session_state, 'user') or st.session_state.user is None:
        st.warning("Por favor, faça login para acessar esta página.")
        st.info("💡 Dica: Use as credenciais padrão - usuário: admin, senha: admin123")
        return
    
    # Ensure user object has username field
    if 'username' not in st.session_state.user:
        # For backward compatibility, if username is missing, try to reconstruct it
        if hasattr(st.session_state, 'users'):
            for username, user_data in st.session_state.users.items():
                if (user_data.get('name') == st.session_state.user.get('name') and 
                    user_data.get('role') == st.session_state.user.get('role')):
                    st.session_state.user['username'] = username
                    break
        
        # If still no username, show error
        if 'username' not in st.session_state.user:
            st.error("Erro: Não foi possível identificar o usuário. Por favor, faça logout e login novamente.")
            return
    
    # User Profile Section
    st.subheader("👤 Meu Perfil")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Nome:** {st.session_state.user.get('name', st.session_state.user['username'])}")
        st.info(f"**Usuário:** {st.session_state.user['username']}")
    with col2:
        st.info(f"**Função:** {st.session_state.user['role'].title()}")
        st.info(f"**Status:** ✅ Ativo")
    
    st.markdown("---")
    
    # Change Password Section
    st.subheader("🔑 Alterar Senha")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Senha Atual", type="password")
        new_password = st.text_input("Nova Senha", type="password")
        confirm_password = st.text_input("Confirmar Nova Senha", type="password")
        
        submitted = st.form_submit_button("Alterar Senha", type="primary")
        
        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("Por favor, preencha todos os campos.")
            elif new_password != confirm_password:
                st.error("As senhas não coincidem.")
            elif len(new_password) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                # Verify current password using auth manager
                user_id = st.session_state.user.get('id')
                if user_id:
                    success, message = st.session_state.auth_manager.change_password(
                        user_id, current_password, new_password
                    )
                    if success:
                        st.success("✅ " + message)
                    else:
                        st.error(message)
                else:
                    st.error("Erro: ID do usuário não encontrado")
    
    # Admin Section - User Management
    if st.session_state.user['role'] == 'admin':
        st.markdown("---")
        st.subheader("👨‍💼 Gerenciamento de Usuários")
        
        # Tabs for different admin functions
        tab1, tab2, tab3 = st.tabs(["➕ Adicionar Usuário", "📋 Listar Usuários", "✏️ Editar/Remover"])
        
        with tab1:
            st.markdown("### Adicionar Novo Usuário")
            
            with st.form("add_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("Nome de Usuário")
                    new_password = st.text_input("Senha", type="password")
                    confirm_new_password = st.text_input("Confirmar Senha", type="password")
                
                with col2:
                    new_name = st.text_input("Nome Completo")
                    new_role = st.selectbox("Função", ["user", "admin"])
                    new_email = st.text_input("Email (opcional)")
                
                submitted = st.form_submit_button("Criar Usuário", type="primary")
                
                if submitted:
                    if not new_username or not new_password or not new_name:
                        st.error("Por favor, preencha os campos obrigatórios.")
                    elif new_password != confirm_new_password:
                        st.error("As senhas não coincidem.")
                    elif len(new_password) < 6:
                        st.error("A senha deve ter pelo menos 6 caracteres.")
                    else:
                        # Add new user using auth manager
                        success = st.session_state.auth_manager.create_user(
                            email=new_email if new_email else f"{new_username}@marineseguros.com",
                            username=new_username,
                            password=new_password,
                            role=new_role
                        )
                        if success:
                            st.success(f"✅ Usuário '{new_username}' criado com sucesso!")
                        else:
                            st.error("Erro ao criar usuário. O nome de usuário pode já existir.")
        
        with tab2:
            st.markdown("### Lista de Usuários")
            
            # Get users from auth manager
            users = st.session_state.auth_manager.list_users()
            
            # Create a table of users
            user_data = []
            for user in users:
                user_data.append({
                    "Usuário": user.get("username", "N/A"),
                    "Nome": user.get("name", user.get("username", "N/A")),
                    "Função": user.get("role", "user").title(),
                    "Email": user.get("email", "N/A"),
                    "Status": "✅ Ativo" if user.get("is_active", True) else "❌ Inativo"
                })
            
            st.dataframe(user_data, use_container_width=True)
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Usuários", len(users))
            with col2:
                admin_count = sum(1 for u in users if u.get("role") == "admin")
                st.metric("Administradores", admin_count)
            with col3:
                user_count = sum(1 for u in users if u.get("role") == "user")
                st.metric("Usuários Padrão", user_count)
        
        with tab3:
            st.markdown("### Editar/Remover Usuários")
            
            # Select user to edit
            users = st.session_state.auth_manager.list_users()
            user_options = {u['username']: u for u in users}
            
            if user_options:
                selected_username = st.selectbox(
                    "Selecionar Usuário",
                    list(user_options.keys()),
                    format_func=lambda x: f"{x} - {user_options[x].get('name', x)}"
                )
                selected_user = user_options[selected_username]
            
            if user_options and selected_user:
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Informações Atuais")
                    st.info(f"**Usuário:** {selected_user['username']}")
                    st.info(f"**Nome:** {selected_user.get('name', selected_user['username'])}")
                    st.info(f"**Função:** {selected_user.get('role', 'user').title()}")
                    st.info(f"**Email:** {selected_user.get('email', 'N/A')}")
                
                with col2:
                    st.markdown("#### Ações")
                    
                    # Reset Password functionality would need to be implemented in AuthManager
                    st.info("🆘 Função de reset de senha em desenvolvimento")
                    
                    # Change Role
                    new_role = st.selectbox(
                        "Alterar Função",
                        ["user", "admin"],
                        index=0 if selected_user.get('role') == "user" else 1,
                        key="edit_role"
                    )
                    
                    if st.button("💼 Atualizar Função", use_container_width=True):
                        if selected_user['username'] == st.session_state.user.get('username') and new_role != "admin":
                            st.error("Você não pode remover seus próprios privilégios de admin!")
                        else:
                            # Update role using auth manager
                            success = st.session_state.auth_manager.update_user(
                                selected_user['id'],
                                role=new_role
                            )
                            if success:
                                st.success(f"Função atualizada para: {new_role.title()}")
                            else:
                                st.error("Erro ao atualizar função")
                    
                    # Delete User functionality would need careful implementation
                    st.info("🆘 Função de remoção de usuário em desenvolvimento")
    
    # Security Tips
    st.markdown("---")
    with st.expander("🛡️ Dicas de Segurança"):
        st.markdown("""
        - Use senhas fortes com pelo menos 8 caracteres
        - Inclua letras maiúsculas, minúsculas, números e símbolos
        - Não compartilhe sua senha com ninguém
        - Altere sua senha regularmente
        - Faça logout ao terminar de usar o sistema
        """)