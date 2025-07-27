"""
Micro Analysis Charts Module
Provides visualization functions for detailed cost and expense analysis
"""

import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any, Tuple
from utils import format_currency, get_category_icon, get_category_name


def create_expense_pareto_chart(items: List[Dict], title: str = "Análise de Pareto - Despesas") -> go.Figure:
    """
    Create a Pareto chart showing expenses with cumulative percentage
    
    Args:
        items: List of expense items
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    if not items:
        return go.Figure()
    
    # Sort by value descending
    sorted_items = sorted(items, key=lambda x: x['valor_anual'], reverse=True)[:20]
    
    # Calculate cumulative percentage
    total = sum(item['valor_anual'] for item in sorted_items)
    cumulative_sum = 0
    cumulative_percentages = []
    
    for item in sorted_items:
        cumulative_sum += item['valor_anual']
        cumulative_percentages.append((cumulative_sum / total) * 100)
    
    fig = go.Figure()
    
    # Bar chart for values
    fig.add_trace(
        go.Bar(
            x=[item['descricao'][:30] + '...' if len(item['descricao']) > 30 else item['descricao'] 
               for item in sorted_items],
            y=[item['valor_anual'] for item in sorted_items],
            name='Valor',
            yaxis='y',
            marker_color='#2E86AB',
            text=[format_currency(item['valor_anual']) for item in sorted_items],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Valor: %{text}<extra></extra>'
        )
    )
    
    # Line chart for cumulative percentage
    fig.add_trace(
        go.Scatter(
            x=[item['descricao'][:30] + '...' if len(item['descricao']) > 30 else item['descricao'] 
               for item in sorted_items],
            y=cumulative_percentages,
            name='% Acumulado',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='#E63946', width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>Acumulado: %{y:.1f}%<extra></extra>'
        )
    )
    
    # Add 80% reference line
    fig.add_hline(
        y=80, 
        line_dash="dash", 
        line_color="gray",
        annotation_text="80%",
        annotation_position="right",
        yref='y2'
    )
    
    fig.update_layout(
        title=title,
        xaxis=dict(tickangle=-45),
        yaxis=dict(
            title='Valor (R$)',
            titlefont=dict(color='#2E86AB'),
            tickfont=dict(color='#2E86AB')
        ),
        yaxis2=dict(
            title='% Acumulado',
            titlefont=dict(color='#E63946'),
            tickfont=dict(color='#E63946'),
            anchor='x',
            overlaying='y',
            side='right',
            range=[0, 105]
        ),
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_expense_treemap(items: List[Dict], title: str = "Mapa de Despesas") -> go.Figure:
    """
    Create a treemap visualization of expenses by category and subcategory
    
    Args:
        items: List of expense items
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    if not items:
        return go.Figure()
    
    # Prepare data for treemap
    labels = ['Total']
    parents = ['']
    values = [sum(item['valor_anual'] for item in items)]
    colors = ['lightgray']
    
    # Group by category
    categories = {}
    for item in items:
        cat = item['categoria']
        if cat not in categories:
            categories[cat] = {
                'total': 0,
                'items': []
            }
        categories[cat]['total'] += item['valor_anual']
        categories[cat]['items'].append(item)
    
    # Category colors
    category_colors = {
        'variable_costs': '#FF6B6B',
        'fixed_costs': '#4ECDC4',
        'admin_expenses': '#45B7D1',
        'operational_expenses': '#96CEB4',
        'marketing_expenses': '#FFEAA7',
        'financial_expenses': '#DDA0DD',
        'tax_expenses': '#98D8C8',
        'other_expenses': '#F8B500',
        'other_costs': '#F97F51',
        'other': '#B8B8B8'
    }
    
    # Add categories
    for cat, data in categories.items():
        labels.append(f"{get_category_name(cat)}")
        parents.append('Total')
        values.append(data['total'])
        colors.append(category_colors.get(cat, '#B8B8B8'))
        
        # Add top items for each category
        top_items = sorted(data['items'], key=lambda x: x['valor_anual'], reverse=True)[:10]
        for item in top_items:
            labels.append(item['descricao'])
            parents.append(f"{get_category_name(cat)}")
            values.append(item['valor_anual'])
            colors.append(category_colors.get(cat, '#B8B8B8'))
    
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors),
        textinfo="label+value+percent parent",
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent}<extra></extra>',
        texttemplate='<b>%{label}</b><br>%{percentParent}'
    ))
    
    fig.update_layout(
        title=title,
        height=600,
        margin=dict(t=50, l=0, r=0, b=0)
    )
    
    return fig


