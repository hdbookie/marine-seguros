"""
Category Breakdown Visualization Component
Shows individual charts for each expense category with revenue percentage comparison
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
from utils import format_currency

def render_category_breakdown(financial_data: Dict, selected_years: List[int]):
    """
    Render breakdown charts for each cost category with revenue percentage
    """
    st.header("📊 Análise por Categoria de Custos")
    
    if not financial_data or not selected_years:
        st.info("Selecione anos para visualizar a análise por categoria.")
        return
    
    # Aggregate data for selected years
    aggregated_data = _aggregate_years_data(financial_data, selected_years)
    
    if not aggregated_data:
        st.warning("Nenhum dado disponível para os anos selecionados.")
        return
    
    # Get revenue total for percentage calculations
    revenue_total = aggregated_data.get('revenue', {}).get('total', 0)
    
    if revenue_total == 0:
        st.warning("⚠️ Receita não encontrada. Percentuais não podem ser calculados.")
    
    # Display revenue summary first
    if revenue_total > 0:
        st.markdown("### 💰 Faturamento Total")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Receita Total", format_currency(revenue_total))
        with col2:
            if 'revenue' in aggregated_data and 'hierarchy' in aggregated_data['revenue']:
                num_revenue_items = len(aggregated_data['revenue']['hierarchy'].get('faturamento', {}).get('items', []))
                st.metric("Fontes de Receita", num_revenue_items)
        with col3:
            avg_revenue = revenue_total / len(selected_years) if selected_years else 0
            st.metric("Média Anual", format_currency(avg_revenue))
        
        # Show revenue breakdown if hierarchical
        if 'revenue' in aggregated_data and 'hierarchy' in aggregated_data['revenue']:
            _render_revenue_breakdown(aggregated_data['revenue']['hierarchy'], revenue_total)
    
    st.markdown("---")
    
    # Category selector
    categories = _get_available_categories(aggregated_data)
    
    if not categories:
        st.warning("Nenhuma categoria de custo encontrada.")
        return
    
    # Visualization options
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_category = st.selectbox(
            "📁 Selecione a Categoria",
            ["Todas as Categorias"] + categories,
            key="category_selector"
        )
    with col2:
        chart_type = st.selectbox(
            "📈 Tipo de Gráfico",
            ["Treemap", "Barras", "Pizza", "Sunburst"],
            key="category_chart_type"
        )
    with col3:
        show_percentage = st.checkbox(
            "Mostrar % da Receita",
            value=True,
            key="show_revenue_percentage"
        )
    with col4:
        # Add year comparison mode
        if len(selected_years) > 1:
            comparison_mode = st.selectbox(
                "📊 Modo",
                ["Agregado", "Comparação Anual"],
                key="comparison_mode"
            )
        else:
            comparison_mode = "Agregado"
    
    st.markdown("---")
    
    # Render selected visualization
    if comparison_mode == "Comparação Anual" and len(selected_years) > 1:
        # Show year-by-year comparison
        _render_year_comparison(financial_data, selected_years, selected_category, chart_type, show_percentage)
    else:
        # Show aggregated view
        if selected_category == "Todas as Categorias":
            _render_all_categories_comparison(aggregated_data, revenue_total, chart_type, show_percentage)
        else:
            _render_single_category_breakdown(
                aggregated_data, 
                selected_category, 
                revenue_total, 
                chart_type, 
                show_percentage
            )
    
    # Comparison table at the bottom
    st.markdown("---")
    st.markdown("### 📋 Tabela Comparativa de Categorias")
    _render_category_comparison_table(aggregated_data, revenue_total, show_percentage)


def _aggregate_years_data(financial_data: Dict, selected_years: List[int]) -> Dict:
    """Aggregate data from multiple years"""
    aggregated = {}
    
    for year in selected_years:
        if year not in financial_data:
            continue
        
        year_data = financial_data[year]
        
        # Check if this is Excel hierarchy data with sections
        if 'sections' in year_data:
            # Process sections-based data structure
            for section in year_data['sections']:
                section_name = section.get('name', '').upper()
                
                # Process revenue sections (only FATURAMENTO)
                if section_name == 'FATURAMENTO':
                    if 'revenue' not in aggregated:
                        aggregated['revenue'] = {
                            'total': 0,
                            'hierarchy': {'faturamento': {'name': 'Faturamento', 'total': 0, 'subcategories': {}, 'items': []}}
                        }
                    
                    section_value = section.get('value', 0)
                    aggregated['revenue']['total'] += section_value
                    aggregated['revenue']['hierarchy']['faturamento']['total'] += section_value
                    
                    # Process subcategories if available
                    for subcat in section.get('subcategories', []):
                        subcat_name = subcat.get('name', '')
                        subcat_key = subcat_name.lower().replace(' ', '_')
                        
                        if subcat_key not in aggregated['revenue']['hierarchy']['faturamento']['subcategories']:
                            aggregated['revenue']['hierarchy']['faturamento']['subcategories'][subcat_key] = {
                                'name': subcat_name,
                                'total': 0,
                                'items': []
                            }
                        
                        aggregated['revenue']['hierarchy']['faturamento']['subcategories'][subcat_key]['total'] += subcat.get('value', 0)
                        
                        # Add items
                        for item in subcat.get('items', []):
                            aggregated['revenue']['hierarchy']['faturamento']['subcategories'][subcat_key]['items'].append({
                                'label': item.get('name', ''),
                                'annual': item.get('value', 0)
                            })
                
                # Process expense sections
                elif section_name in ['CUSTOS FIXOS', 'CUSTOS VARIÁVEIS', 'CUSTOS NÃO OPERACIONAIS', 
                                     'DESPESAS ADMINISTRATIVAS', 'DESPESAS DE MARKETING', 
                                     'DESPESAS OPERACIONAIS', 'DESPESAS FINANCEIRAS', 
                                     'IMPOSTOS', 'COMISSÕES']:
                    # Map section names to category keys
                    category_map = {
                        'CUSTOS FIXOS': 'fixed_costs',
                        'CUSTOS VARIÁVEIS': 'variable_costs',
                        'CUSTOS NÃO OPERACIONAIS': 'non_operational_costs',
                        'DESPESAS ADMINISTRATIVAS': 'administrative_expenses',
                        'DESPESAS DE MARKETING': 'marketing_expenses',
                        'DESPESAS OPERACIONAIS': 'operational_costs',
                        'DESPESAS FINANCEIRAS': 'financial_expenses',
                        'IMPOSTOS': 'taxes',
                        'COMISSÕES': 'commissions'
                    }
                    
                    category_key = category_map.get(section_name, section_name.lower().replace(' ', '_'))
                    
                    if category_key not in aggregated:
                        aggregated[category_key] = {
                            'total': 0,
                            'line_items': {}
                        }
                    
                    # Add section total
                    aggregated[category_key]['total'] += section.get('value', 0)
                    
                    # Process subcategories and items
                    for subcat in section.get('subcategories', []):
                        # Process items within subcategory
                        for item in subcat.get('items', []):
                            item_name = item.get('name', '')
                            item_key = item_name.lower().replace(' ', '_')
                            
                            if item_key not in aggregated[category_key]['line_items']:
                                aggregated[category_key]['line_items'][item_key] = {
                                    'label': item_name,
                                    'total': 0,
                                    'count': 0
                                }
                            
                            aggregated[category_key]['line_items'][item_key]['total'] += item.get('value', 0)
                            aggregated[category_key]['line_items'][item_key]['count'] += 1
                        
                        # Also add subcategory itself if it has no items
                        if not subcat.get('items'):
                            subcat_name = subcat.get('name', '')
                            subcat_key = subcat_name.lower().replace(' ', '_')
                            
                            if subcat_key not in aggregated[category_key]['line_items']:
                                aggregated[category_key]['line_items'][subcat_key] = {
                                    'label': subcat_name,
                                    'total': 0,
                                    'count': 0
                                }
                            
                            aggregated[category_key]['line_items'][subcat_key]['total'] += subcat.get('value', 0)
                            aggregated[category_key]['line_items'][subcat_key]['count'] += 1
        
        # Process revenue if it has hierarchy (old format support)
        elif 'revenue' in year_data:
            if 'revenue' not in aggregated:
                aggregated['revenue'] = {
                    'total': 0,
                    'hierarchy': {'faturamento': {'name': 'Faturamento', 'total': 0, 'subcategories': {}, 'items': []}}
                }
            
            if isinstance(year_data['revenue'], dict):
                if 'hierarchy' in year_data['revenue']:
                    # Aggregate hierarchical revenue
                    for cat_key, cat_data in year_data['revenue']['hierarchy'].items():
                        if cat_key == 'faturamento':
                            aggregated['revenue']['hierarchy']['faturamento']['total'] += cat_data.get('total', 0)
                            aggregated['revenue']['total'] += cat_data.get('total', 0)
                            
                            # Aggregate subcategories
                            for subcat_key, subcat_data in cat_data.get('subcategories', {}).items():
                                if subcat_key not in aggregated['revenue']['hierarchy']['faturamento']['subcategories']:
                                    aggregated['revenue']['hierarchy']['faturamento']['subcategories'][subcat_key] = {
                                        'name': subcat_data.get('name', subcat_key),
                                        'total': 0,
                                        'items': []
                                    }
                                aggregated['revenue']['hierarchy']['faturamento']['subcategories'][subcat_key]['total'] += subcat_data.get('total', 0)
                                aggregated['revenue']['hierarchy']['faturamento']['subcategories'][subcat_key]['items'].extend(subcat_data.get('items', []))
                else:
                    # Simple revenue format
                    aggregated['revenue']['total'] += year_data['revenue'].get('annual', 0)
            else:
                # Direct value
                aggregated['revenue']['total'] += year_data.get('revenue', 0)
        
        # Process expense categories
        expense_categories = [
            'fixed_costs', 'variable_costs', 'administrative_expenses',
            'marketing_expenses', 'operational_costs', 'financial_expenses',
            'taxes', 'commissions', 'non_operational_costs'
        ]
        
        for category in expense_categories:
            if category in year_data:
                if category not in aggregated:
                    aggregated[category] = {
                        'total': 0,
                        'line_items': {}
                    }
                
                cat_data = year_data[category]
                if isinstance(cat_data, dict):
                    # Add total
                    aggregated[category]['total'] += cat_data.get('annual', 0)
                    
                    # Add line items
                    if 'line_items' in cat_data:
                        for item_key, item_data in cat_data['line_items'].items():
                            if item_key not in aggregated[category]['line_items']:
                                aggregated[category]['line_items'][item_key] = {
                                    'label': item_data.get('label', item_key),
                                    'total': 0,
                                    'count': 0
                                }
                            aggregated[category]['line_items'][item_key]['total'] += item_data.get('annual', 0)
                            aggregated[category]['line_items'][item_key]['count'] += 1
    
    return aggregated


def _get_available_categories(aggregated_data: Dict) -> List[str]:
    """Get list of available expense categories"""
    categories = []
    category_names = {
        'fixed_costs': 'Custos Fixos',
        'variable_costs': 'Custos Variáveis',
        'administrative_expenses': 'Despesas Administrativas',
        'marketing_expenses': 'Despesas de Marketing',
        'operational_costs': 'Custos Operacionais',
        'financial_expenses': 'Despesas Financeiras',
        'taxes': 'Impostos',
        'commissions': 'Comissões',
        'non_operational_costs': 'Custos Não Operacionais'
    }
    
    for key, name in category_names.items():
        if key in aggregated_data and aggregated_data[key].get('total', 0) > 0:
            categories.append(name)
    
    return categories


def _render_revenue_breakdown(revenue_hierarchy: Dict, total_revenue: float):
    """Render revenue breakdown visualization"""
    with st.expander("📊 Detalhamento do Faturamento", expanded=False):
        faturamento = revenue_hierarchy.get('faturamento', {})
        subcategories = faturamento.get('subcategories', {})
        
        if subcategories:
            # Create pie chart of revenue subcategories
            labels = []
            values = []
            
            for subcat_key, subcat_data in subcategories.items():
                labels.append(subcat_data.get('name', subcat_key))
                values.append(subcat_data.get('total', 0))
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percent}',
                hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percent} do faturamento<extra></extra>'
            )])
            
            fig.update_layout(
                title="Composição do Faturamento",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)


def _render_all_categories_comparison(aggregated_data: Dict, revenue_total: float, chart_type: str, show_percentage: bool):
    """Render comparison of all expense categories"""
    st.markdown("### 📊 Comparação de Todas as Categorias")
    
    # Prepare data
    categories_data = []
    category_map = {
        'fixed_costs': 'Custos Fixos',
        'variable_costs': 'Custos Variáveis',
        'administrative_expenses': 'Despesas Administrativas',
        'marketing_expenses': 'Despesas de Marketing',
        'operational_costs': 'Custos Operacionais',
        'financial_expenses': 'Despesas Financeiras',
        'taxes': 'Impostos',
        'commissions': 'Comissões',
        'non_operational_costs': 'Custos Não Operacionais'
    }
    
    for key, name in category_map.items():
        if key in aggregated_data:
            total = aggregated_data[key].get('total', 0)
            if total > 0:
                percentage = (total / revenue_total * 100) if revenue_total > 0 else 0
                categories_data.append({
                    'category': name,
                    'value': total,
                    'percentage': percentage
                })
    
    if not categories_data:
        st.info("Nenhuma categoria com valores encontrada.")
        return
    
    # Sort by value
    categories_data.sort(key=lambda x: x['value'], reverse=True)
    
    # Create visualization based on type
    if chart_type == "Barras":
        fig = go.Figure()
        
        # Add bars
        fig.add_trace(go.Bar(
            x=[d['category'] for d in categories_data],
            y=[d['value'] for d in categories_data],
            text=[f"{format_currency(d['value'])}<br>({d['percentage']:.1f}% da receita)" 
                  if show_percentage and revenue_total > 0 
                  else format_currency(d['value']) 
                  for d in categories_data],
            textposition='outside',
            marker_color=px.colors.qualitative.Set3[:len(categories_data)],
            hovertemplate='<b>%{x}</b><br>Valor: R$ %{y:,.0f}<br>%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Custos por Categoria",
            xaxis_title="Categoria",
            yaxis_title="Valor (R$)",
            height=500,
            showlegend=False
        )
        
    elif chart_type == "Pizza":
        fig = go.Figure(data=[go.Pie(
            labels=[d['category'] for d in categories_data],
            values=[d['value'] for d in categories_data],
            hole=0.3,
            texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percent}' + 
                       ('<br>%{customdata:.1f}% receita' if show_percentage and revenue_total > 0 else ''),
            customdata=[d['percentage'] for d in categories_data] if show_percentage else None,
            hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percent} do total de custos' +
                         ('<br>%{customdata:.1f}% da receita' if show_percentage and revenue_total > 0 else '') +
                         '<extra></extra>'
        )])
        
        fig.update_layout(
            title="Distribuição de Custos por Categoria",
            height=500
        )
        
    elif chart_type == "Treemap":
        fig = go.Figure(go.Treemap(
            labels=[d['category'] for d in categories_data],
            parents=[""] * len(categories_data),
            values=[d['value'] for d in categories_data],
            texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}' +
                       ('<br>%{customdata:.1f}% receita' if show_percentage and revenue_total > 0 else ''),
            customdata=[d['percentage'] for d in categories_data] if show_percentage else None,
            hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent} do total' +
                         ('<br>%{customdata:.1f}% da receita' if show_percentage and revenue_total > 0 else '') +
                         '<extra></extra>',
            marker=dict(colors=px.colors.qualitative.Set3[:len(categories_data)])
        ))
        
        fig.update_layout(
            title="Mapa de Custos por Categoria",
            height=500
        )
    
    else:  # Sunburst
        # Create hierarchical structure for sunburst
        labels = ["Total de Custos"]
        parents = [""]
        values = [sum(d['value'] for d in categories_data)]
        colors = ["lightgray"]
        
        for i, d in enumerate(categories_data):
            labels.append(d['category'])
            parents.append("Total de Custos")
            values.append(d['value'])
            colors.append(px.colors.qualitative.Set3[i % len(px.colors.qualitative.Set3)])
        
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors),
            hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Hierarquia de Custos",
            height=500
        )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_single_category_breakdown(aggregated_data: Dict, category_name: str, revenue_total: float, chart_type: str, show_percentage: bool):
    """Render breakdown of a single expense category"""
    st.markdown(f"### 📂 Detalhamento: {category_name}")
    
    # Map display name to data key
    category_map = {
        'Custos Fixos': 'fixed_costs',
        'Custos Variáveis': 'variable_costs',
        'Despesas Administrativas': 'administrative_expenses',
        'Despesas de Marketing': 'marketing_expenses',
        'Custos Operacionais': 'operational_costs',
        'Despesas Financeiras': 'financial_expenses',
        'Impostos': 'taxes',
        'Comissões': 'commissions',
        'Custos Não Operacionais': 'non_operational_costs'
    }
    
    category_key = category_map.get(category_name)
    if not category_key or category_key not in aggregated_data:
        st.warning(f"Categoria {category_name} não encontrada.")
        return
    
    category_data = aggregated_data[category_key]
    line_items = category_data.get('line_items', {})
    
    if not line_items:
        st.info(f"Nenhum item encontrado para {category_name}.")
        return
    
    # Show category metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total da Categoria", format_currency(category_data['total']))
    with col2:
        if revenue_total > 0:
            percentage = (category_data['total'] / revenue_total) * 100
            st.metric("% da Receita", f"{percentage:.1f}%")
    with col3:
        st.metric("Número de Itens", len(line_items))
    
    st.markdown("---")
    
    # Prepare items data
    items_data = []
    for item_key, item_info in line_items.items():
        total = item_info.get('total', 0)
        if total > 0:
            percentage = (total / revenue_total * 100) if revenue_total > 0 else 0
            items_data.append({
                'label': item_info.get('label', item_key),
                'value': total,
                'percentage': percentage,
                'category_percentage': (total / category_data['total'] * 100) if category_data['total'] > 0 else 0
            })
    
    # Sort by value
    items_data.sort(key=lambda x: x['value'], reverse=True)
    
    # Create visualization
    if chart_type == "Barras":
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=[d['label'] for d in items_data],
            x=[d['value'] for d in items_data],
            orientation='h',
            text=[f"{format_currency(d['value'])} ({d['percentage']:.1f}% receita)" 
                  if show_percentage and revenue_total > 0 
                  else format_currency(d['value']) 
                  for d in items_data],
            textposition='outside',
            marker_color=px.colors.qualitative.Set2[:len(items_data)],
            hovertemplate='<b>%{y}</b><br>Valor: R$ %{x:,.0f}<br>%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"Itens de {category_name}",
            xaxis_title="Valor (R$)",
            yaxis_title="",
            height=max(400, len(items_data) * 30),
            showlegend=False
        )
        
    elif chart_type == "Pizza":
        fig = go.Figure(data=[go.Pie(
            labels=[d['label'] for d in items_data[:15]],  # Limit to top 15 for readability
            values=[d['value'] for d in items_data[:15]],
            hole=0.3,
            texttemplate='<b>%{label}</b><br>%{percent}',
            customdata=[[d['percentage'], d['category_percentage']] for d in items_data[:15]],
            hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>' +
                         '%{percent} da categoria<br>' +
                         ('%{customdata[0]:.1f}% da receita' if show_percentage and revenue_total > 0 else '') +
                         '<extra></extra>'
        )])
        
        if len(items_data) > 15:
            st.info(f"Mostrando os 15 principais itens de {len(items_data)} total")
        
        fig.update_layout(
            title=f"Distribuição - {category_name}",
            height=500
        )
        
    elif chart_type == "Treemap":
        fig = go.Figure(go.Treemap(
            labels=[d['label'] for d in items_data],
            parents=[category_name] * len(items_data),
            values=[d['value'] for d in items_data],
            texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}' +
                       ('<br>%{customdata:.1f}% receita' if show_percentage and revenue_total > 0 else ''),
            customdata=[d['percentage'] for d in items_data] if show_percentage else None,
            hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>' +
                         '%{percentParent} da categoria<br>' +
                         ('%{customdata:.1f}% da receita' if show_percentage and revenue_total > 0 else '') +
                         '<extra></extra>',
            marker=dict(colors=px.colors.qualitative.Set2[:len(items_data)])
        ))
        
        fig.update_layout(
            title=f"Mapa de {category_name}",
            height=500
        )
    
    else:  # Sunburst
        labels = [category_name]
        parents = [""]
        values = [category_data['total']]
        colors = ["lightgray"]
        
        for i, d in enumerate(items_data):
            labels.append(d['label'])
            parents.append(category_name)
            values.append(d['value'])
            colors.append(px.colors.qualitative.Set2[i % len(px.colors.qualitative.Set2)])
        
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(colors=colors),
            hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"Hierarquia - {category_name}",
            height=500
        )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_year_comparison(financial_data: Dict, selected_years: List[int], selected_category: str, chart_type: str, show_percentage: bool):
    """Render year-by-year comparison of categories"""
    st.markdown(f"### 📊 Comparação Anual: {selected_category}")
    
    # Prepare data for each year
    year_data = {}
    for year in selected_years:
        if year not in financial_data:
            continue
        
        # Aggregate just this year's data
        single_year_data = _aggregate_years_data(financial_data, [year])
        year_data[year] = single_year_data
    
    if not year_data:
        st.warning("Nenhum dado disponível para comparação.")
        return
    
    # Map category names to keys
    category_map = {
        'Custos Fixos': 'fixed_costs',
        'Custos Variáveis': 'variable_costs',
        'Despesas Administrativas': 'administrative_expenses',
        'Despesas de Marketing': 'marketing_expenses',
        'Custos Operacionais': 'operational_costs',
        'Despesas Financeiras': 'financial_expenses',
        'Impostos': 'taxes',
        'Comissões': 'commissions',
        'Custos Não Operacionais': 'non_operational_costs'
    }
    
    if selected_category == "Todas as Categorias":
        # Compare all categories across years
        _render_all_categories_year_comparison(year_data, chart_type, show_percentage)
    else:
        # Compare specific category across years
        category_key = category_map.get(selected_category, selected_category.lower().replace(' ', '_'))
        _render_single_category_year_comparison(year_data, category_key, selected_category, chart_type, show_percentage)


def _render_all_categories_year_comparison(year_data: Dict, chart_type: str, show_percentage: bool):
    """Render comparison of all categories across years"""
    
    # Prepare data for visualization
    categories = set()
    for year, data in year_data.items():
        for key in data.keys():
            if key != 'revenue' and isinstance(data.get(key), dict) and 'total' in data[key]:
                categories.add(key)
    
    category_names = {
        'fixed_costs': 'Custos Fixos',
        'variable_costs': 'Custos Variáveis',
        'administrative_expenses': 'Despesas Administrativas',
        'marketing_expenses': 'Despesas de Marketing',
        'operational_costs': 'Custos Operacionais',
        'financial_expenses': 'Despesas Financeiras',
        'taxes': 'Impostos',
        'commissions': 'Comissões',
        'non_operational_costs': 'Custos Não Operacionais'
    }
    
    # Create comparison chart
    if chart_type == "Barras":
        fig = go.Figure()
        
        for year in sorted(year_data.keys()):
            values = []
            labels = []
            revenue = year_data[year].get('revenue', {}).get('total', 0)
            
            for cat_key in sorted(categories):
                if cat_key in year_data[year]:
                    value = year_data[year][cat_key].get('total', 0)
                    values.append(value)
                    labels.append(category_names.get(cat_key, cat_key))
            
            # Add bars for this year
            fig.add_trace(go.Bar(
                name=str(year),
                x=labels,
                y=values,
                text=[f"{format_currency(v)}<br>({(v/revenue*100):.1f}% receita)" if show_percentage and revenue > 0 else format_currency(v) for v in values],
                textposition='outside'
            ))
        
        fig.update_layout(
            title="Comparação de Categorias por Ano",
            xaxis_title="Categoria",
            yaxis_title="Valor (R$)",
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Pizza":
        # Show pie charts side by side for each year
        cols = st.columns(len(year_data))
        
        for i, (year, data) in enumerate(sorted(year_data.items())):
            with cols[i]:
                st.markdown(f"#### {year}")
                
                labels = []
                values = []
                
                for cat_key in categories:
                    if cat_key in data:
                        value = data[cat_key].get('total', 0)
                        if value > 0:
                            labels.append(category_names.get(cat_key, cat_key))
                            values.append(value)
                
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    texttemplate='<b>%{label}</b><br>%{percent}'
                )])
                
                fig.update_layout(height=400, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Treemap":
        # Show treemaps side by side for each year
        cols = st.columns(len(year_data))
        
        for i, (year, data) in enumerate(sorted(year_data.items())):
            with cols[i]:
                st.markdown(f"#### {year}")
                
                labels = []
                values = []
                parents = []
                revenue = data.get('revenue', {}).get('total', 0)
                
                for cat_key in categories:
                    if cat_key in data:
                        cat_value = data[cat_key].get('total', 0)
                        if cat_value > 0:
                            cat_name = category_names.get(cat_key, cat_key)
                            labels.append(cat_name)
                            values.append(cat_value)
                            parents.append("")
                            
                            # Add line items for this category
                            if 'line_items' in data[cat_key]:
                                for item_key, item_data in data[cat_key]['line_items'].items():
                                    if item_data['total'] > 0:
                                        labels.append(item_data['label'])
                                        values.append(item_data['total'])
                                        parents.append(cat_name)
                
                # Create treemap with revenue percentage if enabled
                texttemplate = '<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}'
                if show_percentage and revenue > 0:
                    customdata = [(v/revenue*100) for v in values]
                    texttemplate = '<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}<br>%{customdata:.1f}% receita'
                else:
                    customdata = None
                
                fig = go.Figure(go.Treemap(
                    labels=labels,
                    parents=parents,
                    values=values,
                    customdata=customdata,
                    texttemplate=texttemplate,
                    hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent}<extra></extra>',
                    marker=dict(colors=px.colors.qualitative.Set3[:len(labels)])
                ))
                
                fig.update_layout(height=600, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Sunburst":
        # Show sunburst charts for each year
        num_years = len(year_data)
        if num_years <= 2:
            cols = st.columns(num_years)
        else:
            # For more than 2 years, arrange in rows
            cols = st.columns(2)
            
        for i, (year, data) in enumerate(sorted(year_data.items())):
            col_idx = i % 2 if num_years > 2 else i
            with cols[col_idx] if num_years <= 2 else cols[col_idx]:
                st.markdown(f"#### {year}")
                
                labels = []
                values = []
                parents = []
                
                for cat_key in categories:
                    if cat_key in data:
                        cat_value = data[cat_key].get('total', 0)
                        if cat_value > 0:
                            cat_name = category_names.get(cat_key, cat_key)
                            labels.append(cat_name)
                            values.append(cat_value)
                            parents.append("")
                
                fig = go.Figure(go.Sunburst(
                    labels=labels,
                    parents=parents,
                    values=values,
                    branchvalues="total",
                    hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent}<extra></extra>'
                ))
                
                fig.update_layout(height=400, margin=dict(t=30, b=30, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
    
    # Show comparison table
    st.markdown("#### 📊 Tabela de Comparação")
    
    table_data = []
    for cat_key in sorted(categories):
        row = {'Categoria': category_names.get(cat_key, cat_key)}
        
        for year in sorted(year_data.keys()):
            value = 0
            if cat_key in year_data[year]:
                value = year_data[year][cat_key].get('total', 0)
            
            row[f"{year}"] = format_currency(value)
            
            if show_percentage:
                revenue = year_data[year].get('revenue', {}).get('total', 0)
                if revenue > 0:
                    row[f"{year} %"] = f"{(value/revenue*100):.1f}%"
        
        # Calculate variation if 2 years
        if len(year_data) == 2:
            years = sorted(year_data.keys())
            val1 = year_data[years[0]].get(cat_key, {}).get('total', 0)
            val2 = year_data[years[1]].get(cat_key, {}).get('total', 0)
            
            if val1 > 0:
                variation = ((val2 - val1) / val1) * 100
                row['Variação %'] = f"{variation:+.1f}%"
            else:
                row['Variação %'] = "N/A"
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_single_category_year_comparison(year_data: Dict, category_key: str, category_name: str, chart_type: str, show_percentage: bool):
    """Render comparison of a single category across years"""
    
    st.markdown(f"#### 📂 {category_name}")
    
    # Collect items across all years
    all_items = set()
    for year, data in year_data.items():
        if category_key in data and 'line_items' in data[category_key]:
            all_items.update(data[category_key]['line_items'].keys())
    
    if not all_items:
        st.info(f"Nenhum item encontrado para {category_name}")
        return
    
    # Create comparison visualization
    if chart_type in ["Barras", "Treemap"]:
        fig = go.Figure()
        
        for year in sorted(year_data.keys()):
            items = []
            values = []
            revenue = year_data[year].get('revenue', {}).get('total', 0)
            
            if category_key in year_data[year] and 'line_items' in year_data[year][category_key]:
                for item_key in sorted(all_items):
                    if item_key in year_data[year][category_key]['line_items']:
                        item_data = year_data[year][category_key]['line_items'][item_key]
                        items.append(item_data['label'])
                        values.append(item_data['total'])
                    else:
                        items.append(item_key.replace('_', ' ').title())
                        values.append(0)
            
            fig.add_trace(go.Bar(
                name=str(year),
                x=items,
                y=values,
                text=[f"{format_currency(v)}" for v in values],
                textposition='outside'
            ))
        
        fig.update_layout(
            title=f"Comparação de {category_name} por Ano",
            xaxis_title="Item",
            yaxis_title="Valor (R$)",
            barmode='group',
            height=500,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Show detailed comparison table
    st.markdown("#### 📋 Tabela Detalhada")
    
    table_data = []
    for item_key in sorted(all_items):
        row = {}
        
        # Get item label from first year that has it
        item_label = item_key.replace('_', ' ').title()
        for year, data in year_data.items():
            if category_key in data and 'line_items' in data[category_key]:
                if item_key in data[category_key]['line_items']:
                    item_label = data[category_key]['line_items'][item_key]['label']
                    break
        
        row['Item'] = item_label
        
        for year in sorted(year_data.keys()):
            value = 0
            if category_key in year_data[year] and 'line_items' in year_data[year][category_key]:
                if item_key in year_data[year][category_key]['line_items']:
                    value = year_data[year][category_key]['line_items'][item_key]['total']
            
            row[f"{year}"] = format_currency(value)
            
            if show_percentage:
                revenue = year_data[year].get('revenue', {}).get('total', 0)
                if revenue > 0:
                    row[f"{year} % Receita"] = f"{(value/revenue*100):.2f}%"
        
        # Calculate variation if 2 years
        if len(year_data) == 2:
            years = sorted(year_data.keys())
            val1 = 0
            val2 = 0
            
            if category_key in year_data[years[0]] and 'line_items' in year_data[years[0]][category_key]:
                if item_key in year_data[years[0]][category_key]['line_items']:
                    val1 = year_data[years[0]][category_key]['line_items'][item_key]['total']
            
            if category_key in year_data[years[1]] and 'line_items' in year_data[years[1]][category_key]:
                if item_key in year_data[years[1]][category_key]['line_items']:
                    val2 = year_data[years[1]][category_key]['line_items'][item_key]['total']
            
            if val1 > 0:
                variation = ((val2 - val1) / val1) * 100
                row['Variação %'] = f"{variation:+.1f}%"
            elif val2 > 0:
                row['Variação %'] = "Novo"
            else:
                row['Variação %'] = "-"
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_category_comparison_table(aggregated_data: Dict, revenue_total: float, show_percentage: bool):
    """Render a comparison table of all categories"""
    
    category_map = {
        'fixed_costs': 'Custos Fixos',
        'variable_costs': 'Custos Variáveis',
        'administrative_expenses': 'Despesas Administrativas',
        'marketing_expenses': 'Despesas de Marketing',
        'operational_costs': 'Custos Operacionais',
        'financial_expenses': 'Despesas Financeiras',
        'taxes': 'Impostos',
        'commissions': 'Comissões',
        'non_operational_costs': 'Custos Não Operacionais'
    }
    
    table_data = []
    total_costs = 0
    
    for key, name in category_map.items():
        if key in aggregated_data:
            total = aggregated_data[key].get('total', 0)
            if total > 0:
                total_costs += total
                num_items = len(aggregated_data[key].get('line_items', {}))
                
                row = {
                    'Categoria': name,
                    'Valor Total': format_currency(total),
                    'Número de Itens': num_items,
                    'Média por Item': format_currency(total / num_items) if num_items > 0 else '-'
                }
                
                if show_percentage and revenue_total > 0:
                    row['% da Receita'] = f"{(total / revenue_total * 100):.1f}%"
                
                table_data.append(row)
    
    if table_data:
        # Add total row
        total_row = {
            'Categoria': '**TOTAL**',
            'Valor Total': f"**{format_currency(total_costs)}**",
            'Número de Itens': f"**{sum(len(aggregated_data[k].get('line_items', {})) for k in category_map.keys() if k in aggregated_data)}**",
            'Média por Item': '-'
        }
        
        if show_percentage and revenue_total > 0:
            total_row['% da Receita'] = f"**{(total_costs / revenue_total * 100):.1f}%**"
        
        table_data.append(total_row)
        
        # Create DataFrame and display
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Add margin calculation if revenue is available
        if revenue_total > 0:
            margin = ((revenue_total - total_costs) / revenue_total) * 100
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Margem Operacional", f"{margin:.1f}%")
            with col2:
                st.metric("Lucro/Prejuízo", format_currency(revenue_total - total_costs))
            with col3:
                efficiency = (total_costs / revenue_total) * 100
                st.metric("Eficiência Operacional", f"{efficiency:.1f}%", 
                         help="Percentual da receita consumido por custos (menor é melhor)")