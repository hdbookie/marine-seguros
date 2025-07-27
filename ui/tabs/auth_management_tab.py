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
        st.info(f"**Nome:** {st.session_state.user['name']}")
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
                # Verify current password
                users = st.session_state.users
                username = st.session_state.user['username']
                
                if users[username]["password"] == hash_password(current_password):
                    # Update password
                    users[username]["password"] = hash_password(new_password)
                    save_users(users)
                    st.session_state.users = users
                    st.success("✅ Senha alterada com sucesso!")
                else:
                    st.error("Senha atual incorreta.")
    
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
                    elif new_username in st.session_state.users:
                        st.error("Este nome de usuário já existe.")
                    else:
                        # Add new user
                        users = st.session_state.users
                        users[new_username] = {
                            "password": hash_password(new_password),
                            "role": new_role,
                            "name": new_name,
                            "email": new_email if new_email else ""
                        }
                        save_users(users)
                        st.session_state.users = users
                        st.success(f"✅ Usuário '{new_username}' criado com sucesso!")
        
        with tab2:
            st.markdown("### Lista de Usuários")
            
            users = st.session_state.users
            
            # Create a table of users
            user_data = []
            for username, data in users.items():
                user_data.append({
                    "Usuário": username,
                    "Nome": data.get("name", "N/A"),
                    "Função": data.get("role", "user").title(),
                    "Email": data.get("email", "N/A"),
                    "Status": "✅ Ativo"
                })
            
            st.dataframe(user_data, use_container_width=True)
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Usuários", len(users))
            with col2:
                admin_count = sum(1 for u in users.values() if u.get("role") == "admin")
                st.metric("Administradores", admin_count)
            with col3:
                user_count = sum(1 for u in users.values() if u.get("role") == "user")
                st.metric("Usuários Padrão", user_count)
        
        with tab3:
            st.markdown("### Editar/Remover Usuários")
            
            # Select user to edit
            usernames = list(st.session_state.users.keys())
            selected_user = st.selectbox(
                "Selecionar Usuário",
                usernames,
                format_func=lambda x: f"{x} - {st.session_state.users[x]['name']}"
            )
            
            if selected_user:
                user_data = st.session_state.users[selected_user]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Informações Atuais")
                    st.info(f"**Usuário:** {selected_user}")
                    st.info(f"**Nome:** {user_data['name']}")
                    st.info(f"**Função:** {user_data['role'].title()}")
                    st.info(f"**Email:** {user_data.get('email', 'N/A')}")
                
                with col2:
                    st.markdown("#### Ações")
                    
                    # Reset Password
                    if st.button("🔄 Resetar Senha", use_container_width=True):
                        new_temp_password = "temp123"
                        users = st.session_state.users
                        users[selected_user]["password"] = hash_password(new_temp_password)
                        save_users(users)
                        st.session_state.users = users
                        st.success(f"Senha resetada para: {new_temp_password}")
                    
                    # Change Role
                    new_role = st.selectbox(
                        "Alterar Função",
                        ["user", "admin"],
                        index=0 if user_data['role'] == "user" else 1,
                        key="edit_role"
                    )
                    
                    if st.button("💼 Atualizar Função", use_container_width=True):
                        if selected_user == st.session_state.user['username'] and new_role != "admin":
                            st.error("Você não pode remover seus próprios privilégios de admin!")
                        else:
                            users = st.session_state.users
                            users[selected_user]["role"] = new_role
                            save_users(users)
                            st.session_state.users = users
                            st.success(f"Função atualizada para: {new_role.title()}")
                    
                    # Delete User
                    if st.button("🗑️ Remover Usuário", type="secondary", use_container_width=True):
                        if selected_user == st.session_state.user['username']:
                            st.error("Você não pode remover sua própria conta!")
                        else:
                            if st.checkbox("Confirmar exclusão"):
                                users = st.session_state.users
                                del users[selected_user]
                                save_users(users)
                                st.session_state.users = users
                                st.success(f"Usuário '{selected_user}' removido com sucesso!")
                                st.rerun()
    
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