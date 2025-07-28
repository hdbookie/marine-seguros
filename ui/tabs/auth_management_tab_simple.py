"""
Simple Authentication Management Tab
Works with the existing auth system
"""

import streamlit as st


def render_auth_management_tab():
    """Render the authentication management tab"""
    
    st.header("🔐 Gerenciamento de Autenticação")
    
    # Check if user is authenticated
    if not hasattr(st.session_state, 'user') or st.session_state.user is None:
        st.warning("Por favor, faça login para acessar esta página.")
        st.info("💡 Dica: Use as credenciais padrão - usuário: admin, senha: admin123")
        return
    
    # User Profile Section
    st.subheader("👤 Meu Perfil")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Nome:** {st.session_state.user.get('name', st.session_state.user.get('username', 'N/A'))}")
        st.info(f"**Usuário:** {st.session_state.user.get('username', 'N/A')}")
    with col2:
        st.info(f"**Função:** {st.session_state.user.get('role', 'user').title()}")
        st.info(f"**Email:** {st.session_state.user.get('email', 'N/A')}")
    
    st.markdown("---")
    
    # Change Password Section
    st.subheader("🔑 Alterar Senha")
    
    st.info("Para alterar sua senha, use a função de alteração de senha no menu do usuário.")
    
    # Admin Section - Basic Info
    if st.session_state.user.get('role') == 'admin':
        st.markdown("---")
        st.subheader("👨‍💼 Painel Administrativo")
        
        st.info("""
        As funções administrativas avançadas estão em desenvolvimento.
        
        Por enquanto, você pode:
        - Ver seu perfil
        - Alterar sua senha através do menu
        - Fazer logout e login com diferentes usuários
        """)
        
        # Show basic user info if auth_manager exists
        if hasattr(st.session_state, 'auth_manager'):
            try:
                users = st.session_state.auth_manager.list_users()
                st.subheader("📋 Usuários do Sistema")
                
                # Create a simple table
                user_data = []
                for user in users:
                    user_data.append({
                        "Usuário": user.get("username", "N/A"),
                        "Email": user.get("email", "N/A"),
                        "Função": user.get("role", "user").title(),
                        "Status": "✅ Ativo" if user.get("is_active", True) else "❌ Inativo"
                    })
                
                if user_data:
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
            except Exception as e:
                st.warning(f"Não foi possível listar usuários: {str(e)}")
    
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