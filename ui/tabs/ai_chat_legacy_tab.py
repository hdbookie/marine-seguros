"""
AI Chat Tab - Legacy version extracted from app.py
Preserves all original functionality while organizing code
"""

import streamlit as st
from ai.chat_assistant import AIChatAssistant


def render_ai_chat_tab(gemini_api_key):
    """Render the AI chat tab with conversational interface"""
    
    st.header("💬 AI Chat Assistant")
    
    if not gemini_api_key:
        st.warning("⚠️ Please enter your Gemini API key in the sidebar to use AI Chat.")
        st.info("You can get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)")
        return
    
    # Initialize AI chat assistant if not already done
    if st.session_state.ai_chat_assistant is None:
        st.session_state.ai_chat_assistant = AIChatAssistant(api_key=gemini_api_key)
    
    # Check if we have financial data
    if not hasattr(st.session_state, 'extracted_data') or not st.session_state.extracted_data:
        st.info("👆 Please upload files and process data in the 'Upload' tab first.")
        return
    
    # Prepare filter context
    filter_context = "All available data"
    if hasattr(st.session_state, 'selected_years') and st.session_state.selected_years:
        years = st.session_state.selected_years
        filter_context = f"Years: {', '.join(map(str, years))}"
        if hasattr(st.session_state, 'selected_months') and st.session_state.selected_months:
            months = st.session_state.selected_months
            filter_context += f" | Months: {', '.join(months)}"
    
    # Use the AIChatAssistant's built-in interface
    st.session_state.ai_chat_assistant.render_chat_interface(
        data=st.session_state.extracted_data,
        filter_context=filter_context
    )