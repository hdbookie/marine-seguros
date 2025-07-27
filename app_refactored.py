"""
Marine Seguros - Financial Analytics Dashboard
Refactored version using modular architecture
"""

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
from typing import Dict

# Import authentication
from auth import init_auth, require_auth, show_login_page, show_user_menu, show_admin_panel

# Import database manager
from database_manager import DatabaseManager

# Import utilities
from utils.legacy_helpers import (
    initialize_session_state,
    generate_monthly_data_from_extracted,
    convert_extracted_to_processed
)

# Import tab modules
from ui.tabs.upload_legacy_tab import render_upload_tab
from ui.tabs.dashboard_legacy_tab import render_dashboard_tab
from ui.tabs.micro_analysis_tab import render_micro_analysis_tab
from ui.tabs.ai_insights_legacy_tab import render_ai_insights_tab
from ui.tabs.ai_chat_legacy_tab import render_ai_chat_tab

# Load environment variables
load_dotenv()

# Initialize authentication
init_auth()

# Initialize database manager
db = DatabaseManager()

# Page configuration
st.set_page_config(
    page_title="Marine Seguros - Financial Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
if not require_auth():
    show_login_page()
    st.stop()

# Main app header
st.title("📊 Marine Seguros - Financial Analytics Dashboard")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # User menu
    show_user_menu()
    
    # Admin panel (if admin)
    if st.session_state.user and st.session_state.user.get('role') == 'admin':
        show_admin_panel()
    
    # API Key input
    gemini_api_key = st.text_input(
        "🔑 Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Get your API key from Google AI Studio"
    )
    
    # Settings
    st.subheader("🎛️ Settings")
    
    # Language selector
    language = st.selectbox(
        "🌐 Language / Idioma",
        ["Português", "English"],
        index=0
    )
    
    # Feature toggles
    use_flexible_extractor = st.checkbox(
        "🔍 Advanced Data Extraction",
        value=True,
        help="Enable flexible extraction for detailed analysis"
    )
    
    show_anomalies = st.checkbox(
        "⚠️ Show Anomalies",
        value=False,
        help="Highlight unusual patterns in data"
    )
    
    # About section
    st.markdown("---")
    st.markdown("### About")
    st.info("""
    **Marine Seguros Financial Analytics**  
    Version 3.0 - Refactored  
    
    Features:
    - 📊 Financial Dashboard
    - 🔬 Micro Analysis
    - 🤖 AI Insights
    - 💬 AI Chat Assistant
    """)

# Load state from database
data_loaded = db.auto_load_state(st.session_state)

# Convert extracted data to processed format if needed
if data_loaded and hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
    if not hasattr(st.session_state, 'processed_data') or st.session_state.processed_data is None:
        st.session_state.processed_data = convert_extracted_to_processed(st.session_state.extracted_data)
        
    # Generate monthly data from extracted data
    if not hasattr(st.session_state, 'monthly_data') or st.session_state.monthly_data is None:
        try:
            st.session_state.monthly_data = generate_monthly_data_from_extracted(st.session_state.extracted_data)
        except Exception as e:
            print(f"Error generating monthly data: {e}")
            import traceback
            traceback.print_exc()

# Initialize session state
initialize_session_state(db, data_loaded)

# Main content - Tabs
if use_flexible_extractor:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📁 Upload", 
        "📊 Dashboard Macro", 
        "🔬 Análise Micro", 
        "🤖 AI Insights", 
        "💬 AI Chat",
        "📈 Previsões", 
        "⚡ Integração"
    ])
else:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📁 Upload", 
        "📊 Dashboard", 
        "🤖 AI Insights", 
        "💬 AI Chat",
        "📈 Previsões", 
        "⚡ Integração"
    ])

# Tab 1: File Upload
with tab1:
    render_upload_tab(db, use_flexible_extractor, show_anomalies)

# Tab 2: Dashboard
with tab2:
    render_dashboard_tab(db, use_flexible_extractor)

# Tab 3: Detailed Breakdown (only for flexible mode)
if use_flexible_extractor:
    with tab3:
        if hasattr(st.session_state, 'flexible_data') and st.session_state.flexible_data is not None:
            render_micro_analysis_tab(st.session_state.flexible_data)
        else:
            st.info("👆 Carregue arquivos na aba 'Upload' primeiro.")

# Tab 3/4: AI Insights
tab_ai = tab4 if use_flexible_extractor else tab3
with tab_ai:
    render_ai_insights_tab(db, gemini_api_key, language)

# Tab 4/5: AI Chat
tab_chat = tab5 if use_flexible_extractor else tab4
with tab_chat:
    render_ai_chat_tab(gemini_api_key)

# Tab 5/6: Predictions (placeholder)
tab_predictions = tab6 if use_flexible_extractor else tab5
with tab_predictions:
    st.header("📈 Previsões Financeiras")
    st.info("🚧 Esta funcionalidade está em desenvolvimento...")
    st.markdown("""
    Em breve você poderá:
    - Prever receitas futuras
    - Estimar custos projetados
    - Simular cenários financeiros
    - Análise de tendências com ML
    """)

# Tab 6/7: Integration (placeholder)
tab_integration = tab7 if use_flexible_extractor else tab6
with tab_integration:
    st.header("⚡ Integração de Dados")
    st.info("🚧 Esta funcionalidade está em desenvolvimento...")
    st.markdown("""
    Em breve você poderá:
    - Conectar com sistemas ERP
    - Importar dados de APIs
    - Sincronizar com planilhas Google
    - Exportar relatórios automatizados
    """)

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