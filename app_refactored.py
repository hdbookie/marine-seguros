"""
Marine Seguros - Financial Analytics Dashboard
Refactored version using modular architecture
"""

import streamlit as st
import pandas as pd
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
from typing import Dict

# Add the project root to sys.path to ensure imports work
# This helps with module imports in different deployment environments
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import authentication
from auth import init_auth, require_auth, show_login_page, show_user_menu, show_admin_panel

# Import database manager
from core.database_manager import DatabaseManager

# Import utilities
from utils.legacy_helpers import (
    initialize_session_state,
    generate_monthly_data_from_extracted,
    convert_extracted_to_processed
)
from utils.formatters import format_time_difference

# Import tab modules
from ui.tabs.upload_legacy_tab import render_upload_tab
from ui.tabs.dashboard_legacy_tab import render_dashboard_tab
from ui.tabs.enhanced_dashboard_tab import render_enhanced_dashboard_tab
from ui.tabs.micro_analysis import render_micro_analysis_tab
from ui.tabs.micro_analysis_v2 import render_micro_analysis_v2_tab
from ui.tabs.ai_insights_v2_tab import render_ai_insights_v2_tab  # AI Insights
from ui.tabs.ai_chat_v2_tab import render_ai_chat_v2_tab
from ui.tabs.auth_management_tab_simple import render_auth_management_tab
from ui.tabs.debug_extractors_tab import render_debug_extractors_tab
from ui.tabs.forecast_tab import render_forecast_tab  # New forecast tab

# Load environment variables
load_dotenv()

# Page configuration (must be first)
st.set_page_config(
    page_title="Marine Seguros - Financial Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication
init_auth()

# Check for logout in URL parameters or session flag
if st.query_params.get('logout') == 'true' or st.session_state.get('logout_clicked', False):
    # Clear ALL query params including token
    for key in list(st.query_params.keys()):
        del st.query_params[key]
    st.session_state.clear()
    st.rerun()

# Check for email verification token
if 'verify_token' in st.query_params:
    verify_token = st.query_params['verify_token']
    success, message = st.session_state.auth_manager.verify_email(verify_token)
    
    if success:
        st.success(message)
        st.info("Você já pode fazer login com seu usuário e senha.")
    else:
        st.error(message)
    
    # Clear the token from URL
    del st.query_params['verify_token']
    st.rerun()

# Initialize database manager
db = DatabaseManager()

# Custom CSS
st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .category-header {
        background-color: #e1e4e8;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        cursor: pointer;
        font-weight: bold;
    }
    .category-item {
        padding-left: 2rem;
        margin: 0.25rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Check authentication
if not st.session_state.get('user'):
    show_login_page()
    st.stop()

# Main app header
col1, col2 = st.columns([4, 1])
with col1:
    st.title("📊 Marine Seguros - Financial Analytics Dashboard")
    # Show welcome message
    if st.session_state.get('user'):
        display_name = st.session_state.user.get('username', st.session_state.user['email'].split('@')[0])
        st.caption(f"Bem-vindo, {display_name.capitalize()}!")
with col2:
    # Add refresh button
    if st.button("🔄 Atualizar Dados", help="Carregar dados mais recentes"):
        # Clear cache and reload
        keys_to_clear = ['processed_data', 'extracted_data', 'monthly_data', 'financial_data', 'gemini_insights', 'unified_data']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuração")
    
    
    # User menu
    show_user_menu()
    
    # Admin panel (if admin)
    if st.session_state.user and st.session_state.user.get('role') == 'admin':
        show_admin_panel()
    
    # API Key input
    gemini_api_key = st.text_input(
        "🔑 Chave API Gemini",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Obtenha sua chave API no Google AI Studio"
    )
    
    # Settings
    st.subheader("🎛️ Configurações")
    
    # Language selector
    language = st.selectbox(
        "🌐 Idioma",
        ["Português", "English"],
        index=0
    )
    
    # Feature toggles - Always enabled
    use_flexible_extractor = True
    show_anomalies = True
    
    # About section
    st.markdown("---")
    st.markdown("### Sobre")
    st.info("""
    **Marine Seguros Análise Financeira**  
    Versão 3.0 - Refatorada  
    
    Recursos:
    - 📊 Dashboard Financeiro
    - 🔬 Análise Micro (🚧 Em construção)
    - 🤖 Insights IA*
    - 💬 Assistente de Chat IA*
    
    *IA será muito mais poderosa com análise micro completa
    """)

# Initialize session state
initialize_session_state(db, False) # Initialize with data_loaded = False

# Always load state from database to ensure data persistence
data_loaded = db.auto_load_state(st.session_state)

# If no data in session but database has data, force reload
if not hasattr(st.session_state, 'extracted_data') or not st.session_state.extracted_data:
    financial_data = db.load_shared_financial_data()
    if financial_data:
        st.session_state.extracted_data = financial_data
        data_loaded = True

# Check if new data is available
if data_loaded:
    last_upload = db.get_last_upload_info()
    if last_upload:
        # Check if data is fresh (uploaded in last 5 minutes)
        from datetime import datetime, timedelta
        upload_time = datetime.fromisoformat(last_upload['created_at'].replace(' ', 'T'))
        time_diff = datetime.now() - upload_time
        if time_diff < timedelta(minutes=5):
            st.success(f"🔄 Novos dados disponíveis! Atualizados por {last_upload['username']} {format_time_difference(time_diff)}")

# Convert extracted data to processed format if needed
# This block should always regenerate processed_data from extracted_data
# if extracted_data is present, to ensure consistency.
if hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
    st.session_state.processed_data = convert_extracted_to_processed(st.session_state.extracted_data)

    # Always regenerate monthly data from extracted data to ensure it's up to date
    try:
        st.session_state.monthly_data = generate_monthly_data_from_extracted(st.session_state.extracted_data)
    except Exception as e:
        print(f"Error generating monthly data: {e}")
        import traceback
        traceback.print_exc()

# Main content - Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📁 Upload", 
    "📊 Dashboard Macro", 
    "🆕 Micro V2",
    "🤖 AI Insights", 
    "💬 AI Chat",
    "🔐 Autenticação",
    "📈 Previsões", 
    "⚡ Integração",
    "🔍 Debug Extractors"
])

