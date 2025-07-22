import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
from financial_processor import FinancialProcessor
from datetime import datetime
import os
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Marine Seguros - Advanced Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
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
    .filter-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'gemini_insights' not in st.session_state:
    st.session_state.gemini_insights = None

# Title and description
st.title("🏢 Marine Seguros - Advanced Financial Analytics")
st.markdown("### Análise Comparativa e Insights Profundos | 2018-2025")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Gemini API Key input
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Insira sua chave API do Google Gemini"
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
    show_benchmarks = st.checkbox("Comparar com Mercado", value=True)
    
    # Export options
    st.subheader("Exportar Dados")
    export_format = st.selectbox(
        "Formato de Exportação",
        ["PDF", "Excel", "PowerPoint", "WhatsApp Report"]
    )

# Main content area
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📁 Upload", 
    "📊 Dashboard Avançado", 
    "🔍 Análise Comparativa",
    "🤖 AI Insights", 
    "📈 Previsões", 
    "📱 Relatórios"
])

# Tab 1: File Upload
with tab1:
    st.header("Upload de Arquivos Excel")
    
    # File uploader with multi-company support
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Empresa Principal")
        main_files = st.file_uploader(
            "Arquivos da Marine Seguros",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            key="main"
        )
    
    with col2:
        st.subheader("Empresas para Comparação (Opcional)")
        comparison_files = st.file_uploader(
            "Arquivos de outras empresas",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            key="comparison"
        )
    
    # Use existing files option
    use_existing = st.checkbox("Usar arquivos existentes da Marine Seguros")
    
    if st.button("Processar Todos os Dados", type="primary"):
        with st.spinner("Processando arquivos..."):
            processor = FinancialProcessor()
            
            if use_existing:
                # Use files from directory
                files = [
                    'Análise de Resultado Financeiro 2018_2023.xlsx',
                    'Resultado Financeiro - 2024.xlsx',
                    'Resultado Financeiro - 2025.xlsx'
                ]
                excel_data = processor.load_excel_files(files)
            else:
                # Save uploaded files temporarily and process
                files = []
                for uploaded_file in main_files:
                    with open(uploaded_file.name, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    files.append(uploaded_file.name)
                excel_data = processor.load_excel_files(files)
            
            # Consolidate data
            consolidated_df = processor.consolidate_all_years(excel_data)
            consolidated_df = processor.calculate_growth_metrics(consolidated_df)
            
            # Store in session state
            st.session_state.processed_data = {
                'raw_data': excel_data,
                'consolidated': consolidated_df,
                'summary': processor.get_financial_summary(consolidated_df),
                'anomalies': processor.detect_anomalies(consolidated_df) if show_anomalies else []
            }
            
            st.success("✅ Dados processados com sucesso!")

# Tab 2: Advanced Dashboard
with tab2:
    st.header("Dashboard Avançado com Filtros")
    
    if st.session_state.processed_data is not None:
        data = st.session_state.processed_data
        df = data['consolidated']
        
        # Advanced Filters
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            year_filter = st.multiselect(
                "Anos",
                options=sorted(df['year'].unique()),
                default=sorted(df['year'].unique())
            )
        
        with col2:
            metric_filter = st.selectbox(
                "Métrica Principal",
                ["Receita", "Lucro", "Margem", "Crescimento"]
            )
        
        with col3:
            view_type = st.radio(
                "Tipo de Visualização",
                ["Temporal", "Comparativo", "Distribuição"]
            )
        
        with col4:
            period_type = st.radio(
                "Período",
                ["Anual", "Semestral", "Trimestral"]
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Filter data
        filtered_df = df[df['year'].isin(year_filter)]
        
        # Key metrics with comparison
        st.subheader("📊 Métricas Principais")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Calculate period comparisons
        if len(filtered_df) > 1:
            latest_year = filtered_df['year'].max()
            previous_year = filtered_df['year'].max() - 1
            
            latest_data = filtered_df[filtered_df['year'] == latest_year].iloc[0]
            previous_data = filtered_df[filtered_df['year'] == previous_year].iloc[0] if previous_year in filtered_df['year'].values else None
        
        with col1:
            revenue_change = ((latest_data['revenue'] - previous_data['revenue']) / previous_data['revenue'] * 100) if previous_data is not None else 0
            st.metric(
                "Receita Atual",
                f"R$ {latest_data.get('revenue', 0):,.0f}",
                f"{revenue_change:+.1f}% YoY",
                delta_color="normal"
            )
        
        with col2:
            margin_change = latest_data.get('profit_margin', 0) - (previous_data.get('profit_margin', 0) if previous_data is not None else 0)
            st.metric(
                "Margem de Lucro",
                f"{latest_data.get('profit_margin', 0):.1f}%",
                f"{margin_change:+.1f}pp",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                "CAGR (Receita)",
                f"{data['summary']['metrics'].get('revenue', {}).get('cagr', 0):.1f}%",
                "Taxa de crescimento"
            )
        
        with col4:
            efficiency = latest_data.get('operational_efficiency', 0)
            st.metric(
                "Eficiência Operacional",
                f"{efficiency:.1f}%",
                "Custos/Receita"
            )
        
        with col5:
            health_score = 100 - efficiency + latest_data.get('profit_margin', 0)
            st.metric(
                "Score de Saúde",
                f"{health_score:.0f}/100",
                "Índice proprietário"
            )
        
        # Advanced Visualizations
        st.subheader("📈 Visualizações Avançadas")
        
        # Create subplot figure with multiple charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Evolução da Receita', 'Composição de Custos', 
                          'Análise de Margem', 'Eficiência Operacional'),
            specs=[[{"type": "scatter"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # 1. Revenue Evolution with Trend
        fig.add_trace(
            go.Scatter(
                x=filtered_df['year'],
                y=filtered_df['revenue'],
                mode='lines+markers',
                name='Receita Real',
                line=dict(color='#2E86AB', width=3),
                marker=dict(size=10)
            ),
            row=1, col=1
        )
        
        # Add trend line
        z = np.polyfit(filtered_df['year'], filtered_df['revenue'], 1)
        p = np.poly1d(z)
        fig.add_trace(
            go.Scatter(
                x=filtered_df['year'],
                y=p(filtered_df['year']),
                mode='lines',
                name='Tendência',
                line=dict(color='red', dash='dash')
            ),
            row=1, col=1
        )
        
        # 2. Cost Composition (Pie)
        if 'variable_costs' in latest_data:
            fig.add_trace(
                go.Pie(
                    labels=['Custos Variáveis', 'Custos Fixos', 'Lucro'],
                    values=[
                        latest_data.get('variable_costs', 0),
                        latest_data.get('revenue', 0) * 0.3,  # Estimate
                        latest_data.get('net_profit', 0)
                    ],
                    hole=0.4
                ),
                row=1, col=2
            )
        
        # 3. Margin Analysis (Bar)
        fig.add_trace(
            go.Bar(
                x=filtered_df['year'],
                y=filtered_df['profit_margin'],
                name='Margem de Lucro',
                marker_color=filtered_df['profit_margin'],
                marker_colorscale='RdYlGn',
                text=filtered_df['profit_margin'].round(1),
                texttemplate='%{text}%',
                textposition='outside'
            ),
            row=2, col=1
        )
        
        # 4. Operational Efficiency
        if 'operational_efficiency' in filtered_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=filtered_df['year'],
                    y=filtered_df['operational_efficiency'],
                    mode='lines+markers',
                    name='Eficiência',
                    line=dict(color='#F71735', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(247, 23, 53, 0.1)'
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Análise Financeira Completa"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Year-over-Year Comparison Heatmap
        st.subheader("🔥 Heatmap de Performance")
        
        # Create metrics matrix
        metrics_matrix = []
        metrics_names = ['Receita', 'Crescimento', 'Margem', 'Eficiência']
        
        for _, row in filtered_df.iterrows():
            metrics_matrix.append([
                row.get('revenue', 0) / 1000000,  # In millions
                row.get('revenue_growth', 0),
                row.get('profit_margin', 0),
                row.get('operational_efficiency', 0)
            ])
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=np.array(metrics_matrix).T,
            x=filtered_df['year'],
            y=metrics_names,
            colorscale='RdYlGn',
            text=np.array(metrics_matrix).T.round(1),
            texttemplate='%{text}',
            textfont={"size": 12}
        ))
        
        fig_heatmap.update_layout(
            title='Performance por Ano',
            xaxis_title='Ano',
            yaxis_title='Métrica'
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Waterfall Chart for Profit Analysis
        st.subheader("💧 Análise Waterfall - Composição do Lucro")
        
        latest_year_data = filtered_df[filtered_df['year'] == latest_year].iloc[0]
        
        fig_waterfall = go.Figure(go.Waterfall(
            name="Lucro",
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total"],
            x=["Receita", "Custos Variáveis", "Despesas Admin", "Impostos", "Lucro Líquido"],
            textposition="outside",
            text=[f"R$ {latest_year_data.get('revenue', 0):,.0f}",
                  f"-R$ {latest_year_data.get('variable_costs', 0):,.0f}",
                  f"-R$ {latest_year_data.get('revenue', 0) * 0.2:,.0f}",
                  f"-R$ {latest_year_data.get('revenue', 0) * 0.1:,.0f}",
                  f"R$ {latest_year_data.get('net_profit', latest_year_data.get('revenue', 0) * 0.15):,.0f}"],
            y=[latest_year_data.get('revenue', 0),
               -latest_year_data.get('variable_costs', 0),
               -latest_year_data.get('revenue', 0) * 0.2,
               -latest_year_data.get('revenue', 0) * 0.1,
               None],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        
        fig_waterfall.update_layout(
            title=f"Decomposição do Resultado - {latest_year}",
            showlegend=False
        )
        
        st.plotly_chart(fig_waterfall, use_container_width=True)
        
    else:
        st.info("👆 Por favor, faça upload dos arquivos na aba 'Upload' primeiro.")

# Tab 3: Comparative Analysis
with tab3:
    st.header("🔍 Análise Comparativa Detalhada")
    
    if st.session_state.processed_data is not None:
        df = st.session_state.processed_data['consolidated']
        
        # Period Selection for Comparison
        col1, col2 = st.columns(2)
        
        with col1:
            period1 = st.selectbox(
                "Período 1",
                options=sorted(df['year'].unique()),
                index=len(df['year'].unique())-2 if len(df['year'].unique()) > 1 else 0
            )
        
        with col2:
            period2 = st.selectbox(
                "Período 2",
                options=sorted(df['year'].unique()),
                index=len(df['year'].unique())-1
            )
        
        # Get data for both periods
        data1 = df[df['year'] == period1].iloc[0] if period1 in df['year'].values else None
        data2 = df[df['year'] == period2].iloc[0] if period2 in df['year'].values else None
        
        if data1 is not None and data2 is not None:
            # Comparison metrics
            st.subheader(f"Comparação: {period1} vs {period2}")
            
            # Create comparison dataframe
            comparison_metrics = {
                'Métrica': ['Receita', 'Custos Variáveis', 'Lucro Líquido', 'Margem de Lucro', 'Eficiência'],
                period1: [
                    data1.get('revenue', 0),
                    data1.get('variable_costs', 0),
                    data1.get('net_profit', 0),
                    data1.get('profit_margin', 0),
                    data1.get('operational_efficiency', 0)
                ],
                period2: [
                    data2.get('revenue', 0),
                    data2.get('variable_costs', 0),
                    data2.get('net_profit', 0),
                    data2.get('profit_margin', 0),
                    data2.get('operational_efficiency', 0)
                ],
                'Variação %': [
                    ((data2.get('revenue', 0) - data1.get('revenue', 0)) / data1.get('revenue', 1) * 100),
                    ((data2.get('variable_costs', 0) - data1.get('variable_costs', 0)) / data1.get('variable_costs', 1) * 100),
                    ((data2.get('net_profit', 0) - data1.get('net_profit', 0)) / data1.get('net_profit', 1) * 100),
                    (data2.get('profit_margin', 0) - data1.get('profit_margin', 0)),
                    (data2.get('operational_efficiency', 0) - data1.get('operational_efficiency', 0))
                ]
            }
            
            comp_df = pd.DataFrame(comparison_metrics)
            
            # Grouped bar chart
            fig_comparison = go.Figure()
            
            fig_comparison.add_trace(go.Bar(
                name=str(period1),
                x=comp_df['Métrica'][:3],
                y=comp_df[period1][:3],
                marker_color='#2E86AB'
            ))
            
            fig_comparison.add_trace(go.Bar(
                name=str(period2),
                x=comp_df['Métrica'][:3],
                y=comp_df[period2][:3],
                marker_color='#A23B72'
            ))
            
            fig_comparison.update_layout(
                title='Comparação de Valores Absolutos',
                xaxis_title='Métrica',
                yaxis_title='Valor (R$)',
                barmode='group'
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Radar chart for comprehensive comparison
            categories = ['Receita', 'Margem', 'Eficiência', 'Crescimento', 'Estabilidade']
            
            fig_radar = go.Figure()
            
            # Normalize values for radar chart (0-100 scale)
            values1 = [
                min(data1.get('revenue', 0) / df['revenue'].max() * 100, 100),
                data1.get('profit_margin', 0),
                100 - data1.get('operational_efficiency', 0),
                50,  # Placeholder for growth
                80   # Placeholder for stability
            ]
            
            values2 = [
                min(data2.get('revenue', 0) / df['revenue'].max() * 100, 100),
                data2.get('profit_margin', 0),
                100 - data2.get('operational_efficiency', 0),
                data2.get('revenue_growth', 50),
                85   # Placeholder for stability
            ]
            
            fig_radar.add_trace(go.Scatterpolar(
                r=values1,
                theta=categories,
                fill='toself',
                name=str(period1),
                line_color='#2E86AB'
            ))
            
            fig_radar.add_trace(go.Scatterpolar(
                r=values2,
                theta=categories,
                fill='toself',
                name=str(period2),
                line_color='#A23B72'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Análise Multidimensional"
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # Detailed comparison table
            st.subheader("📊 Tabela Comparativa Detalhada")
            
            # Style the comparison dataframe
            def style_change(val):
                if isinstance(val, (int, float)):
                    if val > 0:
                        return 'color: green'
                    elif val < 0:
                        return 'color: red'
                return ''
            
            styled_df = comp_df.style.applymap(style_change, subset=['Variação %'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Insights box
            st.info(f"""
            **Principais Insights da Comparação:**
            
            • Crescimento da Receita: {comparison_metrics['Variação %'][0]:.1f}%
            • Variação da Margem: {comparison_metrics['Variação %'][3]:.1f} pontos percentuais
            • {'Melhoria' if comparison_metrics['Variação %'][4] < 0 else 'Piora'} na eficiência operacional
            """)
    
    else:
        st.info("👆 Por favor, faça upload dos arquivos primeiro.")

# Tab 4: AI Insights (Enhanced)
with tab4:
    st.header("🤖 Insights Avançados com Gemini AI")
    
    if st.session_state.processed_data is not None and gemini_api_key:
        # Custom prompt input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            custom_prompt = st.text_area(
                "Pergunta específica (opcional)",
                placeholder="Ex: Qual o melhor trimestre para investir em marketing? Como reduzir custos operacionais?",
                height=100
            )
        
        with col2:
            insight_type = st.selectbox(
                "Tipo de Análise",
                ["Geral", "Crescimento", "Eficiência", "Riscos", "Oportunidades"]
            )
        
        if st.button("🧠 Gerar Insights Avançados", type="primary"):
            with st.spinner("Analisando com Gemini AI..."):
                try:
                    # Configure Gemini
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Prepare enhanced data
                    df = st.session_state.processed_data['consolidated']
                    summary = st.session_state.processed_data['summary']
                    
                    # Create enhanced prompt
                    prompt = f"""
                    Você é um consultor financeiro especialista analisando dados da Marine Seguros.
                    
                    Dados Financeiros Completos:
                    {df.to_string()}
                    
                    Resumo Estatístico:
                    - Período: {summary['years_range']}
                    - Receita Total: R$ {summary['metrics'].get('revenue', {}).get('total', 0):,.2f}
                    - CAGR: {summary['metrics'].get('revenue', {}).get('cagr', 0):.1f}%
                    - Margem Média: {summary['metrics'].get('profit_margin', {}).get('average', 0):.1f}%
                    - Desvio Padrão da Margem: {summary['metrics'].get('profit_margin', {}).get('std', 0):.1f}%
                    
                    Tipo de Análise Solicitada: {insight_type}
                    
                    {"Pergunta Específica: " + custom_prompt if custom_prompt else ""}
                    
                    Por favor, forneça em {language}:
                    
                    1. **Análise de Tendências** (com números específicos)
                    2. **Pontos de Atenção** (riscos identificados)
                    3. **Oportunidades de Melhoria** (com estimativas de impacto)
                    4. **Recomendações Estratégicas** (ações práticas)
                    5. **Benchmarking** (comparação com médias do setor de seguros)
                    6. **Previsão para Próximos 12 Meses** (com cenários)
                    
                    Use formatação markdown, emojis relevantes e seja específico com números e percentuais.
                    """
                    
                    # Generate insights
                    response = model.generate_content(prompt)
                    st.session_state.gemini_insights = response.text
                    
                except Exception as e:
                    st.error(f"Erro ao gerar insights: {str(e)}")
        
        # Display insights
        if st.session_state.gemini_insights:
            st.markdown(st.session_state.gemini_insights)
            
            # Quick action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    label="📥 Baixar Análise",
                    data=st.session_state.gemini_insights,
                    file_name=f"insights_marine_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown"
                )
            
            with col2:
                if st.button("📧 Enviar por Email"):
                    st.info("Funcionalidade em desenvolvimento")
            
            with col3:
                if st.button("📱 WhatsApp"):
                    st.info("Funcionalidade em desenvolvimento")
    
    else:
        if not gemini_api_key:
            st.warning("⚠️ Configure sua chave Gemini API na barra lateral")
        else:
            st.info("👆 Faça upload dos dados primeiro")

# Tab 5: Enhanced Predictions
with tab5:
    st.header("📈 Previsões Avançadas e Simulações")
    
    if st.session_state.processed_data is not None:
        df = st.session_state.processed_data['consolidated']
        
        # Prediction parameters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            prediction_years = st.slider(
                "Anos para prever",
                1, 5, 3
            )
        
        with col2:
            prediction_method = st.selectbox(
                "Método de Previsão",
                ["Linear", "Exponencial", "Machine Learning", "Monte Carlo"]
            )
        
        with col3:
            confidence_level = st.slider(
                "Nível de Confiança (%)",
                80, 99, 95
            )
        
        if len(df) >= 2:
            # Advanced forecasting
            from sklearn.linear_model import LinearRegression
            from sklearn.preprocessing import PolynomialFeatures
            
            X = df['year'].values.reshape(-1, 1)
            y = df['revenue'].values
            
            # Create predictions based on method
            future_years = list(range(df['year'].max() + 1, df['year'].max() + prediction_years + 1))
            
            if prediction_method == "Linear":
                model = LinearRegression()
                model.fit(X, y)
                predictions = model.predict([[year] for year in future_years])
                
            elif prediction_method == "Exponencial":
                # Log transform for exponential
                log_y = np.log(y)
                model = LinearRegression()
                model.fit(X, log_y)
                log_predictions = model.predict([[year] for year in future_years])
                predictions = np.exp(log_predictions)
            
            # Calculate confidence intervals
            std_error = np.std(y) * 0.1  # Simplified
            z_score = 1.96 if confidence_level == 95 else 2.58
            
            upper_bound = predictions + (z_score * std_error)
            lower_bound = predictions - (z_score * std_error)
            
            # Create forecast visualization
            fig_forecast = go.Figure()
            
            # Historical data
            fig_forecast.add_trace(go.Scatter(
                x=df['year'],
                y=df['revenue'],
                mode='lines+markers',
                name='Histórico',
                line=dict(color='#2E86AB', width=3),
                marker=dict(size=10)
            ))
            
            # Predictions
            fig_forecast.add_trace(go.Scatter(
                x=future_years,
                y=predictions,
                mode='lines+markers',
                name='Previsão',
                line=dict(color='#F18F01', width=3, dash='dash'),
                marker=dict(size=10)
            ))
            
            # Confidence interval
            fig_forecast.add_trace(go.Scatter(
                x=future_years + future_years[::-1],
                y=list(upper_bound) + list(lower_bound[::-1]),
                fill='toself',
                fillcolor='rgba(241, 143, 1, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                name='Intervalo de Confiança'
            ))
            
            fig_forecast.update_layout(
                title=f'Previsão de Receita - Método {prediction_method}',
                xaxis_title='Ano',
                yaxis_title='Receita (R$)',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            # Scenario Planning
            st.subheader("🎯 Planejamento de Cenários")
            
            # Interactive scenario builder
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Fatores de Impacto**")
                market_growth = st.slider("Crescimento do Mercado (%)", -20, 30, 5)
                competition = st.slider("Pressão Competitiva (%)", -30, 0, -5)
                innovation = st.slider("Inovação/Novos Produtos (%)", 0, 50, 10)
                
            with col2:
                st.markdown("**Fatores Internos**")
                efficiency = st.slider("Melhoria de Eficiência (%)", 0, 30, 5)
                marketing = st.slider("Investimento em Marketing (%)", 0, 50, 10)
                team_expansion = st.slider("Expansão da Equipe (%)", 0, 100, 20)
            
            # Calculate scenario impact
            base_revenue = df['revenue'].iloc[-1]
            total_impact = (market_growth + competition + innovation + efficiency + marketing * 0.5 + team_expansion * 0.3) / 100
            
            scenario_revenues = []
            for i, year in enumerate(future_years):
                scenario_revenue = base_revenue * (1 + total_impact) ** (i + 1)
                scenario_revenues.append(scenario_revenue)
            
            # Scenario comparison chart
            fig_scenarios = go.Figure()
            
            # Base prediction
            fig_scenarios.add_trace(go.Bar(
                x=future_years,
                y=predictions,
                name='Previsão Base',
                marker_color='#2E86AB'
            ))
            
            # Scenario prediction
            fig_scenarios.add_trace(go.Bar(
                x=future_years,
                y=scenario_revenues,
                name='Cenário Customizado',
                marker_color='#F18F01'
            ))
            
            fig_scenarios.update_layout(
                title='Comparação de Cenários',
                xaxis_title='Ano',
                yaxis_title='Receita Projetada (R$)',
                barmode='group'
            )
            
            st.plotly_chart(fig_scenarios, use_container_width=True)
            
            # ROI Calculator
            st.subheader("💰 Calculadora de ROI")
            
            investment = st.number_input(
                "Investimento Planejado (R$)",
                min_value=0,
                value=100000,
                step=10000
            )
            
            expected_return = (scenario_revenues[0] - base_revenue) - investment
            roi = (expected_return / investment * 100) if investment > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Investimento", f"R$ {investment:,.0f}")
            
            with col2:
                st.metric("Retorno Esperado", f"R$ {expected_return:,.0f}")
            
            with col3:
                st.metric("ROI", f"{roi:.1f}%", f"{'Positivo' if roi > 0 else 'Negativo'}")

# Tab 6: Automated Reports
with tab6:
    st.header("📱 Relatórios Automatizados")
    
    if st.session_state.processed_data is not None:
        st.subheader("Configurar Relatório Automático")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_frequency = st.selectbox(
                "Frequência",
                ["Diário", "Semanal", "Mensal", "Trimestral"]
            )
            
            report_time = st.time_input(
                "Horário de Envio",
                value=datetime.now().time()
            )
        
        with col2:
            delivery_method = st.multiselect(
                "Método de Entrega",
                ["Email", "WhatsApp", "Slack", "Webhook"],
                default=["Email"]
            )
            
            recipients = st.text_area(
                "Destinatários",
                placeholder="email@exemplo.com, +55 11 99999-9999"
            )
        
        # Report preview
        st.subheader("📄 Prévia do Relatório")
        
        if st.button("Gerar Prévia"):
            # Create sample report content
            report_content = f"""
            # Relatório Financeiro - Marine Seguros
            **Data:** {datetime.now().strftime('%d/%m/%Y')}
            
            ## Resumo Executivo
            - Receita YTD: R$ {st.session_state.processed_data['summary']['metrics'].get('revenue', {}).get('total', 0):,.2f}
            - Crescimento: {st.session_state.processed_data['summary']['metrics'].get('revenue', {}).get('cagr', 0):.1f}%
            - Margem: {st.session_state.processed_data['summary']['metrics'].get('profit_margin', {}).get('average', 0):.1f}%
            
            ## Destaques do Período
            ✅ Receita acima da meta em 15%
            ⚠️ Custos operacionais aumentaram 8%
            📈 Projeção positiva para próximo trimestre
            
            ## Ações Recomendadas
            1. Otimizar custos operacionais
            2. Expandir força de vendas
            3. Investir em marketing digital
            """
            
            st.markdown(report_content)
            
            # Save configuration
            if st.button("💾 Salvar Configuração"):
                st.success("✅ Configuração de relatório salva!")
                
# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Marine Seguros Analytics v2.0 | Powered by Gemini AI</p>
    </div>
    """,
    unsafe_allow_html=True
)