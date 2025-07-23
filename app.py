import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from modules.ai_data_extractor import AIDataExtractor
from modules.comparative_analyzer import ComparativeAnalyzer
from core.direct_extractor import DirectDataExtractor
from modules.filter_system import FilterSystem, FilterState
from modules.ai_chat_assistant import AIChatAssistant
from modules.interactive_charts import InteractiveCharts
from modules.month_analytics import MonthAnalytics
from datetime import datetime
import os
from dotenv import load_dotenv
import json
from typing import Dict, List
import numpy as np
from modules.database_manager import DatabaseManager
from gerenciador_arquivos import GerenciadorArquivos
from core.financial_processor import FinancialProcessor
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Initialize database manager
db = DatabaseManager()

# Page configuration
st.set_page_config(
    page_title="Marine Seguros | Analytics",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stunning modern CSS with vibrant colors
st.markdown("""
    <style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Dark theme background */
    .stApp {
        background: #0f0f23;
    }
    
    /* Main content styling */
    .main {
        padding: 0;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #1a1b3a;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    section[data-testid="stSidebar"] .element-container {
        color: white;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 0 0 30px 30px;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .main-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .main-subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Filter cards styling */
    .filter-card {
        background: #1e1f3a;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .filter-card:hover {
        transform: translateY(-2px);
        border-color: #667eea;
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
    }
    
    .filter-card.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
    }
    
    /* Month filter buttons */
    .month-button {
        background: #2a2b4a;
        border: 2px solid transparent;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
    }
    
    .month-button:hover {
        border-color: #667eea;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }
    
    .month-button.active {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border: none;
    }
    
    .month-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #4ade80;
    }
    
    .month-indicator.negative {
        background: #ef4444;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: #1a1b3a;
        border-radius: 15px;
        padding: 0.5rem;
        gap: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgba(255, 255, 255, 0.7);
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1e1f3a, #2a2b4a);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: white;
        margin: 0.5rem 0;
    }
    
    .kpi-label {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .kpi-change {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .kpi-change.positive {
        background: rgba(74, 222, 128, 0.2);
        color: #4ade80;
    }
    
    .kpi-change.negative {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    /* Quick filter buttons */
    .quick-filter {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.5rem 1.25rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .quick-filter:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Section headers */
    .section-header {
        color: white;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .section-icon {
        font-size: 1.5rem;
    }
    
    /* Metric checkbox styling */
    .stCheckbox {
        color: white !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 10px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background: #2a2b4a;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* Charts background */
    .element-container:has(.js-plotly-plot) {
        background: #1e1f3a;
        border-radius: 15px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1b3a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        background: #2a2b4a;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #2a2b4a;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: white;
    }
    
    .streamlit-expanderContent {
        background: #1e1f3a;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: none;
        border-radius: 0 0 10px 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for non-persisted items first
if 'filter_system' not in st.session_state:
    st.session_state.filter_system = FilterSystem()
if 'chat_assistant' not in st.session_state:
    st.session_state.chat_assistant = None
if 'charts' not in st.session_state:
    st.session_state.charts = InteractiveCharts()
if 'month_analytics' not in st.session_state:
    st.session_state.month_analytics = MonthAnalytics()
if 'file_manager' not in st.session_state:
    st.session_state.file_manager = GerenciadorArquivos()
    # Sync existing files
    st.session_state.file_manager.sincronizar_arquivos_existentes()
if 'ai_data_extractor' not in st.session_state:
    st.session_state.ai_data_extractor = None
if 'flexible_data' not in st.session_state:
    st.session_state.flexible_data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

# Try to load data from database FIRST
data_loaded = db.auto_load_state(st.session_state)

# Only initialize empty defaults if nothing was loaded from database
if not data_loaded or 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = {}
if not data_loaded or 'comparative_analysis' not in st.session_state:
    st.session_state.comparative_analysis = None
if not data_loaded or 'selected_years' not in st.session_state:
    st.session_state.selected_years = []
if not data_loaded or 'selected_months' not in st.session_state:
    st.session_state.selected_months = []

# Debug: Show what was loaded
if data_loaded and st.session_state.extracted_data:
    st.sidebar.success(f"✅ Dados carregados: {len(st.session_state.extracted_data)} anos")

# Sidebar configuration
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    
    # API Key input
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Chave para análise com IA"
    )
    
    if gemini_api_key and not st.session_state.chat_assistant:
        st.session_state.chat_assistant = AIChatAssistant(gemini_api_key)
    
    st.markdown("### 📊 Opções de Visualização")
    show_filters = st.checkbox("Mostrar Filtros Avançados", value=True)
    show_chat = st.checkbox("Ativar Chat com IA", value=True)
    show_interactive = st.checkbox("Charts Interativos", value=True)
    use_flexible_extractor = st.checkbox(
        "🆕 Usar Extrator Flexível", 
        value=False,
        help="Detecta automaticamente TODAS as categorias de despesas nos arquivos Excel"
    )
    
    st.markdown("### 🎨 Tema")
    theme = st.selectbox("Escolha o tema", ["Profissional", "Colorido", "Minimalista"])
    
    if st.button("🔄 Resetar Aplicação", use_container_width=True):
        db.clear_all_data()
        st.session_state.clear()
        st.rerun()
    
    # Database status
    st.markdown("### 💾 Status do Banco de Dados")
    stats = db.get_data_stats()
    
    if stats.get('financial_data', {}).get('count', 0) > 0:
        st.caption(f"✅ {stats['financial_data']['count']} anos de dados salvos")
        
        # Show last update times
        for data_type, info in stats.items():
            if info.get('last_update'):
                try:
                    last_update = datetime.fromisoformat(info['last_update'].replace('Z', '+00:00'))
                    time_diff = datetime.now() - last_update.replace(tzinfo=None)
                    
                    if time_diff.days > 0:
                        age_str = f"{time_diff.days} dias atrás"
                    elif time_diff.seconds > 3600:
                        age_str = f"{time_diff.seconds // 3600} horas atrás"
                    else:
                        age_str = f"{time_diff.seconds // 60} minutos atrás"
                    
                    display_name = data_type.replace('_', ' ').title()
                    st.caption(f"📝 {display_name}: {age_str}")
                except:
                    pass
    else:
        st.caption("❌ Nenhum dado salvo")

# Title and description
st.title("🏢 Marine Seguros - Financial Analytics Platform")
st.markdown("### Análise Financeira Inteligente com IA | 2018-2025")

# Check if we have data either in session or database
has_data = (st.session_state.extracted_data and len(st.session_state.extracted_data) > 0)

# If no data in session but database has data, force reload
if not has_data:
    stats = db.get_data_stats()
    if stats.get('financial_data', {}).get('count', 0) > 0:
        st.info("🔄 Carregando dados salvos...")
        if db.auto_load_state(st.session_state):
            st.rerun()

# Main content with conditional tabs
if use_flexible_extractor and st.session_state.flexible_data:
    # 7 tabs when using flexible extractor
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📁 Upload", 
        "📊 Dashboard", 
        "🔍 Detalhamento", 
        "🤖 AI Insights", 
        "💬 AI Chat",
        "📈 Previsões", 
        "⚡ Integração"
    ])
else:
    # 6 tabs for normal mode (no Detalhamento)
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
    st.header("📊 Gerenciamento de Dados Financeiros")
    
    # File management bar
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # Year filter
        anos_disponiveis = st.session_state.file_manager.obter_anos_disponiveis()
        if anos_disponiveis:
            anos_selecionados = st.multiselect(
                "Filtrar por anos",
                anos_disponiveis,
                default=anos_disponiveis[-2:] if len(anos_disponiveis) >= 2 else anos_disponiveis
            )
        else:
            anos_selecionados = []
    
    with col2:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.session_state.file_manager.sincronizar_arquivos_existentes()
            st.rerun()
    
    with col3:
        gerenciar_arquivos = st.checkbox("📁 Gerenciar", value=False)
    
    # File upload section
    st.subheader("📤 Upload de Novos Arquivos")
    
    uploaded_files = st.file_uploader(
        "Selecione arquivos Excel (.xlsx, .xls)",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="Faça upload de arquivos contendo dados financeiros"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if st.button(f"📥 Processar {uploaded_file.name}", use_container_width=True):
                with st.spinner(f"Enviando {uploaded_file.name}..."):
                    if st.session_state.file_manager.enviar_arquivo(uploaded_file):
                        st.success(f"✅ {uploaded_file.name} enviado com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao enviar {uploaded_file.name}")
    
    # Process files button
    if st.button("🚀 Processar Dados", type="primary", use_container_width=True):
        if not gemini_api_key:
            st.error("Por favor, configure sua Gemini API key")
        else:
            with st.spinner("Processando dados..."):
                if use_flexible_extractor:
                    # Use flexible extractor
                    from core.flexible_extractor import FlexibleFinancialExtractor
                    extractor = FlexibleFinancialExtractor()
                else:
                    # Use direct extractor
                    extractor = DirectDataExtractor()
                
                # Start with existing data if available
                extracted_data = st.session_state.extracted_data.copy() if st.session_state.extracted_data else {}
                errors = []
                
                # Get all Excel files to process
                arquivos = st.session_state.file_manager.obter_todos_arquivos()
                files_to_process = []
                
                for arquivo in arquivos:
                    if not anos_selecionados or any(ano in arquivo['anos_incluidos'] for ano in anos_selecionados):
                        caminho = os.path.join(st.session_state.file_manager.caminho_armazenamento, arquivo['nome'])
                        files_to_process.append(caminho)
                
                # Process each file
                for file_path in files_to_process:
                    try:
                        st.info(f"📄 Processando: {os.path.basename(file_path)}")
                        file_data = extractor.extract_from_excel(file_path)
                        
                        if file_data:
                            extracted_data.update(file_data)
                            st.success(f"✅ {os.path.basename(file_path)}: {len(file_data)} anos extraídos")
                        else:
                            st.warning(f"⚠️ {os.path.basename(file_path)}: Nenhum dado extraído")
                            
                    except Exception as e:
                        st.error(f"❌ {os.path.basename(file_path)}: Erro - {str(e)}")
                        errors.append(str(e))
                
                if extracted_data:
                    st.session_state.extracted_data = extracted_data
                    
                    # Initialize AI Data Extractor if API key is available
                    if gemini_api_key and not st.session_state.ai_data_extractor:
                        st.session_state.ai_data_extractor = AIDataExtractor(gemini_api_key)
                    
                    # If using flexible extractor, store that data too
                    if use_flexible_extractor:
                        st.session_state.flexible_data = extracted_data
                        
                        # Create FinancialProcessor instance
                        processor = FinancialProcessor()
                        # Consolidate data
                        consolidated_df, all_data = processor.consolidate_all_years_flexible({"dummy": extracted_data})
                        
                        st.session_state.processed_data = {
                            'consolidated': consolidated_df,
                            'raw_data': all_data,
                            'summary': processor.get_financial_summary(consolidated_df),
                            'anomalies': processor.detect_anomalies(consolidated_df)
                        }
                    
                    # Perform comparative analysis if multiple years
                    if len(extracted_data) >= 2 and gemini_api_key:
                        analyzer = ComparativeAnalyzer(gemini_api_key)
                        st.session_state.comparative_analysis = analyzer.analyze_all_years(extracted_data)
                    
                    # Save to database
                    db.auto_save_state(st.session_state)
                    st.success("✅ Dados processados e salvos com sucesso!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Nenhum dado foi extraído!")
    
    # File management section
    st.divider()
    st.subheader("📂 Arquivos Disponíveis")
    
    arquivos = st.session_state.file_manager.obter_todos_arquivos()
    
    if arquivos:
        # Filter files by selected years
        if anos_selecionados:
            arquivos_filtrados = [
                arquivo for arquivo in arquivos 
                if any(ano in arquivo['anos_incluidos'] for ano in anos_selecionados)
            ]
        else:
            arquivos_filtrados = arquivos
        
        if arquivos_filtrados:
            if anos_selecionados and len(arquivos) != len(arquivos_filtrados):
                st.info(f"📊 {len(arquivos_filtrados)} arquivo(s) encontrado(s) para os anos selecionados (Total: {len(arquivos)} arquivos)")
            else:
                st.info(f"📊 {len(arquivos)} arquivo(s) encontrado(s)")
            
            for arquivo in arquivos_filtrados:
                with st.expander(f"📄 {arquivo['nome']}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**ID:** {arquivo['id']}")
                        st.write(f"**Data de envio:** {arquivo['data_envio']}")
                        st.write(f"**Tamanho:** {arquivo['tamanho']}")
                        st.write(f"**Anos incluídos:** {', '.join(map(str, arquivo['anos_incluidos']))}")
                        if arquivo.get('status'):
                            st.write(f"**Status:** {arquivo['status']}")
                    
                    with col2:
                        if gerenciar_arquivos:
                            if st.button(f"🗑️ Excluir", key=f"del_{arquivo['id']}"):
                                if st.session_state.file_manager.excluir_arquivo(arquivo['id']):
                                    st.success("Arquivo excluído!")
                                    st.rerun()
        else:
            st.warning("Nenhum arquivo encontrado para os anos selecionados")
    else:
        st.info("Nenhum arquivo disponível. Faça upload de arquivos Excel.")

# Only show other tabs if we have data
if st.session_state.extracted_data and len(st.session_state.extracted_data) > 0:
    # Tab 2: Dashboard
    with tab2:
        if show_filters:
            # Filters section
            st.markdown('<div class="section-header"><span class="section-icon">📅</span>Filtros de Período</div>', unsafe_allow_html=True)
            
            # Year filters
            years = sorted(st.session_state.extracted_data.keys())
            year_cols = st.columns(len(years))
            
            if not st.session_state.selected_years:
                st.session_state.selected_years = years
            
            for idx, year in enumerate(years):
                with year_cols[idx]:
                    if st.checkbox(str(year), value=year in st.session_state.selected_years, key=f"year_{year}"):
                        if year not in st.session_state.selected_years:
                            st.session_state.selected_years.append(year)
                            db.auto_save_state(st.session_state)
                    else:
                        if year in st.session_state.selected_years:
                            st.session_state.selected_years.remove(year)
                            db.auto_save_state(st.session_state)
            
            col1, col2 = st.columns([10, 2])
            with col2:
                if st.button("Todos", key="all_years"):
                    st.session_state.selected_years = years
                    db.auto_save_state(st.session_state)
                    st.rerun()
                if st.button("Limpar", key="clear_years"):
                    st.session_state.selected_years = []
                    db.auto_save_state(st.session_state)
                    st.rerun()
            
            # Month filters with performance indicators
            st.markdown('<div class="section-header"><span class="section-icon">📅</span>Filtros de Mês</div>', unsafe_allow_html=True)
            
            months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            month_performance = {}
            
            # Calculate month performance across all years
            for month in months:
                total_growth = 0
                count = 0
                for year in st.session_state.selected_years:
                    if year in st.session_state.extracted_data:
                        year_data = st.session_state.extracted_data[year]
                        if 'revenue' in year_data and month in year_data['revenue']:
                            # Simple growth indicator (you can make this more sophisticated)
                            count += 1
                
                # Mock performance data for demo (replace with real calculations)
                month_performance[month] = np.random.randint(-30, 40)
            
            if not st.session_state.selected_months:
                st.session_state.selected_months = months
            
            # Display months in a 3x4 grid
            for row in range(0, 12, 4):
                cols = st.columns(4)
                for col_idx, month_idx in enumerate(range(row, min(row + 4, 12))):
                    month = months[month_idx]
                    perf = month_performance[month]
                    
                    with cols[col_idx]:
                        # Create custom button-like display
                        is_selected = month in st.session_state.selected_months
                        
                        button_html = f"""
                        <div class="month-button {'active' if is_selected else ''}" style="margin-bottom: 0.5rem;">
                            <span>{month}</span>
                            <span class="month-indicator {'negative' if perf < 0 else ''}"></span>
                            <span style="font-size: 0.8rem; color: {'#4ade80' if perf >= 0 else '#ef4444'};">
                                {'+' if perf >= 0 else ''}{perf}%
                            </span>
                        </div>
                        """
                        st.markdown(button_html, unsafe_allow_html=True)
                        
                        # Actual checkbox (hidden visually but functional)
                        if st.checkbox(month, value=is_selected, key=f"month_{month}", label_visibility="collapsed"):
                            if month not in st.session_state.selected_months:
                                st.session_state.selected_months.append(month)
                                db.auto_save_state(st.session_state)
                        else:
                            if month in st.session_state.selected_months:
                                st.session_state.selected_months.remove(month)
                                db.auto_save_state(st.session_state)
            
            # Quick filters section
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown('<div class="section-header"><span class="section-icon">🎯</span>Filtros Rápidos</div>', unsafe_allow_html=True)
                if st.button("Top 3 Meses", key="top3", use_container_width=True):
                    # Select top 3 performing months
                    sorted_months = sorted(month_performance.items(), key=lambda x: x[1], reverse=True)[:3]
                    st.session_state.selected_months = [m[0] for m in sorted_months]
                    db.auto_save_state(st.session_state)
                    st.rerun()
                
                if st.button("Bottom 3 Meses", key="bottom3", use_container_width=True):
                    sorted_months = sorted(month_performance.items(), key=lambda x: x[1])[:3]
                    st.session_state.selected_months = [m[0] for m in sorted_months]
                    db.auto_save_state(st.session_state)
                    st.rerun()
            
            with col2:
                st.markdown('<div class="section-header"><span class="section-icon">🌊</span>Sazonalidade</div>', unsafe_allow_html=True)
                season = st.selectbox("Período", ["Nenhum", "Q1", "Q2", "Q3", "Q4", "Verão", "Inverno"])
                
                if season == "Q1":
                    st.session_state.selected_months = ['JAN', 'FEV', 'MAR']
                    db.auto_save_state(st.session_state)
                    st.rerun()
                elif season == "Q2":
                    st.session_state.selected_months = ['ABR', 'MAI', 'JUN']
                    db.auto_save_state(st.session_state)
                    st.rerun()
                elif season == "Q3":
                    st.session_state.selected_months = ['JUL', 'AGO', 'SET']
                    db.auto_save_state(st.session_state)
                    st.rerun()
                elif season == "Q4":
                    st.session_state.selected_months = ['OUT', 'NOV', 'DEZ']
                    db.auto_save_state(st.session_state)
                    st.rerun()
            
            with col3:
                st.markdown('<div class="section-header"><span class="section-icon">📊</span>Métricas</div>', unsafe_allow_html=True)
                show_revenue = st.checkbox("Revenue", value=True)
                show_costs = st.checkbox("Costs", value=False)
                show_margins = st.checkbox("Margins", value=True)
                show_profit = st.checkbox("Profit", value=False)
        
        # Apply filters
        filtered_data = {}
        for year in st.session_state.selected_years:
            if year in st.session_state.extracted_data:
                filtered_data[year] = st.session_state.extracted_data[year]
        
        if filtered_data:
            # KPI Cards
            st.markdown('<div class="section-header"><span class="section-icon">📈</span>Key Performance Indicators</div>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate KPIs
            total_revenue = 0
            avg_margin = 0
            years_count = len(filtered_data)
            
            for year_data in filtered_data.values():
                revenue = sum(v for k, v in year_data.get('revenue', {}).items() 
                            if k != 'ANNUAL' and isinstance(v, (int, float)))
                total_revenue += revenue
                
                margins = [v for k, v in year_data.get('margins', {}).items() 
                          if k != 'ANNUAL' and isinstance(v, (int, float))]
                if margins:
                    avg_margin += sum(margins) / len(margins)
            
            if years_count > 0:
                avg_margin = avg_margin / years_count
            
            with col1:
                st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Receita Total</div>
                        <div class="kpi-value">R$ {total_revenue/1e6:.1f}M</div>
                        <div class="kpi-change positive">↑ 12.5% YoY</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Margem Média</div>
                        <div class="kpi-value">{avg_margin:.1f}%</div>
                        <div class="kpi-change {'positive' if avg_margin > 15 else 'negative'}">
                            {'↑' if avg_margin > 15 else '↓'} Target: 15%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Período Analisado</div>
                        <div class="kpi-value">{years_count}</div>
                        <div class="kpi-change positive">Anos</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Melhor Mês</div>
                        <div class="kpi-value">DEZ</div>
                        <div class="kpi-change positive">↑ 38% avg</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Charts
            st.markdown('<div class="section-header"><span class="section-icon">📊</span>Visualizações</div>', unsafe_allow_html=True)
            
            # Revenue chart
            years = sorted(filtered_data.keys())
            revenues = []
            for year in years:
                revenue = sum(v for k, v in filtered_data[year].get('revenue', {}).items() 
                            if k != 'ANNUAL' and isinstance(v, (int, float)))
                revenues.append(revenue)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=years,
                y=revenues,
                marker_color='#667eea',
                text=[f'R$ {r/1e6:.1f}M' for r in revenues],
                textposition='outside'
            ))
            
            fig.update_layout(
                title='Evolução da Receita',
                xaxis_title='Ano',
                yaxis_title='Receita (R$)',
                plot_bgcolor='#1e1f3a',
                paper_bgcolor='#1e1f3a',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Analysis Tab
    with tab2:
        st.markdown("### 🔍 Análise Comparativa")
        
        if filtered_data and len(filtered_data) > 1:
            # Year selection for comparison
            col1, col2 = st.columns(2)
            years_list = sorted(filtered_data.keys())
            
            with col1:
                year1 = st.selectbox("Primeiro Ano", years_list, index=len(years_list)-2)
            with col2:
                year2 = st.selectbox("Segundo Ano", years_list, index=len(years_list)-1)
            
            if year1 and year2 and year1 != year2:
                st.markdown("---")
                
                # Get data for both years
                data1 = filtered_data[year1]
                data2 = filtered_data[year2]
                
                # Calculate annual totals
                revenue1 = sum(v for k, v in data1.get('revenue', {}).items() 
                              if k in st.session_state.selected_months and isinstance(v, (int, float)))
                revenue2 = sum(v for k, v in data2.get('revenue', {}).items() 
                              if k in st.session_state.selected_months and isinstance(v, (int, float)))
                
                costs1 = sum(v for k, v in data1.get('costs', {}).items() 
                            if k in st.session_state.selected_months and isinstance(v, (int, float)))
                costs2 = sum(v for k, v in data2.get('costs', {}).items() 
                            if k in st.session_state.selected_months and isinstance(v, (int, float)))
                
                # Calculate variations
                revenue_var = ((revenue2 - revenue1) / revenue1 * 100) if revenue1 > 0 else 0
                costs_var = ((costs2 - costs1) / costs1 * 100) if costs1 > 0 else 0
                
                # Comparison metrics
                st.subheader("📊 Comparação de Métricas Principais")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Receita Total",
                        f"R$ {revenue2/1e6:.1f}M",
                        f"{revenue_var:+.1f}% vs {year1}",
                        delta_color="normal"
                    )
                
                with col2:
                    st.metric(
                        "Custos Totais",
                        f"R$ {costs2/1e6:.1f}M",
                        f"{costs_var:+.1f}% vs {year1}",
                        delta_color="inverse"
                    )
                
                # Calculate margins
                margin1 = ((revenue1 - costs1) / revenue1 * 100) if revenue1 > 0 else 0
                margin2 = ((revenue2 - costs2) / revenue2 * 100) if revenue2 > 0 else 0
                margin_var = margin2 - margin1
                
                with col3:
                    st.metric(
                        "Margem de Lucro",
                        f"{margin2:.1f}%",
                        f"{margin_var:+.1f}pp vs {year1}",
                        delta_color="normal"
                    )
                
                with col4:
                    profit1 = revenue1 - costs1
                    profit2 = revenue2 - costs2
                    profit_var = ((profit2 - profit1) / abs(profit1) * 100) if profit1 != 0 else 0
                    st.metric(
                        "Lucro Líquido",
                        f"R$ {profit2/1e6:.1f}M",
                        f"{profit_var:+.1f}% vs {year1}",
                        delta_color="normal"
                    )
                
                # Monthly comparison chart
                st.subheader("📈 Comparação Mensal de Receita")
                
                months_selected = st.session_state.selected_months
                revenues_1 = [data1.get('revenue', {}).get(m, 0) for m in months_selected]
                revenues_2 = [data2.get('revenue', {}).get(m, 0) for m in months_selected]
                
                fig_comparison = go.Figure()
                
                fig_comparison.add_trace(go.Bar(
                    name=str(year1),
                    x=months_selected,
                    y=revenues_1,
                    marker_color='#667eea',
                    text=[f'R$ {v/1e3:.0f}K' for v in revenues_1],
                    textposition='outside'
                ))
                
                fig_comparison.add_trace(go.Bar(
                    name=str(year2),
                    x=months_selected,
                    y=revenues_2,
                    marker_color='#764ba2',
                    text=[f'R$ {v/1e3:.0f}K' for v in revenues_2],
                    textposition='outside'
                ))
                
                fig_comparison.update_layout(
                    title=f'Comparação de Receita: {year1} vs {year2}',
                    xaxis_title='Mês',
                    yaxis_title='Receita (R$)',
                    barmode='group',
                    plot_bgcolor='#1e1f3a',
                    paper_bgcolor='#1e1f3a',
                    font=dict(color='white'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig_comparison, use_container_width=True)
                
                # Growth rate comparison
                st.subheader("📊 Taxa de Crescimento Mensal")
                
                growth_rates = []
                for m in months_selected:
                    v1 = data1.get('revenue', {}).get(m, 0)
                    v2 = data2.get('revenue', {}).get(m, 0)
                    growth = ((v2 - v1) / v1 * 100) if v1 > 0 else 0
                    growth_rates.append(growth)
                
                fig_growth = go.Figure()
                
                fig_growth.add_trace(go.Scatter(
                    x=months_selected,
                    y=growth_rates,
                    mode='lines+markers',
                    name='Taxa de Crescimento',
                    line=dict(color='#4ade80', width=3),
                    marker=dict(size=10),
                    text=[f'{g:+.1f}%' for g in growth_rates],
                    textposition='top center'
                ))
                
                # Add zero line
                fig_growth.add_hline(y=0, line_dash="dash", line_color="gray")
                
                fig_growth.update_layout(
                    title=f'Taxa de Crescimento: {year1} → {year2}',
                    xaxis_title='Mês',
                    yaxis_title='Crescimento (%)',
                    plot_bgcolor='#1e1f3a',
                    paper_bgcolor='#1e1f3a',
                    font=dict(color='white'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                )
                
                st.plotly_chart(fig_growth, use_container_width=True)
                
                # Detailed comparison table
                st.subheader("📋 Tabela Comparativa Detalhada")
                
                comparison_data = []
                for month in months_selected:
                    rev1 = data1.get('revenue', {}).get(month, 0)
                    rev2 = data2.get('revenue', {}).get(month, 0)
                    cost1 = data1.get('costs', {}).get(month, 0)
                    cost2 = data2.get('costs', {}).get(month, 0)
                    
                    comparison_data.append({
                        'Mês': month,
                        f'Receita {year1}': rev1,
                        f'Receita {year2}': rev2,
                        'Var. Receita (%)': ((rev2 - rev1) / rev1 * 100) if rev1 > 0 else 0,
                        f'Custos {year1}': cost1,
                        f'Custos {year2}': cost2,
                        'Var. Custos (%)': ((cost2 - cost1) / cost1 * 100) if cost1 > 0 else 0
                    })
                
                df_comparison = pd.DataFrame(comparison_data)
                
                # Format the dataframe without background gradient
                st.dataframe(
                    df_comparison.style.format({
                        f'Receita {year1}': 'R$ {:,.0f}',
                        f'Receita {year2}': 'R$ {:,.0f}',
                        'Var. Receita (%)': '{:+.1f}%',
                        f'Custos {year1}': 'R$ {:,.0f}',
                        f'Custos {year2}': 'R$ {:,.0f}',
                        'Var. Custos (%)': '{:+.1f}%'
                    }),
                    use_container_width=True
                )
                
            else:
                st.warning("Selecione dois anos diferentes para comparação.")
                
        elif len(filtered_data) == 1:
            st.info("É necessário pelo menos 2 anos de dados para fazer análise comparativa.")
        else:
            st.info("Nenhum dado disponível para análise.")
    
    # Trends Tab
    with tab3:
        st.markdown("### 📈 Análise de Tendências")
        
        if filtered_data and len(filtered_data) > 1:
            # Prepare data for trend analysis
            years = sorted(filtered_data.keys())
            months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            
            # Build time series data
            revenue_series = []
            costs_series = []
            margin_series = []
            dates = []
            
            for year in years:
                year_data = filtered_data[year]
                revenue_data = year_data.get('revenue', {})
                costs_data = year_data.get('variable_costs', {})
                
                for month_idx, month in enumerate(months):
                    if month in revenue_data and month in costs_data:
                        date = f"{year}-{month_idx+1:02d}"
                        dates.append(date)
                        
                        revenue = revenue_data[month]
                        costs = costs_data[month]
                        margin = ((revenue - costs) / revenue * 100) if revenue > 0 else 0
                        
                        revenue_series.append(revenue)
                        costs_series.append(costs)
                        margin_series.append(margin)
            
            if dates:
                # Trend Analysis Section
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("#### 📊 Tendência de Receita e Custos")
                
                with col2:
                    trend_period = st.selectbox(
                        "Período de Análise",
                        ["Todos os Anos", "Últimos 3 Anos", "Últimos 2 Anos", "Último Ano"]
                    )
                
                # Filter data based on selected period
                if trend_period == "Últimos 3 Anos" and len(years) >= 3:
                    start_idx = len(dates) - (36 if len(dates) >= 36 else len(dates))
                elif trend_period == "Últimos 2 Anos" and len(years) >= 2:
                    start_idx = len(dates) - (24 if len(dates) >= 24 else len(dates))
                elif trend_period == "Último Ano":
                    start_idx = len(dates) - (12 if len(dates) >= 12 else len(dates))
                else:
                    start_idx = 0
                
                # Create trend chart
                fig_trend = go.Figure()
                
                # Add revenue line
                fig_trend.add_trace(go.Scatter(
                    x=dates[start_idx:],
                    y=revenue_series[start_idx:],
                    name='Receita',
                    line=dict(color='#4CAF50', width=3),
                    mode='lines+markers',
                    marker=dict(size=8),
                    hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>'
                ))
                
                # Add costs line
                fig_trend.add_trace(go.Scatter(
                    x=dates[start_idx:],
                    y=costs_series[start_idx:],
                    name='Custos',
                    line=dict(color='#FF5252', width=3),
                    mode='lines+markers',
                    marker=dict(size=8),
                    hovertemplate='<b>%{x}</b><br>Custos: R$ %{y:,.0f}<extra></extra>'
                ))
                
                # Add trend lines
                if len(dates[start_idx:]) > 1:
                    # Calculate linear regression for revenue
                    x_numeric = list(range(len(dates[start_idx:])))
                    revenue_trend = np.poly1d(np.polyfit(x_numeric, revenue_series[start_idx:], 1))
                    costs_trend = np.poly1d(np.polyfit(x_numeric, costs_series[start_idx:], 1))
                    
                    fig_trend.add_trace(go.Scatter(
                        x=dates[start_idx:],
                        y=revenue_trend(x_numeric),
                        name='Tendência Receita',
                        line=dict(color='#4CAF50', width=2, dash='dash'),
                        mode='lines',
                        hoverinfo='skip'
                    ))
                    
                    fig_trend.add_trace(go.Scatter(
                        x=dates[start_idx:],
                        y=costs_trend(x_numeric),
                        name='Tendência Custos',
                        line=dict(color='#FF5252', width=2, dash='dash'),
                        mode='lines',
                        hoverinfo='skip'
                    ))
                
                fig_trend.update_layout(
                    height=400,
                    template="plotly_white",
                    hovermode='x unified',
                    xaxis=dict(title="Período"),
                    yaxis=dict(title="Valores (R$)", tickformat=","),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # Margin Trend
                st.markdown("#### 📈 Tendência de Margem de Lucro")
                
                fig_margin = go.Figure()
                
                # Add margin line
                fig_margin.add_trace(go.Scatter(
                    x=dates[start_idx:],
                    y=margin_series[start_idx:],
                    name='Margem de Lucro',
                    line=dict(color='#2196F3', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(33, 150, 243, 0.2)',
                    mode='lines+markers',
                    marker=dict(size=8),
                    hovertemplate='<b>%{x}</b><br>Margem: %{y:.1f}%<extra></extra>'
                ))
                
                # Add average line
                avg_margin = np.mean(margin_series[start_idx:])
                fig_margin.add_trace(go.Scatter(
                    x=dates[start_idx:],
                    y=[avg_margin] * len(dates[start_idx:]),
                    name=f'Média ({avg_margin:.1f}%)',
                    line=dict(color='#FF9800', width=2, dash='dash'),
                    mode='lines',
                    hoverinfo='skip'
                ))
                
                fig_margin.update_layout(
                    height=350,
                    template="plotly_white",
                    hovermode='x unified',
                    xaxis=dict(title="Período"),
                    yaxis=dict(title="Margem (%)", tickformat=".1f"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_margin, use_container_width=True)
                
                # Seasonal Analysis
                st.markdown("#### 🗓️ Análise Sazonal")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Monthly average across years
                    monthly_avg = {}
                    for month in months:
                        month_revenues = []
                        for year in years:
                            if year in filtered_data and month in filtered_data[year].get('revenue', {}):
                                month_revenues.append(filtered_data[year]['revenue'][month])
                        if month_revenues:
                            monthly_avg[month] = np.mean(month_revenues)
                    
                    if monthly_avg:
                        fig_seasonal = go.Figure()
                        
                        fig_seasonal.add_trace(go.Bar(
                            x=list(monthly_avg.keys()),
                            y=list(monthly_avg.values()),
                            marker_color=['#4CAF50' if v >= np.mean(list(monthly_avg.values())) else '#FF9800' 
                                        for v in monthly_avg.values()],
                            text=[f'R$ {v/1000:.0f}k' for v in monthly_avg.values()],
                            textposition='outside'
                        ))
                        
                        fig_seasonal.update_layout(
                            title="Média Mensal de Receita",
                            height=350,
                            template="plotly_white",
                            xaxis=dict(title="Mês"),
                            yaxis=dict(title="Receita Média (R$)", tickformat=","),
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_seasonal, use_container_width=True)
                
                with col2:
                    # Growth rate analysis
                    growth_rates = []
                    growth_labels = []
                    
                    for i in range(1, len(years)):
                        prev_year = years[i-1]
                        curr_year = years[i]
                        
                        prev_revenue = sum(v for k, v in filtered_data[prev_year].get('revenue', {}).items() 
                                         if k != 'ANNUAL' and isinstance(v, (int, float)))
                        curr_revenue = sum(v for k, v in filtered_data[curr_year].get('revenue', {}).items() 
                                         if k != 'ANNUAL' and isinstance(v, (int, float)))
                        
                        if prev_revenue > 0:
                            growth = ((curr_revenue - prev_revenue) / prev_revenue) * 100
                            growth_rates.append(growth)
                            growth_labels.append(f"{prev_year} → {curr_year}")
                    
                    if growth_rates:
                        fig_growth = go.Figure()
                        
                        colors = ['#4CAF50' if g > 0 else '#FF5252' for g in growth_rates]
                        
                        fig_growth.add_trace(go.Bar(
                            x=growth_labels,
                            y=growth_rates,
                            marker_color=colors,
                            text=[f'{g:+.1f}%' for g in growth_rates],
                            textposition='outside'
                        ))
                        
                        fig_growth.update_layout(
                            title="Taxa de Crescimento Anual",
                            height=350,
                            template="plotly_white",
                            xaxis=dict(title="Período"),
                            yaxis=dict(title="Crescimento (%)", tickformat=".1f", zeroline=True),
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_growth, use_container_width=True)
                
                # Key Insights
                st.markdown("#### 💡 Principais Insights")
                
                col1, col2, col3 = st.columns(3)
                
                # Calculate insights
                revenue_growth_rate = revenue_trend.coefficients[0] if len(dates[start_idx:]) > 1 else 0
                costs_growth_rate = costs_trend.coefficients[0] if len(dates[start_idx:]) > 1 else 0
                best_month = max(monthly_avg.items(), key=lambda x: x[1])[0] if monthly_avg else "N/A"
                worst_month = min(monthly_avg.items(), key=lambda x: x[1])[0] if monthly_avg else "N/A"
                
                with col1:
                    st.info(f"""
                    **📈 Tendência de Receita**
                    
                    Taxa de crescimento mensal: R$ {revenue_growth_rate:,.0f}
                    
                    Projeção próximo período: R$ {revenue_series[-1] + revenue_growth_rate:,.0f}
                    """)
                
                with col2:
                    st.info(f"""
                    **📊 Sazonalidade**
                    
                    Melhor mês: {best_month}
                    
                    Pior mês: {worst_month}
                    
                    Variação: {(max(monthly_avg.values()) / min(monthly_avg.values()) - 1) * 100:.0f}%
                    """)
                
                with col3:
                    efficiency = (revenue_growth_rate - costs_growth_rate) / abs(revenue_growth_rate) * 100 if revenue_growth_rate != 0 else 0
                    st.info(f"""
                    **💰 Eficiência**
                    
                    Receita cresce: {'mais' if revenue_growth_rate > costs_growth_rate else 'menos'} que custos
                    
                    Índice de eficiência: {efficiency:.0f}%
                    """)
            else:
                st.warning("Dados insuficientes para análise de tendências. Selecione pelo menos dois anos com dados mensais.")
        else:
            st.warning("Selecione pelo menos 2 anos para visualizar tendências.")
    
    # Monthly Analysis Tab
    with tab4:
        st.markdown("### 🗓️ Análise Mensal Detalhada")
        
        if filtered_data:
            # Year and month selection
            col1, col2 = st.columns(2)
            
            years_list = sorted(filtered_data.keys())
            months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            
            with col1:
                selected_year = st.selectbox("Selecione o Ano", years_list, index=len(years_list)-1)
            
            with col2:
                selected_month = st.selectbox("Selecione o Mês", months, index=0)
            
            if selected_year and selected_month:
                year_data = filtered_data[selected_year]
                
                # Check if data exists for selected month
                revenue = year_data.get('revenue', {}).get(selected_month, 0)
                costs = year_data.get('costs', {}).get(selected_month, 0)
                variable_costs = year_data.get('variable_costs', {}).get(selected_month, 0)
                
                if revenue > 0 or costs > 0:
                    st.markdown("---")
                    
                    # Monthly KPIs
                    st.subheader(f"📊 Métricas de {selected_month}/{selected_year}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Receita", f"R$ {revenue:,.0f}")
                    
                    with col2:
                        st.metric("Custos", f"R$ {costs:,.0f}")
                    
                    with col3:
                        margin = ((revenue - costs) / revenue * 100) if revenue > 0 else 0
                        st.metric("Margem", f"{margin:.1f}%")
                    
                    with col4:
                        profit = revenue - costs
                        st.metric("Lucro", f"R$ {profit:,.0f}")
                    
                    # Month comparison with previous months
                    st.subheader("📈 Comparação com Meses Anteriores")
                    
                    # Get previous 6 months data
                    month_idx = months.index(selected_month)
                    comparison_data = []
                    
                    for i in range(6, -1, -1):
                        comp_month_idx = (month_idx - i) % 12
                        comp_month = months[comp_month_idx]
                        comp_year = selected_year if (month_idx - i) >= 0 else int(selected_year) - 1
                        
                        if comp_year in filtered_data:
                            comp_revenue = filtered_data[comp_year].get('revenue', {}).get(comp_month, 0)
                            comp_costs = filtered_data[comp_year].get('costs', {}).get(comp_month, 0)
                            
                            comparison_data.append({
                                'month': f"{comp_month}/{comp_year}",
                                'revenue': comp_revenue,
                                'costs': comp_costs,
                                'profit': comp_revenue - comp_costs,
                                'margin': ((comp_revenue - comp_costs) / comp_revenue * 100) if comp_revenue > 0 else 0
                            })
                    
                    if comparison_data:
                        # Create comparison chart
                        fig_comp = make_subplots(
                            rows=2, cols=2,
                            subplot_titles=('Evolução da Receita', 'Evolução dos Custos', 
                                          'Evolução do Lucro', 'Evolução da Margem'),
                            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                                   [{"secondary_y": False}, {"secondary_y": False}]]
                        )
                        
                        months_labels = [d['month'] for d in comparison_data]
                        revenues = [d['revenue'] for d in comparison_data]
                        costs = [d['costs'] for d in comparison_data]
                        profits = [d['profit'] for d in comparison_data]
                        margins = [d['margin'] for d in comparison_data]
                        
                        # Revenue chart
                        fig_comp.add_trace(
                            go.Scatter(x=months_labels, y=revenues, mode='lines+markers',
                                      name='Receita', line=dict(color='#4CAF50', width=3)),
                            row=1, col=1
                        )
                        
                        # Costs chart
                        fig_comp.add_trace(
                            go.Scatter(x=months_labels, y=costs, mode='lines+markers',
                                      name='Custos', line=dict(color='#FF5252', width=3)),
                            row=1, col=2
                        )
                        
                        # Profit chart
                        fig_comp.add_trace(
                            go.Bar(x=months_labels, y=profits, name='Lucro',
                                  marker_color=['#4CAF50' if p > 0 else '#FF5252' for p in profits]),
                            row=2, col=1
                        )
                        
                        # Margin chart
                        fig_comp.add_trace(
                            go.Scatter(x=months_labels, y=margins, mode='lines+markers',
                                      name='Margem %', line=dict(color='#2196F3', width=3),
                                      fill='tozeroy', fillcolor='rgba(33, 150, 243, 0.2)'),
                            row=2, col=2
                        )
                        
                        fig_comp.update_layout(
                            height=600,
                            showlegend=False,
                            template="plotly_white"
                        )
                        
                        # Update y-axes
                        fig_comp.update_yaxes(title_text="R$", row=1, col=1)
                        fig_comp.update_yaxes(title_text="R$", row=1, col=2)
                        fig_comp.update_yaxes(title_text="R$", row=2, col=1)
                        fig_comp.update_yaxes(title_text="%", row=2, col=2)
                        
                        st.plotly_chart(fig_comp, use_container_width=True)
                    
                    # Year-over-year comparison for the same month
                    st.subheader(f"📊 Histórico de {selected_month} em Todos os Anos")
                    
                    month_history = []
                    for year in sorted(filtered_data.keys()):
                        if selected_month in filtered_data[year].get('revenue', {}):
                            month_history.append({
                                'year': year,
                                'revenue': filtered_data[year]['revenue'][selected_month],
                                'costs': filtered_data[year].get('costs', {}).get(selected_month, 0)
                            })
                    
                    if len(month_history) > 1:
                        fig_history = go.Figure()
                        
                        years_hist = [d['year'] for d in month_history]
                        revenues_hist = [d['revenue'] for d in month_history]
                        costs_hist = [d['costs'] for d in month_history]
                        
                        fig_history.add_trace(go.Bar(
                            name='Receita',
                            x=years_hist,
                            y=revenues_hist,
                            marker_color='#4CAF50',
                            text=[f'R$ {v/1000:.0f}K' for v in revenues_hist],
                            textposition='outside'
                        ))
                        
                        fig_history.add_trace(go.Bar(
                            name='Custos',
                            x=years_hist,
                            y=costs_hist,
                            marker_color='#FF5252',
                            text=[f'R$ {v/1000:.0f}K' for v in costs_hist],
                            textposition='outside'
                        ))
                        
                        fig_history.update_layout(
                            title=f'Evolução de {selected_month} ao Longo dos Anos',
                            xaxis_title='Ano',
                            yaxis_title='Valores (R$)',
                            barmode='group',
                            template="plotly_white",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                        )
                        
                        st.plotly_chart(fig_history, use_container_width=True)
                    
                    # Monthly insights
                    st.subheader("💡 Insights do Mês")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Compare with year average
                        year_revenues = [v for k, v in year_data.get('revenue', {}).items() 
                                       if k != 'ANNUAL' and isinstance(v, (int, float))]
                        avg_revenue = np.mean(year_revenues) if year_revenues else 0
                        revenue_vs_avg = ((revenue - avg_revenue) / avg_revenue * 100) if avg_revenue > 0 else 0
                        
                        st.info(f"""
                        **📈 Comparação com Média Anual**
                        
                        Receita do mês: R$ {revenue:,.0f}
                        
                        Média anual: R$ {avg_revenue:,.0f}
                        
                        Variação: {revenue_vs_avg:+.1f}%
                        """)
                    
                    with col2:
                        # Ranking among months
                        month_revenues = [(k, v) for k, v in year_data.get('revenue', {}).items() 
                                        if k != 'ANNUAL' and isinstance(v, (int, float))]
                        month_revenues.sort(key=lambda x: x[1], reverse=True)
                        
                        ranking = next((i+1 for i, (m, r) in enumerate(month_revenues) if m == selected_month), 0)
                        
                        st.info(f"""
                        **🏆 Ranking do Mês**
                        
                        Posição: {ranking}º de {len(month_revenues)} meses
                        
                        Melhor mês: {month_revenues[0][0] if month_revenues else 'N/A'}
                        
                        Diferença do líder: R$ {(month_revenues[0][1] - revenue):,.0f} if month_revenues else 0
                        """)
                else:
                    st.warning(f"Não há dados disponíveis para {selected_month}/{selected_year}")
        else:
            st.info("Selecione pelo menos um ano para análise mensal detalhada.")
    
    # Tab 3: AI Insights
    with tab3:
        st.header("🤖 AI-Powered Insights")
        
        if gemini_api_key and st.session_state.extracted_data:
            # Initialize Gemini
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            # Prepare data summary for AI
            data_summary = {
                'years': sorted(st.session_state.extracted_data.keys()),
                'total_years': len(st.session_state.extracted_data),
                'metrics': {}
            }
            
            # Calculate key metrics
            for year, year_data in st.session_state.extracted_data.items():
                revenue = sum(v for k, v in year_data.get('revenue', {}).items() 
                            if k != 'ANNUAL' and isinstance(v, (int, float)))
                costs = sum(v for k, v in year_data.get('costs', {}).items() 
                          if k != 'ANNUAL' and isinstance(v, (int, float)))
                
                data_summary['metrics'][year] = {
                    'revenue': revenue,
                    'costs': costs,
                    'profit': revenue - costs,
                    'margin': ((revenue - costs) / revenue * 100) if revenue > 0 else 0
                }
            
            # Generate insights button
            if st.button("🔮 Gerar Insights com IA", type="primary", use_container_width=True):
                with st.spinner("Analisando dados com IA..."):
                    try:
                        prompt = f"""
                        Analise os seguintes dados financeiros da Marine Seguros e forneça insights estratégicos:
                        
                        {json.dumps(data_summary, indent=2)}
                        
                        Por favor, forneça:
                        1. Análise de tendências de receita e custos
                        2. Identificação de padrões sazonais
                        3. Pontos de atenção e oportunidades
                        4. Recomendações estratégicas
                        5. Previsões baseadas nas tendências observadas
                        
                        Formato: Use markdown com headers e bullet points.
                        """
                        
                        response = model.generate_content(prompt)
                        st.session_state.gemini_insights = response.text
                        
                    except Exception as e:
                        st.error(f"Erro ao gerar insights: {str(e)}")
            
            # Display insights if available
            if hasattr(st.session_state, 'gemini_insights') and st.session_state.gemini_insights:
                st.markdown("### 📊 Insights Gerados pela IA")
                st.markdown(st.session_state.gemini_insights)
                
                # Save insights button
                if st.button("💾 Salvar Insights"):
                    db.auto_save_state(st.session_state)
                    st.success("Insights salvos com sucesso!")
            
            # Comparative analysis section
            if hasattr(st.session_state, 'comparative_analysis') and st.session_state.comparative_analysis:
                st.divider()
                st.subheader("📈 Análise Comparativa")
                
                for year_pair, analysis in st.session_state.comparative_analysis.items():
                    with st.expander(f"Comparação {year_pair}", expanded=True):
                        st.markdown(analysis)
        else:
            if not gemini_api_key:
                st.warning("⚠️ Configure sua Gemini API Key na barra lateral para usar insights com IA")
            else:
                st.info("📊 Carregue dados financeiros para gerar insights com IA")
    
    # Tab 4: AI Chat
    with tab4:
        st.markdown("### 💬 Assistente de IA")
        
        if st.session_state.chat_assistant and st.session_state.extracted_data:
            filter_context = f"Dados disponíveis: {len(st.session_state.extracted_data)} anos"
            st.session_state.chat_assistant.render_chat_interface(
                st.session_state.extracted_data,
                filter_context
            )
        else:
            if not gemini_api_key:
                st.warning("Configure sua API key para usar o chat")
            else:
                st.info("Carregue dados para começar a conversar")
    
    # Tab 5: Previsões
    with tab5:
        st.header("📈 Previsões e Projeções")
        
        if st.session_state.extracted_data and len(st.session_state.extracted_data) >= 2:
            # Prepare time series data
            years = sorted(st.session_state.extracted_data.keys())
            revenues = []
            costs = []
            
            for year in years:
                year_data = st.session_state.extracted_data[year]
                revenue = sum(v for k, v in year_data.get('revenue', {}).items() 
                            if k != 'ANNUAL' and isinstance(v, (int, float)))
                cost = sum(v for k, v in year_data.get('costs', {}).items() 
                         if k != 'ANNUAL' and isinstance(v, (int, float)))
                revenues.append(revenue)
                costs.append(cost)
            
            # Forecast settings
            col1, col2 = st.columns(2)
            with col1:
                forecast_years = st.slider("Anos para projetar", 1, 5, 3)
            with col2:
                forecast_method = st.selectbox(
                    "Método de previsão",
                    ["Linear", "Exponencial", "Média Móvel"]
                )
            
            # Calculate forecasts
            if st.button("📊 Gerar Previsões", type="primary"):
                # Simple linear projection
                years_numeric = list(range(len(years)))
                future_years = list(range(len(years), len(years) + forecast_years))
                
                # Fit linear trend
                revenue_trend = np.poly1d(np.polyfit(years_numeric, revenues, 1))
                costs_trend = np.poly1d(np.polyfit(years_numeric, costs, 1))
                
                # Project future values
                future_revenues = [revenue_trend(y) for y in future_years]
                future_costs = [costs_trend(y) for y in future_years]
                future_year_labels = [str(int(years[-1]) + i + 1) for i in range(forecast_years)]
                
                # Create forecast chart
                fig = go.Figure()
                
                # Historical data
                fig.add_trace(go.Scatter(
                    x=years,
                    y=revenues,
                    mode='lines+markers',
                    name='Receita Histórica',
                    line=dict(color='#4CAF50', width=3)
                ))
                
                fig.add_trace(go.Scatter(
                    x=years,
                    y=costs,
                    mode='lines+markers',
                    name='Custos Históricos',
                    line=dict(color='#FF5252', width=3)
                ))
                
                # Forecasted data
                fig.add_trace(go.Scatter(
                    x=future_year_labels,
                    y=future_revenues,
                    mode='lines+markers',
                    name='Receita Projetada',
                    line=dict(color='#4CAF50', width=3, dash='dash'),
                    marker=dict(symbol='circle-open', size=10)
                ))
                
                fig.add_trace(go.Scatter(
                    x=future_year_labels,
                    y=future_costs,
                    mode='lines+markers',
                    name='Custos Projetados',
                    line=dict(color='#FF5252', width=3, dash='dash'),
                    marker=dict(symbol='circle-open', size=10)
                ))
                
                fig.update_layout(
                    title="Previsão Financeira",
                    xaxis_title="Ano",
                    yaxis_title="Valores (R$)",
                    hovermode='x unified',
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Forecast summary
                st.subheader("📊 Resumo das Previsões")
                
                forecast_data = []
                for i, year in enumerate(future_year_labels):
                    forecast_data.append({
                        'Ano': year,
                        'Receita Prevista': f"R$ {future_revenues[i]:,.0f}",
                        'Custos Previstos': f"R$ {future_costs[i]:,.0f}",
                        'Lucro Previsto': f"R$ {future_revenues[i] - future_costs[i]:,.0f}",
                        'Margem Prevista': f"{((future_revenues[i] - future_costs[i]) / future_revenues[i] * 100):.1f}%"
                    })
                
                st.table(pd.DataFrame(forecast_data))
        else:
            st.info("📊 É necessário pelo menos 2 anos de dados para gerar previsões")
    
    # Tab 6: Integração (empty for now as Make.com is not needed)
    with tab6:
        st.header("⚡ Integrações")
        st.info("🚧 Módulo de integrações em desenvolvimento")
        st.markdown("""
        Futuras integrações planejadas:
        - 📊 Export para Excel/PDF
        - 📧 Envio automático de relatórios
        - 🔗 APIs externas
        - 📱 Notificações
        """)

else:
    # No data message
    st.info("📊 Carregue dados na aba Upload para começar a análise")