
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

    # Check all possible data sources
    has_unified_data = hasattr(st.session_state, 'unified_data') and bool(st.session_state.unified_data)
    has_extracted_data = hasattr(st.session_state, 'extracted_data') and bool(st.session_state.extracted_data)
    has_processed_data = hasattr(st.session_state, 'processed_data') and bool(st.session_state.processed_data)
    
    # Don't overwrite existing data - just load from DB if truly empty
    if not any([
        hasattr(st.session_state, 'unified_data') and st.session_state.unified_data,
        hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data,
        hasattr(st.session_state, 'processed_data') and st.session_state.processed_data
    ]):
        shared_data = db.load_shared_financial_data()
        if shared_data:
            st.session_state.extracted_data = shared_data
            print(f"DEBUG: Loaded {len(shared_data)} years from database")

    tab1, tab2 = st.tabs(["Análise Macro", "Análise Micro"])

    with tab1:
        render_macro_analysis(db, ai_analyzer)

    with tab2:
        render_micro_analysis(db, ai_analyzer)

def generate_ai_prompt(df, all_data):
    language_instruction = "Responda em Português."
    analysis_request = "Por favor, analise os seguintes dados financeiros da Marine Seguros e forneça insights detalhados de negócios:"
    
    # Ensure we have valid data
    if df.empty:
        return f"{language_instruction}\n\n{analysis_request}\n\nNenhum dado disponível para análise."
    
    # Calculate summary metrics
    years = sorted(df['year'].unique())
    years_range = f"{years[0]}-{years[-1]}" if len(years) > 1 else str(years[0])
    
    # Calculate total revenue
    total_revenue = df['revenue'].sum() if 'revenue' in df.columns else 0
    
    # Calculate CAGR if we have multiple years
    cagr = 0
    if len(df) > 1 and 'revenue' in df.columns and df['revenue'].iloc[0] > 0:
        try:
            years_diff = df['year'].iloc[-1] - df['year'].iloc[0]
            if years_diff > 0:
                cagr = (pow(df['revenue'].iloc[-1] / df['revenue'].iloc[0], 1 / years_diff) - 1) * 100
        except:
            cagr = 0
    
    # Calculate average profit margin
    avg_margin = df['profit_margin'].mean() if 'profit_margin' in df.columns else 0
    
    # Get additional details from all_data if available
    flexible_summary = ""
    if all_data:
        try:
            all_categories = set()
            all_items = set()
            for year_data in all_data.values():
                if isinstance(year_data, dict):
                    if 'categories' in year_data:
                        all_categories.update(year_data['categories'].keys())
                    if 'line_items' in year_data:
                        all_items.update(item.get('label', '') for item in year_data['line_items'].values())
            
            if all_categories or all_items:
                flexible_summary = f"\n\nCategorias detectadas: {len(all_categories)}\nTotal de linhas de dados: {len(all_items)}"
        except:
            pass

    # Create a formatted dataframe for display
    display_df = df.copy()
    if 'revenue' in display_df.columns:
        display_df['revenue'] = display_df['revenue'].apply(lambda x: f"R$ {x:,.2f}")
    if 'net_profit' in display_df.columns:
        display_df['net_profit'] = display_df['net_profit'].apply(lambda x: f"R$ {x:,.2f}")
    if 'profit_margin' in display_df.columns:
        display_df['profit_margin'] = display_df['profit_margin'].apply(lambda x: f"{x:.2f}%")

    prompt = f"""
    {language_instruction}
    
    {analysis_request}
    
    Dados Resumidos:
    - Período: {years_range}
    - Anos analisados: {len(years)} ({', '.join(map(str, years))})
    - Receita Total: R$ {total_revenue:,.2f}
    - CAGR da Receita: {cagr:.1f}%
    - Margem de Lucro Média: {avg_margin:.1f}%
    {flexible_summary}
    
    Dados Anuais Detalhados:
    {display_df.to_string(index=False) if not display_df.empty else 'Nenhum dado disponível'}
    
    Por favor, forneça uma análise abrangente cobrindo:
    1. **Análise das Principais Tendências Financeiras**
    2. **Pontos Fortes de Performance & Vantagens Competitivas**
    3. **Áreas de Preocupação & Gestão de Riscos**
    4. **Recomendações Acionáveis para Crescimento**
    5. **Análise Competitiva do Setor**
    
    Estruture sua resposta em um formato de relatório profissional com seções claras, bullet points e recomendações específicas.
    
    IMPORTANTE: Use apenas os dados fornecidos acima. Não faça suposições sobre anos ou valores não mencionados.
    """
    return prompt

