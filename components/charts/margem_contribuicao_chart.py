"""
Gráfico de Margem de Contribuição (Contribution Margin Chart)
"""
import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def create_margem_contribuicao_chart(
    display_df: pd.DataFrame,
    view_type: str = "Anual",
    title: Optional[str] = None
) -> Optional[go.Figure]:
    """
    Create bar chart for contribution margin (monetary values)
    
    Args:
        display_df: DataFrame with margin data
        view_type: Type of view (Anual, Mensal, etc.)
        title: Optional custom title
        
    Returns:
        Plotly figure or None if no data
    """
    if display_df.empty:
        return None
    
    # Calculate contribution margin if not present
    if 'contribution_margin' not in display_df.columns:
        if 'revenue' in display_df.columns and 'variable_costs' in display_df.columns:
            display_df['contribution_margin'] = (
                display_df['revenue'] - display_df['variable_costs']
            )
        else:
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
    pct_changes = display_df['contribution_margin'].pct_change() * 100
    pct_changes = pct_changes.fillna(0).round(2)  # First period has no change, round to 2 decimal places
    
    # Create figure with bars for contribution margin
    fig = go.Figure()
    
    # Add contribution margin bars
    fig.add_trace(go.Bar(
        x=display_df[x_col],
        y=display_df['contribution_margin'],
        name='Margem de Contribuição',
        marker_color='#9c27b0',  # Purple color for contribution margin
        text=[f'R$ {v:,.0f}' if i % 2 == 0 or view_type == "Anual" else '' for i, v in enumerate(display_df['contribution_margin'])] if view_type != "Mensal" or len(display_df) <= 20 else None,
        textposition='outside',
        customdata=pct_changes.values.reshape(-1, 1),
        hovertemplate='<b>%{x}</b><br>' +
                      'Margem de Contribuição: R$ %{y:,.0f}<br>' +
                      '<b>Variação: %{customdata[0]:+.2f}%</b><br>' +
                      '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=title or f'Margem de Contribuição {view_type}',
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