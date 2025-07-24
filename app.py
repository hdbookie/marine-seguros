import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
from core import FinancialProcessor
from datetime import datetime
import os
from dotenv import load_dotenv
import json
from typing import Dict, List, Tuple
from gerenciador_arquivos import GerenciadorArquivos
from ai_chat_assistant import AIChatAssistant
from database_manager import DatabaseManager
from core.direct_extractor import DirectDataExtractor
from comparative_analyzer import ComparativeAnalyzer

# Load environment variables
load_dotenv()

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
    .new-badge {
        background-color: #28a745;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        margin-left: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Helper functions for data conversion (must be defined before use)
def convert_extracted_to_processed(extracted_data):
    """Convert extracted_data format (from database) to processed_data format (for app)"""
    if not extracted_data:
        return None
    
    try:
        # Create a DataFrame from extracted_data
        consolidated_data = []
        for year, year_data in sorted(extracted_data.items()):
            revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
            costs = year_data.get('costs', {}).get('ANNUAL', 0)
            
            # Calculate other metrics
            if revenue > 0:
                margin = ((revenue - costs) / revenue) * 100
            else:
                margin = 0
            
            # Extract fixed_costs and operational_costs properly
            fixed_costs_data = year_data.get('fixed_costs', 0)
            operational_costs_data = year_data.get('operational_costs', 0)
            
            # If it's a dictionary, get the ANNUAL value
            if isinstance(fixed_costs_data, dict):
                fixed_costs = fixed_costs_data.get('ANNUAL', 0)
            else:
                fixed_costs = fixed_costs_data
                
            if isinstance(operational_costs_data, dict):
                operational_costs = operational_costs_data.get('ANNUAL', 0)
            else:
                operational_costs = operational_costs_data
            
            consolidated_data.append({
                'year': int(year),
                'revenue': revenue,
                'variable_costs': costs,
                'gross_profit': revenue - costs,
                'gross_margin': margin,
                'fixed_costs': fixed_costs,
                'operational_costs': operational_costs
            })
        
        if consolidated_data:
            consolidated_df = pd.DataFrame(consolidated_data)
            
            # Calculate growth metrics
            processor = FinancialProcessor()
            consolidated_df = processor.calculate_growth_metrics(consolidated_df)
            
            return {
                'raw_data': extracted_data,
                'consolidated': consolidated_df,
                'summary': processor.get_financial_summary(consolidated_df),
                'anomalies': []
            }
    except Exception as e:
        print(f"Error converting data: {e}")
        return None

def sync_processed_to_extracted():
    """Sync processed_data to extracted_data format for database saving"""
    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data and 'raw_data' in st.session_state.processed_data:
        # If we have raw_data, it's already in extracted format with all monthly data
        st.session_state.extracted_data = st.session_state.processed_data['raw_data']
    elif hasattr(st.session_state, 'processed_data') and st.session_state.processed_data and 'consolidated' in st.session_state.processed_data:
        # If we don't have raw_data, but we have monthly_data, use that
        if (hasattr(st.session_state, 'monthly_data') and 
            st.session_state.monthly_data is not None and
            not st.session_state.monthly_data.empty and
            'year' in st.session_state.monthly_data.columns):
            extracted = {}
            monthly_df = st.session_state.monthly_data
            
            # Group by year and rebuild the extracted format with monthly data
            for year in monthly_df['year'].unique():
                year_data = monthly_df[monthly_df['year'] == year]
                revenue_dict = {}
                costs_dict = {}
                
                # Add monthly data
                for _, row in year_data.iterrows():
                    month = row['month']
                    revenue_dict[month] = row.get('revenue', 0)
                    # Handle both 'costs' and 'variable_costs' columns
                    if 'variable_costs' in row:
                        costs_dict[month] = row.get('variable_costs', 0)
                    else:
                        costs_dict[month] = row.get('costs', 0)
                
                # Add annual totals
                revenue_dict['ANNUAL'] = sum(v for k, v in revenue_dict.items() if k != 'ANNUAL')
                costs_dict['ANNUAL'] = sum(v for k, v in costs_dict.items() if k != 'ANNUAL')
                
                extracted[str(year)] = {
                    'revenue': revenue_dict,
                    'costs': costs_dict,
                    'year': int(year)
                }
            
            st.session_state.extracted_data = extracted
        else:
            # Fallback: only ANNUAL data available
            extracted = {}
            df = st.session_state.processed_data.get('consolidated', pd.DataFrame())
            
            for _, row in df.iterrows():
                year = str(int(row['year']))
                extracted[year] = {
                    'revenue': {'ANNUAL': row.get('revenue', 0)},
                    'costs': {'ANNUAL': row.get('variable_costs', 0)},
                    'fixed_costs': row.get('fixed_costs', 0),
                    'operational_costs': row.get('operational_costs', 0),
                    'year': int(year)
                }
            
            st.session_state.extracted_data = extracted

# Try to load data from database FIRST
data_loaded = db.auto_load_state(st.session_state)

# If data was loaded from database, convert it to processed format
if data_loaded and hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
    print(f"DEBUG: About to convert {len(st.session_state.extracted_data)} years to processed format")
    processed = convert_extracted_to_processed(st.session_state.extracted_data)
    if processed:
        st.session_state.processed_data = processed
        print(f"DEBUG: Successfully converted to processed format with {len(processed['consolidated'])} rows")
    
    # Also need to generate monthly data from extracted data
    try:
        # Create monthly DataFrame from extracted data
        monthly_data = []
        for year, year_data in st.session_state.extracted_data.items():
            revenue_data = year_data.get('revenue', {})
            costs_data = year_data.get('costs', {})
            
            for month in ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']:
                if month in revenue_data:
                    monthly_data.append({
                        'year': int(year),
                        'month': month,
                        'revenue': revenue_data.get(month, 0),
                        'costs': costs_data.get(month, 0)
                    })
        
        if monthly_data:
            st.session_state.monthly_data = pd.DataFrame(monthly_data)
    except Exception as e:
        print(f"Error generating monthly data: {e}")

# Initialize session state
if 'file_manager' not in st.session_state:
    st.session_state.file_manager = GerenciadorArquivos()
    # Sincronizar arquivos existentes
    st.session_state.file_manager.sincronizar_arquivos_existentes()
if 'ai_chat_assistant' not in st.session_state:
    st.session_state.ai_chat_assistant = None

# Only initialize empty defaults if nothing was loaded from database
if not data_loaded:
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'gemini_insights' not in st.session_state:
        st.session_state.gemini_insights = None
    if 'flexible_data' not in st.session_state:
        st.session_state.flexible_data = None
    if 'monthly_data' not in st.session_state:
        st.session_state.monthly_data = None
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = {}
    if 'selected_years' not in st.session_state:
        st.session_state.selected_years = []
    if 'selected_months' not in st.session_state:
        st.session_state.selected_months = []

# Debug: Show loaded data status
if data_loaded and hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
    print(f"DEBUG: Successfully loaded {len(st.session_state.extracted_data)} years from database")
    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data and 'consolidated' in st.session_state.processed_data:
        df = st.session_state.processed_data.get('consolidated', pd.DataFrame())
        print(f"DEBUG: Processed data contains {len(df)} years: {sorted(df['year'].tolist())}")
    else:
        print("DEBUG: WARNING - No processed_data despite successful database load")

# Helper functions
def format_currency(value):
    """Format value as Brazilian currency"""
    if abs(value) >= 1_000_000:
        # For millions, show 1 decimal place and 'M' suffix
        return f"R$ {value/1_000_000:,.1f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    elif abs(value) >= 1_000:
        # For thousands, show as full number with thousands separator
        return f"R$ {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        # For smaller amounts, show 2 decimal places
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100


def get_category_icon(category):
    """Get icon for each category"""
    icons = {
        'revenue': '💰',
        'variable_costs': '📦',
        'fixed_costs': '🏢',
        'admin_expenses': '📋',
        'operational_expenses': '⚙️',
        'marketing_expenses': '📢',
        'financial_expenses': '💳',
        'tax_expenses': '📊',
        'other_expenses': '📌',
        'other_costs': '📍',
        'results': '📈',
        'margins': '📊',
        'calculated_results': '🧮',
        'other': '📄'
    }
    return icons.get(category, '📄')

def get_category_name(category):
    """Get friendly name for category"""
    names = {
        'revenue': 'Receitas',
        'variable_costs': 'Custos Variáveis',
        'fixed_costs': 'Custos Fixos',
        'admin_expenses': 'Despesas Administrativas',
        'operational_expenses': 'Despesas Operacionais',
        'marketing_expenses': 'Despesas de Marketing',
        'financial_expenses': 'Despesas Financeiras',
        'tax_expenses': 'Impostos e Taxas',
        'other_expenses': 'Outras Despesas',
        'other_costs': 'Outros Custos',
        'results': 'Resultados',
        'margins': 'Margens',
        'calculated_results': 'Resultados Calculados',
        'other': 'Outros'
    }
    return names.get(category, category.title())


def prepare_x_axis(df, view_type):
    """Prepare x-axis column and title based on view type"""
    if view_type == "Anual":
        return 'year', 'Ano'
    elif view_type == "Mensal":
        # Check if we actually have monthly data (with 'month' column)
        if 'month' in df.columns:
            if 'period' not in df.columns:
                # Create more readable period format
                month_abbr = {
                    'JAN': 'Jan', 'FEV': 'Fev', 'MAR': 'Mar', 'ABR': 'Abr',
                    'MAI': 'Mai', 'JUN': 'Jun', 'JUL': 'Jul', 'AGO': 'Ago',
                    'SET': 'Set', 'OUT': 'Out', 'NOV': 'Nov', 'DEZ': 'Dez'
                }
                df['period'] = df.apply(lambda x: f"{month_abbr.get(x['month'], x['month'])}/{str(int(x['year']))[-2:]}", axis=1)
            return 'period', 'Período'
        else:
            # Fallback to annual view when monthly data is not available
            return 'year', 'Ano'
    elif view_type in ["Trimestral", "Trimestre Personalizado", "Semestral"]:
        return 'period', 'Período'
    else:
        return 'year', 'Ano'

# Title and description
st.title("🏢 Marine Seguros - Financial Analytics Platform")
st.markdown("### Análise Financeira Inteligente com IA | 2018-2025")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Database status
    st.markdown("### 💾 Status do Banco de Dados")
    stats = db.get_data_stats()
    
    if stats.get('financial_data', {}).get('count', 0) > 0:
        st.success(f"✅ {stats['financial_data']['count']} anos de dados salvos")
        
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
        
        # Add reload button
        if st.button("🔄 Recarregar Dados Salvos", use_container_width=True):
            if db.auto_load_state(st.session_state):
                # Convert loaded data
                if hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
                    processed = convert_extracted_to_processed(st.session_state.extracted_data)
                    if processed:
                        st.session_state.processed_data = processed
                st.success("✅ Dados carregados!")
                st.rerun()
    else:
        st.warning("❌ Nenhum dado salvo")
    
    st.divider()
    
    # Gemini API Key input
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Enter your Google Gemini API key"
    )
    
    # Language selection
    language = st.selectbox(
        "Idioma / Language",
        ["Português", "English"],
        index=0
    )
    
    # Analysis options
    st.subheader("Opções de Análise")
    show_predictions = st.checkbox("Mostrar Previsões", value=True)
    show_anomalies = st.checkbox("Detectar Anomalias", value=True)
    use_flexible_extractor = st.checkbox(
        "🆕 Usar Extrator Flexível", 
        value=False,
        help="Detecta automaticamente TODAS as categorias de despesas nos arquivos Excel"
    )
    show_all_categories = st.checkbox("Mostrar Todas as Categorias", value=True)
    
    # Export options
    st.subheader("Exportar Dados")
    export_format = st.selectbox(
        "Formato de Exportação",
        ["PDF", "Excel", "PowerPoint"]
    )