# Tab 1: File Upload
with tab1:
    render_upload_tab(db, use_unified_extractor=True, show_anomalies=show_anomalies)

# Tab 2: Dashboard
with tab2:
    render_dashboard_tab(db, use_unified_extractor=True)

# Tab 3: New Micro Analysis V2
with tab3:
    if hasattr(st.session_state, 'unified_data') and st.session_state.unified_data is not None:
        render_micro_analysis_v2_tab(st.session_state.unified_data)
    elif hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data is not None:
        render_micro_analysis_v2_tab(st.session_state.extracted_data)
    else:
        st.info("👆 Carregue arquivos na aba 'Upload' primeiro para ver a nova análise hierárquica.")

# Tab 4: AI Insights
with tab4:
    render_ai_insights_v2_tab(db, gemini_api_key, language)

# Tab 5: AI Chat
with tab5:
    render_ai_chat_v2_tab(db, gemini_api_key, language)

# Tab 6: Authentication Management
with tab6:
    render_auth_management_tab()

# Tab 7: Predictions
with tab7:
    if hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
        render_forecast_tab(db, st.session_state.extracted_data)
    else:
        st.info("👆 Carregue arquivos na aba 'Upload' primeiro para usar as previsões financeiras.")

# Tab 8: Integration (placeholder)
with tab8:
    st.header("⚡ Integração de Dados")
    st.info("🚧 Esta funcionalidade está em desenvolvimento...")
    st.markdown("""
    Em breve você poderá:
    - Conectar com sistemas ERP
    - Importar dados de APIs
    - Sincronizar com planilhas Google
    - Exportar relatórios automatizados
    """)

# Tab 9: Debug Extractors
with tab9:
    render_debug_extractors_tab()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Marine Seguros © 2024 | Financial Analytics Platform</p>
    </div>
    """,
    unsafe_allow_html=True
)