import streamlit as st
from auth import init_auth, require_auth, show_login_page, show_user_menu, show_admin_panel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize authentication
init_auth()

# Configure page
st.set_page_config(
    page_title="Marine Seguros - Dashboard Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check if user is logged in
if st.session_state.user is None:
    show_login_page()
else:
    # Show user menu in sidebar
    show_user_menu()
    
    # Check if admin panel should be shown
    if 'show_admin' in st.session_state and st.session_state.show_admin:
        show_admin_panel()
        if st.button("← Voltar ao Dashboard"):
            st.session_state.show_admin = False
            st.rerun()
    else:
        # Your existing app code goes here
        @require_auth()
        def main_app():
            st.title("📊 Marine Seguros - Dashboard Financeiro")
            
            # Example: Show different content based on user role
            if st.session_state.user['role'] == 'admin':
                st.info("👑 Você tem acesso administrativo total.")
            else:
                st.info("👤 Você tem acesso de usuário.")
            
            # Add your existing dashboard code here
            st.write("Seu dashboard financeiro aqui...")
            
            # Example of role-based feature
            if st.session_state.user['role'] == 'admin':
                with st.expander("⚙️ Configurações Avançadas (Admin)"):
                    st.write("Configurações disponíveis apenas para administradores")
        
        main_app()

# Example of how to integrate into existing app.py:
# 1. Add these imports at the top:
#    from auth import init_auth, require_auth, show_login_page, show_user_menu
#    from dotenv import load_dotenv
#
# 2. Add after imports:
#    load_dotenv()
#    init_auth()
#
# 3. Wrap your main content:
#    if st.session_state.user is None:
#        show_login_page()
#    else:
#        show_user_menu()
#        # Your existing code here
#
# 4. For sensitive sections, use decorator:
#    @require_auth(role='admin')
#    def admin_only_function():
#        # Admin only code