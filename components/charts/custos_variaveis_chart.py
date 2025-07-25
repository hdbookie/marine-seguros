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
    Create stacked bar chart for variable costs with comparison lines
    
    Shows:
    - Stacked bars for variable cost components
    - Line for total variable costs
    - Line for fixed costs (comparison)
    - Line for revenue (overall context)
    
    Args:
        display_df: DataFrame with cost and revenue data
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
    elif view_type == "Anual":
        x_col = 'year'
    else:
        x_col = 'period'
    
    # Create figure
    fig = go.Figure()
    
    # Variable cost categories
    var_cost_categories = [
        ('commission', 'Comissão', '#FF6B6B'),
        ('card_tax', 'Taxa Cartão', '#4ECDC4'),
        ('shipping', 'Frete', '#45B7D1'),
        ('tax', 'Imposto', '#96CEB4'),
        ('financial_expense', 'Despesa Financeira', '#DDA0DD'),
        ('platform_fee', 'Taxa Plataforma', '#FFD93D')
    ]
    
    # Add traces for each category
    for col, name, color in var_cost_categories:
        if col in display_df.columns:
            values = display_df[col].fillna(0)
            if values.sum() > 0:  # Only add if there's data
                fig.add_trace(go.Bar(
                    name=name,
                    x=display_df[x_col],
                    y=values,
                    marker_color=color,
                    hovertemplate=f'<b>{name}</b><br>' +
                                  'Período: %{x}<br>' +
                                  'Valor: R$ %{y:,.0f}<br>' +
                                  '<extra></extra>'
                ))
    
    # Update layout
    fig.update_layout(
        title=title or f'Custos Variáveis vs Receita e Custos Fixos - {view_type}',
        barmode='stack',
        xaxis_title='Período' if view_type != 'Anual' else 'Ano',
        yaxis_title='Valor (R$)',
        hovermode='x unified',
        xaxis=dict(
            tickangle=-45 if view_type == "Mensal" else 0,
            tickmode='linear'
        ),
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    # Add total lines for both variable and fixed costs
    if 'variable_costs' in display_df.columns:
        fig.add_trace(go.Scatter(
            x=display_df[x_col],
            y=display_df['variable_costs'],
            mode='lines+markers',
            name='Total Custos Variáveis',
            line=dict(color='black', width=2, dash='dash'),
            marker=dict(size=6),
            yaxis='y2',
            hovertemplate='<b>Total Custos Variáveis</b><br>' +
                          'Período: %{x}<br>' +
                          'Valor: R$ %{y:,.0f}<br>' +
                          '<extra></extra>'
        ))
    
    # Add fixed costs line for comparison
    if 'fixed_costs' in display_df.columns:
        fig.add_trace(go.Scatter(
            x=display_df[x_col],
            y=display_df['fixed_costs'],
            mode='lines+markers',
            name='Custos Fixos',
            line=dict(color='red', width=3),
            marker=dict(size=8, symbol='square'),
            yaxis='y2',
            hovertemplate='<b>Custos Fixos</b><br>' +
                          'Período: %{x}<br>' +
                          'Valor: R$ %{y:,.0f}<br>' +
                          '<extra></extra>'
        ))
    
    # Add revenue line for complete picture
    if 'revenue' in display_df.columns:
        fig.add_trace(go.Scatter(
            x=display_df[x_col],
            y=display_df['revenue'],
            mode='lines+markers',
            name='Receita',
            line=dict(color='green', width=3),
            marker=dict(size=8, symbol='diamond'),
            yaxis='y2',
            hovertemplate='<b>Receita</b><br>' +
                          'Período: %{x}<br>' +
                          'Valor: R$ %{y:,.0f}<br>' +
                          '<extra></extra>'
        ))
    
    # Update layout with secondary y-axis
    fig.update_layout(
        yaxis2=dict(
            title='Totais (R$)',
            overlaying='y',
            side='right',
            showgrid=False
        )
    )
    
    return fig