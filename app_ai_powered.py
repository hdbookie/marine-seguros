import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ai_data_extractor import AIDataExtractor
from comparative_analyzer import ComparativeAnalyzer
from direct_extractor import DirectDataExtractor
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Marine Seguros - AI-Powered Analytics",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .comparison-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .insight-box {
        background-color: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 5px 5px 0;
    }
    .metric-comparison {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem;
        background: rgba(255,255,255,0.1);
        border-radius: 5px;
        margin: 0.5rem 0;
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

# Header
st.title("🤖 Marine Seguros - AI-Powered Financial Analytics")
st.markdown("### Análise Inteligente e Comparativa com IA")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help="Chave para análise com IA"
    )
    
    st.subheader("🎯 Modo de Análise")
    analysis_mode = st.radio(
        "Escolha o foco:",
        ["Comparação Temporal", "Análise de Tendências", "Insights Automáticos"]
    )
    
    st.subheader("📊 Visualizações")
    show_ai_explanations = st.checkbox("Mostrar explicações da IA", value=True)
    show_predictions = st.checkbox("Incluir previsões", value=True)
    
    if st.button("🔄 Limpar Cache", type="secondary"):
        st.session_state.clear()
        st.rerun()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📁 Importar Dados", 
    "🔍 Análise Comparativa", 
    "📈 Tendências e Padrões",
    "💡 Insights AI"
])

