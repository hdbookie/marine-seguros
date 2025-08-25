"""Chart creation functions for the dashboard"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.formatters import format_currency, format_percentage
from typing import Dict, List, Optional
import numpy as np


def create_revenue_cost_chart(df, title="Evolução de Receitas vs Custos"):
    """Create a revenue vs costs comparison chart"""
    fig = go.Figure()
    
    # Add Revenue bars
    fig.add_trace(go.Bar(
        name='Receitas',
        x=df['year'],
        y=df['revenue'],
        text=[format_currency(v) for v in df['revenue']],
        textposition='outside',
        marker_color='rgba(50, 171, 96, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Receita:</b> %{text}<extra></extra>'
    ))
    
    # Add Costs bars
    fig.add_trace(go.Bar(
        name='Custos',
        x=df['year'],
        y=df['variable_costs'] + df['fixed_costs'] + df['operational_costs'],
        text=[format_currency(v) for v in df['variable_costs'] + df['fixed_costs'] + df['operational_costs']],
        textposition='outside',
        marker_color='rgba(219, 64, 82, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Custos:</b> %{text}<extra></extra>'
    ))
    
    # Add Profit line
    fig.add_trace(go.Scatter(
        name='Lucro',
        x=df['year'],
        y=df['net_profit'],
        text=[format_currency(v) for v in df['net_profit']],
        mode='lines+markers+text',
        textposition='top center',
        line=dict(color='rgb(55, 83, 109)', width=3),
        marker=dict(size=10),
        yaxis='y2',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Lucro:</b> %{text}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis=dict(
            title='Valores (R$)',
            titlefont=dict(color='rgb(55, 83, 109)'),
            tickfont=dict(color='rgb(55, 83, 109)'),
            side='left'
        ),
        yaxis2=dict(
            title='Lucro (R$)',
            titlefont=dict(color='rgb(55, 83, 109)'),
            tickfont=dict(color='rgb(55, 83, 109)'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        barmode='group',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_margin_evolution_chart(df, title="Evolução da Margem de Lucro"):
    """Create a profit margin evolution chart"""
    fig = go.Figure()
    
    # Add margin line
    fig.add_trace(go.Scatter(
        name='Margem de Lucro',
        x=df['year'],
        y=df['profit_margin'],
        text=[f"{v:.1f}%" for v in df['profit_margin']],
        mode='lines+markers+text',
        textposition='top center',
        line=dict(color='rgb(55, 83, 109)', width=3),
        marker=dict(size=10),
        fill='tonexty',
        fillcolor='rgba(55, 83, 109, 0.1)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Margem:</b> %{text}<extra></extra>'
    ))
    
    # Add reference line at 0%
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break Even")
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis_title='Margem de Lucro (%)',
        hovermode='x',
        template='plotly_white',
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_cost_breakdown_chart(data, title="Composição de Custos"):
    """Create a cost breakdown pie/donut chart"""
    # Prepare data
    categories = []
    values = []
    
    for category, value in data.items():
        if value > 0:
            categories.append(category)
            values.append(value)
    
    # Create donut chart
    fig = go.Figure(data=[go.Pie(
        labels=categories,
        values=values,
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
        marker=dict(
            colors=px.colors.qualitative.Set3
        ),
        hovertemplate='<b>%{label}</b><br>Valor: %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
    )])
    
    # Update layout
    fig.update_layout(
        title=title,
        showlegend=True,
        margin=dict(l=20, r=20, t=80, b=20)
    )
    
    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_monthly_trend_chart(monthly_data, title="Tendência Mensal"):
    """Create a monthly trend chart with moving average"""
    fig = go.Figure()
    
    # Main line
    fig.add_trace(go.Scatter(
        name='Valor Mensal',
        x=monthly_data.index,
        y=monthly_data['value'],
        mode='lines+markers',
        line=dict(color='rgb(55, 83, 109)', width=2),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>Valor: R$ %{y:,.2f}<extra></extra>'
    ))
    
    # Add 3-month moving average
    if len(monthly_data) >= 3:
        ma3 = monthly_data['value'].rolling(window=3).mean()
        fig.add_trace(go.Scatter(
            name='Média Móvel (3M)',
            x=monthly_data.index,
            y=ma3,
            mode='lines',
            line=dict(color='rgba(255, 99, 71, 0.7)', width=2, dash='dash'),
            hovertemplate='<b>%{x}</b><br>MM3: R$ %{y:,.2f}<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Período',
        yaxis_title='Valor (R$)',
        hovermode='x unified',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99)
    )
    
    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_pareto_chart(items, title="Análise de Pareto"):
    """Create a Pareto chart (80/20 analysis)"""
    # Sort items by value
    sorted_items = sorted(items, key=lambda x: x['annual'], reverse=True)[:20]
    
    # Calculate cumulative percentage
    total = sum(item['annual'] for item in sorted_items)
    cumulative_pct = []
    cumulative_sum = 0
    
    for item in sorted_items:
        cumulative_sum += item['annual']
        cumulative_pct.append((cumulative_sum / total) * 100)
    
    # Create figure
    fig = go.Figure()
    
    # Bar chart
    fig.add_trace(go.Bar(
        name='Valor',
        x=list(range(1, len(sorted_items) + 1)),
        y=[item['annual'] for item in sorted_items],
        text=[item['label'][:30] + '...' if len(item['label']) > 30 else item['label'] 
              for item in sorted_items],
        textposition='none',
        marker_color='lightblue',
        yaxis='y',
        hovertemplate='<b>%{text}</b><br>Valor: R$ %{y:,.2f}<extra></extra>'
    ))
    
    # Cumulative line
    fig.add_trace(go.Scatter(
        name='% Acumulado',
        x=list(range(1, len(sorted_items) + 1)),
        y=cumulative_pct,
        mode='lines+markers',
        line=dict(color='red', width=2),
        marker=dict(size=6),
        yaxis='y2',
        hovertemplate='%{y:.1f}% acumulado<extra></extra>'
    ))
    
    # Add 80% reference line
    fig.add_hline(y=80, line_dash="dash", line_color="green", 
                  annotation_text="80%", yref='y2')
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis=dict(title="Ranking", tickmode='linear'),
        yaxis=dict(title="Valor (R$)", side='left'),
        yaxis2=dict(
            title="Percentual Acumulado",
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        hovermode='x unified',
        template='plotly_white',
        showlegend=True,
        margin=dict(b=100)
    )
    
    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_treemap(data, title="Visualização Hierárquica"):
    """Create a treemap visualization"""
    fig = px.treemap(
        data,
        path=['category', 'item'],
        values='value',
        title=title,
        color='value',
        color_continuous_scale='Blues',
        hover_data={'value': ':,.2f'}
    )
    
    fig.update_traces(
        textposition="middle center",
        textfont_size=12,
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>%{percentParent} do total<extra></extra>'
    )
    
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_sankey_diagram(source, target, value, title="Fluxo de Despesas"):
    """Create a Sankey diagram for expense flow"""
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=source + target,
            color="lightblue"
        ),
        link=dict(
            source=[source.index(s) for s in source],
            target=[len(source) + target.index(t) for t in target],
            value=value,
            color="rgba(0,0,255,0.2)"
        )
    )])
    
    fig.update_layout(
        title=title,
        font_size=10,
        height=600
    )
    
    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig

def create_cost_structure_chart(df, title="Estrutura de Custos vs. Receita"):
    """Create a stacked bar chart showing cost structure against revenue"""
    fig = go.Figure()

    # Add Fixed Costs
    fig.add_trace(go.Bar(
        name='Custos Fixos',
        x=df['year'],
        y=df['fixed_costs'],
        text=[format_currency(v) for v in df['fixed_costs']],
        textposition='auto',
        marker_color='rgba(255, 159, 64, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Custos Fixos:</b> %{text}<extra></extra>'
    ))

    # Add Variable Costs
    fig.add_trace(go.Bar(
        name='Custos Variáveis',
        x=df['year'],
        y=df['variable_costs'],
        text=[format_currency(v) for v in df['variable_costs']],
        textposition='auto',
        marker_color='rgba(255, 99, 132, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Custos Variáveis:</b> %{text}<extra></extra>'
    ))

    # Add Operational Costs
    fig.add_trace(go.Bar(
        name='Outros Custos',
        x=df['year'],
        y=df['operational_costs'],
        text=[format_currency(v) for v in df['operational_costs']],
        textposition='auto',
        marker_color='rgba(153, 102, 255, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Outros Custos:</b> %{text}<extra></extra>'
    ))

    # Add Revenue as a line on top
    fig.add_trace(go.Scatter(
        name='Receita Total',
        x=df['year'],
        y=df['revenue'],
        mode='lines+markers+text',
        text=[format_currency(v) for v in df['revenue']],
        textposition='top center',
        line=dict(color='rgba(54, 162, 235, 1)', width=3),
        marker=dict(size=10),
        hovertemplate='<b>Ano:</b> %{x}<br><b>Receita:</b> %{text}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis_title='Valores (R$)',
        barmode='stack',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_fixed_costs_evolution_chart(df, title="Evolução dos Custos Fixos"):
    """Create a line chart showing the evolution of fixed costs over time"""
    fig = go.Figure()
    
    # Determine x-axis based on data structure
    if 'period' in df.columns:
        x_col = 'period'
        x_title = 'Período'
    else:
        x_col = 'year'
        x_title = 'Ano'
    
    # Add fixed costs line
    fig.add_trace(go.Scatter(
        name='Custos Fixos',
        x=df[x_col],
        y=df['fixed_costs'],
        mode='lines+markers+text',
        text=[format_currency(v) for v in df['fixed_costs']],
        textposition='top center',
        line=dict(color='#2E86C1', width=3),
        marker=dict(size=10, color='#2E86C1'),
        hovertemplate=f'<b>{x_title}:</b> %{{x}}<br><b>Custos Fixos:</b> %{{text}}<extra></extra>'
    ))
    
    # Add average line
    avg_fixed_costs = df['fixed_costs'].mean()
    fig.add_hline(
        y=avg_fixed_costs,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Média: {format_currency(avg_fixed_costs)}",
        annotation_position="right"
    )
    
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title='Custos Fixos (R$)',
        template='plotly_white',
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='x unified'
    )
    
    # Format y-axis
    fig.update_yaxis(tickformat=',.')
    
    return fig


def create_detailed_cost_structure_chart(df, title="Estrutura de Custos Detalhada"):
    """Create a detailed stacked bar chart showing cost structure against revenue"""
    fig = go.Figure()

    cost_categories = ['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']
    colors = px.colors.qualitative.Plotly

    for i, cost_type in enumerate(cost_categories):
        fig.add_trace(go.Bar(
            name=cost_type.replace('_', ' ').title(),
            x=df['year'],
            y=df[cost_type],
            text=[format_currency(v) for v in df[cost_type]],
            textposition='auto',
            marker_color=colors[i % len(colors)],
            hovertemplate=f"<b>Ano:</b> %{{x}}<br><b>{cost_type.replace('_', ' ').title()}:</b> %{{text}}<extra></extra>"
        ))

    # Add Revenue as a line on top
    fig.add_trace(go.Scatter(
        name='Receita Total',
        x=df['year'],
        y=df['revenue'],
        mode='lines+markers+text',
        text=[format_currency(v) for v in df['revenue']],
        textposition='top center',
        line=dict(color='rgba(54, 162, 235, 1)', width=3),
        marker=dict(size=10),
        hovertemplate='<b>Ano:</b> %{x}<br><b>Receita:</b> %{text}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis_title='Valores (R$)',
        barmode='stack',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig

def create_pnl_waterfall_chart(df, title="Demonstrativo de Resultados (Cascata)"):
    """Create a P&L waterfall chart"""
    
    last_year_data = df.iloc[-1]
    all_cost_categories = ['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']
    
    # Filter to only include categories that exist in the data
    cost_categories = [cat for cat in all_cost_categories if cat in df.columns and pd.notna(last_year_data.get(cat, 0))]
    
    measures = ["absolute"] * (len(cost_categories) + 2)
    x_labels = ["Receita"] + [cat.replace('_', ' ').title() for cat in cost_categories] + ["Lucro Líquido"]
    y_values = [last_year_data['revenue']] + [-last_year_data.get(cat, 0) for cat in cost_categories] + [last_year_data.get('net_profit', 0)]
    
    fig = go.Figure(go.Waterfall(
        name = "2025",
        orientation = "v",
        measure = measures,
        x = x_labels,
        textposition = "outside",
        text = [format_currency(v) for v in y_values],
        y = y_values,
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))

    fig.update_layout(
            title = title,
            showlegend = True
    )

    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig

def create_pnl_evolution_chart(df, title="Evolução do Demonstrativo de Resultados"):
    """Create a P&L evolution line chart"""
    fig = go.Figure()

    # Add Revenue line
    fig.add_trace(go.Scatter(
        name='Receita',
        x=df['year'],
        y=df['revenue'],
        mode='lines+markers',
        line=dict(color='green', width=2),
        hovertemplate='<b>Ano:</b> %{x}<br><b>Receita:</b> %{y:,.2f}<extra></extra>'
    ))

    # Add Total Costs line
    # Ensure all cost columns exist and are numeric
    cost_columns = ['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 
                    'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']
    
    # Create a clean dataframe for cost calculation
    cost_df = pd.DataFrame()
    for col in cost_columns:
        if col in df.columns:
            # Convert any remaining dict values to numbers
            cost_df[col] = df[col].apply(lambda x: x.get('annual', 0) if isinstance(x, dict) else (x if pd.notna(x) else 0))
        else:
            cost_df[col] = 0
    
    df['total_costs'] = cost_df.sum(axis=1)
    fig.add_trace(go.Scatter(
        name='Custos Totais',
        x=df['year'],
        y=df['total_costs'],
        mode='lines+markers',
        line=dict(color='red', width=2),
        hovertemplate='<b>Ano:</b> %{x}<br><b>Custos Totais:</b> %{y:,.2f}<extra></extra>'
    ))

    # Add Net Profit line
    fig.add_trace(go.Scatter(
        name='Lucro Líquido',
        x=df['year'],
        y=df['net_profit'],
        mode='lines+markers',
        line=dict(color='blue', width=2),
        hovertemplate='<b>Ano:</b> %{x}<br><b>Lucro Líquido:</b> %{y:,.2f}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis_title='Valores (R$)',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig

def create_cost_as_percentage_of_revenue_chart(df, title="Custos como % da Receita"):
    """Create a chart showing costs as a percentage of revenue"""
    fig = go.Figure()

    df['total_costs'] = df[['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']].sum(axis=1)
    df['cost_as_percentage_of_revenue'] = (df['total_costs'] / df['revenue']) * 100

    fig.add_trace(go.Scatter(
        name='Custo como % da Receita',
        x=df['year'],
        y=df['cost_as_percentage_of_revenue'],
        mode='lines+markers',
        line=dict(color='orange', width=2),
        hovertemplate='<b>Ano:</b> %{x}<br><b>Custo:</b> %{y:.2f}%<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis_title='Percentual (%)',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig

def create_margin_comparison_chart(df, title="Comparativo de Margens"):
    """Create a chart comparing profit margin and contribution margin"""
    fig = go.Figure()

    # Add Profit Margin line
    fig.add_trace(go.Scatter(
        name='Margem de Lucro',
        x=df['year'],
        y=df['profit_margin'],
        mode='lines+markers',
        line=dict(color='purple', width=2),
        hovertemplate='<b>Ano:</b> %{x}<br><b>Margem de Lucro:</b> %{y:.2f}%<extra></extra>'
    ))

    # Add Contribution Margin line if available
    if 'contribution_margin' in df.columns:
        df['contribution_margin_percentage'] = (df['contribution_margin'] / df['revenue']) * 100
        fig.add_trace(go.Scatter(
            name='Margem de Contribuição',
            x=df['year'],
            y=df['contribution_margin_percentage'],
            mode='lines+markers',
            line=dict(color='teal', width=2),
            hovertemplate='<b>Ano:</b> %{x}<br><b>Margem de Contribuição:</b> %{y:.2f}%<extra></extra>'
        ))
    else:
        # Calculate contribution margin as revenue - variable costs
        df['contribution_margin'] = df['revenue'] - df.get('variable_costs', 0)
        df['contribution_margin_percentage'] = (df['contribution_margin'] / df['revenue']) * 100
        fig.add_trace(go.Scatter(
            name='Margem de Contribuição',
            x=df['year'],
            y=df['contribution_margin_percentage'],
            mode='lines+markers',
            line=dict(color='teal', width=2),
            hovertemplate='<b>Ano:</b> %{x}<br><b>Margem de Contribuição:</b> %{y:.2f}%<extra></extra>'
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis_title='Percentual (%)',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig


def create_group_evolution_chart(group_df: pd.DataFrame, title: str = "Evolução dos Grupos de Despesas") -> go.Figure:
    """
    Create a line chart showing evolution of expense groups over time
    
    Args:
        group_df: DataFrame with columns ['Grupo', 'Ano', 'Valor', 'Categoria']
        title: Chart title
    """
    fig = px.line(
        group_df,
        x='Ano',
        y='Valor',
        color='Grupo',
        markers=True,
        title=title,
        labels={'Valor': 'Valor (R$)', 'Ano': 'Ano'},
        hover_data={'Categoria': True, 'Itens': True}
    )
    
    # Customize layout
    fig.update_traces(
        mode='lines+markers',
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Ano: %{x}<br>' +
                     'Valor: R$ %{y:,.2f}<br>' +
                     'Categoria: %{customdata[0]}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        hovermode='x unified',
        xaxis=dict(title='Ano', tickmode='linear'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150),
        height=500
    )
    
    return fig


def create_group_comparison_chart(group_df: pd.DataFrame, revenue_df: pd.DataFrame, 
                                 title: str = "Grupos de Despesas como % da Receita") -> go.Figure:
    """
    Create a stacked bar chart showing expense groups as percentage of revenue
    
    Args:
        group_df: DataFrame with expense groups
        revenue_df: DataFrame with revenue data by year
    """
    # Merge with revenue data
    merged_df = group_df.merge(
        revenue_df[['year', 'revenue']], 
        left_on='Ano', 
        right_on='year', 
        how='left'
    )
    
    # Calculate percentage
    merged_df['Percentual'] = (merged_df['Valor'] / merged_df['revenue']) * 100
    
    # Pivot for stacked bars
    pivot_df = merged_df.pivot(index='Ano', columns='Grupo', values='Percentual').fillna(0)
    
    fig = go.Figure()
    
    # Add traces for each group
    for grupo in pivot_df.columns:
        fig.add_trace(go.Bar(
            name=grupo,
            x=pivot_df.index,
            y=pivot_df[grupo],
            text=[f'{v:.1f}%' for v in pivot_df[grupo]],
            textposition='inside',
            hovertemplate=f'<b>{grupo}</b><br>Ano: %{{x}}<br>% da Receita: %{{y:.1f}}%<extra></extra>'
        ))
    
    fig.update_layout(
        barmode='stack',
        title=title,
        xaxis_title='Ano',
        yaxis_title='% da Receita',
        yaxis=dict(tickformat='.1f', ticksuffix='%'),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(r=150)
    )
    
    return fig


def create_margin_impact_by_group_chart(group_df: pd.DataFrame, financial_df: pd.DataFrame,
                                       title: str = "Impacto dos Grupos na Margem de Lucro") -> go.Figure:
    """
    Create a waterfall chart showing how each group impacts profit margin
    """
    # Get the latest year data
    latest_year = group_df['Ano'].max()
    year_data = group_df[group_df['Ano'] == latest_year]
    
    # Get financial data for the year
    fin_data = financial_df[financial_df['year'] == latest_year].iloc[0]
    revenue = fin_data['revenue']
    gross_margin = (revenue - fin_data.get('variable_costs', 0)) / revenue * 100
    
    # Calculate impact of each group
    impacts = []
    groups = year_data['Grupo'].unique()
    
    # Start with gross margin
    impacts.append({
        'x': 'Margem Bruta',
        'y': gross_margin,
        'measure': 'absolute',
        'text': f'{gross_margin:.1f}%'
    })
    
    # Add each group's impact
    running_margin = gross_margin
    for grupo in groups:
        grupo_data = year_data[year_data['Grupo'] == grupo]
        if not grupo_data.empty:
            impact = -(grupo_data['Valor'].iloc[0] / revenue * 100)
            running_margin += impact
            
            impacts.append({
                'x': grupo,
                'y': impact,
                'measure': 'relative',
                'text': f'{impact:.1f}%'
            })
    
    # Add final margin
    impacts.append({
        'x': 'Margem Líquida',
        'y': running_margin,
        'measure': 'total',
        'text': f'{running_margin:.1f}%'
    })
    
    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        x = [d['x'] for d in impacts],
        y = [d['y'] for d in impacts],
        measure = [d['measure'] for d in impacts],
        text = [d['text'] for d in impacts],
        textposition = "outside",
        connector = {"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title = f"{title} - {latest_year}",
        xaxis_title = "Componentes",
        yaxis_title = "Margem (%)",
        yaxis = dict(tickformat='.1f', ticksuffix='%'),
        showlegend = False,
        height = 500,
        margin = dict(b=100)
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_group_treemap(groups_data: Dict[str, Dict], year: int, 
                        title: str = "Composição dos Grupos de Despesas") -> go.Figure:
    """
    Create a treemap showing the composition of expense groups
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color palette
    color_map = {
        'Repasse de Comissão': '#FF6B6B',
        'Funcionários': '#4ECDC4',
        'Telefones': '#45B7D1',
        'Marketing': '#FFA07A',
        'Impostos e Taxas': '#98D8C8',
        'Administrativo': '#F7DC6F',
        'Financeiro': '#BB8FCE'
    }
    
    # Root
    labels.append("Total de Despesas")
    parents.append("")
    values.append(0)  # Will be calculated
    colors.append("#E0E0E0")
    
    total_value = 0
    
    # Add groups and their items
    for group_name, group_data in groups_data.items():
        if year in group_data['years']:
            year_values = group_data['years'][year]
            group_value = year_values['annual']
            
            # Add group
            labels.append(group_name)
            parents.append("Total de Despesas")
            values.append(group_value)
            colors.append(color_map.get(group_name, '#95A5A6'))
            
            total_value += group_value
    
    # Update root value
    values[0] = total_value
    
    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percentParent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"{title} - {year}",
        height=600,
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_pnl_evolution_chart_custom(df, x_col='year', x_title='Ano'):
    """Create a custom P&L evolution chart that works with different time periods"""
    
    if df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # Add Revenue line
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df['revenue'],
        mode='lines+markers',
        name='Receita',
        line=dict(color='#00CC88', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>'
    ))
    
    # Add Total Costs line
    cost_fields = ['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 
                   'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']
    
    # Filter cost fields that exist in the dataframe
    existing_cost_fields = [field for field in cost_fields if field in df.columns]
    
    # Calculate total costs
    if existing_cost_fields:
        df['total_costs'] = df[existing_cost_fields].sum(axis=1)
    else:
        df['total_costs'] = 0
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df['total_costs'],
        mode='lines+markers',
        name='Custos Totais',
        line=dict(color='#FF4444', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Custos: R$ %{y:,.0f}<extra></extra>'
    ))
    
    # Add Net Profit line
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df['net_profit'],
        mode='lines+markers',
        name='Lucro Líquido',
        line=dict(color='#3366CC', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Lucro: R$ %{y:,.0f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title="Evolução do Demonstrativo de Resultados",
        xaxis_title=x_title,
        yaxis_title="Valores (R$)",
        hovermode='x unified',
        height=500,
        yaxis=dict(tickformat=',.0f'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Adjust x-axis for better readability with many periods
    if x_col == 'period' and len(df) > 12:
        fig.update_xaxes(
            tickangle=-45,
            tickmode='linear',
            dtick=max(1, len(df) // 12)  # Show every Nth label
        )
    elif x_col == 'period':
        fig.update_xaxes(tickangle=-45)
    
    return fig


def create_expense_revenue_percentage_chart(
    expenses: Dict[str, float], 
    revenue: float, 
    title: str = "Despesas como % da Receita"
) -> go.Figure:
    """
    Create a bar chart showing expenses as percentage of revenue
    
    Args:
        expenses: Dictionary of expense categories and values
        revenue: Total revenue value
        title: Chart title
    """
    if revenue <= 0:
        return go.Figure().add_annotation(
            text="Receita não disponível para cálculo de percentuais",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Calculate percentages
    categories = list(expenses.keys())
    values = list(expenses.values())
    percentages = [(v / revenue * 100) for v in values]
    
    # Sort by percentage
    sorted_data = sorted(zip(categories, values, percentages), key=lambda x: x[2], reverse=True)
    categories, values, percentages = zip(*sorted_data)
    
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        x=categories,
        y=percentages,
        text=[f"{p:.1f}%<br>{format_currency(v)}" for v, p in zip(values, percentages)],
        textposition='outside',
        marker_color=['red' if p > 30 else 'orange' if p > 20 else 'green' for p in percentages],
        hovertemplate='<b>%{x}</b><br>%{y:.1f}% da receita<br>Valor: %{customdata}<extra></extra>',
        customdata=[format_currency(v) for v in values]
    ))
    
    # Add reference line at 100%
    fig.add_hline(y=100, line_dash="dash", line_color="red", 
                  annotation_text="100% da Receita")
    
    fig.update_layout(
        title=title,
        xaxis_title="Categoria",
        yaxis_title="% da Receita",
        height=500,
        showlegend=False,
        yaxis=dict(range=[0, max(120, max(percentages) * 1.1)])
    )
    
    return fig


def create_category_comparison_sunburst(
    categories_data: Dict[str, Dict[str, float]], 
    revenue: Optional[float] = None
) -> go.Figure:
    """
    Create a sunburst chart for hierarchical category comparison
    
    Args:
        categories_data: Nested dictionary of categories and subcategories with values
        revenue: Optional revenue for percentage calculations
    """
    labels = []
    parents = []
    values = []
    colors = []
    
    # Add root
    total = sum(cat_data.get('total', sum(cat_data.values()) if isinstance(cat_data, dict) else cat_data) 
                for cat_data in categories_data.values())
    labels.append("Total Custos")
    parents.append("")
    values.append(total)
    colors.append("lightgray")
    
    # Color palette
    color_palette = px.colors.qualitative.Set3
    
    # Add categories and subcategories
    for i, (cat_name, cat_data) in enumerate(categories_data.items()):
        if isinstance(cat_data, dict):
            # Category with subcategories
            cat_total = cat_data.get('total', sum(v for k, v in cat_data.items() if k != 'total'))
            labels.append(cat_name)
            parents.append("Total Custos")
            values.append(cat_total)
            colors.append(color_palette[i % len(color_palette)])
            
            # Add subcategories
            for subcat_name, subcat_value in cat_data.items():
                if subcat_name != 'total' and subcat_value > 0:
                    labels.append(subcat_name)
                    parents.append(cat_name)
                    values.append(subcat_value)
                    colors.append(color_palette[i % len(color_palette)])
        else:
            # Simple category
            labels.append(cat_name)
            parents.append("Total Custos")
            values.append(cat_data)
            colors.append(color_palette[i % len(color_palette)])
    
    # Create custom hover text
    if revenue and revenue > 0:
        customdata = [(v / revenue * 100) for v in values]
        hovertemplate = '<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent} do pai<br>%{customdata:.1f}% da receita<extra></extra>'
    else:
        customdata = None
        hovertemplate = '<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent} do pai<extra></extra>'
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors),
        customdata=customdata,
        hovertemplate=hovertemplate
    ))
    
    fig.update_layout(
        title="Hierarquia de Custos com Subcategorias",
        height=600,
        margin=dict(t=50, b=0, l=0, r=0)
    )
    
    return fig


