"""
KPI Section Module for Micro Analysis
Handles the main KPI cards display
"""

import streamlit as st
from utils import format_currency
from .config import GRAPH_CONFIGS


def render_kpi_section(df, view_type="Anual", config=None):
    """
    Render the KPI cards section with period-aware metrics
    
    Args:
        df: DataFrame with financial data
        view_type: Current view type (Anual, Mensal, etc.)
        config: Optional configuration overrides
    """
    if df.empty:
        return
    
    # Get configuration
    kpi_config = {**GRAPH_CONFIGS['kpi_cards'], **(config or {})}
    
    latest_data = df.iloc[-1]
    previous_data = df.iloc[-2] if len(df) > 1 else None
    
    # Determine period labels based on view type
    period_label, prev_period_label = _get_period_labels(latest_data, previous_data, view_type)
    
    # Display header with period
    st.markdown(f"### 📈 Indicadores Principais - {period_label}")
    
    # Create four columns for KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    # Revenue KPI
    with col1:
        _render_revenue_kpi(latest_data, previous_data, prev_period_label, kpi_config)
    
    # Total Costs KPI
    with col2:
        _render_costs_kpi(latest_data, previous_data, prev_period_label, kpi_config)
    
    # Net Profit KPI
    with col3:
        _render_profit_kpi(latest_data, previous_data, prev_period_label, kpi_config)
    
    # Profit Margin KPI
    with col4:
        _render_margin_kpi(latest_data, previous_data, prev_period_label, kpi_config)


def _get_period_labels(latest_data, previous_data, view_type):
    """Extract period labels based on view type"""
    if view_type == "Anual":
        period_label = str(latest_data.get('year', ''))
        prev_period_label = str(previous_data.get('year', '')) if previous_data is not None else ''
    elif view_type == "Mensal":
        period_label = latest_data.get('period', f"{latest_data.get('year', '')}-{latest_data.get('month', '')}")
        prev_period_label = previous_data.get('period', '') if previous_data is not None else ''
    elif view_type == "Trimestral":
        period_label = latest_data.get('period', f"{latest_data.get('year', '')}-Q{latest_data.get('quarter', '')}")
        prev_period_label = previous_data.get('period', '') if previous_data is not None else ''
    elif view_type == "Semestral":
        period_label = latest_data.get('period', f"{latest_data.get('year', '')}-S{latest_data.get('semester', '')}")
        prev_period_label = previous_data.get('period', '') if previous_data is not None else ''
    else:
        period_label = str(latest_data.get('year', ''))
        prev_period_label = str(previous_data.get('year', '')) if previous_data is not None else ''
    
    return period_label, prev_period_label


def _render_revenue_kpi(latest_data, previous_data, prev_period_label, config):
    """Render revenue KPI card"""
    revenue = latest_data.get('revenue', 0)
    delta = revenue - previous_data.get('revenue', 0) if previous_data is not None else None
    
    delta_text = None
    if delta is not None and config.get('comparison_format'):
        delta_text = f"{format_currency(delta)} {config['comparison_format'].format(period=prev_period_label)}"
    
    help_text = f"Valor exato: {format_currency(revenue, compact=False)}" if config.get('show_tooltips') else None
    
    st.metric(
        "Receita", 
        format_currency(revenue, compact=config.get('compact_format', True)), 
        delta_text,
        help=help_text
    )


def _render_costs_kpi(latest_data, previous_data, prev_period_label, config):
    """Render total costs KPI card"""
    # Only sum main cost categories to avoid double counting
    # taxes, commissions are already included in variable_costs
    # administrative_expenses, marketing_expenses, financial_expenses are already included in fixed_costs
    cost_fields = [
        'variable_costs', 'fixed_costs', 'non_operational_costs'
    ]
    
    total_costs = sum(latest_data.get(field, 0) for field in cost_fields)
    prev_total_costs = sum(previous_data.get(field, 0) for field in cost_fields) if previous_data is not None else None
    
    delta = total_costs - prev_total_costs if prev_total_costs is not None else None
    
    delta_text = None
    if delta is not None and config.get('comparison_format'):
        delta_text = f"{format_currency(delta)} {config['comparison_format'].format(period=prev_period_label)}"
    
    help_text = f"Valor exato: {format_currency(total_costs, compact=False)}" if config.get('show_tooltips') else None
    
    st.metric(
        "Custos Totais",
        format_currency(total_costs, compact=config.get('compact_format', True)),
        delta_text,
        help=help_text
    )


def _render_profit_kpi(latest_data, previous_data, prev_period_label, config):
    """Render net profit KPI card"""
    net_profit = latest_data.get('net_profit', 0)
    delta = net_profit - previous_data.get('net_profit', 0) if previous_data is not None else None
    
    delta_text = None
    if delta is not None and config.get('comparison_format'):
        delta_text = f"{format_currency(delta)} {config['comparison_format'].format(period=prev_period_label)}"
    
    help_text = f"Valor exato: {format_currency(net_profit, compact=False)}" if config.get('show_tooltips') else None
    
    st.metric(
        "Lucro Líquido",
        format_currency(net_profit, compact=config.get('compact_format', True)),
        delta_text,
        help=help_text
    )


def _render_margin_kpi(latest_data, previous_data, prev_period_label, config):
    """Render profit margin KPI card"""
    # Calculate profit margin
    profit_margin = latest_data.get('profit_margin', 0)
    if profit_margin == 0 and latest_data.get('revenue', 0) > 0:
        profit_margin = (latest_data.get('net_profit', 0) / latest_data['revenue']) * 100
    
    # Calculate previous margin
    prev_margin = None
    if previous_data is not None:
        prev_margin = previous_data.get('profit_margin', 0)
        if prev_margin == 0 and previous_data.get('revenue', 0) > 0:
            prev_margin = (previous_data.get('net_profit', 0) / previous_data['revenue']) * 100
    
    delta = profit_margin - prev_margin if prev_margin is not None else None
    
    delta_text = None
    if delta is not None and config.get('comparison_format'):
        delta_text = f"{delta:+.2f}pp {config['comparison_format'].format(period=prev_period_label)}"
    
    st.metric(
        "Margem de Lucro",
        f"{profit_margin:.2f}%",
        delta_text
    )