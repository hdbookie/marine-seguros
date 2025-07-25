"""
Gráfico de Custos Fixos (Fixed Costs Chart)
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def create_custos_fixos_chart(
    display_df: pd.DataFrame,
    view_type: str = "Anual", 
    title: Optional[str] = None
) -> Optional[go.Figure]:
    """
    Create bar chart for fixed costs
    
    Args:
        display_df: DataFrame with fixed costs data
        view_type: Type of view (Anual, Mensal, etc.)
        title: Optional custom title
        
    Returns:
        Plotly figure or None if no data
    """
    if display_df.empty or 'fixed_costs' not in display_df.columns:
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
    
    # Create bar chart
    fig = px.bar(
        display_df,
        x=x_col,
        y='fixed_costs',
        title=title or f'Custos Fixos {view_type}',
        text='fixed_costs'
    )
    
    # Update traces
    fig.update_traces(
        texttemplate='R$ %{text:,.0f}',
        textposition='outside',
        marker_color='#FF6B6B',
        hovertemplate='<b>%{x}</b><br>' +
                      'Custos Fixos: R$ %{y:,.0f}<br>' +
                      '<extra></extra>'
    )
    
    # Update layout
    fig.update_layout(
        yaxis_title="Custos Fixos (R$)",
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
    avg_fixed_costs = display_df['fixed_costs'].mean()
    fig.add_hline(
        y=avg_fixed_costs,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Média: R$ {avg_fixed_costs:,.0f}",
        annotation_position="right"
    )
    
    return fig