# Tab 1: Smart Data Import
with tab1:
    st.header("Importação Inteligente de Dados")
    st.info("🤖 Nossa IA entende automaticamente qualquer formato de Excel!")
    
    # File upload
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Arraste seus arquivos Excel aqui",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="A IA identificará automaticamente a estrutura"
        )
        
        use_existing = st.checkbox("Usar arquivos da Marine Seguros (2018-2025)")
    
    with col2:
        st.markdown("### 📋 Status")
        if st.session_state.extracted_data:
            st.success(f"✅ {len(st.session_state.extracted_data)} anos carregados")
            for year in sorted(st.session_state.extracted_data.keys()):
                st.write(f"• {year}")
    
    if st.button("🧠 Processar com IA", type="primary", disabled=not gemini_api_key):
        if not gemini_api_key:
            st.error("Por favor, insira sua chave Gemini API")
        else:
            with st.spinner("🤖 Processando arquivos financeiros..."):
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
                        # Save temporarily
                        with open(uploaded_file.name, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        files_to_process.append(uploaded_file.name)
                
                # Extract data from each file
                extracted_data = {}
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, file in enumerate(files_to_process):
                    status_text.text(f"Analisando: {file}")
                    
                    try:
                        # Use direct extraction for reliability
                        file_data = direct_extractor.extract_from_excel(file)
                        
                        # Merge with existing data
                        for year, data in file_data.items():
                            extracted_data[year] = data
                            st.success(f"✅ {year} - Dados extraídos com sucesso")
                    
                    except Exception as e:
                        st.error(f"Erro em {file}: {str(e)}")
                    
                    progress_bar.progress((idx + 1) / len(files_to_process))
                
                # Store in session state
                st.session_state.extracted_data = extracted_data
                
                # Initialize comparative analyzer
                if len(extracted_data) >= 2:
                    analyzer = ComparativeAnalyzer(gemini_api_key)
                    st.session_state.comparative_analysis = analyzer.analyze_all_years(extracted_data)
                
                status_text.text("✅ Análise concluída!")
                st.balloons()

# Tab 2: Comparative Analysis
with tab2:
    st.header("🔍 Análise Comparativa Inteligente")
    
    if st.session_state.extracted_data and len(st.session_state.extracted_data) >= 2:
        
        # Year selector for comparison
        col1, col2, col3 = st.columns([1, 1, 2])
        
        years = sorted(st.session_state.extracted_data.keys())
        
        with col1:
            year1 = st.selectbox("Primeiro Período", years[:-1], index=len(years)-2)
        
        with col2:
            year2 = st.selectbox("Segundo Período", [y for y in years if y > year1], index=0)
        
        with col3:
            comparison_type = st.selectbox(
                "Tipo de Comparação",
                ["Visão Geral", "Análise Mensal", "Foco em Crescimento", "Análise de Margem"]
            )
        
        # Get data for selected years
        data1 = st.session_state.extracted_data[year1]
        data2 = st.session_state.extracted_data[year2]
        
        # Main comparison metrics
        st.markdown("### 📊 Comparação Principal")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate key metrics
        rev1 = data1['revenue'].get('ANNUAL', sum(v for k, v in data1['revenue'].items() 
                                                if k != 'ANNUAL' and isinstance(v, (int, float))))
        rev2 = data2['revenue'].get('ANNUAL', sum(v for k, v in data2['revenue'].items() 
                                                if k != 'ANNUAL' and isinstance(v, (int, float))))
        
        rev_change = ((rev2 - rev1) / rev1 * 100) if rev1 > 0 else 0
        
        with col1:
            st.metric(
                f"Receita {year1}",
                f"R$ {rev1:,.0f}",
                f"Base"
            )
        
        with col2:
            st.metric(
                f"Receita {year2}",
                f"R$ {rev2:,.0f}",
                f"{rev_change:+.1f}%"
            )
        
        # Get margin data
        margin1 = sum(data1.get('margins', {}).values()) / len(data1.get('margins', {1: 0}))
        margin2 = sum(data2.get('margins', {}).values()) / len(data2.get('margins', {1: 0}))
        
        with col3:
            st.metric(
                "Margem Média",
                f"{margin2:.1f}%",
                f"{(margin2 - margin1):+.1f}pp"
            )
        
        with col4:
            # Growth acceleration
            if st.session_state.comparative_analysis:
                growth_data = st.session_state.comparative_analysis.get('growth_patterns', {})
                trend = growth_data.get('trend', 'stable')
                trend_emoji = {
                    'strong_growth': '🚀',
                    'moderate_growth': '📈',
                    'stable': '➡️',
                    'stagnating': '⚠️',
                    'declining': '📉'
                }.get(trend, '❓')
                
                st.metric(
                    "Tendência Geral",
                    f"{trend_emoji} {trend.replace('_', ' ').title()}",
                    f"CAGR: {growth_data.get('average_growth', 0):.1f}%"
                )
        
        # Monthly comparison chart
        st.markdown("### 📅 Comparação Mensal")
        
        # Prepare monthly comparison data
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        monthly_data = []
        for month in months:
            val1 = data1['revenue'].get(month, 0)
            val2 = data2['revenue'].get(month, 0)
            if val1 > 0:
                change = ((val2 - val1) / val1) * 100
            else:
                change = 0
            
            monthly_data.append({
                'Mês': month,
                year1: val1,
                year2: val2,
                'Variação %': change
            })
        
        monthly_df = pd.DataFrame(monthly_data)
        
        # Create comparison visualization
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(f'Receita Mensal: {year1} vs {year2}', 'Variação Percentual'),
            row_heights=[0.6, 0.4]
        )
        
        # Revenue comparison
        fig.add_trace(
            go.Bar(name=str(year1), x=monthly_df['Mês'], y=monthly_df[year1],
                  marker_color='#667eea'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(name=str(year2), x=monthly_df['Mês'], y=monthly_df[year2],
                  marker_color='#764ba2'),
            row=1, col=1
        )
        
        # Variation chart
        colors = ['green' if x > 0 else 'red' for x in monthly_df['Variação %']]
        fig.add_trace(
            go.Bar(x=monthly_df['Mês'], y=monthly_df['Variação %'],
                  marker_color=colors, showlegend=False,
                  text=monthly_df['Variação %'].round(1),
                  texttemplate='%{text}%',
                  textposition='outside'),
            row=2, col=1
        )
        
        fig.update_layout(height=600, barmode='group')
        st.plotly_chart(fig, use_container_width=True)
        
        # AI Insights for comparison
        if show_ai_explanations and gemini_api_key:
            st.markdown("### 🤖 Análise da IA")
            
            with st.spinner("Gerando insights..."):
                analyzer = ComparativeAnalyzer(gemini_api_key)
                comparison_insights = analyzer.compare_custom_periods(
                    data1, data2, str(year1), str(year2)
                )
                
                if comparison_insights.get('ai_analysis'):
                    st.markdown(
                        f'<div class="insight-box">{comparison_insights["ai_analysis"]}</div>',
                        unsafe_allow_html=True
                    )
        
        # Best/Worst months
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Melhores Meses")
            best_months = monthly_df.nlargest(3, 'Variação %')
            for _, row in best_months.iterrows():
                st.success(f"**{row['Mês']}**: +{row['Variação %']:.1f}% "
                          f"(R$ {row[year1]:,.0f} → R$ {row[year2]:,.0f})")
        
        with col2:
            st.markdown("### 📉 Meses Desafiadores")
            worst_months = monthly_df.nsmallest(3, 'Variação %')
            for _, row in worst_months.iterrows():
                st.error(f"**{row['Mês']}**: {row['Variação %']:.1f}% "
                        f"(R$ {row[year1]:,.0f} → R$ {row[year2]:,.0f})")
    
    else:
        st.info("📊 Carregue pelo menos 2 anos de dados para fazer comparações")

# Tab 3: Trends and Patterns
with tab3:
    st.header("📈 Análise de Tendências e Padrões")
    
    if st.session_state.comparative_analysis:
        analysis = st.session_state.comparative_analysis
        
        # Growth Pattern Analysis
        st.markdown("### 🚀 Padrão de Crescimento")
        
        growth_data = analysis.get('growth_patterns', {})
        growth_rates = growth_data.get('growth_rates', [])
        
        if growth_rates:
            # Create growth visualization
            fig_growth = go.Figure()
            
            periods = [g['period'] for g in growth_rates]
            rates = [g['growth_rate'] for g in growth_rates]
            
            fig_growth.add_trace(go.Scatter(
                x=periods,
                y=rates,
                mode='lines+markers',
                name='Taxa de Crescimento',
                line=dict(width=3, color='#667eea'),
                marker=dict(size=10)
            ))
            
            # Add average line
            avg_growth = growth_data.get('average_growth', 0)
            fig_growth.add_hline(y=avg_growth, line_dash="dash", 
                               annotation_text=f"Média: {avg_growth:.1f}%")
            
            fig_growth.update_layout(
                title='Evolução da Taxa de Crescimento',
                yaxis_title='Crescimento (%)',
                xaxis_title='Período'
            )
            
            st.plotly_chart(fig_growth, use_container_width=True)
            
            # Growth insights
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Crescimento Médio",
                    f"{avg_growth:.1f}%",
                    "CAGR"
                )
            
            with col2:
                volatility = growth_data.get('growth_volatility', 0)
                st.metric(
                    "Volatilidade",
                    f"{volatility:.1f}%",
                    "Desvio padrão"
                )
            
            with col3:
                trend = growth_data.get('trend', 'stable')
                st.metric(
                    "Tendência",
                    trend.replace('_', ' ').title(),
                    "Análise de regressão"
                )
        
        # Seasonal Patterns
        st.markdown("### 🌊 Padrões Sazonais")
        
        seasonal_data = analysis.get('seasonal_trends', {})
        seasonal_index = seasonal_data.get('seasonal_index', {})
        
        if seasonal_index:
            # Create seasonal chart
            months = list(seasonal_index.keys())
            indices = list(seasonal_index.values())
            
            fig_seasonal = go.Figure()
            
            colors = ['green' if idx > 100 else 'red' for idx in indices]
            
            fig_seasonal.add_trace(go.Bar(
                x=months,
                y=indices,
                marker_color=colors,
                text=[f"{idx:.0f}" for idx in indices],
                textposition='outside'
            ))
            
            fig_seasonal.add_hline(y=100, line_dash="dash", 
                                 annotation_text="Média = 100")
            
            fig_seasonal.update_layout(
                title='Índice Sazonal por Mês (100 = média)',
                yaxis_title='Índice Sazonal',
                xaxis_title='Mês'
            )
            
            st.plotly_chart(fig_seasonal, use_container_width=True)
            
            # Seasonal insights
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💪 Meses Fortes")
                strong_months = seasonal_data.get('strong_months', [])
                for month in strong_months:
                    idx = seasonal_index.get(month, 100)
                    st.success(f"**{month}**: Índice {idx:.0f} (+{idx-100:.0f}% vs média)")
            
            with col2:
                st.markdown("#### 📉 Meses Fracos")
                weak_months = seasonal_data.get('weak_months', [])
                for month in weak_months:
                    idx = seasonal_index.get(month, 100)
                    st.warning(f"**{month}**: Índice {idx:.0f} ({idx-100:.0f}% vs média)")
        
        # Quarterly Pattern
        quarterly_data = seasonal_data.get('quarterly_pattern', {})
        if quarterly_data:
            st.markdown("### 📊 Análise Trimestral")
            
            quarters = quarterly_data.get('quarter_index', {})
            
            fig_quarterly = go.Figure(go.Pie(
                labels=list(quarters.keys()),
                values=list(quarters.values()),
                hole=0.4,
                marker_colors=['#667eea', '#764ba2', '#8b5cf6', '#a855f7']
            ))
            
            fig_quarterly.update_layout(
                title='Distribuição de Performance por Trimestre'
            )
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.plotly_chart(fig_quarterly, use_container_width=True)
            
            with col2:
                st.markdown("#### 🏆 Rankings")
                st.success(f"Melhor: **{quarterly_data.get('best_quarter')}**")
                st.error(f"Pior: **{quarterly_data.get('worst_quarter')}**")
                st.info(f"Variância: {quarterly_data.get('variance', 0):.1f}")
        
        # Volatility Analysis
        st.markdown("### 📊 Análise de Volatilidade")
        
        volatility_data = analysis.get('volatility_analysis', {})
        yearly_vol = volatility_data.get('yearly_volatility', {})
        
        if yearly_vol:
            years = sorted(yearly_vol.keys())
            cvs = [yearly_vol[y]['revenue_volatility']['cv'] for y in years]
            
            fig_vol = go.Figure()
            
            fig_vol.add_trace(go.Scatter(
                x=years,
                y=cvs,
                mode='lines+markers',
                fill='tozeroy',
                name='Coeficiente de Variação',
                line=dict(color='orange', width=2)
            ))
            
            fig_vol.update_layout(
                title='Evolução da Volatilidade da Receita',
                yaxis_title='Coeficiente de Variação',
                xaxis_title='Ano'
            )
            
            st.plotly_chart(fig_vol, use_container_width=True)
            
            # Volatility trend
            vol_trend = volatility_data.get('volatility_trend', 'stable')
            if vol_trend == 'increasing':
                st.warning("⚠️ **Atenção**: Volatilidade crescente detectada. "
                          "Isso pode indicar maior incerteza no negócio.")
            else:
                st.success("✅ **Bom sinal**: Volatilidade estável ou decrescente.")
    
    else:
        st.info("📊 Faça a análise dos dados primeiro para ver tendências")

