"""
Gráfico de Margem de Contribuição (Contribution Margin Chart)
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def create_margem_contribuicao_chart(
    display_df: pd.DataFrame,
    view_type: str = "Anual",
    title: Optional[str] = None
) -> Optional[go.Figure]:
    """
    Create bar chart for contribution margin percentage
    
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
                (display_df['revenue'] - display_df['variable_costs']) / 
                display_df['revenue'] * 100
            ).fillna(0)
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
    
    # Create bar chart
    fig = px.bar(
        display_df,
        x=x_col,
        y='contribution_margin',
        title=title or f'Margem de Contribuição {view_type}',
        text='contribution_margin',
        color='contribution_margin',
        color_continuous_scale=['#D32F2F', '#FFC107', '#4CAF50'],
        color_continuous_midpoint=50
    )
    
    # Update traces
    fig.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                      'Margem de Contribuição: %{y:.1f}%<br>' +
                      '<extra></extra>'
    )
    
    # Update layout
    fig.update_layout(
        yaxis_title="Margem de Contribuição (%)",
        xaxis_title=x_title,
        hovermode='x unified',
        xaxis=dict(
            tickangle=-45 if view_type == "Mensal" else 0,
            tickmode='linear',
            dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
        ),
        height=400,
        margin=dict(t=50, b=100 if view_type == "Mensal" else 50),
        coloraxis_showscale=False
    )
    
    # Add reference lines
    fig.add_hline(
        y=50,
        line_dash="dash",
        line_color="gray",
        annotation_text="Meta: 50%",
        annotation_position="right"
    )
    
    # Add average line
    avg_margin = display_df['contribution_margin'].mean()
    fig.add_hline(
        y=avg_margin,
        line_dash="dot",
        line_color="blue",
        annotation_text=f"Média: {avg_margin:.1f}%",
        annotation_position="left"
    )
    
    return fig