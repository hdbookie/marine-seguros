"""
Gráfico de Resultado (Profit/Loss Chart)
"""
import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def create_resultado_chart(
    display_df: pd.DataFrame,
    view_type: str = "Anual",
    title: Optional[str] = None
) -> Optional[go.Figure]:
    """
    Create bar chart showing net profit/loss
    
    Args:
        display_df: DataFrame with financial results
        view_type: Type of view (Anual, Mensal, etc.)
        title: Optional custom title
        
    Returns:
        Plotly figure or None if no data
    """
    if display_df.empty or 'net_profit' not in display_df.columns:
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
    pct_changes = display_df['net_profit'].pct_change() * 100
    pct_changes = pct_changes.fillna(0).round(2)  # First period has no change, round to 2 decimal places
    
    # Create figure with bars for net profit
    fig = go.Figure()
    
    # Add net profit bars
    fig.add_trace(go.Bar(
        x=display_df[x_col],
        y=display_df['net_profit'],
        name='Resultado',
        marker_color='#4CAF50',  # Green for profit
        text=[f'R$ {v:,.0f}' for v in display_df['net_profit']],
        textposition='outside',
        customdata=pct_changes.values.reshape(-1, 1),
        hovertemplate='<b>%{x}</b><br>' +
                      'Resultado: R$ %{y:,.0f}<br>' +
                      '<b>Variação: %{customdata[0]:+.2f}%</b><br>' +
                      '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=title or f'Resultado Anual (Lucro/Prejuízo)',
        yaxis_title="Resultado (R$)",
        xaxis_title=x_title,
        hovermode='x unified',
        xaxis=dict(
            tickangle=-45 if view_type == "Mensal" else 0,
            tickmode='linear',
            dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
        ),
        height=450 if view_type == "Mensal" else 400,
        margin=dict(t=50, b=100 if view_type == "Mensal" else 50)
    )
    
    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        line_width=1
    )
    
    return fig