def create_expense_sankey(items: List[Dict], title: str = "Fluxo de Custos e Despesas") -> go.Figure:
    """
    Create a Sankey diagram showing flow from categories to subcategories to specific items
    
    Args:
        items: List of expense items
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    if not items:
        return go.Figure()
    
    # Prepare nodes and links
    nodes = {
        'label': ['Total'],
        'color': ['lightgray']
    }
    
    links = {
        'source': [],
        'target': [],
        'value': [],
        'color': []
    }
    
    # Category colors with transparency
    category_colors_alpha = {
        'variable_costs': 'rgba(255, 107, 107, 0.5)',
        'fixed_costs': 'rgba(78, 205, 196, 0.5)',
        'admin_expenses': 'rgba(69, 183, 209, 0.5)',
        'operational_expenses': 'rgba(150, 206, 180, 0.5)',
        'marketing_expenses': 'rgba(255, 234, 167, 0.5)',
        'financial_expenses': 'rgba(221, 160, 221, 0.5)',
        'tax_expenses': 'rgba(152, 216, 200, 0.5)',
        'other_expenses': 'rgba(248, 181, 0, 0.5)',
        'other_costs': 'rgba(249, 127, 81, 0.5)',
        'other': 'rgba(184, 184, 184, 0.5)'
    }
    
    # Group by category and subcategory
    category_totals = {}
    subcategory_totals = {}
    
    for item in items:
        cat = item['categoria']
        subcat = f"{cat}_{item['subcategoria_principal']}"
        
        if cat not in category_totals:
            category_totals[cat] = 0
        category_totals[cat] += item['valor_anual']
        
        if subcat not in subcategory_totals:
            subcategory_totals[subcat] = {
                'category': cat,
                'value': 0,
                'items': []
            }
        subcategory_totals[subcat]['value'] += item['valor_anual']
        subcategory_totals[subcat]['items'].append(item)
    
    # Add category nodes
    for cat, total in category_totals.items():
        nodes['label'].append(get_category_name(cat))
        nodes['color'].append(category_colors_alpha.get(cat, 'rgba(184, 184, 184, 0.5)'))
        
        # Link from Total to Category
        links['source'].append(0)
        links['target'].append(len(nodes['label']) - 1)
        links['value'].append(total)
        links['color'].append(category_colors_alpha.get(cat, 'rgba(184, 184, 184, 0.5)'))
    
    # Add subcategory nodes and top items
    for subcat, data in subcategory_totals.items():
        if data['value'] > 0:
            # Add subcategory node
            subcat_name = item['subcategoria_nome']
            nodes['label'].append(subcat_name)
            nodes['color'].append(category_colors_alpha.get(data['category'], 'rgba(184, 184, 184, 0.5)'))
            subcat_idx = len(nodes['label']) - 1
            
            # Find category index
            cat_name = get_category_name(data['category'])
            cat_idx = nodes['label'].index(cat_name)
            
            # Link from Category to Subcategory
            links['source'].append(cat_idx)
            links['target'].append(subcat_idx)
            links['value'].append(data['value'])
            links['color'].append(category_colors_alpha.get(data['category'], 'rgba(184, 184, 184, 0.5)'))
            
            # Add top 5 items for each subcategory
            top_items = sorted(data['items'], key=lambda x: x['valor_anual'], reverse=True)[:5]
            for item in top_items:
                nodes['label'].append(item['descricao'][:40])
                nodes['color'].append(category_colors_alpha.get(data['category'], 'rgba(184, 184, 184, 0.5)'))
                
                # Link from Subcategory to Item
                links['source'].append(subcat_idx)
                links['target'].append(len(nodes['label']) - 1)
                links['value'].append(item['valor_anual'])
                links['color'].append(category_colors_alpha.get(data['category'], 'rgba(184, 184, 184, 0.5)'))
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes['label'],
            color=nodes['color']
        ),
        link=dict(
            source=links['source'],
            target=links['target'],
            value=links['value'],
            color=links['color']
        )
    )])
    
    fig.update_layout(
        title=title,
        height=800,
        font_size=12
    )
    
    return fig


def create_growth_analysis_chart(items_by_year: Dict[int, List[Dict]], 
                               top_n: int = 15,
                               title: str = "Análise de Crescimento - Top Despesas") -> go.Figure:
    """
    Create a chart showing growth rate of top expenses across years
    
    Args:
        items_by_year: Dictionary mapping years to lists of items
        top_n: Number of top items to show
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    if not items_by_year or len(items_by_year) < 2:
        return go.Figure()
    
    # Get all unique items across years
    all_items_map = {}
    for year, items in items_by_year.items():
        for item in items:
            key = item['descricao']
            if key not in all_items_map:
                all_items_map[key] = {}
            all_items_map[key][year] = item['valor_anual']
    
    # Calculate growth rates
    growth_data = []
    years_sorted = sorted(items_by_year.keys())
    
    for desc, year_values in all_items_map.items():
        if len(year_values) >= 2:
            # Calculate average growth rate
            growths = []
            for i in range(1, len(years_sorted)):
                if years_sorted[i-1] in year_values and years_sorted[i] in year_values:
                    old_val = year_values[years_sorted[i-1]]
                    new_val = year_values[years_sorted[i]]
                    if old_val > 0:
                        growth = ((new_val - old_val) / old_val) * 100
                        growths.append(growth)
            
            if growths:
                avg_growth = sum(growths) / len(growths)
                latest_value = year_values.get(years_sorted[-1], 0)
                growth_data.append({
                    'description': desc,
                    'avg_growth': avg_growth,
                    'latest_value': latest_value,
                    'values': year_values
                })
    
    # Sort by absolute growth rate and get top N
    growth_data_sorted = sorted(growth_data, key=lambda x: abs(x['avg_growth']), reverse=True)[:top_n]
    
    fig = go.Figure()
    
    # Add traces for each item
    for item_data in growth_data_sorted:
        years = []
        values = []
        
        for year in years_sorted:
            if year in item_data['values']:
                years.append(str(year))
                values.append(item_data['values'][year])
        
        fig.add_trace(go.Scatter(
            x=years,
            y=values,
            mode='lines+markers',
            name=item_data['description'][:30] + '...' if len(item_data['description']) > 30 else item_data['description'],
            line=dict(width=2),
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>Ano: %{x}<br>Valor: R$ %{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Ano",
        yaxis_title="Valor (R$)",
        hovermode='x unified',
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
    
    return fig


def create_monthly_heatmap(items: List[Dict], title: str = "Mapa de Calor - Despesas Mensais") -> go.Figure:
    """
    Create a heatmap showing expense patterns across months
    
    Args:
        items: List of expense items with monthly values
        title: Chart title
        
    Returns:
        Plotly figure object
    """
    if not items:
        return go.Figure()
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
              'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Get top 20 items by annual value
    top_items = sorted(items, key=lambda x: x['valor_anual'], reverse=True)[:20]
    
    # Prepare data for heatmap
    z_data = []
    y_labels = []
    
    for item in top_items:
        monthly_values = []
        for month in months:
            value = item['valores_mensais'].get(month, 0)
            monthly_values.append(value)
        
        z_data.append(monthly_values)
        y_labels.append(item['descricao'][:40] + '...' if len(item['descricao']) > 40 else item['descricao'])
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=months,
        y=y_labels,
        colorscale='RdBu_r',
        hovertemplate='<b>%{y}</b><br>%{x}: R$ %{z:,.0f}<extra></extra>',
        colorbar=dict(
            title="Valor (R$)",
            titleside="right"
        )
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Mês",
        yaxis_title="Despesa",
        height=600,
        yaxis=dict(autorange='reversed')
    )
    
    return fig