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
    Create combination chart showing revenue, costs, and profit
    
    Args:
        display_df: DataFrame with financial results
        view_type: Type of view (Anual, Mensal, etc.)
        title: Optional custom title
        
    Returns:
        Plotly figure or None if no data
    """
    if display_df.empty:
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
    
    # Create figure
    fig = go.Figure()
    
    # Add revenue bars
    if 'revenue' in display_df.columns:
        fig.add_trace(go.Bar(
            name='Receita',
            x=display_df[x_col],
            y=display_df['revenue'],
            marker_color='#2E7D32',
            yaxis='y',
            offsetgroup=1,
            hovertemplate='<b>Receita</b><br>' +
                          'Período: %{x}<br>' +
                          'Valor: R$ %{y:,.0f}<br>' +
                          '<extra></extra>'
        ))
    
    # Add total costs bars
    if 'total_costs' in display_df.columns:
        fig.add_trace(go.Bar(
            name='Custos Totais',
            x=display_df[x_col],
            y=display_df['total_costs'],
            marker_color='#D32F2F',
            yaxis='y',
            offsetgroup=2,
            hovertemplate='<b>Custos Totais</b><br>' +
                          'Período: %{x}<br>' +
                          'Valor: R$ %{y:,.0f}<br>' +
                          '<extra></extra>'
        ))
    
    # Add profit line
    if 'net_profit' in display_df.columns:
        fig.add_trace(go.Scatter(
            name='Resultado',
            x=display_df[x_col],
            y=display_df['net_profit'],
            mode='lines+markers+text',
            line=dict(color='#1976D2', width=3),
            marker=dict(size=10),
            text=[f'R$ {v:,.0f}' for v in display_df['net_profit']],
            textposition='top center',
            textfont=dict(size=10, color='#1976D2', weight='bold'),
            yaxis='y2',
            hovertemplate='<b>Resultado</b><br>' +
                          'Período: %{x}<br>' +
                          'Valor: R$ %{y:,.0f}<br>' +
                          '<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=title or f'Resultado Financeiro {view_type}',
        xaxis_title=x_title,
        hovermode='x unified',
        barmode='group',
        xaxis=dict(
            tickangle=-45 if view_type == "Mensal" else 0,
            tickmode='linear',
            dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
        ),
        yaxis=dict(
            title='Receita e Custos (R$)',
            side='left'
        ),
        yaxis2=dict(
            title='Resultado (R$)',
            overlaying='y',
            side='right',
            showgrid=False,
            zeroline=True,
            zerolinecolor='gray',
            zerolinewidth=2
        ),
        height=500,
        margin=dict(t=50, b=100 if view_type == "Mensal" else 50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add zero line for profit
    fig.add_hline(y=0, line_dash="dash", line_color="gray", yref='y2')
    
    return fig