def render_macro_analysis(db, ai_analyzer):
    """Render the macro analysis section"""
    st.subheader("📈 Insights de Negócios de Nível Macro")

    # Check for data in various session state locations
    has_data = False
    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data is not None:
        has_data = True
    elif hasattr(st.session_state, 'monthly_data') and st.session_state.monthly_data is not None and not st.session_state.monthly_data.empty:
        has_data = True
    
    if has_data:
        # Display existing insights if available
        if hasattr(st.session_state, 'gemini_insights') and st.session_state.gemini_insights:
            st.markdown("### 📊 Relatório de Análise de Negócios")
            st.markdown(st.session_state.gemini_insights)
            st.markdown("---")
            
            # Add button to clear insights
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 Limpar Insights", key="clear_insights"):
                    del st.session_state.gemini_insights
                    st.success("✅ Insights limpos. Clique em 'Gerar Insights' para nova análise.")
                    st.rerun()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            generate_button = st.button("🤖 Gerar Insights de Negócios com IA", type="primary", use_container_width=True)
        
        if generate_button:
            with st.spinner("Analisando dados com IA... Por favor, aguarde..."):
                try:
                    # Get data from the best available source
                    df = pd.DataFrame()
                    all_data = {}
                    
                    # First try to get consolidated data from processed_data
                    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data:
                        print("DEBUG: Found processed_data in session state")
                        consolidated = st.session_state.processed_data.get('consolidated', pd.DataFrame())
                        raw_data = st.session_state.processed_data.get('raw_data', {})
                        
                        if not consolidated.empty:
                            # Create a clean dataframe with numeric values
                            df = consolidated.copy()
                            all_data = raw_data  # Use raw_data for detailed analysis
                            
                            print(f"DEBUG: Consolidated DF shape: {df.shape}")
                            print(f"DEBUG: Consolidated DF columns: {list(df.columns)}")
                            print(f"DEBUG: First row of consolidated DF:")
                            print(df.head(1).to_dict())
                            
                            # Convert dictionary values to numeric only if they are dictionaries
                            for col in ['revenue', 'variable_costs', 'fixed_costs', 'net_profit', 'profit_margin']:
                                if col in df.columns:
                                    # Check if any values are dictionaries before converting
                                    if df[col].apply(lambda x: isinstance(x, dict)).any():
                                        df[col] = df[col].apply(lambda x: x.get('annual', 0) if isinstance(x, dict) else (x if x is not None else 0))
                                    # If values are already numeric, keep them as is
                            
                            print(f"DEBUG: Got dataframe from processed_data with {len(df)} rows")
                            print(f"DEBUG: Revenue sum from processed_data: {df['revenue'].sum() if 'revenue' in df.columns else 'No revenue column'}")
                            print(f"DEBUG: Sample revenue values: {df['revenue'].head().tolist() if 'revenue' in df.columns else 'No revenue'}")
                    
                    # If no consolidated data, try to aggregate from monthly data
                    if df.empty and hasattr(st.session_state, 'monthly_data') and st.session_state.monthly_data is not None and not st.session_state.monthly_data.empty:
                        monthly_df = st.session_state.monthly_data
                        # Aggregate monthly data by year
                        yearly_agg = monthly_df.groupby('year').agg({
                            'revenue': 'sum',
                            'variable_costs': 'sum',
                            'fixed_costs': 'sum',
                            'operational_costs': 'sum',
                            'net_profit': 'sum',
                            'profit_margin': 'mean'  # Average the monthly margins
                        }).reset_index()
                        df = yearly_agg
                    
                    # Load fresh data from database if needed
                    if df.empty:
                        # Try unified_data first (has the most complete data)
                        if hasattr(st.session_state, 'unified_data') and st.session_state.unified_data:
                            financial_data = st.session_state.unified_data
                            print(f"DEBUG: Using unified_data from session state")
                        elif hasattr(st.session_state, 'extracted_data') and st.session_state.extracted_data:
                            financial_data = st.session_state.extracted_data
                            print(f"DEBUG: Using extracted_data from session state")
                        else:
                            # Try shared data from database
                            financial_data = db.load_shared_financial_data()
                            print(f"DEBUG: Loading from database")
                        
                        print(f"DEBUG: Loaded {len(financial_data)} years")
                        if financial_data:
                            # Debug the structure of financial_data
                            for year, data in list(financial_data.items())[:1]:  # Check first year
                                print(f"DEBUG: Year {year} data structure:")
                                print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                                if isinstance(data, dict) and 'revenue' in data:
                                    print(f"  Revenue data type: {type(data['revenue'])}")
                                    print(f"  Revenue data: {data['revenue']}")
                            # Create consolidated dataframe from database data
                            years = []
                            revenues = []
                            profits = []
                            margins = []
                            
                            for year, data in financial_data.items():
                                if isinstance(data, dict):
                                    year_int = int(year) if isinstance(year, str) else year
                                    
                                    # Check if this is unified_data format (direct values)
                                    if 'revenue' in data and isinstance(data['revenue'], (int, float)):
                                        years.append(year_int)
                                        revenues.append(data['revenue'])
                                        profits.append(data.get('net_profit', 0))
                                        margins.append(data.get('profit_margin', 0))
                                        pass  # Direct revenue available
                                    # Check if this is the old format with dicts
                                    elif 'revenue' in data and isinstance(data['revenue'], dict):
                                        revenue_dict = data['revenue']
                                        annual_revenue = revenue_dict.get('annual', revenue_dict.get('ANNUAL', 0))
                                        
                                        # If still 0, try summing monthly values
                                        if annual_revenue == 0:
                                            monthly_sum = sum(
                                                v for k, v in revenue_dict.items() 
                                                if k in ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                                         'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'] 
                                                and isinstance(v, (int, float))
                                            )
                                            annual_revenue = monthly_sum if monthly_sum > 0 else 0
                                        
                                        if annual_revenue > 0:  # Only add if we have revenue
                                            years.append(year_int)
                                            revenues.append(annual_revenue)
                                    
                                            # Extract profit and margin for dict format
                                            if 'net_profit' in data:
                                                profit_data = data['net_profit']
                                                if isinstance(profit_data, dict):
                                                    profits.append(profit_data.get('annual', profit_data.get('ANNUAL', 0)))
                                                else:
                                                    profits.append(profit_data if profit_data else 0)
                                            else:
                                                profits.append(0)
                                            
                                            if 'profit_margin' in data:
                                                margin_data = data['profit_margin']
                                                if isinstance(margin_data, dict):
                                                    margins.append(margin_data.get('annual', margin_data.get('ANNUAL', 0)))
                                                else:
                                                    margins.append(margin_data if margin_data else 0)
                                            else:
                                                margins.append(0)
                                            
                                            pass  # Revenue from dict format
                            
                            if years:
                                df = pd.DataFrame({
                                    'year': years,
                                    'revenue': revenues,
                                    'net_profit': profits,
                                    'profit_margin': margins
                                })
                                df = df.sort_values('year')

                    if not df.empty:
                        # DataFrame ready for filtering
                        
                        # Ensure all numeric columns are properly converted
                        numeric_columns = ['revenue', 'net_profit', 'profit_margin']
                        for col in numeric_columns:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                        print(f"DEBUG: Revenue after pd.to_numeric: {df['revenue'].tolist()}")
                        print(f"DEBUG: Revenue > 0 check: {(df['revenue'] > 0).tolist()}")
                        
                        # Filter out years with zero revenue or NaN
                        df_filtered = df[df['revenue'] > 0].copy()
                        
                        if df_filtered.empty:
                            st.error("❌ Todos os anos têm receita zero. Por favor, verifique os dados carregados.")
                            # Show the actual data for debugging
                            with st.expander("🔍 Debug: Dados antes do filtro"):
                                st.dataframe(df)
                                st.write(f"Tipo da coluna revenue: {df['revenue'].dtype}")
                                st.write(f"Valores únicos de revenue: {df['revenue'].unique()}")
                                st.write(f"Soma total de revenue: {df['revenue'].sum()}")
                        else:
                            df = df_filtered
                            # Show data preview
                            with st.expander("📋 Visualizar Dados que Serão Analisados"):
                                st.write(f"**Período dos dados:** {df['year'].min()} - {df['year'].max()}")
                                st.write(f"**Anos disponíveis:** {sorted(df['year'].unique())}")
                                preview_df = df[['year', 'revenue', 'net_profit', 'profit_margin']].copy()
                                preview_df['revenue'] = preview_df['revenue'].apply(lambda x: f"R$ {x:,.2f}")
                                preview_df['net_profit'] = preview_df['net_profit'].apply(lambda x: f"R$ {x:,.2f}") 
                                preview_df['profit_margin'] = preview_df['profit_margin'].apply(lambda x: f"{x:.2f}%")
                                st.dataframe(preview_df, use_container_width=True)
                            
                            prompt = generate_ai_prompt(df, all_data)
                            print(f"Years in data: {df['year'].min()} to {df['year'].max()}")
                            print(prompt)
                            
                            # Generate insights
                            response = ai_analyzer.model.generate_content(prompt)
                            
                            # Store in session state
                            st.session_state.gemini_insights = response.text
                            
                            # Display insights
                            st.markdown("### 📊 Relatório de Análise de Negócios")
                            st.markdown(response.text)
                            
                            # Save to database
                            db.auto_save_state(st.session_state)
                    else:
                        st.error("Não foi possível carregar dados para análise. Por favor, faça upload e processe os dados primeiro.")
                    
                except Exception as e:
                    st.error(f"Erro ao gerar insights de IA: {str(e)}")
                    st.info("Por favor, verifique sua chave de API do Gemini na barra lateral.")
                    import traceback
                    with st.expander("Ver detalhes do erro"):
                        st.code(traceback.format_exc())
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