# Main content area with conditional tabs
if use_flexible_extractor:
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
        anos_disponiveis = st.session_state.file_manager.obter_anos_disponiveis() if hasattr(st.session_state, 'file_manager') else []
        if anos_disponiveis:
            anos_selecionados = st.multiselect(
                "Filtrar por Anos:",
                options=sorted(anos_disponiveis),
                default=sorted(anos_disponiveis),
                key="file_year_filter"
            )
        else:
            anos_selecionados = []
    
    with col2:
        if st.button("🔄 Atualizar", help="Atualizar lista de arquivos"):
            if hasattr(st.session_state, 'file_manager'):
                st.session_state.file_manager.sincronizar_arquivos_existentes()
            st.rerun()
    
    with col3:
        gerenciar_mode = st.checkbox("📁 Gerenciar", help="Ativar modo de gerenciamento")
    
    st.markdown("---")
    
    # Upload section
    with st.expander("➕ Enviar Novos Arquivos", expanded=False):
        uploaded_files = st.file_uploader(
            "Selecione arquivos Excel",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="Formatos suportados: .xlsx, .xls | Você pode selecionar múltiplos arquivos"
        )
        
        if uploaded_files:
            if st.button(f"📤 Enviar {len(uploaded_files)} arquivo(s)"):
                success_count = 0
                error_count = 0
                
                for uploaded_file in uploaded_files:
                    if hasattr(st.session_state, 'file_manager') and st.session_state.file_manager.enviar_arquivo(uploaded_file):
                        success_count += 1
                    else:
                        error_count += 1
                
                if success_count > 0:
                    st.success(f"✅ {success_count} arquivo(s) enviado(s) com sucesso!")
                if error_count > 0:
                    st.error(f"❌ {error_count} arquivo(s) com erro")
                
                st.rerun()
    
    # Display available files
    st.subheader("📁 Fontes de Dados Disponíveis")
    
    # Clear all button when in manage mode
    if gerenciar_mode and 'arquivos' in locals() and arquivos:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Limpar Todos", type="secondary", help="Remover todos os arquivos", use_container_width=True):
                if hasattr(st.session_state, 'file_manager'):
                    for arquivo in arquivos:
                        st.session_state.file_manager.excluir_arquivo(arquivo['id'])
                st.success("Todos os arquivos foram removidos!")
                st.rerun()
    
    # Get files filtered by years
    if anos_selecionados and hasattr(st.session_state, 'file_manager'):
        arquivos = st.session_state.file_manager.obter_arquivos_por_anos(anos_selecionados)
    elif hasattr(st.session_state, 'file_manager'):
        arquivos = st.session_state.file_manager.obter_todos_arquivos()
    else:
        arquivos = []
    
    if arquivos:
        for arquivo in arquivos:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"### ✅ {arquivo['nome']}")
                    
                    # File info
                    anos_str = ", ".join(map(str, sorted(arquivo['anos_incluidos'])))
                    st.markdown(f"""
                    **Anos:** {anos_str}  
                    **Enviado:** {arquivo['data_envio']} | **Tamanho:** {arquivo['tamanho']}
                    """)
                
                with col2:
                    if gerenciar_mode:
                        if st.button("🗑️ Excluir", key=f"del_{arquivo['id']}"):
                            if hasattr(st.session_state, 'file_manager') and st.session_state.file_manager.excluir_arquivo(arquivo['id']):
                                st.success("Arquivo excluído!")
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("📭 Nenhum arquivo encontrado. Envie arquivos Excel para começar.")
    
    # Process data button
    if arquivos:
        st.markdown("### 🚀 Processar Dados")
        
        if st.button("Analisar Dados Financeiros", type="primary", use_container_width=True):
            with st.spinner("Processando arquivos..."):
                processor = FinancialProcessor()
                
                # Get file paths
                file_paths = st.session_state.file_manager.obter_caminhos_arquivos() if hasattr(st.session_state, 'file_manager') else []
                
                # Load Excel files
                excel_data = processor.load_excel_files(file_paths)
                
                # Consolidate data
                if use_flexible_extractor:
                    # Use flexible extractor for dynamic categories
                    consolidated_df, flexible_data = processor.consolidate_all_years_flexible(excel_data)
                    st.session_state.flexible_data = flexible_data
                else:
                    # Use standard extractor - now returns both DataFrame and extracted data
                    consolidated_df, extracted_financial_data = processor.consolidate_all_years(excel_data)
                    st.session_state.flexible_data = None
                
                # Check if data extraction was successful
                if consolidated_df.empty:
                    st.error("❌ Não foi possível extrair dados dos arquivos Excel.")
                    st.info("Verifique se os arquivos contêm as seguintes informações:")
                    st.markdown("""
                    - Sheets com anos (ex: 2018, 2019, 2020, etc.)
                    - Linha com 'FATURAMENTO' para receitas
                    - Linha com 'CUSTOS VARIÁVEIS' para custos
                    - Colunas com meses (JAN, FEV, MAR, etc.)
                    - Coluna 'ANUAL' para totais anuais
                    """)
                else:
                    consolidated_df = processor.calculate_growth_metrics(consolidated_df)
                    
                    # Get monthly data
                    monthly_df = processor.get_monthly_data(excel_data)
                    
                    # Store in session state with the CORRECT extracted data
                    st.session_state.processed_data = {
                        'raw_data': extracted_financial_data if not use_flexible_extractor else excel_data,
                        'consolidated': consolidated_df,
                        'summary': processor.get_financial_summary(consolidated_df),
                        'anomalies': processor.detect_anomalies(consolidated_df) if show_anomalies else []
                    }
                    st.session_state.monthly_data = monthly_df
                    
                    # Sync to extracted_data format and save to database
                    sync_processed_to_extracted()
                    
                    # Save to database
                    try:
                        db.auto_save_state(st.session_state)
                        save_success = True
                    except Exception as e:
                        st.error(f"⚠️ Erro ao salvar no banco de dados: {str(e)}")
                        save_success = False
                    
                    if use_flexible_extractor and flexible_data:
                        # Show summary of detected categories
                        all_categories = set()
                        for year_data in flexible_data.values():
                            all_categories.update(year_data['categories'].keys())
                        
                        st.success(f"✅ Dados processados com sucesso!")
                        if save_success:
                            st.success("💾 Dados salvos no banco de dados!")
                        st.info(f"📊 {len(consolidated_df)} anos encontrados | "
                               f"📁 {len(all_categories)} categorias detectadas automaticamente")
                        
                        # Show detected categories
                        with st.expander("Categorias Detectadas"):
                            cols = st.columns(3)
                            for idx, category in enumerate(sorted(all_categories)):
                                col_idx = idx % 3
                                cols[col_idx].write(f"{get_category_icon(category)} {get_category_name(category)}")
                    else:
                        st.success(f"✅ Dados processados com sucesso! {len(consolidated_df)} anos encontrados.")
                        if save_success:
                            st.success("💾 Dados salvos no banco de dados!")