def create_expense_selection_matrix(
    items: List[Dict[str, any]], 
    selected_ids: set,
    revenue: Optional[float] = None
) -> go.Figure:
    """
    Create a matrix/heatmap for expense selection visualization
    
    Args:
        items: List of expense items with 'id', 'label', 'value', 'category'
        selected_ids: Set of selected item IDs
        revenue: Optional revenue for percentage calculations
    """
    # Group items by category
    categories = {}
    for item in items:
        cat = item.get('category', 'Outros')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    # Create matrix data
    max_items = max(len(items) for items in categories.values())
    matrix = []
    hover_text = []
    
    for cat_name, cat_items in categories.items():
        row = []
        hover_row = []
        for i in range(max_items):
            if i < len(cat_items):
                item = cat_items[i]
                is_selected = item['id'] in selected_ids
                value = item['value']
                
                # Color intensity based on value and selection
                if is_selected:
                    intensity = 0.5 + (value / max(i['value'] for i in items)) * 0.5
                else:
                    intensity = (value / max(i['value'] for i in items)) * 0.3
                
                row.append(intensity)
                
                # Hover text
                hover_info = f"<b>{item['label']}</b><br>Valor: {format_currency(value)}"
                if revenue and revenue > 0:
                    hover_info += f"<br>{(value/revenue*100):.1f}% da receita"
                hover_info += f"<br>{'✅ Selecionado' if is_selected else '⬜ Não selecionado'}"
                hover_row.append(hover_info)
            else:
                row.append(0)
                hover_row.append("")
        
        matrix.append(row)
        hover_text.append(hover_row)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        colorscale='RdYlGn',
        showscale=True,
        colorbar=dict(title="Intensidade")
    ))
    
    fig.update_layout(
        title="Matriz de Seleção de Despesas",
        xaxis_title="Posição",
        yaxis_title="Categoria",
        yaxis=dict(ticktext=list(categories.keys()), tickvals=list(range(len(categories)))),
        height=400 + len(categories) * 30
    )
    
    return fig


