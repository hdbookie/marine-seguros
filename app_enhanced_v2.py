import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ai_data_extractor import AIDataExtractor
from comparative_analyzer import ComparativeAnalyzer
from direct_extractor import DirectDataExtractor
from filter_system import FilterSystem, FilterState
from ai_chat_assistant import AIChatAssistant
from interactive_charts import InteractiveCharts
from month_analytics import MonthAnalytics
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Marine Seguros - Analytics Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for new features
st.markdown("""
    <style>
    /* Filter bar styling */
    .filter-bar {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Chat interface styling */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    
    .ai-message {
        background-color: #f3e5f5;
        margin-right: 20%;
    }
    
    /* Interactive chart styling */
    .chart-container {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* Month grid styling */
    .month-button {
        width: 100%;
        padding: 0.75rem;
        margin: 0.25rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .month-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* KPI card styling */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .kpi-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = {}
if 'comparative_analysis' not in st.session_state:
    st.session_state.comparative_analysis = None
if 'ai_insights' not in st.session_state:
    st.session_state.ai_insights = {}
if 'filter_system' not in st.session_state:
    st.session_state.filter_system = FilterSystem()
if 'chat_assistant' not in st.session_state:
    st.session_state.chat_assistant = None
if 'charts' not in st.session_state:
    st.session_state.charts = InteractiveCharts()
if 'month_analytics' not in st.session_state:
    st.session_state.month_analytics = MonthAnalytics()

# Header
st.title("🚀 Marine Seguros - Advanced Analytics Platform")
st.markdown("### Plataforma Inteligente com IA, Filtros Interativos e Chat")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configurações")
    
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Chave para análise com IA"
    )
    
    # Initialize chat assistant if API key is provided
    if gemini_api_key and not st.session_state.chat_assistant:
        st.session_state.chat_assistant = AIChatAssistant(gemini_api_key)
    
    st.subheader("📊 Opções de Visualização")
    show_filters = st.checkbox("Mostrar Filtros Avançados", value=True)
    show_chat = st.checkbox("Ativar Chat com IA", value=True)
    show_interactive = st.checkbox("Charts Interativos", value=True)
    
    st.subheader("🎨 Tema")
    theme = st.selectbox("Escolha o tema", ["Profissional", "Colorido", "Minimalista"])
    
    if st.button("🔄 Resetar Aplicação", type="secondary"):
        st.session_state.clear()
        st.rerun()

# Main content area
# First, show filter bar if enabled
if show_filters and st.session_state.extracted_data:
    with st.container():
        st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
        filter_state = st.session_state.filter_system.render_filter_bar(
            st.session_state.extracted_data
        )
        st.markdown('</div>', unsafe_allow_html=True)

# Main tabs
if show_chat:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📁 Dados", 
        "📊 Dashboard", 
        "🔍 Análise",
        "📈 Tendências",
        "🗓️ Análise Mensal",
        "💬 Chat IA"
    ])
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📁 Dados", 
        "📊 Dashboard", 
        "🔍 Análise",
        "📈 Tendências",
        "🗓️ Análise Mensal"
    ])

# Tab 1: Data Import
with tab1:
    st.header("📁 Importação Inteligente de Dados")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("🤖 Nossa IA entende automaticamente qualquer formato de Excel!")
        
        uploaded_files = st.file_uploader(
            "Arraste seus arquivos Excel aqui",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="A IA identificará automaticamente a estrutura"
        )
        
        use_existing = st.checkbox(
            "Usar arquivos da Marine Seguros (2018-2025)",
            value=True
        )
    
    with col2:
        if st.session_state.extracted_data:
            st.markdown("### 📊 Status dos Dados")
            st.success(f"✅ {len(st.session_state.extracted_data)} anos carregados")
            
            years = sorted(st.session_state.extracted_data.keys())
            for year in years:
                revenue = st.session_state.extracted_data[year].get('revenue', {})
                total = sum(v for k, v in revenue.items() 
                          if k != 'ANNUAL' and isinstance(v, (int, float)))
                st.write(f"**{year}**: R$ {total:,.0f}")
    
    if st.button("🚀 Processar Dados", type="primary", disabled=not gemini_api_key):
        if not gemini_api_key:
            st.error("Por favor, insira sua chave Gemini API")
        else:
            with st.spinner("🤖 Processando dados financeiros..."):
                # Initialize extractors
                direct_extractor = DirectDataExtractor()
                ai_extractor = AIDataExtractor(gemini_api_key)
                
                # Process files
                files_to_process = []
                
                if use_existing:
                    files_to_process = [
                        'Análise de Resultado Financeiro 2018_2023.xlsx',
                        'Resultado Financeiro - 2024.xlsx',
                        'Resultado Financeiro - 2025.xlsx'
                    ]
                else:
                    for uploaded_file in uploaded_files:
                        with open(uploaded_file.name, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        files_to_process.append(uploaded_file.name)
                
                # Extract data
                extracted_data = {}
                progress_bar = st.progress(0)
                
                for idx, file in enumerate(files_to_process):
                    try:
                        file_data = direct_extractor.extract_from_excel(file)
                        extracted_data.update(file_data)
                    except Exception as e:
                        st.error(f"Erro em {file}: {str(e)}")
                    
                    progress_bar.progress((idx + 1) / len(files_to_process))
                
                # Store in session state
                st.session_state.extracted_data = extracted_data
                
                # Initialize comparative analyzer
                if len(extracted_data) >= 2:
                    analyzer = ComparativeAnalyzer(gemini_api_key)
                    st.session_state.comparative_analysis = analyzer.analyze_all_years(extracted_data)
                
                st.success("✅ Dados processados com sucesso!")
                st.balloons()

# Tab 2: Interactive Dashboard
with tab2:
    st.header("📊 Dashboard Interativo")
    
    if st.session_state.extracted_data:
        # Apply filters if active
        filtered_data = st.session_state.extracted_data
        if show_filters:
            filtered_data = st.session_state.filter_system.apply_filters(
                st.session_state.extracted_data
            )
        
        if filtered_data:
            # KPI Cards
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
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Receita Total</div>
                        <div class="kpi-value">R$ {total_revenue/1e6:.1f}M</div>
                        <div class="kpi-label">{years_count} anos</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Margem Média</div>
                        <div class="kpi-value">{avg_margin:.1f}%</div>
                        <div class="kpi-label">Todos os períodos</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col3:
                growth = 0
                if st.session_state.comparative_analysis:
                    growth = st.session_state.comparative_analysis.get(
                        'growth_patterns', {}
                    ).get('average_growth', 0)
                
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Crescimento Médio</div>
                        <div class="kpi-value">{growth:.1f}%</div>
                        <div class="kpi-label">CAGR</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col4:
                best_month = "N/A"
                if st.session_state.comparative_analysis:
                    seasonal = st.session_state.comparative_analysis.get('seasonal_trends', {})
                    strong_months = seasonal.get('strong_months', [])
                    if strong_months:
                        best_month = strong_months[0]
                
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Melhor Mês</div>
                        <div class="kpi-value">{best_month}</div>
                        <div class="kpi-label">Histórico</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Interactive Charts
            st.markdown("### 📈 Visualizações Interativas")
            
            if show_interactive:
                # Main dashboard
                dashboard_fig = st.session_state.charts.create_revenue_dashboard(
                    filtered_data, 
                    st.session_state.filter_state if show_filters else None
                )
                st.plotly_chart(dashboard_fig, use_container_width=True)
                
                # Additional charts
                col1, col2 = st.columns(2)
                
                with col1:
                    heatmap_fig = st.session_state.charts.create_monthly_heatmap(filtered_data)
                    st.plotly_chart(heatmap_fig, use_container_width=True)
                
                with col2:
                    margin_fig = st.session_state.charts.create_margin_analysis(filtered_data)
                    st.plotly_chart(margin_fig, use_container_width=True)
            else:
                # Simple charts if interactive mode is off
                years = sorted(filtered_data.keys())
                revenues = []
                for year in years:
                    revenue = sum(v for k, v in filtered_data[year].get('revenue', {}).items() 
                                if k != 'ANNUAL' and isinstance(v, (int, float)))
                    revenues.append(revenue)
                
                fig = px.line(x=years, y=revenues, 
                             title="Evolução da Receita",
                             labels={'x': 'Ano', 'y': 'Receita (R$)'})
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum dado disponível com os filtros aplicados")
    else:
        st.info("📊 Carregue os dados primeiro para ver o dashboard")

# Tab 3: Comparative Analysis
with tab3:
    st.header("🔍 Análise Comparativa Detalhada")
    
    if st.session_state.extracted_data and len(st.session_state.extracted_data) >= 2:
        # Apply filters
        filtered_data = st.session_state.extracted_data
        if show_filters:
            filtered_data = st.session_state.filter_system.apply_filters(
                st.session_state.extracted_data
            )
        
        if len(filtered_data) >= 2:
            years = sorted(filtered_data.keys())
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                year1 = st.selectbox("Primeiro Período", years[:-1], index=len(years)-2)
            
            with col2:
                year2 = st.selectbox("Segundo Período", 
                                   [y for y in years if y > year1], 
                                   index=0)
            
            with col3:
                comparison_type = st.selectbox(
                    "Tipo de Análise",
                    ["Completa", "Receita", "Margem", "Mensal"]
                )
            
            # Create comparison
            if comparison_type == "Completa":
                comparison_fig = st.session_state.charts.create_comparison_chart(
                    filtered_data, year1, year2
                )
                st.plotly_chart(comparison_fig, use_container_width=True)
                
                # AI insights for comparison
                if gemini_api_key:
                    with st.spinner("🤖 Gerando insights..."):
                        analyzer = ComparativeAnalyzer(gemini_api_key)
                        insights = analyzer.compare_custom_periods(
                            filtered_data[year1], 
                            filtered_data[year2],
                            str(year1), 
                            str(year2)
                        )
                        
                        if insights.get('ai_analysis'):
                            st.markdown("### 🤖 Análise da IA")
                            st.info(insights['ai_analysis'])
            
            # Performance metrics
            st.markdown("### 📊 Métricas de Performance")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Year 1 metrics
                st.markdown(f"#### {year1}")
                revenue1 = sum(v for k, v in filtered_data[year1].get('revenue', {}).items() 
                             if k != 'ANNUAL' and isinstance(v, (int, float)))
                margin1 = sum(filtered_data[year1].get('margins', {}).values()) / 12
                
                st.metric("Receita Total", f"R$ {revenue1:,.0f}")
                st.metric("Margem Média", f"{margin1:.1f}%")
            
            with col2:
                # Year 2 metrics
                st.markdown(f"#### {year2}")
                revenue2 = sum(v for k, v in filtered_data[year2].get('revenue', {}).items() 
                             if k != 'ANNUAL' and isinstance(v, (int, float)))
                margin2 = sum(filtered_data[year2].get('margins', {}).values()) / 12
                
                growth = ((revenue2 - revenue1) / revenue1 * 100) if revenue1 > 0 else 0
                margin_change = margin2 - margin1
                
                st.metric("Receita Total", f"R$ {revenue2:,.0f}", f"{growth:+.1f}%")
                st.metric("Margem Média", f"{margin2:.1f}%", f"{margin_change:+.1f}pp")
        else:
            st.warning("Selecione pelo menos 2 anos nos filtros para comparar")
    else:
        st.info("📊 Carregue pelo menos 2 anos de dados para fazer comparações")

# Tab 4: Trends
with tab4:
    st.header("📈 Análise de Tendências e Padrões")
    
    if st.session_state.comparative_analysis:
        # Growth Pattern Analysis
        st.markdown("### 🚀 Padrão de Crescimento")
        
        growth_data = st.session_state.comparative_analysis.get('growth_patterns', {})
        
        if growth_data:
            # Create metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_growth = growth_data.get('average_growth', 0)
                st.metric("Crescimento Médio", f"{avg_growth:.1f}%", "CAGR")
            
            with col2:
                volatility = growth_data.get('growth_volatility', 0)
                st.metric("Volatilidade", f"{volatility:.1f}%", "Desvio padrão")
            
            with col3:
                trend = growth_data.get('trend', 'stable')
                trend_map = {
                    'strong_growth': 'Forte Crescimento',
                    'moderate_growth': 'Crescimento Moderado',
                    'stable': 'Estável',
                    'declining': 'Declínio'
                }
                st.metric("Tendência", trend_map.get(trend, trend))
            
            with col4:
                consistency = "Sim" if volatility < 20 else "Não"
                st.metric("Crescimento Consistente", consistency)
        
        # Seasonal Analysis
        st.markdown("### 🌊 Análise Sazonal")
        
        seasonal_data = st.session_state.comparative_analysis.get('seasonal_trends', {})
        
        if seasonal_data:
            # Monthly performance
            seasonal_index = seasonal_data.get('seasonal_index', {})
            
            if seasonal_index:
                months = list(seasonal_index.keys())
                indices = list(seasonal_index.values())
                
                fig = go.Figure()
                
                colors = ['green' if idx > 100 else 'red' for idx in indices]
                
                fig.add_trace(go.Bar(
                    x=months,
                    y=indices,
                    marker_color=colors,
                    text=[f"{idx:.0f}" for idx in indices],
                    textposition='outside'
                ))
                
                fig.add_hline(y=100, line_dash="dash", 
                            annotation_text="Média = 100")
                
                fig.update_layout(
                    title='Índice Sazonal por Mês',
                    yaxis_title='Índice',
                    xaxis_title='Mês',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Best and worst months
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 💪 Meses Fortes")
                    strong_months = seasonal_data.get('strong_months', [])[:3]
                    for month in strong_months:
                        idx = seasonal_index.get(month, 100)
                        st.success(f"**{month}**: Índice {idx:.0f}")
                
                with col2:
                    st.markdown("#### 📉 Meses Fracos")
                    weak_months = seasonal_data.get('weak_months', [])[:3]
                    for month in weak_months:
                        idx = seasonal_index.get(month, 100)
                        st.warning(f"**{month}**: Índice {idx:.0f}")
    else:
        st.info("📊 Processe os dados primeiro para ver tendências")

# Tab 5: Month Analytics
with tab5:
    st.header("🗓️ Análise Detalhada por Mês")
    
    if st.session_state.extracted_data:
        # Month selector
        col1, col2 = st.columns([1, 3])
        
        with col1:
            selected_month = st.selectbox(
                "Selecione o Mês",
                st.session_state.month_analytics.months,
                format_func=lambda x: st.session_state.month_analytics.month_names[x]
            )
        
        with col2:
            analysis_type = st.radio(
                "Tipo de Análise",
                ["Performance Individual", "Comparação de Meses", "Correlações"],
                horizontal=True
            )
        
        if analysis_type == "Performance Individual":
            # Analyze selected month
            month_analysis = st.session_state.month_analytics.analyze_month_performance(
                st.session_state.extracted_data,
                selected_month
            )
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            stats = month_analysis['statistics']
            
            with col1:
                st.metric(
                    "Receita Média",
                    f"R$ {stats['avg_revenue']:,.0f}",
                    f"CV: {stats['cv_revenue']:.0f}%"
                )
            
            with col2:
                st.metric(
                    "Margem Média",
                    f"{stats['avg_margin']:.1f}%"
                )
            
            with col3:
                trends = month_analysis['trends']
                if trends:
                    st.metric(
                        "Crescimento Médio",
                        f"{trends['avg_growth']:.1f}%",
                        "ao ano"
                    )
            
            # Yearly performance
            st.markdown("### 📊 Performance Anual")
            
            years = sorted(month_analysis['yearly_performance'].keys())
            revenues = [month_analysis['yearly_performance'][y]['revenue'] for y in years]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=years,
                y=revenues,
                text=[f"R$ {r:,.0f}" for r in revenues],
                textposition='outside'
            ))
            
            fig.update_layout(
                title=f"Receita de {month_analysis['month_name']} por Ano",
                xaxis_title="Ano",
                yaxis_title="Receita (R$)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Insights
            if month_analysis['insights']:
                st.markdown("### 💡 Insights")
                for insight in month_analysis['insights']:
                    st.info(insight)
        
        elif analysis_type == "Comparação de Meses":
            # Multi-month comparison
            selected_months = st.multiselect(
                "Selecione meses para comparar",
                st.session_state.month_analytics.months,
                default=st.session_state.month_analytics.months[:3],
                format_func=lambda x: st.session_state.month_analytics.month_names[x]
            )
            
            if len(selected_months) >= 2:
                comparison = st.session_state.month_analytics.compare_months(
                    st.session_state.extracted_data,
                    selected_months
                )
                
                # Display rankings
                st.markdown("### 🏆 Rankings")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### Receita")
                    for i, (month, value) in enumerate(comparison['rankings']['revenue']):
                        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else ""
                        st.write(f"{medal} {st.session_state.month_analytics.month_names[month]}: R$ {value:,.0f}")
                
                with col2:
                    st.markdown("#### Margem")
                    for i, (month, value) in enumerate(comparison['rankings']['margin']):
                        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else ""
                        st.write(f"{medal} {st.session_state.month_analytics.month_names[month]}: {value:.1f}%")
                
                with col3:
                    st.markdown("#### Estabilidade")
                    for i, (month, value) in enumerate(comparison['rankings']['stability']):
                        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else ""
                        st.write(f"{medal} {st.session_state.month_analytics.month_names[month]}: CV {value:.0f}%")
                
                # Patterns
                if comparison['patterns']:
                    st.markdown("### 🔍 Padrões Identificados")
                    for pattern in comparison['patterns']:
                        st.info(pattern)
        
        else:  # Correlações
            # Month correlations
            correlations = st.session_state.month_analytics.find_month_correlations(
                st.session_state.extracted_data
            )
            
            if correlations['correlation_matrix']:
                st.markdown("### 🔗 Correlações entre Meses")
                
                # Create heatmap
                import numpy as np
                
                months = st.session_state.month_analytics.months
                corr_matrix = []
                for month1 in months:
                    row = []
                    for month2 in months:
                        corr = correlations['correlation_matrix'][month1][month2]
                        row.append(corr)
                    corr_matrix.append(row)
                
                fig = go.Figure(data=go.Heatmap(
                    z=corr_matrix,
                    x=months,
                    y=months,
                    colorscale='RdBu',
                    zmid=0,
                    text=[[f"{v:.2f}" for v in row] for row in corr_matrix],
                    texttemplate="%{text}",
                    textfont={"size": 10}
                ))
                
                fig.update_layout(
                    title="Matriz de Correlação entre Meses",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Strong correlations
                if correlations['strong_correlations']:
                    st.markdown("### 💪 Correlações Fortes")
                    for corr in correlations['strong_correlations']:
                        corr_type = "positiva" if corr['type'] == 'positive' else "negativa"
                        st.info(
                            f"{corr['month1']} e {corr['month2']}: "
                            f"Correlação {corr_type} de {corr['correlation']:.2f}"
                        )
    else:
        st.info("📊 Carregue os dados primeiro para análise mensal")

# Tab 6: AI Chat (if enabled)
if show_chat and 'tab6' in locals():
    with tab6:
        st.header("💬 Chat com IA")
        
        if st.session_state.chat_assistant and st.session_state.extracted_data:
            # Get filter context
            filter_context = st.session_state.filter_system.get_filter_context()
            
            # Apply filters to data for chat
            filtered_data = st.session_state.extracted_data
            if show_filters:
                filtered_data = st.session_state.filter_system.apply_filters(
                    st.session_state.extracted_data
                )
            
            # Render chat interface
            st.session_state.chat_assistant.render_chat_interface(
                filtered_data,
                filter_context
            )
        else:
            if not gemini_api_key:
                st.warning("🔑 Configure sua chave Gemini API para usar o chat")
            else:
                st.info("📊 Carregue os dados primeiro para usar o chat")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Marine Seguros Analytics Platform v2.0 | Powered by AI 🤖</p>
        <p>Desenvolvido com Streamlit, Plotly, e Google Gemini</p>
    </div>
    """,
    unsafe_allow_html=True
)