# Tab 2: Dashboard
with tab2:
    st.header("Dashboard Financeiro")
    
    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data is not None:
        data = st.session_state.processed_data
        df = data.get('consolidated', pd.DataFrame())
        summary = data.get('summary', {})
        
        
        # Ensure monthly data is available and has all required columns
        required_monthly_cols = ['variable_costs', 'fixed_costs', 'net_profit', 'profit_margin']
        monthly_data_invalid = (
            not hasattr(st.session_state, 'monthly_data') or 
            st.session_state.monthly_data is None or 
            st.session_state.monthly_data.empty or
            not all(col in st.session_state.monthly_data.columns for col in required_monthly_cols)
        )
        
        if monthly_data_invalid:
            # Extract monthly data from the known Excel files
            try:
                processor = FinancialProcessor()
                
                # Use the actual Excel files instead of the broken raw_data paths
                excel_files = [
                    "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2023.xlsx",
                    "data/arquivos_enviados/Resultado Financeiro - 2024.xlsx", 
                    "data/arquivos_enviados/Resultado Financeiro - 2025.xlsx"
                ]
                
                # Create a properly formatted excel_data dict with existing files
                excel_data = {}
                for file_path in excel_files:
                    if os.path.exists(file_path):
                        excel_data[file_path] = None  # The processor will handle the file reading
                
                if excel_data:
                    monthly_data = processor.get_monthly_data(excel_data)
                    
                    if monthly_data.empty:
                        st.error("❌ Failed to extract monthly data from Excel files")
                    else:
                        st.success(f"✅ Monthly data extracted: {len(monthly_data)} records from {len(excel_data)} files")
                        st.info(f"Years covered: {sorted(monthly_data['year'].unique()) if 'year' in monthly_data.columns else 'Unknown'}")
                    
                    st.session_state.monthly_data = monthly_data
                else:
                    st.error("❌ No Excel files found for monthly data extraction")
                    st.session_state.monthly_data = pd.DataFrame()
                    
            except Exception as e:
                st.error(f"Error extracting monthly data: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                st.session_state.monthly_data = pd.DataFrame()
        
        
        # Time Period Filters
        st.subheader("🗓️ Filtros de Período")
        
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        
        with col_filter1:
            view_type = st.selectbox(
                "Visualização",
                ["Anual", "Mensal", "Trimestral", "Trimestre Personalizado", "Semestral", "Personalizado"],
                key="view_type"
            )
        
        with col_filter2:
            if view_type in ["Mensal", "Trimestral", "Trimestre Personalizado", "Semestral", "Personalizado"]:
                available_years = sorted(df['year'].unique())
                selected_years = st.multiselect(
                    "Anos",
                    available_years,
                    default=available_years[-3:] if len(available_years) >= 3 else available_years,
                    key="dashboard_selected_years"
                )
            else:
                selected_years = sorted(df['year'].unique())
        
        with col_filter3:
            if view_type == "Mensal":
                month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                selected_months = st.multiselect(
                    "Meses",
                    month_names,
                    default=month_names,
                    key="dashboard_selected_months"
                )
            elif view_type == "Trimestral":
                selected_quarter = st.multiselect(
                    "Trimestres",
                    ["Q1 (Jan-Mar)", "Q2 (Abr-Jun)", "Q3 (Jul-Set)", "Q4 (Out-Dez)"],
                    default=["Q1 (Jan-Mar)", "Q2 (Abr-Jun)", "Q3 (Jul-Set)", "Q4 (Out-Dez)"],
                    key="dashboard_selected_quarters"
                )
            elif view_type == "Trimestre Personalizado":
                month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                start_month = st.selectbox(
                    "Mês Inicial",
                    month_names,
                    key="start_month_custom"
                )
            elif view_type == "Semestral":
                selected_semester = st.multiselect(
                    "Semestres",
                    ["1º Semestre (Jan-Jun)", "2º Semestre (Jul-Dez)"],
                    default=["1º Semestre (Jan-Jun)", "2º Semestre (Jul-Dez)"],
                    key="dashboard_selected_semesters"
                )
        
        with col_filter4:
            if view_type == "Trimestre Personalizado":
                # Calculate end month options (3 months from start)
                month_map = {
                    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
                    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
                    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                }
                month_names = list(month_map.keys())
                start_idx = month_names.index(start_month)
                
                # End month is exactly 2 months after start (for a 3-month period)
                end_idx = (start_idx + 2) % 12
                end_month_display = month_names[end_idx]
                
                st.info(f"Trimestre: {start_month} a {end_month_display} (3 meses)")
                end_month = end_month_display
            elif view_type == "Personalizado":
                date_range = st.date_input(
                    "Período",
                    value=(pd.Timestamp(selected_years[0], 1, 1), pd.Timestamp(selected_years[-1], 12, 31)),
                    key="date_range"
                )
        
        # Prepare data based on view type
        if view_type == "Anual":
            display_df = df[df['year'].isin(selected_years)]
        elif view_type == "Mensal":
            if not hasattr(st.session_state, 'monthly_data') or st.session_state.monthly_data is None or st.session_state.monthly_data.empty:
                st.warning("📋 Dados mensais não disponíveis. Mostrando visualização anual.")
                # Debug info
                if st.checkbox("Mostrar informações de debug"):
                    st.info(f"Debug: monthly_data exists: {hasattr(st.session_state, 'monthly_data')}")
                    if hasattr(st.session_state, 'monthly_data'):
                        st.info(f"Debug: monthly_data is None: {st.session_state.monthly_data is None}")
                        if st.session_state.monthly_data is not None:
                            st.info(f"Debug: monthly_data empty: {st.session_state.monthly_data.empty}")
                            st.info(f"Debug: monthly_data shape: {st.session_state.monthly_data.shape}")
                display_df = df[df['year'].isin(selected_years)]
            else:
                # Use monthly data
                monthly_df = st.session_state.monthly_data
                
                # Ensure month_num column exists
                if 'month_num' not in monthly_df.columns and 'month' in monthly_df.columns:
                    # Create month_num from month names
                    month_to_num = {
                        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
                        'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
                    }
                    monthly_df['month_num'] = monthly_df['month'].map(month_to_num)
                
                # Map month names to numbers
                month_map = {
                    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
                    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
                    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                }
                selected_month_nums = [month_map[m] for m in selected_months]
                
                display_df = monthly_df[
                    (monthly_df['year'].isin(selected_years)) &
                    (monthly_df['month_num'].isin(selected_month_nums))
                ]
                
        elif view_type == "Trimestral":
            if not hasattr(st.session_state, 'monthly_data') or st.session_state.monthly_data is None or st.session_state.monthly_data.empty:
                st.warning("📋 Dados mensais não disponíveis para visualização trimestral. Mostrando visualização anual.")
                display_df = df[df['year'].isin(selected_years)]
            else:
                # Aggregate monthly data by quarter
                monthly_df = st.session_state.monthly_data
            
                # Ensure month_num column exists
                if 'month_num' not in monthly_df.columns and 'month' in monthly_df.columns:
                    month_to_num = {
                        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
                        'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
                    }
                    monthly_df['month_num'] = monthly_df['month'].map(month_to_num)
                
                quarter_map = {
                    "Q1 (Jan-Mar)": [1, 2, 3],
                    "Q2 (Abr-Jun)": [4, 5, 6],
                    "Q3 (Jul-Set)": [7, 8, 9],
                    "Q4 (Out-Dez)": [10, 11, 12]
                }
                selected_months_for_quarters = []
                for q in selected_quarter:
                    selected_months_for_quarters.extend(quarter_map[q])
                
                filtered_monthly = monthly_df[
                    (monthly_df['year'].isin(selected_years)) &
                    (monthly_df['month_num'].isin(selected_months_for_quarters))
                ]
                
                # Aggregate by quarter
                filtered_monthly['quarter'] = (filtered_monthly['month_num'] - 1) // 3 + 1
                display_df = filtered_monthly.groupby(['year', 'quarter']).agg({
                    'revenue': 'sum',
                    'variable_costs': 'sum',
                    'fixed_costs': 'sum',
                    'operational_costs': 'sum',
                    'contribution_margin': 'sum',
                    'net_profit': 'sum'
                }).reset_index()
                display_df['period'] = display_df.apply(lambda x: f"{int(x['year'])}-Q{int(x['quarter'])}", axis=1)
        elif view_type == "Trimestre Personalizado":
            if not hasattr(st.session_state, 'monthly_data') or st.session_state.monthly_data is None or st.session_state.monthly_data.empty:
                st.warning("📋 Dados mensais não disponíveis para trimestre personalizado. Mostrando visualização anual.")
                display_df = df[df['year'].isin(selected_years)]
            else:
                # Custom trimester logic
                monthly_df = st.session_state.monthly_data
            
                # Ensure month_num column exists
                if 'month_num' not in monthly_df.columns and 'month' in monthly_df.columns:
                    month_to_num = {
                        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
                        'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
                    }
                    monthly_df['month_num'] = monthly_df['month'].map(month_to_num)
                
                month_map = {
                    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
                    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
                    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                }
                
                start_month_num = month_map[start_month]
                end_month_num = month_map[end_month]
                
                # Handle year wrap-around
                if end_month_num < start_month_num:
                    # Trimester crosses year boundary
                    selected_months_nums = list(range(start_month_num, 13)) + list(range(1, end_month_num + 1))
                else:
                    selected_months_nums = list(range(start_month_num, end_month_num + 1))
                
                # Filter data
                filtered_monthly = monthly_df[
                    (monthly_df['year'].isin(selected_years)) &
                    (monthly_df['month_num'].isin(selected_months_nums))
                ].copy()
                
                # Group by year and custom trimester
                def get_custom_trimester(row):
                    if row['month_num'] in selected_months_nums:
                        # If the trimester crosses year boundary
                        if end_month_num < start_month_num and row['month_num'] < start_month_num:
                            return f"{int(row['year']-1)}/{int(row['year'])}"
                        else:
                            return str(int(row['year']))
                    return None
                
                filtered_monthly['custom_period'] = filtered_monthly.apply(get_custom_trimester, axis=1)
                
                # Aggregate by custom period
                display_df = filtered_monthly.groupby('custom_period').agg({
                    'revenue': 'sum',
                    'variable_costs': 'sum',
                    'fixed_costs': 'sum',
                    'operational_costs': 'sum',
                    'contribution_margin': 'sum',
                    'net_profit': 'sum'
                }).reset_index()
                
                # Add period label
                display_df['period'] = display_df['custom_period'].apply(
                    lambda x: f"{x} ({start_month[:3]}-{end_month[:3]})"
                )
                display_df['year'] = display_df['custom_period']  # For compatibility
        elif view_type == "Semestral":
            if not hasattr(st.session_state, 'monthly_data') or st.session_state.monthly_data is None or st.session_state.monthly_data.empty:
                st.warning("📋 Dados mensais não disponíveis para visualização semestral. Mostrando visualização anual.")
                display_df = df[df['year'].isin(selected_years)]
            else:
                # Aggregate monthly data by semester
                monthly_df = st.session_state.monthly_data
            
                # Ensure month_num column exists
                if 'month_num' not in monthly_df.columns and 'month' in monthly_df.columns:
                    month_to_num = {
                        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
                        'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
                    }
                    monthly_df['month_num'] = monthly_df['month'].map(month_to_num)
                
                semester_map = {
                    "1º Semestre (Jan-Jun)": [1, 2, 3, 4, 5, 6],
                    "2º Semestre (Jul-Dez)": [7, 8, 9, 10, 11, 12]
                }
                selected_months_for_semesters = []
                for s in selected_semester:
                    selected_months_for_semesters.extend(semester_map[s])
                
                filtered_monthly = monthly_df[
                    (monthly_df['year'].isin(selected_years)) &
                    (monthly_df['month_num'].isin(selected_months_for_semesters))
                ]
                
                # Aggregate by semester
                filtered_monthly['semester'] = (filtered_monthly['month_num'] - 1) // 6 + 1
                display_df = filtered_monthly.groupby(['year', 'semester']).agg({
                    'revenue': 'sum',
                    'variable_costs': 'sum',
                    'fixed_costs': 'sum',
                    'operational_costs': 'sum',
                    'contribution_margin': 'sum',
                    'net_profit': 'sum'
                }).reset_index()
                display_df['period'] = display_df.apply(lambda x: f"{int(x['year'])}-S{int(x['semester'])}", axis=1)
        else:
            # Default to annual view if monthly data not available
            display_df = df[df['year'].isin(selected_years)].copy()
            
            # Ensure all numeric columns contain only numeric values (not dicts)
            numeric_cols = ['revenue', 'variable_costs', 'fixed_costs', 'operational_costs', 
                          'gross_profit', 'net_profit', 'contribution_margin']
            for col in numeric_cols:
                if col in display_df.columns:
                    # Convert any dict values to numbers
                    display_df[col] = display_df[col].apply(
                        lambda x: x.get('ANNUAL', 0) if isinstance(x, dict) else x
                    )
        
        # Debug: Show what data is being displayed
        if not display_df.empty:
            st.caption(f"📊 Exibindo {len(display_df)} {'registros mensais' if view_type == 'Mensal' else 'anos' if view_type == 'Anual' else 'períodos'} | Colunas: {list(display_df.columns)}")
            
            # Ensure profit_margin column exists for all views
            if 'profit_margin' not in display_df.columns and 'revenue' in display_df.columns and 'net_profit' in display_df.columns:
                display_df['profit_margin'] = display_df.apply(
                    lambda row: (row['net_profit'] / row['revenue'] * 100) if row['revenue'] > 0 else 0,
                    axis=1
                )
        else:
            st.caption("⚠️ Nenhum dado disponível para o período selecionado")
        
        # Key metrics - Calculate based on filtered data
        col1, col2, col3, col4 = st.columns(4)
        
        
        # Calculate net_profit if missing
        if 'net_profit' not in display_df.columns and not display_df.empty:
            display_df = display_df.copy()
            
            # Ensure all numeric columns are actually numeric (not dicts)
            for col in ['revenue', 'variable_costs', 'fixed_costs', 'operational_costs']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda x: x.get('ANNUAL', 0) if isinstance(x, dict) else x
                    )
            
            # Check if operational_costs exists and has values
            if 'operational_costs' in display_df.columns:
                operational_costs = display_df['operational_costs']
            else:
                operational_costs = 0
                if st.checkbox("⚠️ Aviso: operational_costs não encontrado", key="warn_op_costs"):
                    st.warning("Coluna 'operational_costs' não encontrada. Usando 0 para custos operacionais.")
            
            # Calculate net profit from available columns
            if all(col in display_df.columns for col in ['revenue', 'variable_costs', 'fixed_costs']):
                display_df['net_profit'] = display_df['revenue'] - display_df['variable_costs'] - display_df['fixed_costs'] - operational_costs
            elif 'gross_profit' in display_df.columns and 'fixed_costs' in display_df.columns:
                display_df['net_profit'] = display_df['gross_profit'] - display_df['fixed_costs'] - operational_costs
        
        # Calculate profit_margin only if missing
        if 'profit_margin' not in display_df.columns and 'net_profit' in display_df.columns and not display_df.empty:
            display_df = display_df.copy()
            display_df['profit_margin'] = (display_df['net_profit'] / display_df['revenue'] * 100).fillna(0)
        
        # Calculate metrics from filtered display_df
        total_revenue = display_df['revenue'].sum() if 'revenue' in display_df.columns and not display_df.empty else 0
        
        # Use existing profit data from the DataFrame
        if not display_df.empty:
            # Debug: Check data types and convert dicts to numbers
            numeric_cols = ['revenue', 'variable_costs', 'fixed_costs', 'net_profit', 'profit_margin']
            for col in numeric_cols:
                if col in display_df.columns:
                    # Check if any values are dicts
                    has_dicts = display_df[col].apply(lambda x: isinstance(x, dict)).any()
                    if has_dicts:
                        # Convert dict values to numbers (using ANNUAL key if available)
                        display_df[col] = display_df[col].apply(
                            lambda x: x.get('ANNUAL', 0) if isinstance(x, dict) else x
                        )
            
            # Use the existing net_profit and profit_margin from the data
            total_profit = display_df['net_profit'].sum() if 'net_profit' in display_df.columns else 0
            avg_profit = display_df['net_profit'].mean() if 'net_profit' in display_df.columns else 0
            avg_margin = display_df['profit_margin'].mean() if 'profit_margin' in display_df.columns else 0
            
        else:
            # Fallback to DataFrame values if we can't calculate
            total_profit = display_df['net_profit'].sum() if 'net_profit' in display_df.columns and not display_df.empty else 0
            avg_profit = display_df['net_profit'].mean() if 'net_profit' in display_df.columns and not display_df.empty else 0
            avg_margin = display_df['profit_margin'].mean() if 'profit_margin' in display_df.columns and not display_df.empty else 0
        
        # For period views, show period count
        period_label = f"{len(display_df)} {'meses' if view_type == 'Mensal' else 'períodos'}" if view_type != 'Anual' else f"{summary['metrics'].get('revenue', {}).get('cagr', 0):.1f}% CAGR"
        
        with col1:
            st.metric(
                "Receita Total",
                format_currency(total_revenue),
                period_label
            )
        
        with col2:
            # For yearly view, show total profit and clarify it's total across all years
            if view_type == "Anual":
                profit_label = "Lucro Total (Todos os Anos)"
                profit_value = total_profit
                profit_delta = f"Média anual: {format_currency(avg_profit)}"
            else:
                profit_label = "Lucro Total"
                profit_value = total_profit
                profit_delta = f"{(total_profit / total_revenue * 100) if total_revenue > 0 else 0:.1f}% da receita"
            
            st.metric(
                profit_label,
                format_currency(profit_value),
                profit_delta
            )
        
        with col3:
            margin_range = display_df['profit_margin'].max() - display_df['profit_margin'].min() if 'profit_margin' in display_df.columns and not display_df.empty else 0
            st.metric(
                "Margem de Lucro Média",
                f"{avg_margin:.2f}%",
                f"{margin_range:.2f}pp variação"
            )
        
        with col4:
            if hasattr(st.session_state, 'flexible_data') and st.session_state.flexible_data:
                total_items = sum(
                    len(year_data['line_items']) 
                    for year_data in st.session_state.flexible_data.values()
                ) / len(st.session_state.flexible_data)
                st.metric(
                    "Linhas de Dados",
                    f"{int(total_items)}",
                    "Média por ano"
                )
            else:
                st.metric(
                    "Anos Analisados",
                    summary['total_years'],
                    summary['years_range']
                )
        
        
        # Revenue Evolution Chart
        st.subheader("📈 Evolução da Receita")
        if not display_df.empty and 'revenue' in display_df.columns and display_df['revenue'].sum() > 0:
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            fig_revenue = px.line(
                display_df, 
                x=x_col, 
                y='revenue',
                title=f'Receita {view_type}',
                markers=True
            )
            
            # Add text annotations with smart positioning for monthly view
            if view_type == "Mensal" and len(display_df) > 20:
                # For crowded monthly view, show values on hover only
                fig_revenue.update_traces(
                    hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>'
                )
            else:
                # For less crowded views, show selected values
                fig_revenue.add_trace(go.Scatter(
                    x=display_df[x_col],
                    y=display_df['revenue'],
                    mode='text',
                    text=[f'R$ {v:,.0f}' if i % 3 == 0 or v == display_df['revenue'].max() or v == display_df['revenue'].min() 
                          else '' for i, v in enumerate(display_df['revenue'])],
                    textposition='top center',
                    textfont=dict(size=10),
                    showlegend=False
                ))
            fig_revenue.update_layout(
                yaxis_title="Receita (R$)",
                xaxis_title=x_title,
                hovermode='x unified',
                xaxis=dict(
                    tickangle=-45 if view_type == "Mensal" else 0,
                    tickmode='linear',
                    dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
                ),
                height=500 if view_type == "Mensal" else 400,
                margin=dict(t=50, b=100 if view_type == "Mensal" else 50)
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            if display_df.empty:
                st.info("📊 Nenhum dado disponível para o período selecionado. Verifique os filtros.")
            else:
                st.info("📊 Dados de receita não disponíveis")
        
        # Profit Margin Evolution
        if not display_df.empty and 'profit_margin' in display_df.columns:
            st.subheader("📊 Margem de Lucro")
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            # Calculate profit margin for aggregated data if needed
            if view_type != "Anual":
                display_df['profit_margin'] = (display_df['net_profit'] / display_df['revenue'] * 100).fillna(0)
            
            fig_margin = px.bar(
                display_df,
                x=x_col,
                y='profit_margin',
                title=f'Margem de Lucro {view_type} (%)',
                color='profit_margin',
                color_continuous_scale='RdYlGn'
            )
            
            # Smart text positioning for monthly view
            if view_type == "Mensal" and len(display_df) > 20:
                fig_margin.update_traces(
                    texttemplate='',
                    hovertemplate='<b>%{x}</b><br>Margem de Lucro: %{y:.2f}%<extra></extra>'
                )
            else:
                fig_margin.update_traces(
                    text=display_df['profit_margin'].apply(lambda x: f'{x:.2f}%'),
                    textposition='outside'
                )
            
            fig_margin.update_layout(
                yaxis_title="Margem de Lucro (%)",
                xaxis_title=x_title,
                xaxis=dict(
                    tickangle=-45 if view_type == "Mensal" else 0,
                    tickmode='linear',
                    dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
                ),
                height=450 if view_type == "Mensal" else 400,
                margin=dict(t=50, b=100 if view_type == "Mensal" else 50),
                showlegend=False
            )
            st.plotly_chart(fig_margin, use_container_width=True)
        
        # Growth Analysis (only for annual view)
        if view_type == "Anual":
            st.subheader("📊 Análise de Crescimento")
            growth_cols = [col for col in display_df.columns if '_growth' in col]
            if growth_cols:
                fig_growth = go.Figure()
                for col in growth_cols:
                    metric_name = col.replace('_growth', '').title()
                    fig_growth.add_trace(go.Scatter(
                        x=display_df['year'],
                        y=display_df[col],
                    mode='lines+markers',
                    name=metric_name,
                    line=dict(width=3)
                ))
            fig_growth.update_layout(
                title="Taxa de Crescimento Anual (%)",
                xaxis_title="Ano",
                yaxis_title="Crescimento (%)",
                hovermode='x unified'
            )
            st.plotly_chart(fig_growth, use_container_width=True)
        
        # New Financial Metrics Graphs
        st.subheader("📊 Análise de Custos e Margens")
        
        # 1. Variable Costs Evolution - Full width
        if not display_df.empty and 'variable_costs' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            fig_var_costs = px.line(
                display_df, 
                x=x_col, 
                y='variable_costs',
                title='💸 Custos Variáveis',
                markers=True,
                color_discrete_sequence=['#ff7f0e']
            )
            
            # Apply same smart positioning as revenue
            if view_type == "Mensal" and len(display_df) > 20:
                fig_var_costs.update_traces(
                    hovertemplate='<b>%{x}</b><br>Custos Variáveis: R$ %{y:,.0f}<extra></extra>'
                )
            else:
                fig_var_costs.add_trace(go.Scatter(
                    x=display_df[x_col],
                    y=display_df['variable_costs'],
                    mode='text',
                    text=[f'R$ {v:,.0f}' if i % 3 == 0 or v == display_df['variable_costs'].max() or v == display_df['variable_costs'].min() 
                          else '' for i, v in enumerate(display_df['variable_costs'])],
                    textposition='top center',
                    textfont=dict(size=10),
                    showlegend=False
                ))
            
            fig_var_costs.update_layout(
                yaxis_title="Custos Variáveis (R$)",
                xaxis_title=x_title,
                xaxis=dict(
                    tickangle=-45 if view_type == "Mensal" else 0,
                    tickmode='linear',
                    dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
                ),
                height=450 if view_type == "Mensal" else 400,
                margin=dict(t=50, b=100 if view_type == "Mensal" else 50)
            )
            st.plotly_chart(fig_var_costs, use_container_width=True)
        
        # 2. Fixed Costs - Full width
        if not display_df.empty and 'fixed_costs' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            fig_fixed = px.bar(
                display_df,
                x=x_col,
                y='fixed_costs',
                title='🏢 Custos Fixos',
                color_discrete_sequence=['#2ca02c']
            )
            
            # Smart text positioning for bars
            if view_type == "Mensal" and len(display_df) > 20:
                fig_fixed.update_traces(
                    texttemplate='',
                    hovertemplate='<b>%{x}</b><br>Custos Fixos: R$ %{y:,.0f}<extra></extra>'
                )
            else:
                fig_fixed.update_traces(
                    text=[f'R$ {v:,.0f}' if i % 2 == 0 else '' for i, v in enumerate(display_df['fixed_costs'])],
                    textposition='outside'
                )
            
            fig_fixed.update_layout(
                yaxis_title="Custos Fixos (R$)",
                xaxis_title=x_title,
                xaxis=dict(
                    tickangle=-45 if view_type == "Mensal" else 0,
                    tickmode='linear',
                    dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
                ),
                height=450 if view_type == "Mensal" else 400,
                margin=dict(t=50, b=100 if view_type == "Mensal" else 50)
            )
            st.plotly_chart(fig_fixed, use_container_width=True)
        
        # 3. Contribution Margin - Full width
        if not display_df.empty and 'contribution_margin' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            fig_contrib = px.bar(
                display_df,
                x=x_col,
                y='contribution_margin',
                title='📈 Margem de Contribuição',
                color='contribution_margin',
                color_continuous_scale='Greens'
            )
            
            # Smart text positioning
            if view_type == "Mensal" and len(display_df) > 20:
                fig_contrib.update_traces(
                    texttemplate='',
                    hovertemplate='<b>%{x}</b><br>Margem de Contribuição: R$ %{y:,.0f}<extra></extra>'
                )
            else:
                fig_contrib.update_traces(
                    text=[f'R$ {v:,.0f}' if i % 2 == 0 else '' for i, v in enumerate(display_df['contribution_margin'])],
                    textposition='outside'
                )
            
            fig_contrib.update_layout(
                yaxis_title="Margem de Contribuição (R$)",
                xaxis_title=x_title,
                showlegend=False,
                xaxis=dict(
                    tickangle=-45 if view_type == "Mensal" else 0,
                    tickmode='linear',
                    dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
                ),
                height=450 if view_type == "Mensal" else 400,
                margin=dict(t=50, b=100 if view_type == "Mensal" else 50)
            )
            st.plotly_chart(fig_contrib, use_container_width=True)
        
        # 4. Operational Costs - Full width  
        if not display_df.empty and 'operational_costs' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            fig_op_costs = px.area(
                display_df,
                x=x_col,
                y='operational_costs',
                title='⚙️ Custos Operacionais',
                color_discrete_sequence=['#d62728']
            )
            
            fig_op_costs.update_layout(
                yaxis_title="Custos Operacionais (R$)",
                xaxis_title=x_title,
                xaxis=dict(
                    tickangle=-45 if view_type == "Mensal" else 0,
                    tickmode='linear',
                    dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
                ),
                height=450 if view_type == "Mensal" else 400,
                margin=dict(t=50, b=100 if view_type == "Mensal" else 50),
                hovermode='x unified'
            )
            st.plotly_chart(fig_op_costs, use_container_width=True)
        
        # 5. Result (Profit) - Full width
        st.subheader("💰 Resultado (Lucro Líquido)")
        if not display_df.empty and 'net_profit' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            # Create a color scale based on positive/negative values
            colors = ['red' if x < 0 else 'green' for x in display_df['net_profit']]
            
            fig_result = go.Figure()
            fig_result.add_trace(go.Bar(
                x=display_df[x_col],
                y=display_df['net_profit'],
                text=display_df['net_profit'].apply(lambda x: f'R$ {x:,.0f}'),
                textposition='outside',
                marker_color=colors,
                name='Resultado'
            ))
            
            # Add a zero line
            fig_result.add_hline(y=0, line_dash="dash", line_color="gray")
            
            fig_result.update_layout(
                title=f'Resultado {view_type} (Lucro/Prejuízo)',
                yaxis_title="Resultado (R$)",
                xaxis_title=x_title,
                height=500,
                showlegend=False
            )
            st.plotly_chart(fig_result, use_container_width=True)
        
        # Cost Structure Comparison
        st.subheader("📊 Estrutura de Custos")
        if not display_df.empty and all(col in display_df.columns for col in ['variable_costs', 'fixed_costs', 'revenue']):
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            # Calculate total costs and profit margins
            display_df['total_costs'] = display_df['variable_costs'] + display_df['fixed_costs']
            display_df['profit'] = display_df['revenue'] - display_df['total_costs']
            display_df['cost_percentage'] = (display_df['total_costs'] / display_df['revenue'] * 100).fillna(0)
            
            # Create stacked bar chart with improved styling
            fig_cost_structure = go.Figure()
            
            # Calculate percentages of revenue for better visualization
            display_df['var_cost_pct'] = (display_df['variable_costs'] / display_df['revenue'] * 100).fillna(0)
            display_df['fixed_cost_pct'] = (display_df['fixed_costs'] / display_df['revenue'] * 100).fillna(0)
            display_df['profit_pct'] = (display_df['profit'] / display_df['revenue'] * 100).fillna(0)
            
            # Add variable costs bar (as percentage)
            fig_cost_structure.add_trace(go.Bar(
                name='Custos Variáveis',
                x=display_df[x_col],
                y=display_df['var_cost_pct'],
                text=display_df['var_cost_pct'].apply(lambda x: f"{x:.2f}%"),
                textposition='inside',
                textfont=dict(color='white', size=11, weight='bold'),
                marker=dict(
                    color='#6366F1',  # Modern purple/indigo for variable costs
                    line=dict(color='#4F46E5', width=1)
                ),
                hovertemplate='<b>Custos Variáveis</b><br>' +
                             'Percentual: %{y:.1f}%<br>' +
                             'Valor: R$ %{customdata[0]:,.0f}<br>' +
                             '<b>Receita Total: R$ %{customdata[1]:,.0f}</b><br>' +
                             '<extra></extra>',
                customdata=list(zip(display_df['variable_costs'], display_df['revenue']))
            ))
            
            # Add fixed costs bar (as percentage)
            fig_cost_structure.add_trace(go.Bar(
                name='Custos Fixos',
                x=display_df[x_col],
                y=display_df['fixed_cost_pct'],
                text=display_df['fixed_cost_pct'].apply(lambda x: f"{x:.2f}%"),
                textposition='inside',
                textfont=dict(color='white', size=11, weight='bold'),
                marker=dict(
                    color='#F59E0B',  # Professional amber for fixed costs
                    line=dict(color='#D97706', width=1)
                ),
                hovertemplate='<b>Custos Fixos</b><br>' +
                             'Percentual: %{y:.1f}%<br>' +
                             'Valor: R$ %{customdata[0]:,.0f}<br>' +
                             '<b>Receita Total: R$ %{customdata[1]:,.0f}</b><br>' +
                             '<extra></extra>',
                customdata=list(zip(display_df['fixed_costs'], display_df['revenue']))
            ))
            
            # Add profit margin bar
            fig_cost_structure.add_trace(go.Bar(
                name='Margem de Lucro',
                x=display_df[x_col],
                y=display_df['profit_pct'],
                text=display_df['profit_pct'].apply(lambda x: f"{x:.2f}%"),
                textposition='inside',
                textfont=dict(color='white', size=11, weight='bold'),
                marker=dict(
                    color='#10B981',  # Green for profit
                    line=dict(color='#047857', width=1)
                ),
                hovertemplate='<b>Margem de Lucro</b><br>' +
                             'Percentual: %{y:.1f}%<br>' +
                             'Valor: R$ %{customdata[0]:,.0f}<br>' +
                             '<b>Receita Total: R$ %{customdata[1]:,.0f}</b><br>' +
                             '<extra></extra>',
                customdata=list(zip(display_df['profit'], display_df['revenue']))
            ))
            
            # Add 100% reference line
            fig_cost_structure.add_hline(
                y=100, 
                line_dash="dot", 
                line_color="#6B7280",
                annotation_text="100% da Receita",
                annotation_position="top right",
                annotation_font=dict(size=12, color="#6B7280")
            )
            
            # Clean x-axis labels with just periods (revenue moved to hover)
            
            
            # Update layout with single y-axis for percentages
            fig_cost_structure.update_layout(
                title={
                    'text': '💰 Estrutura de Custos vs Receita (% da Receita)',
                    'font': {'size': 24, 'color': '#1F2937'}
                },
                barmode='stack',
                yaxis=dict(
                    title=dict(
                        text="Percentual da Receita (%)",
                        font=dict(size=16, color='#1F2937', weight='bold')
                    ),
                    tickformat='.1f',
                    ticksuffix='%',
                    tickfont=dict(size=12, color='#374151'),
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)',
                    range=[0, 100]
                ),
                xaxis=dict(
                    title=dict(
                        text=x_title,
                        font=dict(size=16, color='#1F2937', weight='bold')
                    ),
                    tickfont=dict(size=12, color='#374151'),
                    showgrid=False,
                    tickangle=-90  # Vertical labels to prevent overlap
                ),
                height=600,  # Standard height for all views
                hovermode='x unified',
                plot_bgcolor='rgba(248,249,250,0.8)',
                paper_bgcolor='white',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.1)",
                    borderwidth=1,
                    font=dict(size=14, color='#374151', weight='bold')
                ),
                margin=dict(t=120, b=50)
            )
            
            # Add shapes for visual appeal
            fig_cost_structure.update_xaxes(showline=True, linewidth=2, linecolor='#E5E7EB')
            fig_cost_structure.update_yaxes(showline=True, linewidth=2, linecolor='#E5E7EB')
            
            st.plotly_chart(fig_cost_structure, use_container_width=True)
            
            # Add cost analysis metrics below the chart with clearer descriptions
            st.markdown("### 📊 Análise de Custos - Período Mais Recente")
            
            col1, col2, col3, col4 = st.columns(4)
            
            latest_year = display_df.iloc[-1]
            latest_period = latest_year.get('period', latest_year.get(x_col, 'Último período'))
            
            with col1:
                st.metric(
                    "💵 Custo Total",
                    format_currency(latest_year['total_costs']),
                    f"↑ {latest_year['cost_percentage']:.1f}% da receita",
                    help=f"Soma de todos os custos (variáveis + fixos) em {latest_period}"
                )
            
            with col2:
                variable_pct = (latest_year['variable_costs'] / latest_year['total_costs'] * 100) if latest_year['total_costs'] > 0 else 0
                st.metric(
                    "📊 Custos Variáveis",
                    f"{variable_pct:.1f}%",
                    "↑ do total de custos",
                    help=f"Proporção dos custos variáveis em relação ao custo total em {latest_period}"
                )
            
            with col3:
                fixed_pct = (latest_year['fixed_costs'] / latest_year['total_costs'] * 100) if latest_year['total_costs'] > 0 else 0
                st.metric(
                    "🏢 Custos Fixos",
                    f"{fixed_pct:.1f}%",
                    "↑ do total de custos",
                    help=f"Proporção dos custos fixos em relação ao custo total em {latest_period}"
                )
            
            with col4:
                avg_margin = display_df['profit_margin'].mean() if 'profit_margin' in display_df.columns else 0
                st.metric(
                    "📈 Margem de Lucro Média",
                    f"{avg_margin:.2f}%",
                    "↑ período selecionado",
                    help=f"Margem de lucro média considerando todo o período analisado"
                )
        
        # Anomalies
        if show_anomalies and data['anomalies']:
            st.subheader("⚠️ Anomalias Detectadas")
            for anomaly in data['anomalies']:
                st.warning(
                    f"**{anomaly['year']}**: {anomaly['metric']} - "
                    f"Valor: {anomaly['value']:.2f}% ({anomaly['type']})"
                )
        
        # Data table
        with st.expander("📋 Ver Dados Detalhados"):
            st.dataframe(display_df, use_container_width=True)
    
    else:
        st.info("👆 Please upload files in the 'Upload' tab first.")

