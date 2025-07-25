"""
Indicadores KPI (Key Performance Indicators)
"""
import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any


def format_currency(value: float) -> str:
    """Format value as Brazilian currency"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.1f}%"


def create_kpi_indicators(
    current_data: pd.DataFrame,
    previous_data: Optional[pd.DataFrame] = None,
    period_label: str = "Período"
) -> None:
    """
    Create KPI indicator cards with metrics and comparisons
    
    Args:
        current_data: Current period data
        previous_data: Previous period data for comparison
        period_label: Label for the period (e.g., "2024", "Jan/2024")
    """
    # Calculate current metrics
    metrics = calculate_metrics(current_data)
    
    # Calculate previous metrics if available
    prev_metrics = calculate_metrics(previous_data) if previous_data is not None else None
    
    # Create columns for KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta = None
        delta_color = "normal"
        if prev_metrics:
            delta = ((metrics['revenue'] - prev_metrics['revenue']) / prev_metrics['revenue'] * 100)
            delta_color = "normal" if delta >= 0 else "inverse"
        
        st.metric(
            label=f"📈 Receita Total - {period_label}",
            value=format_currency(metrics['revenue']),
            delta=f"{delta:.1f}%" if delta is not None else None,
            delta_color=delta_color
        )
    
    with col2:
        delta = None
        delta_color = "normal"
        if prev_metrics:
            delta = ((metrics['net_profit'] - prev_metrics['net_profit']) / abs(prev_metrics['net_profit']) * 100) if prev_metrics['net_profit'] != 0 else 0
            delta_color = "normal" if delta >= 0 else "inverse"
        
        st.metric(
            label=f"💰 Resultado Líquido - {period_label}",
            value=format_currency(metrics['net_profit']),
            delta=f"{delta:.1f}%" if delta is not None else None,
            delta_color=delta_color
        )
    
    with col3:
        delta = None
        delta_color = "normal"
        if prev_metrics:
            delta = metrics['profit_margin'] - prev_metrics['profit_margin']
            delta_color = "normal" if delta >= 0 else "inverse"
        
        st.metric(
            label=f"📊 Margem de Lucro - {period_label}",
            value=format_percentage(metrics['profit_margin']),
            delta=f"{delta:.1f}pp" if delta is not None else None,
            delta_color=delta_color
        )
    
    with col4:
        delta = None
        delta_color = "normal"
        if prev_metrics:
            delta = metrics['contribution_margin'] - prev_metrics['contribution_margin']
            delta_color = "normal" if delta >= 0 else "inverse"
        
        st.metric(
            label=f"📉 Margem Contribuição - {period_label}",
            value=format_percentage(metrics['contribution_margin']),
            delta=f"{delta:.1f}pp" if delta is not None else None,
            delta_color=delta_color
        )
    
    # Second row of metrics
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        delta = None
        delta_color = "inverse"  # For costs, negative is good
        if prev_metrics:
            delta = ((metrics['total_costs'] - prev_metrics['total_costs']) / prev_metrics['total_costs'] * 100)
            delta_color = "inverse"
        
        st.metric(
            label=f"💸 Custos Totais - {period_label}",
            value=format_currency(metrics['total_costs']),
            delta=f"{delta:.1f}%" if delta is not None else None,
            delta_color=delta_color
        )
    
    with col6:
        st.metric(
            label=f"🔧 Custos Fixos - {period_label}",
            value=format_currency(metrics['fixed_costs']),
            help="Custos que não variam com o volume de vendas"
        )
    
    with col7:
        st.metric(
            label=f"📦 Custos Variáveis - {period_label}",
            value=format_currency(metrics['variable_costs']),
            help="Custos que variam proporcionalmente às vendas"
        )
    
    with col8:
        cost_ratio = (metrics['variable_costs'] / metrics['revenue'] * 100) if metrics['revenue'] > 0 else 0
        st.metric(
            label=f"⚖️ Custos Var/Receita - {period_label}",
            value=format_percentage(cost_ratio),
            help="Percentual dos custos variáveis sobre a receita"
        )


def calculate_metrics(data: pd.DataFrame) -> Dict[str, float]:
    """Calculate financial metrics from dataframe"""
    if data is None or data.empty:
        return {
            'revenue': 0,
            'net_profit': 0,
            'profit_margin': 0,
            'contribution_margin': 0,
            'total_costs': 0,
            'fixed_costs': 0,
            'variable_costs': 0,
            'operational_costs': 0
        }
    
    # Sum all values if multiple rows
    revenue = data['revenue'].sum() if 'revenue' in data.columns else 0
    net_profit = data['net_profit'].sum() if 'net_profit' in data.columns else 0
    total_costs = data['total_costs'].sum() if 'total_costs' in data.columns else 0
    fixed_costs = data['fixed_costs'].sum() if 'fixed_costs' in data.columns else 0
    variable_costs = data['variable_costs'].sum() if 'variable_costs' in data.columns else 0
    operational_costs = data['operational_costs'].sum() if 'operational_costs' in data.columns else 0
    
    # Calculate percentages
    profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0
    contribution_margin = ((revenue - variable_costs) / revenue * 100) if revenue > 0 else 0
    
    return {
        'revenue': revenue,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        'contribution_margin': contribution_margin,
        'total_costs': total_costs,
        'fixed_costs': fixed_costs,
        'variable_costs': variable_costs,
        'operational_costs': operational_costs
    }