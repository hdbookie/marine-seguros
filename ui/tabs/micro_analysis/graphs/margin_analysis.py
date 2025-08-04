"""
Margin Analysis Graph Module
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from visualizations.charts import create_margin_comparison_chart
from utils import format_currency
from ..config import GRAPH_CONFIGS


def render_margin_analysis(df, config=None):
    """
    Render margin analysis charts
    
    Args:
        df: DataFrame with financial data
        config: Optional configuration overrides
    """
    config = {**GRAPH_CONFIGS.get('margin_analysis', {}), **(config or {})}
    
    st.subheader("📊 Análise da Margem")
    
    # Margin comparison chart
    fig_margin = create_margin_comparison_chart(df)
    st.plotly_chart(fig_margin, use_container_width=True)
    
    # Margin breakdown analysis
    _render_margin_breakdown(df)
    
    # Margin trends
    if len(df) > 1:
        _render_margin_trends(df)


def _render_margin_breakdown(df):
    """Render detailed margin breakdown"""
    st.subheader("📈 Decomposição da Margem")
    
    # Get latest year data
    latest = df.iloc[-1]
    revenue = latest.get('revenue', 0)
    
    if revenue > 0:
        # Calculate margins
        gross_margin = ((revenue - latest.get('variable_costs', 0)) / revenue) * 100
        operating_margin = ((revenue - latest.get('variable_costs', 0) - latest.get('fixed_costs', 0)) / revenue) * 100
        net_margin = (latest.get('net_profit', 0) / revenue) * 100
        
        # Create waterfall chart
        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Margem Bruta", "Custos Fixos", "Outras Despesas", "Margem Líquida"],
            y=[gross_margin, -latest.get('fixed_costs', 0)/revenue*100, 
               -(revenue - latest.get('variable_costs', 0) - latest.get('fixed_costs', 0) - latest.get('net_profit', 0))/revenue*100,
               net_margin],
            text=[f"{gross_margin:.1f}%", 
                  f"-{latest.get('fixed_costs', 0)/revenue*100:.1f}%",
                  f"-{(revenue - latest.get('variable_costs', 0) - latest.get('fixed_costs', 0) - latest.get('net_profit', 0))/revenue*100:.1f}%",
                  f"{net_margin:.1f}%"],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        
        fig.update_layout(
            title=f"Decomposição da Margem - {latest.get('year', '')}",
            yaxis_title="Margem (%)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Margem Bruta", f"{gross_margin:.1f}%")
        with col2:
            st.metric("Margem Operacional", f"{operating_margin:.1f}%")
        with col3:
            st.metric("Margem Líquida", f"{net_margin:.1f}%")


def _render_margin_trends(df):
    """Render margin trend analysis"""
    st.subheader("📊 Tendência das Margens")
    
    # Calculate all margins
    margins_data = []
    for _, row in df.iterrows():
        revenue = row.get('revenue', 0)
        if revenue > 0:
            margins_data.append({
                'year': row.get('year', row.get('period', '')),
                'Margem Bruta': ((revenue - row.get('variable_costs', 0)) / revenue) * 100,
                'Margem Operacional': ((revenue - row.get('variable_costs', 0) - row.get('fixed_costs', 0)) / revenue) * 100,
                'Margem Líquida': (row.get('net_profit', 0) / revenue) * 100
            })
    
    if margins_data:
        margins_df = pd.DataFrame(margins_data)
        
        # Create line chart
        fig = go.Figure()
        
        for margin_type in ['Margem Bruta', 'Margem Operacional', 'Margem Líquida']:
            fig.add_trace(go.Scatter(
                x=margins_df['year'],
                y=margins_df[margin_type],
                mode='lines+markers',
                name=margin_type,
                line=dict(width=2),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="Evolução das Margens",
            xaxis_title="Período",
            yaxis_title="Margem (%)",
            yaxis=dict(tickformat='.1f', ticksuffix='%'),
            hovermode='x unified',
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show statistics
        st.markdown("#### Estatísticas do Período")
        stats_df = margins_df[['Margem Bruta', 'Margem Operacional', 'Margem Líquida']].describe()
        st.dataframe(
            stats_df.loc[['mean', 'std', 'min', 'max']].style.format("{:.1f}%"),
            use_container_width=True
        )