# Tab 3: Detailed Breakdown (only for flexible mode)
if use_flexible_extractor:
    with tab3:
        st.header("🔍 Detalhamento por Categoria")
        
        if hasattr(st.session_state, 'flexible_data') and st.session_state.flexible_data is not None:
            flexible_data = st.session_state.flexible_data
            
            # Year selector
            years = sorted(flexible_data.keys())
            selected_year = st.selectbox("Selecione o Ano", years, index=len(years)-1)
            
            year_data = flexible_data[selected_year]
            
            # Summary metrics for the year
            col1, col2, col3 = st.columns(3)
            
            # Calculate totals
            total_revenue = sum(
                item['annual'] for item in year_data['line_items'].values()
                if item['category'] == 'revenue'
            )
            total_costs = sum(
                item['annual'] for item in year_data['line_items'].values()
                if item['category'] in ['variable_costs', 'fixed_costs', 'other_costs']
            )
            total_expenses = sum(
                item['annual'] for item in year_data['line_items'].values()
                if 'expense' in item['category']
            )
            
            with col1:
                st.metric("Receita Total", format_currency(total_revenue))
            with col2:
                st.metric("Custos Totais", format_currency(total_costs))
            with col3:
                st.metric("Despesas Totais", format_currency(total_expenses))
            
            st.markdown("---")
            
            # Detailed breakdown by category
            st.subheader("Detalhamento por Categoria")
            
            # Create expandable sections for each category
            for category in sorted(year_data['categories'].keys()):
                if not show_all_categories and category in ['calculated_results', 'margins']:
                    continue
                    
                items = year_data['categories'][category]
                
                # Calculate category total
                category_total = sum(
                    year_data['line_items'][item]['annual'] 
                    for item in items
                )
                
                # Create expander for category
                icon = get_category_icon(category)
                name = get_category_name(category)
                
                with st.expander(f"{icon} {name} - {format_currency(category_total)}", expanded=False):
                    # Show items in this category
                    item_df = []
                    for item_key in items:
                        item_data = year_data['line_items'][item_key]
                        item_df.append({
                            'Descrição': item_data['label'],
                            'Valor Anual': item_data['annual'],
                            '% da Receita': (item_data['annual'] / total_revenue * 100) if total_revenue > 0 else 0
                        })
                    
                    item_df = pd.DataFrame(item_df)
                    item_df = item_df.sort_values('Valor Anual', ascending=False)
                    
                    # Format columns
                    st.dataframe(
                        item_df.style.format({
                            'Valor Anual': lambda x: format_currency(x),
                            '% da Receita': '{:.1f}%'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Show monthly breakdown if available
                    if st.checkbox(f"Mostrar detalhamento mensal", key=f"monthly_{category}"):
                        monthly_data = []
                        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                        
                        for item_key in items:
                            item_data = year_data['line_items'][item_key]
                            monthly = item_data['monthly']
                            
                            if monthly:
                                row = {'Item': item_data['label']}
                                for month in months:
                                    row[month] = monthly.get(month, 0)
                                monthly_data.append(row)
                        
                        if monthly_data:
                            monthly_df = pd.DataFrame(monthly_data)
                            st.dataframe(
                                monthly_df.style.format({
                                    month: lambda x: format_currency(x) if x != 0 else '-'
                                    for month in months
                                }),
                                use_container_width=True,
                                hide_index=True
                            )
            
            # Waterfall chart showing path to profit
            st.subheader("💧 Análise Waterfall - Caminho para o Lucro")
            
            # Prepare data for waterfall
            waterfall_data = [
                ('Receita', total_revenue, 'relative'),
                ('Custos Variáveis', -total_costs, 'relative'),
                ('Despesas Operacionais', -total_expenses, 'relative'),
            ]
            
            # Add other expense categories
            other_expenses = sum(
                item['annual'] for item in year_data['line_items'].values()
                if item['category'] not in ['revenue', 'variable_costs', 'fixed_costs', 
                                           'calculated_results', 'margins']
                and 'expense' not in item['category']
            )
            if other_expenses > 0:
                waterfall_data.append(('Outras Despesas', -other_expenses, 'relative'))
            
            # Final result
            net_result = total_revenue - total_costs - total_expenses - other_expenses
            waterfall_data.append(('Resultado Líquido', net_result, 'total'))
            
            # Create waterfall chart
            labels = [item[0] for item in waterfall_data]
            values = [item[1] for item in waterfall_data]
            
            fig_waterfall = go.Figure(go.Waterfall(
                name="",
                orientation="v",
                measure=[item[2] for item in waterfall_data],
                x=labels,
                textposition="outside",
                text=[format_currency(v) for v in values],
                y=values,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            ))
            
            fig_waterfall.update_layout(
                title=f"Fluxo Financeiro - {selected_year}",
                showlegend=False,
                height=500
            )
            
            st.plotly_chart(fig_waterfall, use_container_width=True)
            
            # Year-over-year comparison
            if len(years) > 1:
                st.subheader("📊 Comparação com Ano Anterior")
                
                if years.index(selected_year) > 0:
                    prev_year = years[years.index(selected_year) - 1]
                    prev_data = flexible_data[prev_year]
                    
                    # Compare categories
                    comparison_data = []
                    
                    all_categories_both_years = set(year_data['categories'].keys()) | set(prev_data['categories'].keys())
                    
                    for category in sorted(all_categories_both_years):
                        current_total = 0
                        previous_total = 0
                        
                        if category in year_data['categories']:
                            current_total = sum(
                                year_data['line_items'][item]['annual'] 
                                for item in year_data['categories'][category]
                            )
                        
                        if category in prev_data['categories']:
                            previous_total = sum(
                                prev_data['line_items'][item]['annual'] 
                                for item in prev_data['categories'][category]
                            )
                        
                        change = current_total - previous_total
                        change_pct = calculate_percentage_change(previous_total, current_total)
                        
                        comparison_data.append({
                            'Categoria': f"{get_category_icon(category)} {get_category_name(category)}",
                            f'{prev_year}': previous_total,
                            f'{selected_year}': current_total,
                            'Variação R$': change,
                            'Variação %': change_pct
                        })
                    
                    comparison_df = pd.DataFrame(comparison_data)
                    
                    st.dataframe(
                        comparison_df.style.format({
                            f'{prev_year}': lambda x: format_currency(x),
                            f'{selected_year}': lambda x: format_currency(x),
                            'Variação R$': lambda x: format_currency(x),
                            'Variação %': '{:.1f}%'
                        }).background_gradient(subset=['Variação %'], cmap='RdYlGn', vmin=-50, vmax=50),
                        use_container_width=True,
                        hide_index=True
                    )
            
        else:
            st.info("👆 Please upload files in the 'Upload' tab first.")

# Tab 3/4: AI Insights
tab_ai = tab4 if use_flexible_extractor else tab3
with tab_ai:
    st.header("🤖 Insights com Gemini AI")
    
    # Load extracted data from database if not in session state
    if not hasattr(st.session_state, 'extracted_data') or not st.session_state.extracted_data:
        st.session_state.extracted_data = db.load_all_financial_data()
    
    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data is not None and gemini_api_key:
        if st.button("🤖 Generate AI Business Insights", type="primary"):
            with st.spinner("Analyzing data with AI... Please wait..."):
                try:
                    # Configure Gemini
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Prepare data for analysis
                    df = st.session_state.processed_data.get('consolidated', pd.DataFrame())
                    summary = st.session_state.processed_data.get('summary', {})
                    
                    # Include flexible data insights
                    flexible_summary = ""
                    if hasattr(st.session_state, 'flexible_data') and st.session_state.flexible_data:
                        all_categories = set()
                        all_items = set()
                        for year_data in st.session_state.flexible_data.values():
                            all_categories.update(year_data['categories'].keys())
                            all_items.update(item['label'] for item in year_data['line_items'].values())
                        
                        flexible_summary = f"\n\nDetected categories: {len(all_categories)}\nTotal data lines: {len(all_items)}"
                    
                    # Create prompt with language instruction based on user selection
                    if language == "Português":
                        language_instruction = "INSTRUÇÃO CRÍTICA: Você DEVE responder inteiramente em português brasileiro. NÃO use palavras ou frases em inglês."
                        analysis_request = "Por favor, analise os seguintes dados financeiros da Marine Seguros e forneça insights detalhados de negócios:"
                    else:
                        language_instruction = "CRITICAL INSTRUCTION: You MUST respond entirely in English. Do NOT use Portuguese words or phrases."
                        analysis_request = "Please analyze the following financial data from Marine Seguros and provide detailed business insights:"
                    
                    prompt = f"""
                    {language_instruction}
                    
                    {analysis_request}
                    
                    Summary Data:
                    - Period: {summary['years_range']}
                    - Total Revenue: R$ {summary['metrics'].get('revenue', {}).get('total', 0):,.2f}
                    - Revenue CAGR: {summary['metrics'].get('revenue', {}).get('cagr', 0):.1f}%
                    - Average Profit Margin: {summary['metrics'].get('profit_margin', {}).get('average', 0):.1f}%
                    {flexible_summary}
                    
                    Annual Data:
                    {df.to_string()}
                    
                    {
                        "Por favor, forneça uma análise abrangente cobrindo:" if language == "Português" else "Please provide a comprehensive analysis covering:"
                    }
                    {
                        '''1. **Análise das Principais Tendências Financeiras**
                    2. **Pontos Fortes de Performance & Vantagens Competitivas**
                    3. **Áreas de Risco & Preocupações**
                    4. **Recomendações Estratégicas**''' + (' para categorias de despesas recém-detectadas' if hasattr(st.session_state, 'flexible_data') and st.session_state.flexible_data else '') + '''
                    5. **Previsões Futuras & Perspectivas de Mercado**
                    
                    Requisitos de Formato:
                    - Use markdown com títulos claros (##) e subtítulos (###)
                    - Inclua marcadores para análise detalhada
                    - Use **negrito** para métricas-chave e pontos importantes
                    - Assegure linguagem profissional de negócios em português brasileiro apenas''' if language == "Português" else '''1. **Main Financial Trends Analysis**
                    2. **Performance Strengths & Competitive Advantages**
                    3. **Risk Areas & Concerns**
                    4. **Strategic Recommendations**''' + (' for newly detected expense categories' if hasattr(st.session_state, 'flexible_data') and st.session_state.flexible_data else '') + '''
                    5. **Future Predictions & Market Outlook**
                    
                    Format Requirements:
                    - Use markdown with clear headings (##) and subheadings (###)
                    - Include bullet points for detailed analysis
                    - Use **bold** for key metrics and important points
                    - Ensure professional business language in English only'''
                    }
                    """
                    
                    # Generate insights
                    response = model.generate_content(prompt)
                    insights_text = response.text
                    
                    # Language validation - only check if English is selected
                    if language == "English" and any(word in insights_text.lower() for word in ['receita', 'lucro', 'despesas', 'vendas', 'análise']):
                        # If Portuguese words detected when English is selected, add reminder
                        english_reminder_prompt = f"""
                        CRITICAL: The following text appears to contain Portuguese words. Please translate this ENTIRE analysis to English and ensure all content is in English only:
                        
                        {insights_text}
                        
                        Requirements:
                        - Translate everything to English
                        - Maintain the same structure and insights
                        - Use business terminology
                        - Keep all formatting and markdown
                        """
                        response = model.generate_content(english_reminder_prompt)
                        insights_text = response.text
                    
                    st.session_state.gemini_insights = insights_text
                    
                except Exception as e:
                    st.error(f"Error generating AI insights: {str(e)}")
        
        # Display insights with enhanced styling
        if hasattr(st.session_state, 'gemini_insights') and st.session_state.gemini_insights:
            # Create a styled container for the insights
            st.markdown("### 🧠 AI Business Insights")
            st.markdown("---")
            
            # Apply custom CSS for better formatting
            st.markdown("""
            <style>
            .insights-container {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #0066cc;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .insights-content {
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.8;
                color: #333;
            }
            .insights-content h2 {
                color: #0066cc;
                margin-top: 25px;
                margin-bottom: 15px;
                border-bottom: 2px solid #e9ecef;
                padding-bottom: 8px;
            }
            .insights-content h3 {
                color: #0d47a1;
                margin-top: 20px;
                margin-bottom: 12px;
            }
            .insights-content ul, .insights-content ol {
                margin: 15px 0;
                padding-left: 25px;
            }
            .insights-content li {
                margin: 8px 0;
            }
            .insights-content strong {
                color: #1565c0;
                font-weight: 600;
            }
            .insights-content p {
                margin: 12px 0;
                text-align: justify;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Display insights in styled container
            with st.container():
                st.markdown(f"""
                <div class="insights-container">
                    <div class="insights-content">
                        {st.session_state.gemini_insights}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Add spacing
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Export insights button with improved styling
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Download AI Insights Report",
                    data=st.session_state.gemini_insights,
                    file_name=f"ai_insights_marine_seguros_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    help="Download the complete AI analysis as a markdown file"
                )
        
        # Separator
        st.markdown("---")
        
        # Comparative Analysis Section
        st.subheader("🔍 Análise Comparativa")
        st.markdown("Compare o desempenho entre dois anos específicos:")
        
        # Load extracted data for comparison
        if hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
            available_years = sorted(st.session_state.extracted_data.keys())
            
            col1, col2 = st.columns(2)
            
            with col1:
                year1 = st.selectbox(
                    "Ano 1 (Base)",
                    options=available_years,
                    index=len(available_years)-2 if len(available_years) > 1 else 0,
                    key="comparison_year1"
                )
            
            with col2:
                year2 = st.selectbox(
                    "Ano 2 (Comparação)",
                    options=available_years,
                    index=len(available_years)-1,
                    key="comparison_year2"
                )
            
            if st.button("🔍 Comparar Períodos", type="secondary"):
                with st.spinner("Executando análise comparativa..."):
                    try:
                        # Initialize comparative analyzer
                        analyzer = ComparativeAnalyzer(gemini_api_key)
                        
                        # Get data for both years
                        period1_data = st.session_state.extracted_data.get(year1, {})
                        period2_data = st.session_state.extracted_data.get(year2, {})
                        
                        if period1_data and period2_data:
                            # Perform comparison
                            comparison_result = analyzer.compare_custom_periods(
                                period1_data, period2_data, str(year1), str(year2)
                            )
                            
                            # Store result in session state
                            st.session_state.comparison_result = comparison_result
                            
                            st.success(f"✅ Comparação entre {year1} e {year2} concluída!")
                            
                        else:
                            st.error(f"❌ Dados não encontrados para um ou ambos os anos ({year1}, {year2})")
                            
                    except Exception as e:
                        st.error(f"Erro na análise comparativa: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
            
            # Display comparison results
            if hasattr(st.session_state, 'comparison_result') and st.session_state.comparison_result:
                result = st.session_state.comparison_result
                
                st.subheader("📊 Resultados da Comparação")
                
                # Metrics comparison
                metrics = result.get('metrics', {})
                
                # Revenue comparison
                if 'revenue' in metrics:
                    revenue_metrics = metrics['revenue']
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            f"Receita {year1}",
                            f"R$ {revenue_metrics.get('previous', 0):,.2f}"
                        )
                    
                    with col2:
                        st.metric(
                            f"Receita {year2}",
                            f"R$ {revenue_metrics.get('current', 0):,.2f}"
                        )
                    
                    with col3:
                        change_pct = revenue_metrics.get('percentage_change', 0)
                        st.metric(
                            "Variação",
                            f"{change_pct:+.1f}%",
                            f"R$ {revenue_metrics.get('absolute_change', 0):+,.2f}"
                        )
                
                # AI Analysis
                if 'ai_analysis' in result:
                    st.subheader("🤖 Análise com IA")
                    st.markdown(result['ai_analysis'])
                
                # Monthly detail
                if 'monthly_detail' in result and result['monthly_detail']:
                    st.subheader("📅 Detalhamento Mensal")
                    
                    # Create monthly comparison chart
                    monthly_data = []
                    for month, data in result['monthly_detail'].items():
                        monthly_data.append({
                            'Mês': month,
                            'Variação (%)': data.get('revenue_change_pct', 0),
                            'Variação (R$)': data.get('revenue_change_abs', 0)
                        })
                    
                    if monthly_data:
                        monthly_df = pd.DataFrame(monthly_data)
                        
                        # Bar chart of monthly changes
                        fig = px.bar(
                            monthly_df,
                            x='Mês',
                            y='Variação (%)',
                            title=f'Variação Mensal de Receita: {year1} vs {year2}',
                            color='Variação (%)',
                            color_continuous_scale='RdYlGn'
                        )
                        fig.update_layout(showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Data table
                        st.dataframe(monthly_df, use_container_width=True)
        
        else:
            st.info("📊 Processe os dados primeiro para habilitar a análise comparativa.")
    else:
        if not gemini_api_key:
            st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
        else:
            st.info("👆 Please upload files first.")

# Tab 4/5: AI Chat
tab_chat = tab5 if use_flexible_extractor else tab4
with tab_chat:
    st.header("💬 Chat com IA")
    
    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data is not None and gemini_api_key:
        # Initialize chat assistant if not already done
        if not hasattr(st.session_state, 'ai_chat_assistant') or st.session_state.ai_chat_assistant is None:
            st.session_state.ai_chat_assistant = AIChatAssistant(gemini_api_key)
        
        # Prepare filter context
        filter_context = "Visualizando todos os dados"
        if 'view_type' in st.session_state:
            filter_context = f"Visualização: {st.session_state.view_type}"
            if 'selected_years' in st.session_state and hasattr(st.session_state, 'selected_years'):
                years = st.session_state.selected_years
                filter_context += f" | Anos: {', '.join(map(str, years))}"
        
        # Prepare data for AI chat
        if use_flexible_extractor and hasattr(st.session_state, 'flexible_data') and st.session_state.flexible_data:
            # Use flexible data format
            chat_data = st.session_state.flexible_data
        else:
            # Convert standard data to the format expected by AI chat
            # The AI chat expects data in format: {year: {revenue: {...}, costs: {...}, ...}}
            chat_data = {}
            if (hasattr(st.session_state, 'monthly_data') and 
                st.session_state.monthly_data is not None and 
                not st.session_state.monthly_data.empty and
                'year' in st.session_state.monthly_data.columns):
                # Group monthly data by year
                monthly_df = st.session_state.monthly_data
                for year in monthly_df['year'].unique():
                    year_data = monthly_df[monthly_df['year'] == year]
                    # Convert numpy int64 to regular int
                    year_int = int(year)
                    # Check which cost column exists (could be 'costs' or 'variable_costs')
                    if 'variable_costs' in year_data.columns:
                        costs_col = 'variable_costs'
                    elif 'costs' in year_data.columns:
                        costs_col = 'costs'
                    else:
                        costs_col = None
                    
                    chat_data[year_int] = {
                        'revenue': dict(zip(year_data['month'], year_data['revenue'])),
                        'costs': dict(zip(year_data['month'], year_data[costs_col])) if costs_col else {},
                        'fixed_costs': year_data['fixed_costs'].iloc[0] if 'fixed_costs' in year_data.columns and len(year_data) > 0 else 0,
                        'operational_costs': year_data['operational_costs'].iloc[0] if 'operational_costs' in year_data.columns and len(year_data) > 0 else 0
                    }
                    # Add annual totals
                    chat_data[year_int]['revenue']['ANNUAL'] = year_data['revenue'].sum()
                    chat_data[year_int]['costs']['ANNUAL'] = year_data[costs_col].sum() if costs_col else 0
            
            # If monthly data is not available, use consolidated data
            if not chat_data and 'consolidated' in st.session_state.processed_data:
                consolidated_df = st.session_state.processed_data.get('consolidated', pd.DataFrame())
                for _, row in consolidated_df.iterrows():
                    year = int(row['year'])  # Convert to regular int
                    chat_data[year] = {
                        'revenue': {'ANNUAL': row.get('revenue', 0)},
                        'costs': {'ANNUAL': row.get('variable_costs', 0)},
                        'fixed_costs': row.get('fixed_costs', 0),
                        'operational_costs': row.get('operational_costs', 0),
                        'net_profit': row.get('net_profit', 0),
                        'profit_margin': row.get('profit_margin', 0)
                    }
        
        # Render chat interface
        st.session_state.ai_chat_assistant.render_chat_interface(
            data=chat_data,
            filter_context=filter_context
        )
    else:
        if not gemini_api_key:
            st.warning("⚠️ Please enter your Gemini API key in the sidebar.")
        else:
            st.info("👆 Please upload files first.")

# Tab 5/6: Predictions
tab_pred = tab6 if use_flexible_extractor else tab5
with tab_pred:
    st.header("📈 Previsões e Cenários")
    
    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data is not None and show_predictions:
        df = st.session_state.processed_data.get('consolidated', pd.DataFrame())
        
        if 'revenue' in df.columns:
            # Simple forecast
            st.subheader("Previsão Simples")
            
            # Calculate trend
            if len(df) >= 2:
                # Linear regression for revenue
                from sklearn.linear_model import LinearRegression
                
                X = df['year'].values.reshape(-1, 1)
                y = df['revenue'].values
                
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict next 3 years
                future_years = [2026, 2027, 2028]
                predictions = model.predict([[year] for year in future_years])
                
                # Create forecast dataframe
                forecast_df = pd.DataFrame({
                    'year': future_years,
                    'revenue_forecast': predictions,
                    'type': 'Previsão'
                })
                
                # Combine with historical data
                historical_df = df[['year', 'revenue']].copy()
                historical_df['type'] = 'Histórico'
                historical_df.rename(columns={'revenue': 'revenue_forecast'}, inplace=True)
                
                combined_df = pd.concat([historical_df, forecast_df])
                
                # Plot
                fig_forecast = px.line(
                    combined_df,
                    x='year',
                    y='revenue_forecast',
                    color='type',
                    title='Previsão de Receita (2026-2028)',
                    markers=True
                )
                fig_forecast.update_layout(
                    yaxis_title="Receita (R$)",
                    xaxis_title="Ano"
                )
                st.plotly_chart(fig_forecast, use_container_width=True)
                
                # Scenario analysis
                st.subheader("Análise de Cenários")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    growth_rate_optimistic = st.slider(
                        "Crescimento Otimista (%)",
                        0, 50, 20
                    )
                
                with col2:
                    growth_rate_realistic = st.slider(
                        "Crescimento Realista (%)",
                        0, 30, 10
                    )
                
                with col3:
                    growth_rate_pessimistic = st.slider(
                        "Crescimento Pessimista (%)",
                        -20, 10, 0
                    )
                
                # Calculate scenarios
                last_revenue = df['revenue'].iloc[-1]
                
                scenarios_df = pd.DataFrame({
                    'Cenário': ['Otimista', 'Realista', 'Pessimista'],
                    '2026': [
                        last_revenue * (1 + growth_rate_optimistic/100),
                        last_revenue * (1 + growth_rate_realistic/100),
                        last_revenue * (1 + growth_rate_pessimistic/100)
                    ],
                    '2027': [
                        last_revenue * (1 + growth_rate_optimistic/100)**2,
                        last_revenue * (1 + growth_rate_realistic/100)**2,
                        last_revenue * (1 + growth_rate_pessimistic/100)**2
                    ],
                    '2028': [
                        last_revenue * (1 + growth_rate_optimistic/100)**3,
                        last_revenue * (1 + growth_rate_realistic/100)**3,
                        last_revenue * (1 + growth_rate_pessimistic/100)**3
                    ]
                })
                
                st.dataframe(
                    scenarios_df.style.format({
                        '2026': 'R$ {:,.2f}',
                        '2027': 'R$ {:,.2f}',
                        '2028': 'R$ {:,.2f}'
                    }),
                    use_container_width=True
                )
        else:
            st.warning("Dados de receita não encontrados para fazer previsões.")
    else:
        st.info("👆 Please upload files first.")

# Tab 6/7: Integration
tab_int = tab7 if use_flexible_extractor else tab6
with tab_int:
    st.header("⚡ Integração Make.com")
    
    st.markdown("""
    ### Como configurar a integração bancária
    
    1. **Crie uma conta no Make.com** (se ainda não tiver)
    2. **Configure o webhook** abaixo
    3. **Conecte sua conta bancária** através do Make
    4. **Automatize atualizações** dos dados financeiros
    """)
    
    # Webhook configuration
    webhook_url = st.text_input(
        "Webhook URL",
        placeholder="https://hook.make.com/...",
        help="Cole aqui a URL do webhook do Make.com"
    )
    
    if webhook_url:
        st.code(f"""
# Exemplo de payload para o webhook:
{{
    "company": "Marine Seguros",
    "year": {datetime.now().year},
    "month": {datetime.now().month},
    "revenue": 250000.00,
    "costs": 150000.00,
    "profit": 100000.00
}}
        """, language="json")
        
        if st.button("Testar Webhook"):
            st.info("Funcionalidade de teste será implementada na versão completa.")
    
    # Make.com template
    st.subheader("📋 Template Make.com")
    st.markdown("""
    Baixe nosso template pronto para Make.com que inclui:
    - Conexão com bancos via Plaid/TrueLayer
    - Processamento de transações
    - Atualização automática de Excel
    - Disparo de análises
    """)
    
    # Download template button (placeholder)
    st.download_button(
        label="📥 Baixar Template Make.com",
        data="Template será gerado na versão completa",
        file_name="marine_seguros_make_template.json",
        mime="application/json"
    )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>{'Sistema Flexível - Detecta automaticamente novas categorias de despesas' if use_flexible_extractor else 'Sistema Padrão - Categorias Fixas'}</p>
        <p>Desenvolvido para Marine Seguros | Powered by Gemini AI</p>
    </div>
    """,
    unsafe_allow_html=True
)