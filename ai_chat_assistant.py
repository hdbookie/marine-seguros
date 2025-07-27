import streamlit as st
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
import numpy as np

class AIChatAssistant:
    """AI-powered chat assistant for financial data Q&A with filter awareness"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test API key on initialization
        self.api_key_valid = self._test_api_key()
        
        # Initialize chat history in session state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Track last processed message to prevent duplicates
        if 'last_processed_message' not in st.session_state:
            st.session_state.last_processed_message = None
        
        # Suggested questions templates
        self.suggested_questions = {
            'general': [
                "Qual foi o melhor ano em termos de receita?",
                "Como está a tendência de crescimento?",
                "Quais meses têm melhor desempenho?",
                "Mostre um resumo executivo dos últimos 3 anos"
            ],
            'comparison': [
                "Compare {year1} com {year2}",
                "Qual a diferença entre Q1 e Q4?",
                "Como março se compara com outros meses?",
                "Mostre a evolução mensal da margem"
            ],
            'analysis': [
                "Por que março sempre tem desempenho ruim?",
                "Quais fatores contribuíram para o crescimento em 2024?",
                "Identifique padrões sazonais nos dados",
                "Quais são os principais riscos que você vê?"
            ],
            'prediction': [
                "Qual a previsão para o próximo trimestre?",
                "Se mantivermos o crescimento atual, onde estaremos em 2026?",
                "Qual seria o impacto de reduzir custos em 10%?",
                "Projete a receita para os próximos 6 meses"
            ]
        }
    
    def render_chat_interface(self, data: Dict, filter_context: str):
        """Render the chat interface with message history"""
        
        st.markdown("### 💬 Assistente de IA")
        st.caption(f"📊 {filter_context}")
        
        # Show API status for debugging
        if not self.api_key_valid:
            st.warning("⚠️ API do Gemini não está funcionando corretamente. Verifique sua chave API.")
        else:
            st.success("✅ Conexão com Gemini OK - Pode fazer perguntas e solicitar gráficos!")
        
        # Show data availability
        if data:
            years_available = sorted(data.keys())
            st.info(f"📈 Dados disponíveis: {len(years_available)} anos ({years_available[0]} - {years_available[-1]})")
        else:
            st.warning("⚠️ Nenhum dado financeiro disponível")
        
        # Suggested questions based on current data
        self._render_suggested_questions(data, filter_context)
        
        # Chat messages container
        chat_container = st.container()
        
        with chat_container:
            # Display chat history
            for message in st.session_state.chat_history:
                self._render_message(message)
        
        # Input area
        with st.form(key="chat_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                user_input = st.text_input(
                    "Faça uma pergunta sobre os dados",
                    placeholder="Ex: Por que dezembro tem melhor desempenho?",
                    key="chat_input_field"
                )
            
            with col2:
                send_button = st.form_submit_button("Enviar", type="primary")
            
            # Process user input
            if send_button and user_input:
                self._process_user_message(user_input, data, filter_context)
        
        # Export chat button
        if st.session_state.chat_history:
            if st.button("📥 Exportar conversa", key="export_chat"):
                self._export_chat()
    
    def _render_suggested_questions(self, data: Dict, filter_context: str):
        """Render suggested questions based on current data"""
        with st.expander("💡 Perguntas sugeridas", expanded=False):
            
            # Get relevant questions based on data
            questions = []
            
            # Add general questions
            questions.extend(self.suggested_questions['general'][:2])
            
            # Add year-specific questions if we have multiple years
            years = sorted(data.keys())
            if len(years) >= 2:
                recent_years = years[-2:]
                question = self.suggested_questions['comparison'][0].format(
                    year1=recent_years[0], year2=recent_years[1]
                )
                questions.append(question)
            
            # Add analysis questions
            questions.append(self.suggested_questions['analysis'][0])
            
            # Create buttons for suggested questions
            cols = st.columns(2)
            for i, question in enumerate(questions[:4]):
                with cols[i % 2]:
                    if st.button(question, key=f"suggested_{i}"):
                        # Process the suggested question directly
                        self._process_user_message(question, data, filter_context)
    
    def _render_message(self, message: Dict):
        """Render a single chat message"""
        if message['role'] == 'user':
            st.markdown(f"**🧑 Você:** {message['content']}")
        else:
            # AI message might contain charts
            if 'chart' in message:
                col1, col2 = st.columns([2, 1])
                with col1:
                    # Display AI label and content separately for better formatting
                    st.markdown("**🤖 IA:**")
                    st.markdown(message['content'])
                with col2:
                    st.plotly_chart(message['chart'], use_container_width=True)
            else:
                # Display AI label and content separately for better formatting
                st.markdown("**🤖 IA:**")
                st.markdown(message['content'])
        
        st.markdown("---")
    
    def _process_user_message(self, user_input: str, data: Dict, filter_context: str):
        """Process user message and generate AI response"""
        
        # Create unique message ID to prevent duplicates within same session
        current_time = datetime.now()
        message_id = f"{user_input}_{current_time.strftime('%H%M%S')}"
        
        # Check if this exact message was processed very recently (within 2 seconds)
        if (hasattr(st.session_state, 'last_message_time') and 
            st.session_state.last_processed_message == user_input and
            (current_time - st.session_state.last_message_time).total_seconds() < 2):
            return
        
        st.session_state.last_processed_message = user_input
        st.session_state.last_message_time = current_time
        
        # Validate API key before processing
        if not self.api_key_valid:
            st.error("❌ Chave API do Gemini inválida. Verifique sua configuração.")
            return
        
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': current_time
        })
        
        # Show processing indicator with detailed status
        with st.spinner("🤔 Analisando sua pergunta..."):
            # Check if user is asking for a chart
            with st.status("Verificando se precisa de gráfico...", expanded=False):
                needs_chart = self._check_if_needs_chart(user_input)
                if needs_chart:
                    st.write("📊 Gráfico será gerado")
                else:
                    st.write("💬 Resposta textual")
            
            # Check if user wants to change filters
            filter_request = self._extract_filter_request(user_input)
            
            # Prepare context for AI
            with st.status("Preparando contexto dos dados...", expanded=False):
                context = self._prepare_context(data, filter_context)
                st.write(f"✅ Contexto preparado: {len(str(context))} caracteres")
            
            # Generate AI response
            prompt = f"""
            Você é um analista financeiro especializado e detalhista, com acesso a dados financeiros anuais (macro) e mensais detalhados (micro) da Marine Seguros. Sua função é fornecer insights precisos e acionáveis.
            
            Contexto atual de filtros: {filter_context}
            
            Dados financeiros disponíveis para análise:
            {context}
            
            Pergunta do usuário: {user_input}
            
            Instruções CRÍTICAS para sua resposta:
            1. Responda **sempre** em português brasileiro.
            2. Seja extremamente específico e use números dos dados fornecidos. Para perguntas sobre meses ou períodos específicos, utilize os 'Dados Mensais Detalhados'.
            3. Se a pergunta envolver comparação histórica ou análise de desempenho entre períodos (ex: "Por que março foi melhor que abril de 2024?", "Qual foi o mês mais lucrativo na história?"), utilize os dados detalhados para identificar as causas e tendências.
            4. Se não tiver dados suficientes para uma análise específica (ex: dados mensais para um ano não carregado), diga claramente que a informação não está disponível nos dados fornecidos.
            5. Forneça insights acionáveis e recomendações práticas quando possível, baseando-se nos dados.
            6. Use formatação markdown simples para clareza:
               - Use **texto** para negrito.
               - Use quebras de linha para separar parágrafos.
               - Formate números grandes com pontos para milhares e vírgula para decimais (ex: 1.234.567,89).
            
            Sua resposta deve ser concisa, profissional e diretamente relevante à pergunta do usuário, explorando a profundidade dos dados disponíveis.
            """
            
            try:
                # Generate AI response with status
                with st.status("Consultando Gemini AI...", expanded=False):
                    response = self.model.generate_content(prompt)
                    ai_response = response.text
                    st.write(f"✅ Resposta recebida: {len(ai_response)} caracteres")
                
                # Create response message
                response_message = {
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': datetime.now()
                }
                
                # Generate chart if needed
                if needs_chart:
                    with st.status("Gerando gráfico...", expanded=False):
                        chart = self._generate_chart_from_query(user_input, data)
                        if chart:
                            response_message['chart'] = chart
                            st.write("📊 Gráfico gerado com sucesso")
                        else:
                            st.write("⚠️ Não foi possível gerar o gráfico")
                
                # Add to history
                st.session_state.chat_history.append(response_message)
                
                # Handle filter requests
                if filter_request:
                    st.info(f"💡 Dica: Use os filtros acima para {filter_request}")
                
                # Clear the input by setting a flag
                st.session_state.clear_chat_input = True
                
                # Force interface refresh to show new message
                st.rerun()
                
            except Exception as e:
                # Show detailed error information for debugging
                error_msg = f"Erro ao processar pergunta: {str(e)}"
                st.error(error_msg)
                
                # Add error message to chat history for visibility
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"❌ **Erro**: {str(e)}\n\nPor favor, verifique sua chave API do Gemini e tente novamente.",
                    'timestamp': current_time,
                    'error': True
                })
                
                # Force interface refresh even on error
                st.rerun()
    
    def _test_api_key(self) -> bool:
        """Test if the Gemini API key is valid"""
        try:
            # Simple test query to validate API key
            test_response = self.model.generate_content("Hello")
            return test_response.text is not None
        except Exception as e:
            print(f"API key validation failed: {e}")
            return False
    
    def _check_if_needs_chart(self, query: str) -> bool:
        """Check if user query requires a chart"""
        chart_keywords = [
            'mostre', 'gráfico', 'visualize', 'compare visualmente',
            'evolução', 'tendência', 'progressão', 'histórico',
            'show me', 'chart', 'graph', 'plot', 'desenhe', 'crie um gráfico',
            'pizza', 'pie', 'barra', 'bar', 'linha', 'line', 'cascata', 'waterfall',
            'heatmap', 'mapa de calor', 'dispersão', 'scatter', 'empilhado', 'stacked'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in chart_keywords)
    
    def _extract_filter_request(self, query: str) -> Optional[str]:
        """Extract filter change requests from query"""
        # Patterns for filter requests
        patterns = {
            r'mostre.*(2\d{3})': 'year',
            r'compare.*(2\d{3}).*(2\d{3})': 'year_comparison',
            r'(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)': 'month',
            r'(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)': 'month',
            r'(q1|q2|q3|q4|trimestre)': 'quarter',
            r'(melhores|piores|top|bottom).*(meses)': 'performance'
        }
        
        query_lower = query.lower()
        for pattern, filter_type in patterns.items():
            if re.search(pattern, query_lower):
                return f"filtrar por {filter_type}"
        
        return None
    
    def _parse_chart_requirements(self, query: str, data: Dict) -> Dict:
        """Use AI to parse chart requirements from natural language query"""
        # Prepare context about available data
        available_years = sorted(data.keys())
        available_metrics = set()
        
        # Collect all available metrics from the data
        for year_data in data.values():
            if 'revenue' in year_data:
                available_metrics.add('revenue')
            if 'costs' in year_data:
                available_metrics.add('costs')
            if 'margins' in year_data:
                available_metrics.add('margins')
            if 'profits' in year_data:
                available_metrics.add('profits')
            if 'line_items' in year_data:  # For flexible data
                for item_key in year_data['line_items'].keys():
                    available_metrics.add(item_key)
        
        prompt = f"""
        Analyze this chart request and extract the requirements:
        Query: {query}
        
        Available years: {available_years}
        Available metrics: {list(available_metrics)}
        
        Extract and return in JSON format:
        {{
            "chart_type": "pie|bar|line|scatter|heatmap|waterfall|stacked_bar|box|area|auto",
            "metrics": [list of metrics to display],
            "time_period": {{
                "type": "all|specific_years|last_n_years|specific_months",
                "years": [list of years or null for all],
                "months": [list of month names or null for all]
            }},
            "grouping": "year|month|quarter|category|none",
            "comparison_type": "time_series|side_by_side|proportion|correlation|none",
            "title": "suggested chart title",
            "format_options": {{
                "show_values": true/false,
                "show_percentages": true/false,
                "currency": true/false
            }}
        }}
        
        Guidelines:
        - If chart type is not specified, set to "auto" and choose based on data and query
        - For expense/cost breakdowns, prefer "pie" or "stacked_bar"
        - For trends over time, prefer "line" or "area"
        - For comparisons, prefer "bar" or "grouped_bar"
        - For profit flow, prefer "waterfall"
        - For correlations, prefer "scatter"
        - For patterns across time, prefer "heatmap"
        
        Return ONLY valid JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            requirements = json.loads(response.text)
            
            # Auto-select chart type if needed
            if requirements.get('chart_type') == 'auto':
                requirements['chart_type'] = self._auto_select_chart_type(
                    requirements['metrics'],
                    requirements.get('comparison_type', 'none'),
                    requirements.get('grouping', 'none')
                )
            
            return requirements
        except Exception as e:
            # Fallback to basic parsing
            print(f"Error parsing chart requirements: {e}")
            return {
                'chart_type': 'line',
                'metrics': ['revenue'],
                'time_period': {'type': 'all', 'years': None, 'months': None},
                'grouping': 'year',
                'comparison_type': 'time_series',
                'title': 'Visão Geral Financeira',
                'format_options': {
                    'show_values': True,
                    'show_percentages': False,
                    'currency': True
                }
            }
    
    def _auto_select_chart_type(self, metrics: List[str], comparison_type: str, grouping: str) -> str:
        """Auto-select the best chart type based on data characteristics"""
        # If showing proportions of a whole
        if comparison_type == 'proportion' or (len(metrics) > 2 and grouping == 'category'):
            return 'pie'
        
        # If showing flow from one value to another
        if 'revenue' in metrics and any(cost in metrics for cost in ['costs', 'variable_costs', 'fixed_costs']):
            if comparison_type == 'none':
                return 'waterfall'
        
        # If comparing multiple categories over time
        if len(metrics) > 1 and grouping in ['year', 'month']:
            return 'stacked_bar'
        
        # If showing correlation
        if comparison_type == 'correlation' and len(metrics) == 2:
            return 'scatter'
        
        # If showing patterns across two dimensions
        if grouping == 'month' and comparison_type == 'time_series':
            return 'heatmap'
        
        # Default to line chart for time series
        if grouping in ['year', 'month', 'quarter']:
            return 'line'
        
        # Default to bar chart
        return 'bar'
    
    def _prepare_context(self, data: Dict, filter_context: str) -> str:
        """Prepare data context for AI"""
        context_parts = []
        
        # Define months list universally for this function
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                  'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        # Define months list universally for this function
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                  'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

        # Summarize available data
        years = sorted(data.keys())
        context_parts.append(f"Anos disponíveis: {years}")
        
        # Revenue summary
        total_revenue_by_year = {}
        for year, year_data in data.items():
            revenue = year_data.get('revenue', {})
            total = sum(v for k, v in revenue.items() if k != 'ANNUAL' and isinstance(v, (int, float)))
            # Ensure year is a regular int, not numpy int64
            total_revenue_by_year[int(year)] = float(total)
        
        context_parts.append(f"Receita por ano: {json.dumps(total_revenue_by_year, indent=2)}")
        
        # Growth rates
        if len(years) > 1:
            growth_rates = []
            sorted_years = sorted(total_revenue_by_year.keys())
            for i in range(1, len(sorted_years)):
                prev_year = sorted_years[i-1]
                curr_year = sorted_years[i]
                if total_revenue_by_year[prev_year] > 0:
                    growth = ((total_revenue_by_year[curr_year] - total_revenue_by_year[prev_year]) 
                             / total_revenue_by_year[prev_year] * 100)
                    growth_rates.append(f"{prev_year}-{curr_year}: {growth:.1f}%")
            
            context_parts.append(f"Crescimento anual: {', '.join(growth_rates)}")
        
        # Month performance if not filtered
        if 'filter_state' not in st.session_state or not hasattr(st.session_state.filter_state, 'months') or not st.session_state.filter_state.months:
            month_totals = {}
            month_revenues = {month: [] for month in months}
            month_variable_costs = {month: [] for month in months}
            month_fixed_costs = {month: [] for month in months}
            month_net_profits = {month: [] for month in months}

            for year_data in data.values():
                for month in months:
                    if month in year_data.get('revenue', {}):
                        month_revenues[month].append(year_data['revenue'][month])
                        month_variable_costs[month].append(year_data.get('costs', {}).get(month, 0))
                        month_fixed_costs[month].append(year_data.get('fixed_costs', {}).get(month, 0))
                        
                        # Calculate monthly net profit if possible
                        monthly_revenue = year_data.get('revenue', {}).get(month, 0)
                        monthly_variable_costs = year_data.get('costs', {}).get(month, 0)
                        monthly_fixed_costs = year_data.get('fixed_costs', {}).get(month, 0)
                        monthly_net_profit = monthly_revenue - monthly_variable_costs - monthly_fixed_costs
                        month_net_profits[month].append(monthly_net_profit)

            for month in months:
                if month_revenues[month]:
                    month_totals[month] = sum(month_revenues[month]) / len(month_revenues[month])

            best_months = sorted(month_totals.items(), key=lambda x: x[1], reverse=True)[:3]
            worst_months = sorted(month_totals.items(), key=lambda x: x[1])[:3]
            
            context_parts.append(f"Melhores meses (Receita Média): {[m[0] for m in best_months]}")
            context_parts.append(f"Piores meses (Receita Média): {[m[0] for m in worst_months]}")

            # Add detailed monthly data
            detailed_monthly_data = []
            for year in sorted(data.keys()):
                year_data = data[year]
                for month in months:
                    monthly_revenue = year_data.get('revenue', {}).get(month, 0)
                    monthly_variable_costs = year_data.get('costs', {}).get(month, 0)
                    monthly_fixed_costs = year_data.get('fixed_costs', {}).get(month, 0)
                    monthly_net_profit = monthly_revenue - monthly_variable_costs - monthly_fixed_costs
                    
                    detailed_monthly_data.append({
                        "Ano": year,
                        "Mês": month,
                        "Receita": monthly_revenue,
                        "Custos Variáveis": monthly_variable_costs,
                        "Custos Fixos": monthly_fixed_costs,
                        "Lucro Líquido": monthly_net_profit
                    })
            context_parts.append("\nDados Mensais Detalhados:\n" + pd.DataFrame(detailed_monthly_data).to_string(index=False))
        
        return "\n".join(context_parts)
    
    def _generate_chart_from_query(self, query: str, data: Dict) -> Optional[go.Figure]:
        """Generate appropriate chart based on parsed requirements"""
        # Parse requirements using AI
        requirements = self._parse_chart_requirements(query, data)
        
        # Route to appropriate chart generator
        chart_type = requirements['chart_type']
        
        try:
            if chart_type == 'pie':
                return self._create_pie_chart(data, requirements)
            elif chart_type == 'waterfall':
                return self._create_waterfall_chart(data, requirements)
            elif chart_type == 'heatmap':
                return self._create_heatmap(data, requirements)
            elif chart_type == 'scatter':
                return self._create_scatter_plot(data, requirements)
            elif chart_type == 'stacked_bar':
                return self._create_stacked_bar_chart(data, requirements)
            elif chart_type == 'box':
                return self._create_box_plot(data, requirements)
            elif chart_type == 'area':
                return self._create_area_chart(data, requirements)
            elif chart_type == 'bar':
                return self._create_bar_chart(data, requirements)
            elif chart_type == 'line':
                return self._create_enhanced_line_chart(data, requirements)
            else:
                # Fallback to existing methods
                query_lower = query.lower()
                if 'evolução' in query_lower or 'tendência' in query_lower:
                    return self._create_trend_chart(data)
                elif 'compare' in query_lower or 'comparar' in query_lower:
                    return self._create_comparison_chart(data)
                elif 'mensal' in query_lower or 'mês' in query_lower:
                    return self._create_monthly_chart(data)
                elif 'margem' in query_lower or 'margin' in query_lower:
                    return self._create_margin_chart(data)
                else:
                    return self._create_trend_chart(data)
        except Exception as e:
            print(f"Error generating chart: {e}")
            # Fallback to simple trend chart
            return self._create_trend_chart(data)
    
    def _create_trend_chart(self, data: Dict) -> go.Figure:
        """Create revenue trend chart"""
        years = sorted(data.keys())
        revenues = []
        
        for year in years:
            revenue_data = data[year].get('revenue', {})
            total = sum(v for k, v in revenue_data.items() 
                       if k != 'ANNUAL' and isinstance(v, (int, float)))
            revenues.append(total)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years,
            y=revenues,
            mode='lines+markers',
            name='Receita',
            line=dict(width=3, color='#667eea'),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title='Evolução da Receita',
            xaxis_title='Ano',
            yaxis_title='Receita (R$)',
            height=300
        )
        
        return fig
    
    def _create_comparison_chart(self, data: Dict) -> go.Figure:
        """Create comparison chart"""
        years = sorted(data.keys())[-2:]  # Last 2 years
        
        if len(years) < 2:
            return None
        
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        fig = go.Figure()
        
        for year in years:
            values = []
            for month in months:
                value = data[year].get('revenue', {}).get(month, 0)
                values.append(value)
            
            fig.add_trace(go.Bar(
                x=months,
                y=values,
                name=str(year)
            ))
        
        fig.update_layout(
            title=f'Comparação {years[0]} vs {years[1]}',
            xaxis_title='Mês',
            yaxis_title='Receita (R$)',
            barmode='group',
            height=300
        )
        
        return fig
    
    def _create_monthly_chart(self, data: Dict) -> go.Figure:
        """Create monthly performance chart"""
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        # Calculate average for each month
        month_avgs = []
        for month in months:
            total = 0
            count = 0
            for year_data in data.values():
                if month in year_data.get('revenue', {}):
                    total += year_data['revenue'][month]
                    count += 1
            avg = total / count if count > 0 else 0
            month_avgs.append(avg)
        
        # Color based on performance
        colors = ['green' if avg > sum(month_avgs)/len(month_avgs) else 'red' 
                 for avg in month_avgs]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=months,
            y=month_avgs,
            marker_color=colors,
            text=[f"R$ {avg:,.0f}" for avg in month_avgs],
            textposition='outside'
        ))
        
        fig.update_layout(
            title='Desempenho Médio por Mês',
            xaxis_title='Mês',
            yaxis_title='Receita Média (R$)',
            height=300
        )
        
        return fig
    
    def _create_margin_chart(self, data: Dict) -> go.Figure:
        """Create margin evolution chart"""
        years = sorted(data.keys())
        margins = []
        
        for year in years:
            margin_data = data[year].get('margins', {})
            # Calculate average margin for the year
            year_margins = [v for k, v in margin_data.items() 
                          if k != 'ANNUAL' and isinstance(v, (int, float))]
            avg_margin = sum(year_margins) / len(year_margins) if year_margins else 0
            margins.append(avg_margin)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years,
            y=margins,
            mode='lines+markers',
            name='Margem',
            line=dict(width=3, color='#764ba2'),
            marker=dict(size=10),
            text=[f"{m:.1f}%" for m in margins],
            textposition='top center'
        ))
        
        fig.update_layout(
            title='Evolução da Margem de Lucro',
            xaxis_title='Ano',
            yaxis_title='Margem (%)',
            height=300
        )
        
        return fig
    
    def _create_pie_chart(self, data: Dict, requirements: Dict) -> go.Figure:
        """Create pie chart for proportional data"""
        metrics = requirements['metrics']
        time_period = requirements['time_period']
        title = requirements.get('title', 'Distribuição')
        
        # Get years to analyze
        if time_period['years']:
            years = [str(y) for y in time_period['years'] if str(y) in data]
        else:
            years = sorted(data.keys())[-1:]  # Latest year by default
        
        # Aggregate data
        values = []
        labels = []
        
        for metric in metrics:
            total = 0
            for year in years:
                year_data = data[year]
                
                # Handle different data structures
                if metric == 'costs' and 'costs' in year_data:
                    total += year_data['costs'].get('ANNUAL', 0)
                elif metric == 'variable_costs' and 'costs' in year_data:
                    total += year_data['costs'].get('ANNUAL', 0)
                elif metric == 'fixed_costs' and 'fixed_costs' in year_data:
                    total += year_data['fixed_costs']
                elif metric == 'operational_costs' and 'operational_costs' in year_data:
                    total += year_data['operational_costs']
                elif 'line_items' in year_data and metric in year_data['line_items']:
                    total += year_data['line_items'][metric].get('annual', 0)
                elif metric in year_data:
                    if isinstance(year_data[metric], dict):
                        total += year_data[metric].get('ANNUAL', 0)
                    else:
                        total += year_data[metric]
            
            if total > 0:
                values.append(total)
                labels.append(self._translate_metric_name(metric))
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,  # Donut chart
            textinfo='label+percent',
            textposition='auto',
            marker=dict(
                colors=px.colors.qualitative.Set3[:len(labels)]
            )
        )])
        
        fig.update_layout(
            title=title,
            height=400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )
        
        return fig
    
    def _create_waterfall_chart(self, data: Dict, requirements: Dict) -> go.Figure:
        """Create waterfall chart showing profit flow"""
        time_period = requirements['time_period']
        title = requirements.get('title', 'Fluxo de Resultado')
        
        # Get year to analyze
        if time_period['years']:
            year = str(time_period['years'][-1])
        else:
            year = sorted(data.keys())[-1]
        
        if year not in data:
            return None
        
        year_data = data[year]
        
        # Build waterfall data
        x_labels = []
        y_values = []
        measure = []
        
        # Revenue (starting point)
        revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
        x_labels.append('Receita')
        y_values.append(revenue)
        measure.append('absolute')
        
        # Variable costs
        var_costs = year_data.get('costs', {}).get('ANNUAL', 0)
        if var_costs > 0:
            x_labels.append('Custos Variáveis')
            y_values.append(-var_costs)
            measure.append('relative')
        
        # Fixed costs
        fixed_costs = year_data.get('fixed_costs', 0)
        if fixed_costs > 0:
            x_labels.append('Custos Fixos')
            y_values.append(-fixed_costs)
            measure.append('relative')
        
        # Operational costs
        op_costs = year_data.get('operational_costs', 0)
        if op_costs > 0:
            x_labels.append('Custos Operacionais')
            y_values.append(-op_costs)
            measure.append('relative')
        
        # Net profit (total)
        x_labels.append('Lucro Líquido')
        y_values.append(revenue - var_costs - fixed_costs - op_costs)
        measure.append('total')
        
        # Create waterfall
        fig = go.Figure(go.Waterfall(
            x=x_labels,
            y=y_values,
            measure=measure,
            text=[f"R$ {abs(v):,.0f}" for v in y_values],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#FF6B6B"}},
            increasing={"marker": {"color": "#4ECDC4"}},
            totals={"marker": {"color": "#45B7D1"}}
        ))
        
        fig.update_layout(
            title=f"{title} - {year}",
            yaxis_title="Valor (R$)",
            height=500,
            showlegend=False
        )
        
        return fig
    
    def _create_heatmap(self, data: Dict, requirements: Dict) -> go.Figure:
        """Create heatmap for patterns across time"""
        metrics = requirements['metrics']
        title = requirements.get('title', 'Mapa de Calor')
        
        # Default to revenue if no metric specified
        metric = metrics[0] if metrics else 'revenue'
        
        # Prepare data matrix
        years = sorted(data.keys())
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                  'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        z_values = []
        for month in months:
            month_values = []
            for year in years:
                year_data = data[year]
                value = 0
                
                if metric in year_data and isinstance(year_data[metric], dict):
                    value = year_data[metric].get(month, 0)
                elif 'line_items' in year_data:
                    for item_key, item_data in year_data['line_items'].items():
                        if metric in item_key.lower():
                            value = item_data.get(month, 0)
                            break
                
                month_values.append(value)
            z_values.append(month_values)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=years,
            y=months,
            colorscale='RdYlGn',
            text=[[f"R$ {v:,.0f}" for v in row] for row in z_values],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=f"{title} - {self._translate_metric_name(metric)}",
            xaxis_title="Ano",
            yaxis_title="Mês",
            height=500
        )
        
        return fig
    
    def _create_scatter_plot(self, data: Dict, requirements: Dict) -> go.Figure:
        """Create scatter plot for correlations"""
        metrics = requirements['metrics']
        title = requirements.get('title', 'Análise de Correlação')
        
        if len(metrics) < 2:
            return None
        
        x_metric = metrics[0]
        y_metric = metrics[1]
        
        # Collect data points
        x_values = []
        y_values = []
        labels = []
        
        for year in sorted(data.keys()):
            year_data = data[year]
            
            # Get x value
            x_val = self._get_metric_value(year_data, x_metric)
            y_val = self._get_metric_value(year_data, y_metric)
            
            if x_val > 0 and y_val > 0:
                x_values.append(x_val)
                y_values.append(y_val)
                labels.append(str(year))
        
        # Create scatter plot
        fig = go.Figure(data=go.Scatter(
            x=x_values,
            y=y_values,
            mode='markers+text',
            text=labels,
            textposition="top center",
            marker=dict(
                size=12,
                color=list(range(len(x_values))),
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Ano")
            )
        ))
        
        # Add trend line
        if len(x_values) > 1:
            z = np.polyfit(x_values, y_values, 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=x_values,
                y=p(x_values),
                mode='lines',
                name='Tendência',
                line=dict(color='red', dash='dash')
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=self._translate_metric_name(x_metric),
            yaxis_title=self._translate_metric_name(y_metric),
            height=500,
            showlegend=True
        )
        
        return fig
    
    def _create_stacked_bar_chart(self, data: Dict, requirements: Dict) -> go.Figure:
        """Create stacked bar chart for multi-metric comparison"""
        metrics = requirements['metrics']
        time_period = requirements['time_period']
        title = requirements.get('title', 'Comparação de Métricas')
        
        # Get years to display
        if time_period['years']:
            years = [str(y) for y in time_period['years'] if str(y) in data]
        else:
            years = sorted(data.keys())
        
        # Create traces for each metric
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        for i, metric in enumerate(metrics):
            values = []
            for year in years:
                value = self._get_metric_value(data[year], metric)
                values.append(value)
            
            fig.add_trace(go.Bar(
                name=self._translate_metric_name(metric),
                x=years,
                y=values,
                text=[f"R$ {v:,.0f}" for v in values],
                textposition='inside',
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            barmode='stack',
            title=title,
            xaxis_title="Ano",
            yaxis_title="Valor (R$)",
            height=500,
            showlegend=True
        )
        
        return fig
    
    def _create_box_plot(self, data: Dict, requirements: Dict) -> go.Figure:
        """Create box plot for distribution analysis"""
        metrics = requirements['metrics']
        title = requirements.get('title', 'Análise de Distribuição')
        
        metric = metrics[0] if metrics else 'revenue'
        
        # Collect monthly values for each year
        fig = go.Figure()
        
        for year in sorted(data.keys()):
            year_data = data[year]
            monthly_values = []
            
            if metric in year_data and isinstance(year_data[metric], dict):
                for month in ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                             'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']:
                    if month in year_data[metric]:
                        monthly_values.append(year_data[metric][month])
            
            if monthly_values:
                fig.add_trace(go.Box(
                    y=monthly_values,
                    name=str(year),
                    boxpoints='all',
                    jitter=0.3,
                    pointpos=-1.8
                ))
        
        fig.update_layout(
            title=f"{title} - {self._translate_metric_name(metric)}",
            yaxis_title="Valor (R$)",
            height=500,
            showlegend=False
        )
        
        return fig
    
    def _create_area_chart(self, data: Dict, requirements: Dict) -> go.Figure:
        """Create area chart for cumulative visualization"""
        metrics = requirements['metrics']
        title = requirements.get('title', 'Evolução Acumulada')
        
        years = sorted(data.keys())
        
        fig = go.Figure()
        
        for metric in metrics:
            values = []
            for year in years:
                value = self._get_metric_value(data[year], metric)
                values.append(value)
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                mode='lines',
                name=self._translate_metric_name(metric),
                fill='tonexty',
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Ano",
            yaxis_title="Valor (R$)",
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def _create_bar_chart(self, data: Dict, requirements: Dict) -> go.Figure:
        """Create enhanced bar chart based on requirements"""
        metrics = requirements['metrics']
        time_period = requirements['time_period']
        title = requirements.get('title', 'Comparação')
        
        # Get years to display
        if time_period['years']:
            years = [str(y) for y in time_period['years'] if str(y) in data]
        else:
            years = sorted(data.keys())
        
        fig = go.Figure()
        
        # Single metric bar chart
        if len(metrics) == 1:
            metric = metrics[0]
            values = []
            for year in years:
                value = self._get_metric_value(data[year], metric)
                values.append(value)
            
            fig.add_trace(go.Bar(
                x=years,
                y=values,
                text=[f"R$ {v:,.0f}" for v in values],
                textposition='outside',
                marker_color='#667eea'
            ))
        else:
            # Multiple metrics grouped bar chart
            for metric in metrics:
                values = []
                for year in years:
                    value = self._get_metric_value(data[year], metric)
                    values.append(value)
                
                fig.add_trace(go.Bar(
                    name=self._translate_metric_name(metric),
                    x=years,
                    y=values,
                    text=[f"R$ {v:,.0f}" for v in values],
                    textposition='outside'
                ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Ano",
            yaxis_title="Valor (R$)",
            height=500,
            barmode='group' if len(metrics) > 1 else None,
            showlegend=len(metrics) > 1
        )
        
        return fig
    
    def _create_enhanced_line_chart(self, data: Dict, requirements: Dict) -> go.Figure:
        """Create enhanced line chart based on requirements"""
        metrics = requirements['metrics']
        time_period = requirements['time_period']
        title = requirements.get('title', 'Evolução Temporal')
        
        # Get years to display
        if time_period['years']:
            years = [str(y) for y in time_period['years'] if str(y) in data]
        else:
            years = sorted(data.keys())
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set2
        for i, metric in enumerate(metrics):
            values = []
            for year in years:
                value = self._get_metric_value(data[year], metric)
                values.append(value)
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                mode='lines+markers',
                name=self._translate_metric_name(metric),
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Ano",
            yaxis_title="Valor (R$)",
            height=500,
            hovermode='x unified',
            showlegend=len(metrics) > 1
        )
        
        return fig
    
    def _get_metric_value(self, year_data: Dict, metric: str) -> float:
        """Extract metric value from year data"""
        if metric in year_data:
            if isinstance(year_data[metric], dict):
                return year_data[metric].get('ANNUAL', 0)
            else:
                return year_data[metric]
        elif metric == 'costs' and 'costs' in year_data:
            return year_data['costs'].get('ANNUAL', 0)
        elif metric == 'variable_costs' and 'costs' in year_data:
            return year_data['costs'].get('ANNUAL', 0)
        elif 'line_items' in year_data:
            for item_key, item_data in year_data['line_items'].items():
                if metric in item_key.lower():
                    return item_data.get('annual', 0)
        return 0
    
    def _translate_metric_name(self, metric: str) -> str:
        """Translate metric names to Portuguese"""
        translations = {
            'revenue': 'Receita',
            'costs': 'Custos',
            'variable_costs': 'Custos Variáveis',
            'fixed_costs': 'Custos Fixos',
            'operational_costs': 'Custos Operacionais',
            'net_profit': 'Lucro Líquido',
            'gross_profit': 'Lucro Bruto',
            'margins': 'Margem',
            'profits': 'Lucros',
            'contribution_margin': 'Margem de Contribuição'
        }
        return translations.get(metric, metric.replace('_', ' ').title())
    
    def _export_chat(self):
        """Export chat history"""
        chat_text = "# Conversa com IA - Marine Seguros\n\n"
        chat_text += f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        
        for message in st.session_state.chat_history:
            timestamp = message['timestamp'].strftime('%H:%M')
            role = "Você" if message['role'] == 'user' else "IA"
            chat_text += f"**[{timestamp}] {role}:** {message['content']}\n\n"
        
        st.download_button(
            label="💾 Baixar conversa",
            data=chat_text,
            file_name=f"chat_marine_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown"
        )
    
    def set_filter_from_query(self, query: str) -> Optional[Dict]:
        """Extract filter settings from natural language query"""
        filters = {}
        
        # Extract years
        year_pattern = r'\b(20\d{2})\b'
        years = re.findall(year_pattern, query)
        if years:
            filters['years'] = [int(y) for y in years]
        
        # Extract months
        month_map = {
            'janeiro': 'JAN', 'jan': 'JAN',
            'fevereiro': 'FEV', 'fev': 'FEV',
            'março': 'MAR', 'mar': 'MAR',
            'abril': 'ABR', 'abr': 'ABR',
            'maio': 'MAI', 'mai': 'MAI',
            'junho': 'JUN', 'jun': 'JUN',
            'julho': 'JUL', 'jul': 'JUL',
            'agosto': 'AGO', 'ago': 'AGO',
            'setembro': 'SET', 'set': 'SET',
            'outubro': 'OUT', 'out': 'OUT',
            'novembro': 'NOV', 'nov': 'NOV',
            'dezembro': 'DEZ', 'dez': 'DEZ'
        }
        
        query_lower = query.lower()
        months_found = []
        for pt_month, month_code in month_map.items():
            if pt_month in query_lower:
                months_found.append(month_code)
        
        if months_found:
            filters['months'] = list(set(months_found))
        
        # Extract quarters
        quarter_pattern = r'\b(q[1-4]|[1-4]º?\s*trimestre)\b'
        quarters = re.findall(quarter_pattern, query_lower)
        if quarters:
            filters['quarters'] = quarters
        
        return filters if filters else None