# Tab 4: AI Insights
with tab4:
    st.header("💡 Insights Profundos com IA")
    
    if st.session_state.comparative_analysis and gemini_api_key:
        
        # Insight categories
        insight_type = st.selectbox(
            "Tipo de Insight",
            ["Análise Executiva", "Oportunidades de Crescimento", 
             "Análise de Riscos", "Recomendações Estratégicas", 
             "Previsões e Cenários"]
        )
        
        if st.button("🧠 Gerar Insights", type="primary"):
            with st.spinner("IA analisando dados..."):
                # Get AI insights
                ai_insights = st.session_state.comparative_analysis.get('ai_insights', '')
                
                if ai_insights:
                    st.markdown(ai_insights)
                    
                    # Save insights
                    st.session_state.ai_insights[insight_type] = ai_insights
                    
                    # Download button
                    st.download_button(
                        label="📥 Baixar Relatório",
                        data=ai_insights,
                        file_name=f"insights_marine_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )
        
        # Display saved insights
        if st.session_state.ai_insights:
            st.markdown("### 📚 Insights Salvos")
            
            for category, content in st.session_state.ai_insights.items():
                with st.expander(f"📌 {category}"):
                    st.markdown(content)
        
        # Custom questions
        st.markdown("### ❓ Perguntas Personalizadas")
        
        custom_question = st.text_area(
            "Faça uma pergunta específica sobre os dados",
            placeholder="Ex: Por que março sempre tem performance ruim? Como melhorar Q4?",
            height=100
        )
        
        if custom_question and st.button("🔍 Buscar Resposta"):
            with st.spinner("Analisando sua pergunta..."):
                analyzer = ComparativeAnalyzer(gemini_api_key)
                
                # Prepare context
                context = {
                    'data': st.session_state.extracted_data,
                    'analysis': st.session_state.comparative_analysis,
                    'question': custom_question
                }
                
                # Get AI response
                response = analyzer.model.generate_content(
                    f"Based on this financial data: {json.dumps(context, default=str)}, "
                    f"answer this question: {custom_question}"
                )
                
                st.markdown("### 💬 Resposta da IA")
                st.markdown(response.text)
    
    else:
        if not gemini_api_key:
            st.warning("🔑 Configure sua chave Gemini API para insights com IA")
        else:
            st.info("📊 Processe os dados primeiro para gerar insights")

# Footer with insights summary
if st.session_state.comparative_analysis:
    st.markdown("---")
    st.markdown("### 🎯 Resumo Executivo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📈 Crescimento**")
        growth = st.session_state.comparative_analysis.get('growth_patterns', {})
        avg_growth = growth.get('average_growth', 0)
        trend = growth.get('trend', 'stable')
        
        if avg_growth > 20:
            st.success(f"Excelente: {avg_growth:.1f}% ao ano")
        elif avg_growth > 5:
            st.info(f"Saudável: {avg_growth:.1f}% ao ano")
        else:
            st.warning(f"Atenção: {avg_growth:.1f}% ao ano")
    
    with col2:
        st.markdown("**🎢 Volatilidade**")
        vol = st.session_state.comparative_analysis.get('volatility_analysis', {})
        vol_trend = vol.get('volatility_trend', 'stable')
        
        if vol_trend == 'increasing':
            st.warning("Crescente - Requer atenção")
        else:
            st.success("Controlada - Bom sinal")
    
    with col3:
        st.markdown("**🎯 Próximos Passos**")
        seasonal = st.session_state.comparative_analysis.get('seasonal_trends', {})
        weak_months = seasonal.get('weak_months', [])
        
        if weak_months:
            st.info(f"Focar em: {', '.join(weak_months[:3])}")
        else:
            st.success("Manter estratégia atual")