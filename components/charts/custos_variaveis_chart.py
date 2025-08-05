"""
Gráfico de Custos Variáveis (Variable Costs Chart)
"""
import plotly.graph_objects as go
import pandas as pd
from typing import Optional, List


def create_custos_variaveis_chart(
    display_df: pd.DataFrame,
    view_type: str = "Anual",
    title: Optional[str] = None
) -> Optional[go.Figure]:
    """
    Create bar chart for variable costs with revenue line
    
    Shows:
    - Orange bars for total variable costs
    - Blue line for revenue (comparison)
    
    Args:
        display_df: DataFrame with cost and revenue data
        view_type: Type of view (Anual, Mensal, etc.)
        title: Optional custom title
        
    Returns:
        Plotly figure or None if no data
    """
    if display_df.empty or 'variable_costs' not in display_df.columns:
        return None
    
    # Determine x-axis based on view type
    if view_type == "Mensal":
        x_col = 'month_year'
        x_title = 'Mês'
    elif view_type == "Anual":
        x_col = 'year'
        x_title = 'Ano'
    else:
        x_col = 'period'
        x_title = 'Período'
    
    # Calculate period-over-period percentage changes
    pct_changes = display_df['variable_costs'].pct_change() * 100
    pct_changes = pct_changes.fillna(0).round(2)  # First period has no change, round to 2 decimal places
    
    # Create figure
    fig = go.Figure()
    
    # Add revenue line first so it appears first in hover
    if 'revenue' in display_df.columns:
        pct_changes_revenue = display_df['revenue'].pct_change() * 100
        pct_changes_revenue = pct_changes_revenue.fillna(0).round(2)
        
        fig.add_trace(go.Scatter(
            x=display_df[x_col],
            y=display_df['revenue'],
            name='Receita',
            mode='lines+markers',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            customdata=pct_changes_revenue.values.reshape(-1, 1),
            hovertemplate='<b>%{x}</b><br>' +
                          'Receita: R$ %{y:,.0f}<br>' +
                          '<b>Variação: %{customdata[0]:+.2f}%</b><br>' +
                          '<extra></extra>'
        ))
    
    # Add variable costs bars second
    fig.add_trace(go.Bar(
        x=display_df[x_col],
        y=display_df['variable_costs'],
        name='Custos Variáveis',
        marker_color='#ff7f0e',
        text=[f'R$ {v:,.0f}' if i % 2 == 0 or view_type == "Anual" else '' for i, v in enumerate(display_df['variable_costs'])] if view_type != "Mensal" or len(display_df) <= 20 else None,
        textposition='outside',
        customdata=pct_changes.values.reshape(-1, 1),
        hovertemplate='<b>%{x}</b><br>' +
                      'Custos Variáveis: R$ %{y:,.0f}<br>' +
                      '<b>Variação: %{customdata[0]:+.2f}%</b><br>' +
                      '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=title or f'Custos Variáveis vs Receita {view_type}',
        yaxis_title="Valores (R$)",
        xaxis_title=x_title,
        hovermode='x unified',
        xaxis=dict(
            tickangle=-45 if view_type == "Mensal" else 0,
            tickmode='linear',
            dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
        ),
        height=450 if view_type == "Mensal" else 400,
        margin=dict(t=50, b=100 if view_type == "Mensal" else 50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig