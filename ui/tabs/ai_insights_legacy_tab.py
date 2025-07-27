"""
AI Insights Tab - Legacy version extracted from app.py
Preserves all original functionality while organizing code
"""

import streamlit as st
import pandas as pd
import google.generativeai as genai


def render_ai_insights_tab(db, gemini_api_key, language):
    """Render the AI insights tab with Gemini AI analysis"""
    
    st.header("🤖 Insights com Gemini AI")

    # Load extracted data from database if not in session state
    if not hasattr(st.session_state, 'extracted_data') or not st.session_state.extracted_data:
        st.session_state.extracted_data = db.load_all_financial_data()

    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data is not None and gemini_api_key:
        # Display existing insights if available
        if hasattr(st.session_state, 'gemini_insights') and st.session_state.gemini_insights:
            st.markdown("### 📊 Business Analysis Report")
            st.markdown(st.session_state.gemini_insights)
            st.markdown("---")
        
        if st.button("🤖 Generate AI Business Insights", type="primary"):
            with st.spinner("Analyzing data with AI... Please wait..."):
                try:
                    # Configure Gemini
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
            
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
                    - Period: {summary.get('years_range', 'N/A')}
                    - Total Revenue: R$ {summary.get('metrics', {}).get('revenue', {}).get('total', 0):,.2f}
                    - Revenue CAGR: {summary.get('metrics', {}).get('revenue', {}).get('cagr', 0):.1f}%
                    - Average Profit Margin: {summary.get('metrics', {}).get('profit_margin', {}).get('average', 0):.1f}%
                    {flexible_summary}
                    
                    Annual Data:
                    {df.to_string() if not df.empty else 'No data available'}
                    
                    {
                        "Por favor, forneça uma análise abrangente cobrindo:" if language == "Português" else "Please provide a comprehensive analysis covering:"
                    }
                    {
                        '''1. **Análise das Principais Tendências Financeiras**
                    2. **Pontos Fortes de Performance & Vantagens Competitivas**
                    3. **Áreas de Preocupação & Gestão de Riscos**
                    4. **Recomendações Acionáveis para Crescimento**
                    5. **Análise Competitiva do Setor**
                    
                    Estruture sua resposta em um formato de relatório profissional com seções claras, bullet points e recomendações específicas.''' if language == "Português" else 
                        '''1. **Key Financial Trends Analysis**
                    2. **Performance Strengths & Competitive Advantages**
                    3. **Areas of Concern & Risk Management**
                    4. **Actionable Recommendations for Growth**
                    5. **Industry Competitive Analysis**
                    
                    Structure your response in a professional report format with clear sections, bullet points, and specific recommendations.'''
                    }
                    """
                    
                    # Generate insights
                    response = model.generate_content(prompt)
                    
                    # Store in session state
                    st.session_state.gemini_insights = response.text
                    
                    # Display insights
                    st.markdown("### 📊 Business Analysis Report")
                    st.markdown(response.text)
                    
                    # Save to database
                    db.auto_save_state(st.session_state)
                    
                except Exception as e:
                    st.error(f"Error generating AI insights: {str(e)}")
                    st.info("Please check your Gemini API key in the sidebar.")
    
    elif not gemini_api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar to use AI insights.")
        st.info("You can get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)")
    else:
        st.info("👆 Please upload files and process data in the 'Upload' tab first.")