def create_comparative_waterfall(
    base_value: float,
    changes: Dict[str, float],
    title: str = "Análise Waterfall de Mudanças"
) -> go.Figure:
    """
    Create a waterfall chart showing changes from base value
    
    Args:
        base_value: Starting value
        changes: Dictionary of change categories and values
        title: Chart title
    """
    # Prepare data
    x = ["Base"] + list(changes.keys()) + ["Total"]
    measure = ["absolute"] + ["relative"] * len(changes) + ["total"]
    y = [base_value] + list(changes.values()) + [None]
    
    # Colors for positive and negative changes
    marker_colors = ["lightgray"]
    for change in changes.values():
        marker_colors.append("green" if change >= 0 else "red")
    marker_colors.append("blue")
    
    # Text labels
    text = [format_currency(base_value)]
    for change in changes.values():
        text.append(f"{'+' if change >= 0 else ''}{format_currency(change)}")
    total = base_value + sum(changes.values())
    text.append(format_currency(total))
    
    fig = go.Figure(go.Waterfall(
        x=x,
        measure=measure,
        y=y,
        text=text,
        textposition="outside",
        connector={"line": {"color": "gray", "width": 2}},
        increasing={"marker": {"color": "green"}},
        decreasing={"marker": {"color": "red"}},
        totals={"marker": {"color": "blue"}}
    ))
    
    fig.update_layout(
        title=title,
        showlegend=False,
        height=500,
        xaxis_tickangle=-45
    )
    
    return fig
