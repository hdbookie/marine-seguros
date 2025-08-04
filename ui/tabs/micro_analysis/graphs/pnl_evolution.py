"""
P&L Evolution Graph Module
"""

import streamlit as st
from visualizations.charts import create_pnl_evolution_chart_custom, create_pnl_waterfall_chart
from ..config import GRAPH_CONFIGS, TIME_PERIOD_CONFIGS


def render_pnl_evolution(df, view_type="Anual", config=None):
    """
    Render P&L evolution charts
    
    Args:
        df: DataFrame with financial data
        view_type: Current time period view
        config: Optional configuration overrides
    """
    # Get configurations
    pnl_config = {**GRAPH_CONFIGS['pnl_evolution'], **(config or {})}
    time_config = TIME_PERIOD_CONFIGS.get(view_type, TIME_PERIOD_CONFIGS['Anual'])
    
    # Main evolution chart
    st.subheader(pnl_config['title'])
    
    # Create chart with appropriate x-axis
    fig_evolution = create_pnl_evolution_chart_custom(
        df, 
        x_col=time_config['x_column'],
        x_title=time_config['x_title']
    )
    
    # Apply custom configuration
    fig_evolution.update_layout(
        height=pnl_config['height'],
        showlegend=True,
        hovermode='x unified'
    )
    
    # Apply tick angle if specified
    if 'tick_angle' in time_config:
        fig_evolution.update_xaxes(tickangle=time_config['tick_angle'])
    
    st.plotly_chart(fig_evolution, use_container_width=True)
    
    # Waterfall chart only for annual view
    if view_type == "Anual" and len(df) > 0:
        st.subheader("Demonstrativo de Resultados (Cascata) - Último Ano")
        
        # Get the latest year data
        latest_data = df.iloc[-1]
        
        # Create waterfall chart
        fig_waterfall = create_pnl_waterfall_chart(df)
        fig_waterfall.update_layout(height=pnl_config.get('waterfall_height', 500))
        
        st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # Show summary metrics
    if st.checkbox("📊 Mostrar Resumo", key="pnl_summary"):
        _render_pnl_summary(df, view_type)


def _render_pnl_summary(df, view_type):
    """Render summary statistics for P&L"""
    st.markdown("#### Resumo do Período")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_revenue = df['revenue'].mean()
        st.metric("Receita Média", f"R$ {avg_revenue:,.0f}")
    
    with col2:
        avg_profit = df['net_profit'].mean()
        st.metric("Lucro Médio", f"R$ {avg_profit:,.0f}")
    
    with col3:
        avg_margin = df['profit_margin'].mean() if 'profit_margin' in df else 0
        st.metric("Margem Média", f"{avg_margin:.1f}%")