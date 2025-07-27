"""
Marine Seguros Financial Dashboard - Modular Version
Main entry point for the Streamlit application
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import core modules
from database_manager import DatabaseManager
from core.financial_processor import FinancialProcessor
from core.flexible_extractor import FlexibleFinancialExtractor

# Import modular components
from utils import format_currency, get_category_name
from ui.tabs.dashboard_tab import render_dashboard_tab
from ui.tabs.micro_analysis_tab import render_micro_analysis_tab

# Page configuration
st.set_page_config(
    page_title="Marine Seguros - Dashboard Financeiro",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state and database
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()

db = st.session_state.db_manager

# Main app function
def main():
    """Main application function"""
    
    # Sidebar configuration
    render_sidebar()
    
    # Load data from database
    load_persistent_data()
    
    # Main content area
    render_main_content()


def render_sidebar():
    """Render the sidebar with configuration options"""
    st.sidebar.title("⚙️ Configurações")
    
    # Language selection
    language = st.sidebar.selectbox(
        "🌐 Idioma / Language",
        ["Português", "English"],
        key="language"
    )
    
    # Data extractor selection
    use_flexible_extractor = st.sidebar.checkbox(
        "🔧 Usar Extrator Flexível",
        value=True,
        help="Usar o extrator flexível para análise detalhada de despesas"
    )
    
    # Gemini API key
    gemini_api_key = st.sidebar.text_input(
        "🤖 Gemini API Key (Opcional)",
        type="password",
        help="Para análises com IA"
    )
    
    # Store in session state
    st.session_state.language = language
    st.session_state.use_flexible_extractor = use_flexible_extractor
    st.session_state.gemini_api_key = gemini_api_key
    
    # Data management section
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Gestão de Dados")
    
    # Clear cache button
    if st.sidebar.button("🗑️ Limpar Cache"):
        clear_cache()
        st.rerun()
    
    # Data statistics
    stats = db.get_data_stats()
    if stats:
        st.sidebar.markdown("**Dados armazenados:**")
        st.sidebar.text(f"• {stats.get('financial_data', {}).get('count', 0)} anos")
        
        last_update = stats.get('financial_data', {}).get('last_update')
        if last_update:
            st.sidebar.text(f"• Última atualização: {last_update[:10]}")


def load_persistent_data():
    """Load data from database into session state"""
    try:
        # Load financial data
        if not hasattr(st.session_state, 'extracted_data') or not st.session_state.extracted_data:
            db.auto_load_state(st.session_state)
        
        # Process data if needed
        if hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
            if not hasattr(st.session_state, 'processed_data') or not st.session_state.processed_data:
                process_loaded_data()
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")


def process_loaded_data():
    """Process loaded data for dashboard use"""
    try:
        processor = FinancialProcessor()
        
        # Create mock excel_data structure from loaded data
        excel_data = {"loaded_data": st.session_state.extracted_data}
        
        if st.session_state.use_flexible_extractor:
            # Use flexible extractor
            consolidated_df, flexible_data = processor.consolidate_all_years_flexible(excel_data)
            st.session_state.flexible_data = flexible_data
        else:
            # Use standard processor
            consolidated_df, extracted_data = processor.consolidate_all_years(excel_data)
        
        # Store processed data
        st.session_state.processed_data = {
            'consolidated': consolidated_df,
            'summary': processor.get_financial_summary(consolidated_df) if not consolidated_df.empty else {}
        }
        
        # Process monthly data
        monthly_data = processor.get_monthly_data(excel_data)
        st.session_state.monthly_data = monthly_data
        
    except Exception as e:
        st.error(f"Erro ao processar dados: {str(e)}")


def render_main_content():
    """Render the main content area with tabs"""
    
    # Main title
    st.title("🏢 Marine Seguros - Dashboard Financeiro")
    
    # Create main tabs
    if st.session_state.use_flexible_extractor:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard Macro",
            "🔬 Análise Micro",
            "📁 Upload",
            "🤖 Insights IA",
            "💬 Chat IA"
        ])
    else:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Dashboard", 
            "📁 Upload",
            "🤖 Insights IA",
            "💬 Chat IA"
        ])
    
    # Dashboard Tab
    with tab1:
        render_dashboard_content()
    
    # Micro Analysis Tab (only for flexible extractor)
    if st.session_state.use_flexible_extractor:
        with tab2:
            render_micro_analysis_content()
        upload_tab = tab3
        ai_insights_tab = tab4
        ai_chat_tab = tab5
    else:
        upload_tab = tab2
        ai_insights_tab = tab3
        ai_chat_tab = tab4
    
    # Upload Tab
    with upload_tab:
        render_upload_tab()
    
    # AI Insights Tab
    with ai_insights_tab:
        render_ai_insights_tab()
    
    # AI Chat Tab
    with ai_chat_tab:
        render_ai_chat_tab()


def render_dashboard_content():
    """Render the dashboard tab content"""
    if not hasattr(st.session_state, 'processed_data') or not st.session_state.processed_data:
        st.info("👆 Carregue dados na aba 'Upload' primeiro.")
        return
    
    df = st.session_state.processed_data.get('consolidated', pd.DataFrame())
    monthly_data = getattr(st.session_state, 'monthly_data', None)
    
    render_dashboard_tab(df, monthly_data)


def render_upload_tab():
    """Render the upload tab"""
    st.header("📁 Upload de Arquivos")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Selecione os arquivos Excel com dados financeiros",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files:
        # Process uploaded files
        if st.button("🔄 Processar Arquivos", type="primary"):
            process_uploaded_files(uploaded_files)
    
    # Show current data status
    if hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
        st.success(f"✅ Dados carregados para {len(st.session_state.extracted_data)} anos")
        
        # Show years available
        years = sorted(st.session_state.extracted_data.keys())
        st.info(f"📅 Anos disponíveis: {', '.join(map(str, years))}")


def process_uploaded_files(uploaded_files):
    """Process uploaded Excel files"""
    try:
        with st.spinner("Processando arquivos..."):
            processor = FinancialProcessor()
            
            # Save files temporarily and process
            temp_files = {}
            for uploaded_file in uploaded_files:
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                temp_files[temp_path] = uploaded_file.name
            
            # Load and process files
            excel_data = processor.load_excel_files(list(temp_files.keys()))
            
            if st.session_state.use_flexible_extractor:
                # Use flexible extractor
                extractor = FlexibleFinancialExtractor()
                extracted_data = {}
                
                for file_path in temp_files.keys():
                    file_data = extractor.extract_from_excel(file_path)
                    if file_data:
                        extracted_data.update(file_data)
                
                st.session_state.extracted_data = extracted_data
                
                # Process with flexible data
                consolidated_df, flexible_data = processor.consolidate_all_years_flexible(excel_data)
                st.session_state.flexible_data = flexible_data
            else:
                # Use standard processor
                consolidated_df, extracted_data = processor.consolidate_all_years(excel_data)
                st.session_state.extracted_data = extracted_data
            
            # Store processed data
            st.session_state.processed_data = {
                'consolidated': consolidated_df,
                'summary': processor.get_financial_summary(consolidated_df) if not consolidated_df.empty else {}
            }
            
            # Process monthly data
            st.session_state.monthly_data = processor.get_monthly_data(excel_data)
            
            # Save to database
            db.auto_save_state(st.session_state)
            
            # Clean up temporary files
            for temp_path in temp_files.keys():
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            st.success("✅ Arquivos processados com sucesso!")
            st.rerun()
    
    except Exception as e:
        st.error(f"Erro ao processar arquivos: {str(e)}")


def render_micro_analysis_content():
    """Render the micro analysis tab content"""
    if not hasattr(st.session_state, 'flexible_data') or not st.session_state.flexible_data:
        st.info("📊 Carregue dados usando o extrator flexível para acessar a análise micro.")
        return
    
    render_micro_analysis_tab(st.session_state.flexible_data)


def render_ai_insights_tab():
    """Render the AI insights tab (placeholder)"""
    st.header("🤖 Insights com IA")
    st.info("🚧 Esta seção está sendo refatorada...")


def render_ai_chat_tab():
    """Render the AI chat tab (placeholder)"""
    st.header("💬 Chat com IA")
    st.info("🚧 Esta seção está sendo refatorada...")


def clear_cache():
    """Clear all cached data"""
    # Clear session state
    keys_to_keep = ['db_manager', 'language', 'use_flexible_extractor', 'gemini_api_key']
    keys_to_remove = [k for k in st.session_state.keys() if k not in keys_to_keep]
    
    for key in keys_to_remove:
        del st.session_state[key]
    
    # Clear database cache
    db.clear_session_data()
    
    st.success("Cache limpo com sucesso!")


if __name__ == "__main__":
    main()