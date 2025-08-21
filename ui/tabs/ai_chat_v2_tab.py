"""
AI Chat Tab V2 - Enhanced conversational interface
Uses the new ChatInterface with structured responses and Marine Seguros-specific analysis
"""

import streamlit as st
from ai.insights_v2.chat_interface import ChatInterface
from ai.insights_v2 import EnhancedAIAnalyzer


def render_ai_chat_v2_tab(db, gemini_api_key, language="Português"):
    """Render the enhanced AI chat tab with structured conversational interface"""
    
    st.header("💬 Assistente de Análise Financeira")
    
    if not gemini_api_key:
        st.warning("⚠️ Configure sua chave API Gemini na barra lateral para usar o Chat IA.")
        st.info("Obtenha uma chave gratuita no [Google AI Studio](https://makersuite.google.com/app/apikey)")
        return
    
    # Check if we have financial data
    if not hasattr(st.session_state, 'extracted_data') or not st.session_state.extracted_data:
        st.info("👆 Carregue arquivos na aba 'Upload' primeiro para usar o assistente de chat.")
        return
    
    # Initialize AI analyzer if not already done
    if 'ai_analyzer_v2' not in st.session_state or st.session_state.ai_analyzer_v2 is None:
        try:
            st.session_state.ai_analyzer_v2 = EnhancedAIAnalyzer(api_key=gemini_api_key)
        except Exception as e:
            st.error(f"Erro ao inicializar analisador IA: {str(e)}")
            return
    
    # Initialize chat interface
    if 'chat_interface_v2' not in st.session_state:
        st.session_state.chat_interface_v2 = ChatInterface(analyzer=st.session_state.ai_analyzer_v2)
    
    # Show data context info
    with st.expander("📊 Contexto dos Dados", expanded=False):
        if hasattr(st.session_state, 'extracted_data'):
            data_years = list(st.session_state.extracted_data.keys()) if st.session_state.extracted_data else []
            st.info(f"**Dados disponíveis:** {', '.join(map(str, data_years))}")
            
            # Show quick data overview
            total_records = 0
            categories = set()
            for year_data in st.session_state.extracted_data.values():
                if isinstance(year_data, dict):
                    for category, items in year_data.items():
                        categories.add(category)
                        if isinstance(items, list):
                            total_records += len(items)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Registros", total_records)
            with col2:
                st.metric("Categorias", len(categories))
            
            if categories:
                st.markdown("**Categorias disponíveis:**")
                st.write(", ".join(sorted(categories)))
    
    # Render the enhanced chat interface
    try:
        st.session_state.chat_interface_v2.render_chat_interface(
            financial_data=st.session_state.extracted_data
        )
    except Exception as e:
        st.error(f"Erro ao renderizar interface de chat: {str(e)}")
        st.info("Tente recarregar a página ou verificar os dados carregados.")
    
    # Show help section
    with st.expander("❓ Ajuda - Como usar o Chat IA", expanded=False):
        st.markdown("""
        ### 🎯 Tipos de Análise Disponíveis
        
        **📊 Análise de Saúde Financeira:**
        - "Qual é a saúde financeira geral da empresa?"
        - "Como está nossa situação financeira?"
        
        **💰 Otimização de Custos:**
        - "Onde posso reduzir custos sem impactar operações?"
        - "Quais custos variáveis podem ser otimizados?"
        
        **⚠️ Análise de Riscos:**
        - "Quais são os principais riscos financeiros?"
        - "Que ameaças financeiras devemos monitorar?"
        
        **📈 Crescimento de Receita:**
        - "Como melhorar nossa receita?"
        - "Qual o potencial de crescimento?"
        
        **🔍 Perguntas Personalizadas:**
        - Faça qualquer pergunta específica sobre seus dados financeiros
        
        ### 💡 Dicas
        - Use as **perguntas sugeridas** para começar
        - As respostas incluem **métricas**, **insights** e **recomendações**
        - Dê **feedback** (👍/👎) para melhorar as respostas
        - **Export** suas conversas para análise posterior
        """)