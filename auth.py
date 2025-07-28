"""
Simple authentication module for Marine Seguros
"""

import streamlit as st
import hashlib
import json
import os
from datetime import datetime


def init_auth():
    """Initialize authentication state"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'users' not in st.session_state:
        st.session_state.users = load_users()


def load_users():
    """Load users from file or create default"""
    users_file = "data/users.json"
    
    # Default users
    default_users = {
        "admin": {
            "password": hash_password("admin123"),
            "role": "admin",
            "name": "Administrator"
        },
        "user": {
            "password": hash_password("user123"),
            "role": "user",
            "name": "User"
        }
    }
    
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                return json.load(f)
        except:
            return default_users
    
    return default_users


def save_users(users):
    """Save users to file"""
    users_file = "data/users.json"
    os.makedirs("data", exist_ok=True)
    
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)


def hash_password(password):
    """Hash a password"""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username, password):
    """Authenticate a user"""
    users = st.session_state.users
    
    if username in users:
        if users[username]["password"] == hash_password(password):
            return {
                "username": username,
                "role": users[username]["role"],
                "name": users[username]["name"]
            }
    
    return None


def require_auth():
    """Check if user is authenticated"""
    return st.session_state.user is not None


def show_login_page():
    """Show login page"""
    st.title("🔐 Marine Seguros - Login")
    
    with st.container():
        st.markdown("### Por favor, faça login para continuar")
        
        with st.form("login_form"):
            username = st.text_input("Nome de usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", type="primary")
            
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.success(f"Bem-vindo, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Nome de usuário ou senha inválidos")
        
        # Show default credentials hint
        with st.expander("ℹ️ Credenciais de Demonstração"):
            st.info("""
            **Acesso Administrador:**
            - Usuário: admin
            - Senha: admin123
            
            **Acesso Usuário:**
            - Usuário: user
            - Senha: user123
            """)


def show_user_menu():
    """Show user menu in sidebar"""
    if st.session_state.user:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 {st.session_state.user['name']}**")
        role_pt = "Administrador" if st.session_state.user['role'] == 'admin' else "Usuário"
        st.sidebar.caption(f"Função: {role_pt}")
        
        if st.sidebar.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None
            st.rerun()


def show_admin_panel():
    """Show admin panel in sidebar"""
    if st.session_state.user and st.session_state.user['role'] == 'admin':
        with st.sidebar.expander("👨‍💼 Painel Administrativo"):
            st.markdown("### Gerenciamento de Usuários")
            
            # Add new user
            st.markdown("**Adicionar Novo Usuário**")
            new_username = st.text_input("Nome de usuário", key="new_username")
            new_password = st.text_input("Senha", key="new_password", type="password")
            new_name = st.text_input("Nome completo", key="new_name")
            new_role = st.selectbox("Função", ["user", "admin"], key="new_role", format_func=lambda x: "Usuário" if x == "user" else "Administrador")
            
            if st.button("➕ Adicionar Usuário"):
                if new_username and new_password and new_name:
                    users = st.session_state.users
                    if new_username not in users:
                        users[new_username] = {
                            "password": hash_password(new_password),
                            "role": new_role,
                            "name": new_name
                        }
                        save_users(users)
                        st.session_state.users = users
                        st.success(f"Usuário '{new_username}' adicionado com sucesso!")
                    else:
                        st.error("Nome de usuário já existe")
                else:
                    st.error("Por favor, preencha todos os campos")
            
            # List users
            st.markdown("**Usuários Atuais**")
            users = st.session_state.users
            for username, user_data in users.items():
                role_display = "admin" if user_data['role'] == 'admin' else "usuário"
                st.text(f"• {username} ({role_display})")