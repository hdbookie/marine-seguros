"""
AI Insights Tab - Legacy version extracted from app.py
Preserves all original functionality while organizing code
"""

import streamlit as st
import pandas as pd
from core.ai_analyzer import AIAnalyzer
from utils.legacy_helpers import process_detailed_monthly_data


def render_ai_insights_tab(db, gemini_api_key, language):
    """Render the AI insights tab with Gemini AI analysis"""
    
    st.header("🤖 Insights com Gemini AI")

    if not gemini_api_key:
        st.warning("⚠️ Por favor, insira sua chave de API do Gemini na barra lateral para usar os insights de IA.")
        st.info("Você pode obter uma chave de API gratuita no [Google AI Studio](https://makersuite.google.com/app/apikey)")
        return

    # Initialize AI Analyzer
    try:
        ai_analyzer = AIAnalyzer(api_key=gemini_api_key, language=language)
    except Exception as e:
        st.error(f"Erro ao inicializar o Analisador de IA: {e}")
        return

    # Load extracted data from database if not in session state
    if not hasattr(st.session_state, 'extracted_data') or not st.session_state.extracted_data:
        st.session_state.extracted_data = db.load_all_financial_data()

    tab1, tab2 = st.tabs(["Análise Macro", "Análise Micro"])

    with tab1:
        render_macro_analysis(db, ai_analyzer)

    with tab2:
        render_micro_analysis(db, ai_analyzer)


def render_macro_analysis(db, ai_analyzer):
    """Render the macro analysis section"""
    st.subheader("📈 Insights de Negócios de Nível Macro")

    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data is not None:
        # Display existing insights if available
        if hasattr(st.session_state, 'gemini_insights') and st.session_state.gemini_insights:
            st.markdown("### 📊 Relatório de Análise de Negócios")
            st.markdown(st.session_state.gemini_insights)
            st.markdown("---")
        
        if st.button("🤖 Gerar Insights de Negócios com IA", type="primary"):
            with st.spinner("Analisando dados com IA... Por favor, aguarde..."):
                try:
                    # Prepare data for analysis
                    df = st.session_state.processed_data.get('consolidated', pd.DataFrame())
                    if not isinstance(df, pd.DataFrame):
                        df = pd.DataFrame()
                    summary = st.session_state.processed_data.get('summary', {})
                    
                    # Include flexible data insights
                    flexible_summary = ""
                    if hasattr(st.session_state, 'flexible_data') and st.session_state.flexible_data:
                        all_categories = set()
                        all_items = set()
                        for year_data in st.session_state.flexible_data.values():
                            all_categories.update(year_data['categories'].keys())
                            all_items.update(item['label'] for item in year_data['line_items'].values())
                        
                        flexible_summary = f"\n\nCategorias detectadas: {len(all_categories)}\nTotal de linhas de dados: {len(all_items)}"
                    
                    # Create prompt with language instruction based on user selection
                    language_instruction = ai_analyzer._get_prompt_language()
                    analysis_request = "Por favor, analise os seguintes dados financeiros da Marine Seguros e forneça insights detalhados de negócios:"
                    
                    prompt = f"""
                    {language_instruction}
                    
                    {analysis_request}
                    
                    Dados Resumidos:
                    - Período: {summary.get('years_range', 'N/A')}
                    - Receita Total: R$ {summary.get('metrics', {}).get('revenue', {}).get('total', 0):,.2f}
                    - CAGR da Receita: {summary.get('metrics', {}).get('revenue', {}).get('cagr', 0):.1f}%
                    - Margem de Lucro Média: {summary.get('metrics', {}).get('profit_margin', {}).get('average', 0):.1f}%
                    {flexible_summary}
                    
                    Dados Anuais:
                    {df.to_string() if not df.empty else 'Nenhum dado disponível'}
                    
                    Por favor, forneça uma análise abrangente cobrindo:
                    1. **Análise das Principais Tendências Financeiras**
                    2. **Pontos Fortes de Performance & Vantagens Competitivas**
                    3. **Áreas de Preocupação & Gestão de Riscos**
                    4. **Recomendações Acionáveis para Crescimento**
                    5. **Análise Competitiva do Setor**
                    
                    Estruture sua resposta em um formato de relatório profissional com seções claras, bullet points e recomendações específicas.
                    """
                    
                    # Generate insights
                    response = ai_analyzer.model.generate_content(prompt)
                    
                    # Store in session state
                    st.session_state.gemini_insights = response.text
                    
                    # Display insights
                    st.markdown("### 📊 Relatório de Análise de Negócios")
                    st.markdown(response.text)
                    
                    # Save to database
                    db.auto_save_state(st.session_state)
                    
                except Exception as e:
                    st.error(f"Erro ao gerar insights de IA: {str(e)}")
                    st.info("Por favor, verifique sua chave de API do Gemini na barra lateral.")
    else:
        st.info("👆 Por favor, carregue os arquivos e processe os dados na aba 'Upload' primeiro.")


def render_micro_analysis(db, ai_analyzer):
    """Render the micro analysis section"""
    st.subheader("🔬 Análise de Despesas de Nível Micro")

    if hasattr(st.session_state, 'flexible_data') and st.session_state.flexible_data:
        if st.button("🕵️ Analisar Despesas Detalhadas", type="primary"):
            with st.spinner("Realizando análise aprofundada das despesas..."):
                try:
                    # Process data to get line items
                    detailed_data = process_detailed_monthly_data(st.session_state.flexible_data)
                    
                    if detailed_data and detailed_data['line_items']:
                        df_line_items = pd.DataFrame(detailed_data['line_items'])
                        
                        # Select relevant columns for analysis
                        analysis_df = df_line_items[[
                            'ano', 'subcategoria_principal_nome', 
                            'subcategoria_nome', 'descricao', 'valor_anual'
                        ]].copy()
                        analysis_df.rename(columns={
                            'ano': 'Ano',
                            'subcategoria_principal_nome': 'Categoria Principal',
                            'subcategoria_nome': 'Subcategoria',
                            'descricao': 'Descrição',
                            'valor_anual': 'Valor Anual'
                        }, inplace=True)

                        # Generate insights
                        insights = ai_analyzer.generate_micro_analysis_insights(analysis_df)
                        
                        # Store and display insights
                        st.session_state.micro_insights = insights
                        st.markdown("### 📝 Relatório de Análise de Nível Micro")
                        st.markdown(insights)
                        
                        # Save to database
                        db.auto_save_state(st.session_state)
                    else:
                        st.warning("Nenhum item de linha detalhado encontrado para analisar.")

                except Exception as e:
                    st.error(f"Ocorreu um erro durante a análise de nível micro: {e}")

        # Display existing micro insights if available
        if hasattr(st.session_state, 'micro_insights') and st.session_state.micro_insights:
            st.markdown("### 📝 Relatório de Análise de Nível Micro")
            st.markdown(st.session_state.micro_insights)
            st.markdown("---")
    else:
        st.info("👆 Por favor, carregue arquivos com dados detalhados de despesas primeiro.")
