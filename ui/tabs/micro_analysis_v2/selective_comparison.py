"""
Selective Comparison Component
Allows users to select specific expenses to compare
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any, Set
from utils import format_currency

def render_selective_comparison(financial_data: Dict, selected_years: List[int]):
    """
    Render interface for selecting and comparing specific expenses
    """
    st.header("🔍 Comparação Seletiva de Despesas")
    
    if not financial_data or not selected_years:
        st.info("Selecione anos para realizar comparações.")
        return
    
    # Aggregate data
    aggregated_data = _aggregate_years_data(financial_data, selected_years)
    
    if not aggregated_data:
        st.warning("Nenhum dado disponível para os anos selecionados.")
        return
    
    # Get all available expense items
    all_items = _get_all_expense_items(aggregated_data)
    
    if not all_items:
        st.warning("Nenhuma despesa encontrada para comparação.")
        return
    
    # Get revenue for percentage calculations
    revenue_total = aggregated_data.get('revenue', {}).get('total', 0)
    
    # Selection interface
    st.markdown("### 🎯 Seleção de Despesas")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"📊 Total de {len(all_items)} despesas disponíveis para comparação")
    
    with col2:
        if st.button("🔄 Limpar Seleção"):
            st.session_state.selected_expenses = set()
            st.rerun()
    
    # Initialize selected expenses in session state
    if 'selected_expenses' not in st.session_state:
        st.session_state.selected_expenses = set()
    
    # Filter and search options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Category filter
        categories = list(set(item['category'] for item in all_items))
        selected_categories = st.multiselect(
            "Filtrar por Categoria",
            categories,
            default=categories,
            key="category_filter"
        )
    
    with col2:
        # Value range filter
        min_value = st.number_input(
            "Valor Mínimo",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="min_value_filter"
        )
    
    with col3:
        # Search
        search_term = st.text_input(
            "🔍 Buscar despesa",
            key="expense_search"
        )
    
    # Apply filters
    filtered_items = [
        item for item in all_items
        if item['category'] in selected_categories
        and item['value'] >= min_value
        and (not search_term or search_term.lower() in item['label'].lower())
    ]
    
    # Sort options
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox(
            "Ordenar por",
            ["Valor (Maior → Menor)", "Valor (Menor → Maior)", "Nome (A → Z)", "Nome (Z → A)"],
            key="sort_option"
        )
    
    # Apply sorting
    if sort_by == "Valor (Maior → Menor)":
        filtered_items.sort(key=lambda x: x['value'], reverse=True)
    elif sort_by == "Valor (Menor → Maior)":
        filtered_items.sort(key=lambda x: x['value'])
    elif sort_by == "Nome (A → Z)":
        filtered_items.sort(key=lambda x: x['label'])
    else:
        filtered_items.sort(key=lambda x: x['label'], reverse=True)
    
    # Display items for selection
    st.markdown("### 📋 Selecione as Despesas para Comparar")
    
    # Quick selection buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("✅ Selecionar Top 10"):
            top_10 = sorted(filtered_items, key=lambda x: x['value'], reverse=True)[:10]
            for item in top_10:
                st.session_state.selected_expenses.add(item['id'])
            st.rerun()
    
    with col2:
        if st.button("📊 Selecionar Maiores de Cada Categoria"):
            category_tops = {}
            for item in filtered_items:
                if item['category'] not in category_tops or item['value'] > category_tops[item['category']]['value']:
                    category_tops[item['category']] = item
            for item in category_tops.values():
                st.session_state.selected_expenses.add(item['id'])
            st.rerun()
    
    # Display selection grid
    items_per_page = 20
    total_pages = (len(filtered_items) - 1) // items_per_page + 1 if filtered_items else 1
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # Pagination controls
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀ Anterior") and st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()
        with col2:
            st.write(f"Página {st.session_state.current_page} de {total_pages}")
        with col3:
            if st.button("Próxima ▶") and st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()
    
    # Display items for current page
    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_items))
    
    for item in filtered_items[start_idx:end_idx]:
        col1, col2, col3, col4 = st.columns([0.5, 3, 2, 2])
        
        with col1:
            is_selected = item['id'] in st.session_state.selected_expenses
            if st.checkbox("", value=is_selected, key=f"select_{item['id']}"):
                st.session_state.selected_expenses.add(item['id'])
            else:
                st.session_state.selected_expenses.discard(item['id'])
        
        with col2:
            st.write(f"**{item['label']}**")
            st.caption(item['category'])
        
        with col3:
            st.write(format_currency(item['value']))
        
        with col4:
            if revenue_total > 0:
                percentage = (item['value'] / revenue_total) * 100
                st.write(f"{percentage:.2f}% da receita")
    
    # Show selected items count
    st.markdown("---")
    st.info(f"✅ {len(st.session_state.selected_expenses)} despesas selecionadas")
    
    # Render comparison if items are selected
    if st.session_state.selected_expenses:
        selected_items = [
            item for item in all_items 
            if item['id'] in st.session_state.selected_expenses
        ]
        
        st.markdown("---")
        st.markdown("### 📊 Visualização Comparativa")
        
        # Visualization options
        col1, col2, col3 = st.columns(3)
        with col1:
            viz_type = st.selectbox(
                "Tipo de Visualização",
                ["Barras Horizontais", "Barras Verticais", "Pizza", "Treemap", "Radar"],
                key="comparison_viz_type"
            )
        
        with col2:
            show_percentage = st.checkbox(
                "Mostrar % da Receita",
                value=True,
                key="comparison_show_percentage"
            )
        
        with col3:
            group_by_category = st.checkbox(
                "Agrupar por Categoria",
                value=False,
                key="comparison_group_by_category"
            )
        
        # Render selected visualization
        _render_comparison_visualization(
            selected_items,
            revenue_total,
            viz_type,
            show_percentage,
            group_by_category
        )
        
        # Summary statistics
        st.markdown("---")
        st.markdown("### 📈 Resumo da Seleção")
        _render_selection_summary(selected_items, revenue_total)
        
        # Export option
        st.markdown("---")
        if st.button("📥 Exportar Comparação para CSV"):
            df = _create_comparison_dataframe(selected_items, revenue_total)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="comparacao_despesas.csv",
                mime="text/csv"
            )


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
                        aggregated['revenue'] = {'total': 0}
                    aggregated['revenue']['total'] += section.get('value', 0)
                
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
                                    'total': 0
                                }
                            
                            aggregated[category_key]['line_items'][item_key]['total'] += item.get('value', 0)
                        
                        # Also add subcategory itself if it has no items
                        if not subcat.get('items'):
                            subcat_name = subcat.get('name', '')
                            subcat_key = subcat_name.lower().replace(' ', '_')
                            
                            if subcat_key not in aggregated[category_key]['line_items']:
                                aggregated[category_key]['line_items'][subcat_key] = {
                                    'label': subcat_name,
                                    'total': 0
                                }
                            
                            aggregated[category_key]['line_items'][subcat_key]['total'] += subcat.get('value', 0)
        
        # Process revenue (old format support)
        elif 'revenue' in year_data:
            if 'revenue' not in aggregated:
                aggregated['revenue'] = {'total': 0}
            
            if isinstance(year_data['revenue'], dict):
                aggregated['revenue']['total'] += year_data['revenue'].get('annual', 0)
            else:
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
                    aggregated[category]['total'] += cat_data.get('annual', 0)
                    
                    if 'line_items' in cat_data:
                        for item_key, item_data in cat_data['line_items'].items():
                            if item_key not in aggregated[category]['line_items']:
                                aggregated[category]['line_items'][item_key] = {
                                    'label': item_data.get('label', item_key),
                                    'total': 0
                                }
                            aggregated[category]['line_items'][item_key]['total'] += item_data.get('annual', 0)
    
    return aggregated


def _get_all_expense_items(aggregated_data: Dict) -> List[Dict]:
    """Get all expense items from aggregated data"""
    items = []
    
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
    
    for cat_key, cat_name in category_names.items():
        if cat_key in aggregated_data:
            for item_key, item_data in aggregated_data[cat_key].get('line_items', {}).items():
                if item_data.get('total', 0) > 0:
                    items.append({
                        'id': f"{cat_key}_{item_key}",
                        'label': item_data.get('label', item_key),
                        'category': cat_name,
                        'value': item_data.get('total', 0)
                    })
    
    return items


def _render_comparison_visualization(
    selected_items: List[Dict],
    revenue_total: float,
    viz_type: str,
    show_percentage: bool,
    group_by_category: bool
):
    """Render visualization for selected items comparison"""
    
    if group_by_category:
        # Group items by category
        grouped_data = {}
        for item in selected_items:
            category = item['category']
            if category not in grouped_data:
                grouped_data[category] = {
                    'value': 0,
                    'items': []
                }
            grouped_data[category]['value'] += item['value']
            grouped_data[category]['items'].append(item)
        
        # Create visualization data
        labels = list(grouped_data.keys())
        values = [grouped_data[cat]['value'] for cat in labels]
        
        if show_percentage and revenue_total > 0:
            percentages = [(v / revenue_total * 100) for v in values]
            text_labels = [f"{format_currency(v)}<br>({p:.1f}% da receita)" 
                          for v, p in zip(values, percentages)]
        else:
            text_labels = [format_currency(v) for v in values]
    else:
        # Use individual items
        labels = [item['label'] for item in selected_items]
        values = [item['value'] for item in selected_items]
        categories = [item['category'] for item in selected_items]
        
        if show_percentage and revenue_total > 0:
            percentages = [(v / revenue_total * 100) for v in values]
            text_labels = [f"{format_currency(v)}<br>({p:.1f}% da receita)" 
                          for v, p in zip(values, percentages)]
        else:
            text_labels = [format_currency(v) for v in values]
    
    # Create visualization based on type
    if viz_type == "Barras Horizontais":
        fig = go.Figure()
        
        # Sort by value for better visualization
        sorted_data = sorted(zip(labels, values, text_labels), key=lambda x: x[1])
        labels, values, text_labels = zip(*sorted_data)
        
        fig.add_trace(go.Bar(
            y=labels,
            x=values,
            orientation='h',
            text=text_labels,
            textposition='outside',
            marker_color=px.colors.qualitative.Set3[:len(labels)],
            hovertemplate='<b>%{y}</b><br>Valor: R$ %{x:,.0f}<br>%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Comparação de Despesas Selecionadas",
            xaxis_title="Valor (R$)",
            yaxis_title="",
            height=max(400, len(labels) * 30),
            showlegend=False
        )
    
    elif viz_type == "Barras Verticais":
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=labels,
            y=values,
            text=text_labels,
            textposition='outside',
            marker_color=px.colors.qualitative.Set3[:len(labels)],
            hovertemplate='<b>%{x}</b><br>Valor: R$ %{y:,.0f}<br>%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Comparação de Despesas Selecionadas",
            xaxis_title="",
            yaxis_title="Valor (R$)",
            height=500,
            showlegend=False,
            xaxis_tickangle=-45
        )
    
    elif viz_type == "Pizza":
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            texttemplate='<b>%{label}</b><br>%{percent}',
            hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Distribuição das Despesas Selecionadas",
            height=500
        )
    
    elif viz_type == "Treemap":
        if group_by_category:
            # Create hierarchical structure
            treemap_labels = []
            treemap_parents = []
            treemap_values = []
            
            for category, data in grouped_data.items():
                # Add category
                treemap_labels.append(category)
                treemap_parents.append("")
                treemap_values.append(data['value'])
                
                # Add items within category
                for item in data['items']:
                    treemap_labels.append(item['label'])
                    treemap_parents.append(category)
                    treemap_values.append(item['value'])
        else:
            treemap_labels = labels
            treemap_parents = [""] * len(labels)
            treemap_values = values
        
        fig = go.Figure(go.Treemap(
            labels=treemap_labels,
            parents=treemap_parents,
            values=treemap_values,
            texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
            hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent}<extra></extra>',
            marker=dict(colors=px.colors.qualitative.Set3[:len(treemap_labels)])
        ))
        
        fig.update_layout(
            title="Mapa de Despesas Selecionadas",
            height=500
        )
    
    else:  # Radar
        # Normalize values for radar chart
        max_value = max(values) if values else 1
        normalized_values = [v / max_value * 100 for v in values]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=normalized_values,
            theta=labels,
            fill='toself',
            name='Despesas',
            hovertemplate='<b>%{theta}</b><br>Valor: R$ %{customdata:,.0f}<br>%{r:.1f}% do máximo<extra></extra>',
            customdata=values
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="Comparação Radar das Despesas",
            height=500,
            showlegend=False
        )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_selection_summary(selected_items: List[Dict], revenue_total: float):
    """Render summary statistics for selected items"""
    
    total_selected = sum(item['value'] for item in selected_items)
    
    # Group by category
    category_totals = {}
    for item in selected_items:
        category = item['category']
        if category not in category_totals:
            category_totals[category] = 0
        category_totals[category] += item['value']
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Selecionado", format_currency(total_selected))
    
    with col2:
        if revenue_total > 0:
            percentage = (total_selected / revenue_total) * 100
            st.metric("% da Receita", f"{percentage:.1f}%")
    
    with col3:
        avg_value = total_selected / len(selected_items) if selected_items else 0
        st.metric("Média por Item", format_currency(avg_value))
    
    with col4:
        st.metric("Categorias", len(category_totals))
    
    # Category breakdown
    if category_totals:
        st.markdown("#### Distribuição por Categoria")
        
        category_df = pd.DataFrame([
            {
                'Categoria': cat,
                'Valor': format_currency(value),
                '% do Total Selecionado': f"{(value / total_selected * 100):.1f}%",
                '% da Receita': f"{(value / revenue_total * 100):.1f}%" if revenue_total > 0 else "N/A"
            }
            for cat, value in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        ])
        
        st.dataframe(category_df, use_container_width=True, hide_index=True)


def _create_comparison_dataframe(selected_items: List[Dict], revenue_total: float) -> pd.DataFrame:
    """Create DataFrame for export"""
    
    data = []
    for item in selected_items:
        row = {
            'Despesa': item['label'],
            'Categoria': item['category'],
            'Valor': item['value']
        }
        
        if revenue_total > 0:
            row['% da Receita'] = (item['value'] / revenue_total * 100)
        
        data.append(row)
    
    return pd.DataFrame(data)