"""
Gráfico de Receita (Revenue Chart)
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional, Tuple


def prepare_x_axis(df: pd.DataFrame, view_type: str) -> Tuple[str, str]:
    """Prepare x-axis column and title based on view type"""
    if view_type == "Mensal":
        return 'month_year', 'Mês'
    elif view_type == "Anual":
        return 'year', 'Ano'
    elif view_type in ["Trimestral", "Trimestre Personalizado", "Semestral"]:
        return 'period', 'Período'
    else:
        return 'year', 'Ano'


def create_receita_chart(
    display_df: pd.DataFrame, 
    view_type: str = "Anual",
    title: Optional[str] = None
) -> Optional[go.Figure]:
    """
    Create revenue line chart with annotations
    
    Args:
        display_df: DataFrame with revenue data
        view_type: Type of view (Anual, Mensal, Trimestral, etc.)
        title: Optional custom title
        
    Returns:
        Plotly figure or None if no data
    """
    if display_df.empty or 'revenue' not in display_df.columns:
        return None
    
    x_col, x_title = prepare_x_axis(display_df, view_type)
    
    # Create base line chart
    fig = px.line(
        display_df, 
        x=x_col, 
        y='revenue',
        title=title or f'Receita {view_type}',
        markers=True
    )
    
    # Add text annotations with smart positioning for monthly view
    if view_type == "Mensal" and len(display_df) > 20:
        # For crowded monthly view, show values on hover only
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>'
        )
    else:
        # For less crowded views, show selected values
        fig.add_trace(go.Scatter(
            x=display_df[x_col],
            y=display_df['revenue'],
            mode='text',
            text=[f'R$ {v:,.0f}' if i % 3 == 0 or v == display_df['revenue'].max() or v == display_df['revenue'].min() 
                  else '' for i, v in enumerate(display_df['revenue'])],
            textposition='top center',
            textfont=dict(size=10),
            showlegend=False
        ))
    
    # Update layout
    fig.update_layout(
        yaxis_title="Receita (R$)",
        xaxis_title=x_title,
        hovermode='x unified',
        xaxis=dict(
            tickangle=-45 if view_type == "Mensal" else 0,
            tickmode='linear',
            dtick=2 if view_type == "Mensal" and len(display_df) > 24 else None
        ),
        height=500 if view_type == "Mensal" else 400,
        margin=dict(t=50, b=100 if view_type == "Mensal" else 50)
    )
    
    return fig