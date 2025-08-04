"""
Financial Notes Display Module
"""

import streamlit as st
import os
from core.extractors.financial_analysis_extractor import FinancialAnalysisExtractor
from ..config import GRAPH_CONFIGS


def render_financial_notes(flexible_data, config=None):
    """
    Render financial analysis notes from spreadsheets
    
    Args:
        flexible_data: Raw flexible data
        config: Optional configuration overrides
    """
    config = {**GRAPH_CONFIGS.get('financial_notes', {}), **(config or {})}
    
    st.subheader(f"📝 {config.get('title', 'Análise Financeira Anual')}")
    
    # Extract analysis notes
    extractor = FinancialAnalysisExtractor()
    
    # Get uploaded files info
    if hasattr(st.session_state, 'uploaded_files_info') and st.session_state.uploaded_files_info:
        analysis_notes = {}
        
        for file_info in st.session_state.uploaded_files_info:
            file_path = file_info.get('caminho', '')
            if file_path and os.path.exists(file_path):
                notes = extractor.extract_from_excel(file_path)
                analysis_notes.update(notes)
        
        if analysis_notes:
            _display_analysis_notes(analysis_notes, config)
        else:
            st.info("📄 Nenhuma análise financeira encontrada nas planilhas.")
            _show_analysis_tips()
    else:
        st.info("📁 Carregue arquivos para visualizar as análises financeiras.")
    
    # Automated insights
    _render_automated_insights(flexible_data)


def _display_analysis_notes(analysis_notes, config):
    """Display the extracted analysis notes"""
    # Sort years in reverse order
    sorted_years = sorted(analysis_notes.keys(), reverse=True)
    
    # Year navigation if enabled
    if config.get('show_year_navigation'):
        selected_year = st.selectbox(
            "Selecione o ano",
            sorted_years,
            format_func=lambda x: f"Análise de {x}",
            key="analysis_year_selector"
        )
        
        # Display selected year
        if selected_year in analysis_notes:
            with st.expander(f"📅 Análise de {selected_year}", expanded=True):
                formatted_text = FinancialAnalysisExtractor().format_analysis_for_display(
                    analysis_notes[selected_year]
                )
                st.markdown(formatted_text)
    else:
        # Display all years
        for year in sorted_years:
            expanded = config.get('expanded_by_default', True) and (year == sorted_years[0])
            with st.expander(f"📅 Análise de {year}", expanded=expanded):
                formatted_text = FinancialAnalysisExtractor().format_analysis_for_display(
                    analysis_notes[year]
                )
                st.markdown(formatted_text)


def _show_analysis_tips():
    """Show tips for where to find analysis in spreadsheets"""
    with st.expander("💡 Dica: Onde encontrar análises nas planilhas"):
        st.markdown("""
        As análises financeiras geralmente estão localizadas em:
        - **Cantos das planilhas** (especialmente canto inferior direito)
        - **Seções específicas** com títulos como "Análise Financeira" ou "Observações"
        - **Final de cada aba anual** com comentários sobre o desempenho
        
        Verifique suas planilhas e adicione análises para enriquecer os insights!
        """)


def _render_automated_insights(flexible_data):
    """Render automated insights based on data"""
    st.subheader("🔍 Insights Automáticos")
    
    if flexible_data:
        years = sorted(flexible_data.keys())
        if len(years) >= 2:
            # Revenue and margin trends
            col1, col2 = st.columns(2)
            
            with col1:
                _show_revenue_trend(flexible_data, years)
            
            with col2:
                _show_margin_trend(flexible_data, years)
            
            # Cost analysis
            _show_cost_insights(flexible_data, years)


def _show_revenue_trend(flexible_data, years):
    """Show revenue trend insight"""
    revenues = []
    for year in years:
        year_data = flexible_data.get(year, {})
        if isinstance(year_data, dict):
            revenue_data = year_data.get('revenue', {})
            if isinstance(revenue_data, dict):
                revenues.append(revenue_data.get('annual', 0))
            else:
                revenues.append(revenue_data if revenue_data else 0)
    
    if revenues and revenues[0] > 0:
        growth = ((revenues[-1] - revenues[0]) / revenues[0]) * 100
        
        st.metric(
            "Crescimento da Receita",
            f"{growth:+.1f}%",
            f"De {years[0]} a {years[-1]}",
            delta_color="normal" if growth > 0 else "inverse"
        )


def _show_margin_trend(flexible_data, years):
    """Show margin trend insight"""
    margins = []
    for year in years:
        year_data = flexible_data.get(year, {})
        if isinstance(year_data, dict):
            revenue = year_data.get('revenue', {})
            profit = year_data.get('net_profit', {})
            
            if isinstance(revenue, dict):
                rev_value = revenue.get('annual', 0)
            else:
                rev_value = revenue if revenue else 0
            
            if isinstance(profit, dict):
                profit_value = profit.get('annual', 0)
            else:
                profit_value = profit if profit else 0
            
            if rev_value > 0:
                margins.append((profit_value / rev_value) * 100)
    
    if len(margins) >= 2:
        change = margins[-1] - margins[0]
        
        st.metric(
            "Variação da Margem",
            f"{change:+.1f}pp",
            f"De {margins[0]:.1f}% para {margins[-1]:.1f}%",
            delta_color="normal" if change > 0 else "inverse"
        )


def _show_cost_insights(flexible_data, years):
    """Show cost structure insights"""
    st.markdown("#### 💰 Evolução dos Custos")
    
    # Calculate cost evolution
    first_year = years[0]
    last_year = years[-1]
    
    cost_types = [
        ('Custos Variáveis', 'variable_costs'),
        ('Custos Fixos', 'fixed_costs'),
        ('Impostos', 'taxes'),
        ('Comissões', 'commissions')
    ]
    
    insights = []
    for name, key in cost_types:
        first_value = _get_cost_value(flexible_data, first_year, key)
        last_value = _get_cost_value(flexible_data, last_year, key)
        
        if first_value > 0:
            change = ((last_value - first_value) / first_value) * 100
            if abs(change) > 10:  # Only show significant changes
                insights.append(f"• **{name}**: {change:+.1f}% ({first_year} → {last_year})")
    
    if insights:
        st.markdown("\n".join(insights))
    else:
        st.info("Custos mantiveram-se relativamente estáveis no período.")


def _get_cost_value(flexible_data, year, cost_key):
    """Helper to extract cost value from flexible data"""
    year_data = flexible_data.get(year, {})
    if isinstance(year_data, dict):
        cost_data = year_data.get(cost_key, {})
        if isinstance(cost_data, dict):
            return cost_data.get('annual', 0)
        else:
            return cost_data if cost_data else 0
    return 0