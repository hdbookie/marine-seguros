"""
Interactive chat interface for financial analysis
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import asyncio

class ChatInterface:
    """
    Interactive chat interface for conversational financial analysis
    """
    
    def __init__(self, analyzer=None):
        """
        Initialize chat interface
        
        Args:
            analyzer: AI analyzer instance for generating responses
        """
        self.analyzer = analyzer
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for chat history"""
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        if 'chat_context' not in st.session_state:
            st.session_state.chat_context = {}
        
        if 'suggested_questions' not in st.session_state:
            st.session_state.suggested_questions = self._get_initial_suggestions()
    
    def _get_initial_suggestions(self) -> List[str]:
        """Get initial suggested questions based on available data"""
        return [
            "Qual é a saúde financeira geral da empresa?",
            "Onde posso reduzir custos sem impactar operações?",
            "Quais são os principais riscos financeiros?",
            "Como está nossa performance comparada ao mercado?",
            "Qual a previsão de receita para os próximos meses?",
            "Quais categorias de despesas cresceram mais?",
            "Existe alguma anomalia nos dados financeiros?",
            "Como melhorar a margem de lucro?"
        ]
    
    def render_chat_interface(self, financial_data: Dict = None):
        """
        Render the main chat interface
        
        Args:
            financial_data: Current financial data context
        """
        st.markdown("### 💬 Assistente de Análise Financeira")
        
        # Update context if new data is provided
        if financial_data:
            st.session_state.chat_context = financial_data
        
        # Render suggested questions
        self._render_suggested_questions()
        
        # Render chat history
        self._render_chat_history()
        
        # Render input area
        self._render_chat_input()
        
        # Render chat controls
        self._render_chat_controls()
    
    def _render_suggested_questions(self):
        """Render suggested question buttons"""
        if st.session_state.suggested_questions:
            st.markdown("#### 💡 Perguntas Sugeridas")
            
            # Create columns for question buttons
            cols = st.columns(2)
            
            for idx, question in enumerate(st.session_state.suggested_questions[:4]):
                col_idx = idx % 2
                with cols[col_idx]:
                    if st.button(
                        question,
                        key=f"v2_suggested_{idx}",  # Changed to avoid key conflicts
                        use_container_width=True,
                        help="Clique para fazer esta pergunta"
                    ):
                        self._process_user_message(question)
                        st.rerun()
    
    def _render_chat_history(self):
        """Render the chat message history"""
        if st.session_state.chat_messages:
            st.markdown("#### 📝 Conversa")
            
            # Create a scrollable container for messages
            chat_container = st.container()
            
            with chat_container:
                for msg in st.session_state.chat_messages:
                    self._render_message(msg)
    
    def _render_message(self, message: Dict):
        """
        Render a single chat message
        
        Args:
            message: Message dictionary with role, content, timestamp
        """
        if message['role'] == 'user':
            with st.chat_message("user", avatar="👤"):
                st.markdown(message['content'])
                st.caption(message.get('timestamp', ''))
        
        elif message['role'] == 'assistant':
            with st.chat_message("assistant", avatar="🤖"):
                # Check if content is structured
                if isinstance(message.get('content'), dict):
                    self._render_structured_response(message['content'])
                else:
                    st.markdown(message['content'])
                
                st.caption(message.get('timestamp', ''))
                
                # Add feedback buttons
                col1, col2, col3 = st.columns([1, 1, 8])
                with col1:
                    if st.button("👍", key=f"v2_like_{message.get('id', '')}"):
                        self._record_feedback(message.get('id'), 'positive')
                with col2:
                    if st.button("👎", key=f"v2_dislike_{message.get('id', '')}"):
                        self._record_feedback(message.get('id'), 'negative')
    
    def _render_structured_response(self, content: Dict):
        """
        Render structured AI response with sections
        
        Args:
            content: Structured content dictionary
        """
        # Executive Summary
        if 'executive_summary' in content:
            with st.expander("📊 Resumo Executivo", expanded=True):
                st.markdown(content['executive_summary'])
        
        # Key Metrics
        if 'key_metrics' in content:
            st.markdown("**Métricas Principais:**")
            cols = st.columns(len(content['key_metrics']))
            for idx, metric in enumerate(content['key_metrics']):
                with cols[idx]:
                    st.metric(
                        metric['label'],
                        metric['value'],
                        delta=metric.get('delta')
                    )
        
        # Insights
        if 'insights' in content:
            with st.expander("💡 Insights Detalhados"):
                for insight in content['insights']:
                    st.markdown(f"• **{insight['title']}**: {insight['description']}")
        
        # Recommendations
        if 'recommendations' in content:
            with st.expander("🎯 Recomendações"):
                for rec in content['recommendations']:
                    priority_color = {
                        'Alta': '🔴',
                        'Média': '🟡',
                        'Baixa': '🟢'
                    }.get(rec.get('priority', 'Média'), '⚪')
                    
                    st.markdown(f"{priority_color} **{rec['action']}**")
                    if 'impact' in rec:
                        st.markdown(f"   *Impacto esperado: {rec['impact']}*")
        
        # Charts
        if 'charts' in content:
            for idx, chart in enumerate(content['charts']):
                st.plotly_chart(chart, use_container_width=True, key=f"v2_chart_{idx}")
        
        # Raw text fallback
        if 'raw_text' in content:
            st.markdown(content['raw_text'])
    
    def _render_chat_input(self):
        """Render the chat input area"""
        st.markdown("#### 💭 Sua Pergunta")
        
        # Create input form
        with st.form(key="v2_chat_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                user_input = st.text_area(
                    "Digite sua pergunta sobre os dados financeiros:",
                    height=80,
                    placeholder="Ex: Qual categoria de despesa teve maior crescimento este ano?",
                    key="v2_chat_input"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                submit_button = st.form_submit_button(
                    "Enviar 📤",
                    use_container_width=True,
                    type="primary"
                )
            
            if submit_button and user_input:
                self._process_user_message(user_input)
                st.rerun()
    
    def _render_chat_controls(self):
        """Render chat control buttons"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Nova Conversa", use_container_width=True):
                st.session_state.chat_messages = []
                st.session_state.suggested_questions = self._get_initial_suggestions()
                st.success("Nova conversa iniciada!")
                st.rerun()
        
        with col2:
            if st.button("📥 Exportar Conversa", use_container_width=True):
                self._export_conversation()
        
        with col3:
            if st.button("🎯 Mais Sugestões", use_container_width=True):
                self._update_suggestions()
                st.rerun()
    
    def _process_user_message(self, message: str):
        """
        Process user message and generate AI response
        
        Args:
            message: User's question or message
        """
        # Add user message to history
        user_msg = {
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().strftime("%H:%M"),
            'id': f"user_{len(st.session_state.chat_messages)}"
        }
        st.session_state.chat_messages.append(user_msg)
        
        # Generate AI response
        if self.analyzer:
            with st.spinner("Analisando sua pergunta..."):
                try:
                    # Get response from analyzer
                    response = self._generate_ai_response(message)
                    
                    # Add assistant message to history
                    assistant_msg = {
                        'role': 'assistant',
                        'content': response,
                        'timestamp': datetime.now().strftime("%H:%M"),
                        'id': f"assistant_{len(st.session_state.chat_messages)}"
                    }
                    st.session_state.chat_messages.append(assistant_msg)
                    
                    # Update suggested questions based on conversation
                    self._update_suggestions_based_on_response(message, response)
                    
                except Exception as e:
                    error_msg = {
                        'role': 'assistant',
                        'content': f"Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}",
                        'timestamp': datetime.now().strftime("%H:%M"),
                        'id': f"error_{len(st.session_state.chat_messages)}"
                    }
                    st.session_state.chat_messages.append(error_msg)
        else:
            # Fallback if no analyzer
            fallback_msg = {
                'role': 'assistant',
                'content': "Analisador AI não configurado. Por favor, configure o analisador primeiro.",
                'timestamp': datetime.now().strftime("%H:%M"),
                'id': f"fallback_{len(st.session_state.chat_messages)}"
            }
            st.session_state.chat_messages.append(fallback_msg)
    
    def _generate_ai_response(self, question: str) -> Any:
        """
        Generate AI response for user question
        
        Args:
            question: User's question
        
        Returns:
            Structured or text response
        """
        if not self.analyzer:
            return "Analisador não disponível"
        
        # Prepare context
        context = {
            'financial_data': st.session_state.chat_context,
            'conversation_history': st.session_state.chat_messages[-5:] if st.session_state.chat_messages else []
        }
        
        # Check question type and route to appropriate analysis
        question_lower = question.lower()
        
        # Financial health questions
        if any(term in question_lower for term in ['saúde', 'health', 'situação', 'status']):
            from .prompt_templates import PromptTemplates
            templates = PromptTemplates()
            prompt = templates.executive_summary(
                metrics=self._extract_metrics_from_context(context),
                context={'period': 'Últimos 12 meses'}
            )
        
        # Cost optimization questions
        elif any(term in question_lower for term in ['custo', 'reduzir', 'economizar', 'otimizar']):
            from .prompt_templates import PromptTemplates
            templates = PromptTemplates()
            prompt = templates.cost_optimization(
                expenses_df=str(context.get('financial_data', {})),
                categories=['Fixos', 'Variáveis', 'Administrativos']
            )
        
        # Risk questions
        elif any(term in question_lower for term in ['risco', 'risk', 'perigo', 'ameaça']):
            from .prompt_templates import PromptTemplates
            templates = PromptTemplates()
            prompt = templates.risk_assessment(
                financial_data=context.get('financial_data', {}),
                historical_data=[]
            )
        
        # Revenue growth questions
        elif any(term in question_lower for term in ['receita', 'crescimento', 'revenue', 'vendas']):
            from .prompt_templates import PromptTemplates
            templates = PromptTemplates()
            prompt = templates.revenue_growth(
                revenue_data=self._extract_revenue_data(context),
                market_context={}
            )
        
        # Custom questions
        else:
            from .prompt_templates import PromptTemplates
            templates = PromptTemplates()
            prompt = templates.custom_question(
                question=question,
                data_context=context
            )
        
        # Generate response
        try:
            response = self.analyzer.model.generate_content(prompt)
            return self._parse_ai_response(response.text)
        except Exception as e:
            return f"Erro ao gerar resposta: {str(e)}"
    
    def _parse_ai_response(self, response_text: str) -> Any:
        """
        Parse AI response into structured format if possible
        
        Args:
            response_text: Raw AI response text
        
        Returns:
            Structured dict or raw text
        """
        try:
            # Try to parse as JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Return as raw text
                return response_text
        except:
            return response_text
    
    def _extract_metrics_from_context(self, context: Dict) -> Dict:
        """Extract key metrics from context for prompts"""
        financial_data = context.get('financial_data', {})
        
        metrics = {
            'total_revenue': 0,
            'total_costs': 0,
            'profit_margin': 0,
            'growth_rate': 0
        }
        
        # Extract metrics from financial data
        if isinstance(financial_data, dict):
            for year, data in financial_data.items():
                if isinstance(data, dict):
                    metrics['total_revenue'] += data.get('revenue', 0)
                    metrics['total_costs'] += data.get('total_costs', 0)
        
        return metrics
    
    def _extract_revenue_data(self, context: Dict) -> Dict:
        """Extract revenue data from context"""
        financial_data = context.get('financial_data', {})
        revenue_data = {}
        
        if isinstance(financial_data, dict):
            for year, data in financial_data.items():
                if isinstance(data, dict) and 'revenue' in data:
                    revenue_data[year] = data['revenue']
        
        return revenue_data
    
    def _update_suggestions(self):
        """Update suggested questions based on conversation"""
        # Generate new suggestions based on context
        new_suggestions = [
            "Como posso melhorar a margem de lucro?",
            "Quais são as tendências de custos?",
            "Existe potencial de crescimento não explorado?",
            "Como estamos comparados aos concorrentes?",
            "Qual o impacto de reduzir custos fixos em 10%?",
            "Quais métricas devo monitorar semanalmente?",
            "Há algum padrão sazonal nos dados?",
            "Qual a previsão para o próximo trimestre?"
        ]
        
        # Rotate suggestions
        st.session_state.suggested_questions = new_suggestions
    
    def _update_suggestions_based_on_response(self, question: str, response: Any):
        """Update suggestions based on the conversation flow"""
        # Generate follow-up questions based on the topic
        question_lower = question.lower()
        
        if 'custo' in question_lower:
            follow_ups = [
                "Quais custos variáveis podem ser reduzidos?",
                "Como otimizar custos fixos?",
                "Qual o impacto de terceirização?",
                "Onde temos maior desperdício?"
            ]
        elif 'receita' in question_lower:
            follow_ups = [
                "Quais produtos têm melhor margem?",
                "Como aumentar ticket médio?",
                "Qual o potencial de novos mercados?",
                "Como melhorar retenção de clientes?"
            ]
        elif 'risco' in question_lower:
            follow_ups = [
                "Como mitigar riscos identificados?",
                "Qual nosso nível de exposição?",
                "Precisamos de mais reservas?",
                "Como melhorar liquidez?"
            ]
        else:
            follow_ups = self._get_initial_suggestions()[:4]
        
        st.session_state.suggested_questions = follow_ups
    
    def _export_conversation(self):
        """Export conversation history"""
        if not st.session_state.chat_messages:
            st.warning("Nenhuma conversa para exportar")
            return
        
        # Format conversation for export
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'messages': st.session_state.chat_messages,
            'context': st.session_state.chat_context
        }
        
        # Convert to JSON
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Offer download
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _record_feedback(self, message_id: str, feedback_type: str):
        """
        Record user feedback on AI responses
        
        Args:
            message_id: ID of the message
            feedback_type: 'positive' or 'negative'
        """
        # Store feedback (could be sent to analytics)
        if 'feedback_log' not in st.session_state:
            st.session_state.feedback_log = []
        
        st.session_state.feedback_log.append({
            'message_id': message_id,
            'feedback': feedback_type,
            'timestamp': datetime.now().isoformat()
        })
        
        # Show confirmation
        if feedback_type == 'positive':
            st.success("Obrigado pelo feedback positivo! 👍")
        else:
            st.info("Obrigado pelo feedback. Vamos melhorar! 📈")