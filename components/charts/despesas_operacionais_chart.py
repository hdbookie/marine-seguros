"""
Gráfico de Despesas Operacionais (Operational Expenses Chart)
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def create_despesas_operacionais_chart(
    display_df: pd.DataFrame,
    view_type: str = "Anual",
    title: Optional[str] = None
) -> Optional[go.Figure]:
    """
    Create area chart for operational expenses
    
    Args:
        display_df: DataFrame with operational expenses data
        view_type: Type of view (Anual, Mensal, etc.)
        title: Optional custom title
        
    Returns:
        Plotly figure or None if no data
    """
    if display_df.empty or 'operational_costs' not in display_df.columns:
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
    
    # Create area chart
    fig = px.area(
        display_df,
        x=x_col,
        y='operational_costs',
        title=title or f'Despesas Operacionais {view_type}',
        color_discrete_sequence=['#FF9800']
    )
    
    # Add markers and text
    fig.update_traces(
        mode='lines+markers+text',
        text=[f'R$ {v:,.0f}' for v in display_df['operational_costs']],
        textposition='top center',
        textfont=dict(size=10),
        hovertemplate='<b>%{x}</b><br>' +
                      'Despesas Operacionais: R$ %{y:,.0f}<br>' +
                      '<extra></extra>'
    )
    
    # Update layout
    fig.update_layout(
        yaxis_title="Despesas Operacionais (R$)",
        xaxis_title=x_title,
        hovermode='x unified',
        xaxis=dict(
            tickangle=-45 if view_type == "Mensal" else 0,
            tickmode='linear',
            dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
        ),
        height=400,
        margin=dict(t=50, b=100 if view_type == "Mensal" else 50)
    )
    
    # Add average line
    avg_operational = display_df['operational_costs'].mean()
    fig.add_hline(
        y=avg_operational,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Média: R$ {avg_operational:,.0f}",
        annotation_position="right"
    )
    
    # Add percentage of revenue if available
    if 'revenue' in display_df.columns:
        display_df['op_cost_percentage'] = (
            display_df['operational_costs'] / display_df['revenue'] * 100
        ).fillna(0)
        
        # Add secondary trace for percentage
        fig.add_trace(go.Scatter(
            x=display_df[x_col],
            y=display_df['op_cost_percentage'],
            mode='lines+markers',
            name='% da Receita',
            line=dict(color='darkred', width=2, dash='dot'),
            marker=dict(size=6),
            yaxis='y2',
            hovertemplate='<b>% da Receita</b><br>' +
                          'Período: %{x}<br>' +
                          'Percentual: %{y:.1f}%<br>' +
                          '<extra></extra>'
        ))
        
        # Add secondary y-axis
        fig.update_layout(
            yaxis2=dict(
                title='% da Receita',
                overlaying='y',
                side='right',
                showgrid=False
            )
        )
    
    return fig