"""
Micro Analysis V2 Tab Renderer
Interactive hierarchical expense analysis with drill-down capabilities
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
from core.extractors.hierarchical_extractor import HierarchicalExtractor
from utils.expense_hierarchy import ExpenseHierarchy
from utils import format_currency
from .native_hierarchy_renderer import render_native_hierarchy_tab
from .visualizations import render_annual_comparison, render_cost_breakdown_by_year
from .category_breakdown import render_category_breakdown
from .selective_comparison import render_selective_comparison


def render_micro_analysis_v2_tab(financial_data: Dict = None):
    """
    Main entry point for the new hierarchical micro analysis tab
    """
    st.header("🔬 Análise Micro V2 - Estrutura Hierárquica Excel")
    
    # Initialize session state for navigation
    if 'hierarchy_level' not in st.session_state:
        st.session_state.hierarchy_level = 1
    if 'hierarchy_path' not in st.session_state:
        st.session_state.hierarchy_path = []
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
    
    # Try to extract data using the new Excel hierarchy extractor
    excel_hierarchy_data = None
    
    # Check if we have file paths to process
    if hasattr(st.session_state, 'file_manager') and st.session_state.file_manager:
        file_paths = st.session_state.file_manager.obter_caminhos_arquivos()
        if file_paths:
            # First try the new Excel hierarchy extractor
            excel_extractor = ExcelHierarchyExtractor()
            excel_hierarchy_data = {}
            
            for file_path in file_paths:
                extracted = excel_extractor.extract_from_excel(file_path)
                excel_hierarchy_data.update(extracted)
            
            # If no data from Excel extractor, fall back to old method
            if not excel_hierarchy_data and (not financial_data or 'hierarchy' not in next(iter(financial_data.values()), {})):
                st.info("📊 Processando dados com extrator alternativo...")
                extractor = HierarchicalExtractor()
                hierarchical_data = {}
                
                for file_path in file_paths:
                    extracted = extractor.extract_from_excel(file_path)
                    hierarchical_data.update(extracted)
                
                if hierarchical_data:
                    financial_data = hierarchical_data
        else:
            if not financial_data:
                st.warning("Nenhum arquivo carregado. Por favor, faça upload de arquivos Excel.")
                return
    elif not financial_data:
        st.warning("Por favor, faça upload de arquivos Excel para análise.")
        return
    
    # Simplified interface - controls moved to individual tabs
    # Remove duplicate filters and navigation for cleaner UX
    
    # Create tabs for different views - enhanced with new features
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏗️ Excel Nativa",
        "📊 Análise por Categoria",
        "🔍 Comparação Seletiva",
        "💡 Insights",
        "📈 Análise Temporal"
    ])
    
    with tab1:
        # Use the native Excel hierarchy if available
        if excel_hierarchy_data:
            render_native_hierarchy_tab(excel_hierarchy_data, excel_hierarchy_data)
        else:
            st.info("Estrutura nativa do Excel não disponível. Faça upload de arquivos Excel.")
    
    with tab2:
        # Category breakdown with revenue percentage
        if excel_hierarchy_data:
            available_years = list(excel_hierarchy_data.keys())
            selected_years = st.multiselect(
                "Selecione os anos para análise",
                available_years,
                default=available_years[-2:] if len(available_years) >= 2 else available_years,
                key="category_years"
            )
            if selected_years:
                render_category_breakdown(excel_hierarchy_data, selected_years)
        else:
            st.info("Análise por categoria requer dados da estrutura nativa do Excel.")
    
    with tab3:
        # Selective comparison
        if excel_hierarchy_data:
            available_years = list(excel_hierarchy_data.keys())
            selected_years = st.multiselect(
                "Selecione os anos para comparação",
                available_years,
                default=available_years[-2:] if len(available_years) >= 2 else available_years,
                key="comparison_years"
            )
            if selected_years:
                render_selective_comparison(excel_hierarchy_data, selected_years)
        else:
            st.info("Comparação seletiva requer dados da estrutura nativa do Excel.")
    
    with tab4:
        if excel_hierarchy_data:
            # Use aggregated data from Excel hierarchy for insights
            aggregated_data = _aggregate_selected_years(excel_hierarchy_data, list(excel_hierarchy_data.keys()))
            _render_insights(aggregated_data)
        else:
            st.info("Insights requerem dados da estrutura nativa do Excel.")
    
    with tab5:
        if excel_hierarchy_data:
            available_years = list(excel_hierarchy_data.keys())
            selected_years = st.multiselect(
                "Selecione os anos para análise temporal",
                available_years,
                default=available_years,
                key="temporal_years"
            )
            if selected_years:
                _render_temporal_analysis(excel_hierarchy_data, selected_years)
        else:
            st.info("Análise temporal requer dados da estrutura nativa do Excel.")


def _render_breadcrumb_navigation():
    """Render breadcrumb navigation for hierarchy levels"""
    if st.session_state.hierarchy_path:
        col1, col2 = st.columns([10, 1])
        
        with col1:
            # Build breadcrumb string
            breadcrumb_parts = ["📊 Todas as Categorias"]
            breadcrumb_parts.extend(st.session_state.hierarchy_path)
            breadcrumb = " › ".join(breadcrumb_parts)
            st.markdown(f"**{breadcrumb}**")
        
        with col2:
            if st.button("↩️ Voltar", key="back_nav"):
                if st.session_state.hierarchy_path:
                    st.session_state.hierarchy_path.pop()
                    st.session_state.hierarchy_level = max(1, st.session_state.hierarchy_level - 1)
                    st.rerun()
    else:
        st.markdown("**📊 Todas as Categorias**")


def _render_filters(financial_data: Dict) -> List[int]:
    """Render filter controls"""
    col1, col2, col3, col4 = st.columns(4)
    
    # Get available years
    available_years = sorted([year for year in financial_data.keys() if isinstance(year, int)])
    
    with col1:
        # Check if we need to update the selection
        if 'micro_v2_year_selection' in st.session_state:
            if st.session_state.micro_v2_year_selection == 'last':
                default_years = [available_years[-1]] if available_years else []
            else:
                default_years = available_years[-3:] if len(available_years) >= 3 else available_years
            del st.session_state.micro_v2_year_selection
        else:
            default_years = available_years[-3:] if len(available_years) >= 3 else available_years
        
        selected_years = st.multiselect(
            "Anos",
            available_years,
            default=default_years,
            key="micro_v2_years"
        )
    
    with col2:
        view_type = st.selectbox(
            "Tipo de Visualização",
            ["Treemap", "Sunburst", "Barras", "Pizza"],
            key="micro_v2_view_type"
        )
    
    with col3:
        # Quick filters
        if st.button("📅 Último Ano"):
            # Use a different key to trigger the change
            st.session_state.micro_v2_year_selection = 'last'
            st.rerun()
    
    with col4:
        if st.button("🔄 Resetar Navegação"):
            st.session_state.hierarchy_level = 1
            st.session_state.hierarchy_path = []
            st.session_state.selected_category = None
            st.rerun()
    
    return selected_years


def _aggregate_selected_years(financial_data: Dict, selected_years: List[int]) -> Dict:
    """Aggregate data for selected years"""
    aggregated = {
        'hierarchy': {},
        'totals': {
            'total_costs': 0,
            'revenue': 0,
            'net_profit': 0
        },
        'all_items': []
    }
    
    for year in selected_years:
        if year not in financial_data:
            continue
        
        year_data = financial_data[year]
        
        # Check if we have hierarchy data or need to process it
        if 'hierarchy' in year_data and isinstance(year_data['hierarchy'], dict):
            # Process hierarchical data
            for main_cat_key, main_cat_data in year_data['hierarchy'].items():
                if main_cat_key not in aggregated['hierarchy']:
                    aggregated['hierarchy'][main_cat_key] = {
                        'name': main_cat_data.get('name', main_cat_key),
                        'total': 0,
                        'subcategories': {},
                        'items': []
                    }
                
                aggregated['hierarchy'][main_cat_key]['total'] += main_cat_data.get('total', 0)
                aggregated['hierarchy'][main_cat_key]['items'].extend(main_cat_data.get('items', []))
                
                # Aggregate subcategories
                for subcat_key, subcat_data in main_cat_data.get('subcategories', {}).items():
                    if subcat_key not in aggregated['hierarchy'][main_cat_key]['subcategories']:
                        aggregated['hierarchy'][main_cat_key]['subcategories'][subcat_key] = {
                            'name': subcat_data.get('name', subcat_key),
                            'total': 0,
                            'detail_categories': {},
                            'items': []
                        }
                    
                    aggregated['hierarchy'][main_cat_key]['subcategories'][subcat_key]['total'] += subcat_data.get('total', 0)
                    aggregated['hierarchy'][main_cat_key]['subcategories'][subcat_key]['items'].extend(subcat_data.get('items', []))
                    
                    # Aggregate detail categories
                    for detail_key, detail_data in subcat_data.get('detail_categories', {}).items():
                        if detail_key not in aggregated['hierarchy'][main_cat_key]['subcategories'][subcat_key]['detail_categories']:
                            aggregated['hierarchy'][main_cat_key]['subcategories'][subcat_key]['detail_categories'][detail_key] = {
                                'name': detail_data.get('name', detail_key),
                                'total': 0,
                                'items': []
                            }
                        
                        aggregated['hierarchy'][main_cat_key]['subcategories'][subcat_key]['detail_categories'][detail_key]['total'] += detail_data.get('total', 0)
                        aggregated['hierarchy'][main_cat_key]['subcategories'][subcat_key]['detail_categories'][detail_key]['items'].extend(detail_data.get('items', []))
        else:
            # Fallback: Process data without hierarchy structure
            # This handles data from the old extractor
            from utils.expense_hierarchy import ExpenseHierarchy
            hierarchy_processor = ExpenseHierarchy()
            
            # Collect all expense items from the year data
            expense_items = []
            
            # Debug: Check what data structure we have
            print(f"Year {year} data keys: {year_data.keys() if isinstance(year_data, dict) else 'Not a dict'}")
            
            # Check for line_items structure (flexible extractor format)
            if 'line_items' in year_data and isinstance(year_data['line_items'], dict):
                for category, category_data in year_data['line_items'].items():
                    if isinstance(category_data, dict):
                        # Check if it has line_items sub-structure
                        if 'line_items' in category_data:
                            # This is the unified extractor format
                            for item_key, item_data in category_data['line_items'].items():
                                if isinstance(item_data, dict):
                                    value = item_data.get('annual', 0)
                                    if value > 0:
                                        expense_items.append({
                                            'label': item_data.get('label', item_key),
                                            'value': value,
                                            'annual': value
                                        })
                        else:
                            # Simple key-value format
                            for item_key, item_value in category_data.items():
                                if isinstance(item_value, (int, float)) and item_value > 0:
                                    expense_items.append({
                                        'label': item_key,
                                        'value': item_value,
                                        'annual': item_value
                                    })
            
            # Check for standard cost categories (unified extractor format)
            cost_categories = ['fixed_costs', 'variable_costs', 'non_operational_costs', 
                             'administrative_expenses', 'marketing_expenses', 'financial_expenses',
                             'operational_costs', 'taxes', 'commissions']
            
            for category in cost_categories:
                if category in year_data:
                    cat_data = year_data[category]
                    if isinstance(cat_data, dict):
                        # Check for line_items within the category
                        if 'line_items' in cat_data and isinstance(cat_data['line_items'], dict):
                            for item_key, item_data in cat_data['line_items'].items():
                                if isinstance(item_data, dict):
                                    value = item_data.get('annual', 0)
                                    label = item_data.get('label', item_key)
                                    if value > 0:
                                        expense_items.append({
                                            'label': label,
                                            'value': value,
                                            'annual': value,
                                            'source_category': category
                                        })
                        # Also check for annual total
                        elif cat_data.get('annual', 0) > 0:
                            expense_items.append({
                                'label': category.replace('_', ' ').title(),
                                'value': cat_data['annual'],
                                'annual': cat_data['annual'],
                                'source_category': category
                            })
                    elif isinstance(cat_data, (int, float)) and cat_data > 0:
                        expense_items.append({
                            'label': category.replace('_', ' ').title(),
                            'value': cat_data,
                            'annual': cat_data,
                            'source_category': category
                        })
            
            # Debug: Show collected items
            print(f"Year {year}: Found {len(expense_items)} expense items")
            if expense_items:
                print(f"Sample items: {expense_items[:3]}")
            
            # Process expense items through hierarchy
            for expense in expense_items:
                parsed = hierarchy_processor.parse_expense_item(expense['label'])
                
                # If it falls into non-operational by default, try using source category
                if parsed['main_category'] == 'custos_nao_operacionais' and 'source_category' in expense:
                    alt_parsed = hierarchy_processor._classify_by_source_category(expense['source_category'], expense['label'])
                    if alt_parsed['main_category'] != 'custos_nao_operacionais':
                        parsed = alt_parsed
                
                # Add to hierarchy structure
                main_cat = parsed['main_category']
                if main_cat not in aggregated['hierarchy']:
                    aggregated['hierarchy'][main_cat] = {
                        'name': parsed['main_category_name'],
                        'total': 0,
                        'subcategories': {},
                        'items': []
                    }
                
                aggregated['hierarchy'][main_cat]['total'] += expense['annual']
                
                # Create full item record
                item = {
                    'label': expense['label'],
                    'annual': expense['annual'],
                    'parsed': parsed,
                    'hierarchy_path': hierarchy_processor.get_hierarchy_path(parsed)
                }
                
                aggregated['hierarchy'][main_cat]['items'].append(item)
                aggregated['all_items'].append(item)
                
                # Add to subcategory
                subcat = parsed['subcategory']
                if subcat not in aggregated['hierarchy'][main_cat]['subcategories']:
                    aggregated['hierarchy'][main_cat]['subcategories'][subcat] = {
                        'name': parsed['subcategory_name'],
                        'total': 0,
                        'detail_categories': {},
                        'items': []
                    }
                
                aggregated['hierarchy'][main_cat]['subcategories'][subcat]['total'] += expense['annual']
                aggregated['hierarchy'][main_cat]['subcategories'][subcat]['items'].append(item)
        
        # Aggregate totals
        # First try to get from totals
        if 'totals' in year_data and isinstance(year_data['totals'], dict):
            aggregated['totals']['total_costs'] += year_data['totals'].get('total_costs', 0)
        
        # If no totals or zero, calculate from categories
        if aggregated['totals']['total_costs'] == 0:
            # Calculate from hierarchy if we have it
            if aggregated['hierarchy']:
                for main_cat in aggregated['hierarchy'].values():
                    aggregated['totals']['total_costs'] += main_cat.get('total', 0)
        
        # Handle revenue
        if 'revenue' in year_data:
            if isinstance(year_data['revenue'], dict):
                aggregated['totals']['revenue'] += year_data['revenue'].get('annual', 0)
            elif isinstance(year_data['revenue'], (int, float)):
                aggregated['totals']['revenue'] += year_data['revenue']
        
        # Aggregate all items (if not already done)
        if 'all_items' in year_data:
            aggregated['all_items'].extend(year_data.get('all_items', []))
    
    # Calculate average values if multiple years
    if len(selected_years) > 1:
        num_years = len(selected_years)
        aggregated['totals']['avg_costs'] = aggregated['totals']['total_costs'] / num_years
        aggregated['totals']['avg_revenue'] = aggregated['totals']['revenue'] / num_years
    
    return aggregated


def _render_kpi_cards(aggregated_data: Dict):
    """Render KPI metric cards"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_costs = aggregated_data['totals']['total_costs']
        st.metric(
            "💰 Total de Custos",
            format_currency(total_costs)
        )
    
    with col2:
        revenue = aggregated_data['totals'].get('revenue', 0)
        if revenue > 0:
            margin = ((revenue - total_costs) / revenue) * 100
            st.metric(
                "📊 Margem",
                f"{margin:.1f}%",
                delta=f"{margin - 30:.1f}%" if margin != 30 else None
            )
    
    with col3:
        fixed_costs = aggregated_data['hierarchy'].get('custos_fixos', {}).get('total', 0)
        st.metric(
            "📌 Custos Fixos",
            format_currency(fixed_costs),
            help="Total de custos fixos"
        )
    
    with col4:
        variable_costs = aggregated_data['hierarchy'].get('custos_variaveis', {}).get('total', 0)
        st.metric(
            "📈 Custos Variáveis",
            format_currency(variable_costs),
            help="Total de custos variáveis"
        )
    
    with col5:
        num_items = len(aggregated_data['all_items'])
        st.metric(
            "📋 Itens",
            f"{num_items:,}",
            help="Total de itens de despesa"
        )


def _render_hierarchical_view(aggregated_data: Dict):
    """Render the main hierarchical visualization"""
    st.markdown("### 📊 Visualização Hierárquica")
    
    # Get current level data based on navigation
    current_data = _get_current_level_data(aggregated_data)
    
    if not current_data:
        st.warning("Nenhum dado disponível para este nível.")
        return
    
    # Choose visualization based on user selection
    view_type = st.session_state.get('micro_v2_view_type', 'Treemap')
    
    if view_type == "Treemap":
        _render_treemap(current_data)
    elif view_type == "Sunburst":
        _render_sunburst(aggregated_data)
    elif view_type == "Barras":
        _render_bar_chart(current_data)
    elif view_type == "Pizza":
        _render_pie_chart(current_data)


def _get_current_level_data(aggregated_data: Dict) -> List[Dict]:
    """Get data for current hierarchy level"""
    data = []
    hierarchy = aggregated_data['hierarchy']
    
    if st.session_state.hierarchy_level == 1:
        # Main categories
        for cat_key, cat_data in hierarchy.items():
            data.append({
                'id': cat_key,
                'name': cat_data['name'],
                'value': cat_data['total'],
                'item_count': len(cat_data['items'])
            })
    
    elif st.session_state.hierarchy_level == 2 and st.session_state.hierarchy_path:
        # Subcategories
        main_cat = st.session_state.hierarchy_path[0]
        if main_cat in hierarchy:
            for subcat_key, subcat_data in hierarchy[main_cat]['subcategories'].items():
                data.append({
                    'id': subcat_key,
                    'name': subcat_data['name'],
                    'value': subcat_data['total'],
                    'item_count': len(subcat_data['items'])
                })
    
    elif st.session_state.hierarchy_level == 3 and len(st.session_state.hierarchy_path) >= 2:
        # Detail categories
        main_cat = st.session_state.hierarchy_path[0]
        subcat = st.session_state.hierarchy_path[1]
        if main_cat in hierarchy and subcat in hierarchy[main_cat]['subcategories']:
            subcat_data = hierarchy[main_cat]['subcategories'][subcat]
            
            # Show detail categories if they exist
            if subcat_data.get('detail_categories'):
                for detail_key, detail_data in subcat_data['detail_categories'].items():
                    data.append({
                        'id': detail_key,
                        'name': detail_data['name'],
                        'value': detail_data['total'],
                        'item_count': len(detail_data['items'])
                    })
            else:
                # Show individual items
                for item in subcat_data['items']:
                    data.append({
                        'id': item['label'],
                        'name': item['label'],
                        'value': item['annual'],
                        'item_count': 1
                    })
    
    elif st.session_state.hierarchy_level == 4 and len(st.session_state.hierarchy_path) >= 3:
        # Individual items
        main_cat = st.session_state.hierarchy_path[0]
        subcat = st.session_state.hierarchy_path[1]
        detail_cat = st.session_state.hierarchy_path[2]
        
        if (main_cat in hierarchy and 
            subcat in hierarchy[main_cat]['subcategories'] and
            detail_cat in hierarchy[main_cat]['subcategories'][subcat]['detail_categories']):
            
            detail_data = hierarchy[main_cat]['subcategories'][subcat]['detail_categories'][detail_cat]
            for item in detail_data['items']:
                data.append({
                    'id': item['label'],
                    'name': item['label'],
                    'value': item['annual'],
                    'item_count': 1
                })
    
    return data


def _render_treemap(data: List[Dict]):
    """Render treemap visualization"""
    if not data:
        return
    
    # Prepare data for treemap
    labels = [d['name'] for d in data]
    values = [d['value'] for d in data]
    ids = [d['id'] for d in data]
    
    # Create color scale
    colors = px.colors.qualitative.Set3[:len(data)]
    
    fig = go.Figure(go.Treemap(
        labels=labels,
        values=values,
        ids=ids,
        parents=[""] * len(data),
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent} do total<extra></extra>',
        marker=dict(colors=colors),
        textposition="middle center"
    ))
    
    fig.update_layout(
        height=500,
        margin=dict(t=30, b=0, l=0, r=0)
    )
    
    # Handle click events
    selected = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="treemap_hierarchy"
    )
    
    if selected and selected["selection"]["points"]:
        selected_id = selected["selection"]["points"][0]["id"]
        _handle_category_selection(selected_id)


def _render_sunburst(aggregated_data: Dict):
    """Render sunburst chart showing full hierarchy"""
    labels = []
    parents = []
    values = []
    ids = []
    
    # Add main categories
    for main_key, main_data in aggregated_data['hierarchy'].items():
        labels.append(main_data['name'])
        parents.append("")
        values.append(main_data['total'])
        ids.append(main_key)
        
        # Add subcategories
        for sub_key, sub_data in main_data['subcategories'].items():
            labels.append(sub_data['name'])
            parents.append(main_key)
            values.append(sub_data['total'])
            ids.append(f"{main_key}.{sub_key}")
            
            # Add detail categories
            for detail_key, detail_data in sub_data.get('detail_categories', {}).items():
                labels.append(detail_data['name'])
                parents.append(f"{main_key}.{sub_key}")
                values.append(detail_data['total'])
                ids.append(f"{main_key}.{sub_key}.{detail_key}")
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        ids=ids,
        branchvalues="total",
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent} do pai<extra></extra>'
    ))
    
    fig.update_layout(
        height=600,
        margin=dict(t=30, b=0, l=0, r=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_bar_chart(data: List[Dict]):
    """Render bar chart visualization"""
    if not data:
        return
    
    # Sort data by value
    data_sorted = sorted(data, key=lambda x: x['value'], reverse=True)
    
    # Prepare data
    categories = [d['name'] for d in data_sorted]
    values = [d['value'] for d in data_sorted]
    
    fig = go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation='h',
        text=[format_currency(v) for v in values],
        textposition='outside',
        marker=dict(color=px.colors.qualitative.Set3[:len(data_sorted)])
    ))
    
    fig.update_layout(
        height=max(400, len(categories) * 40),
        margin=dict(l=200, r=100, t=30, b=30),
        xaxis=dict(title="Valor (R$)"),
        yaxis=dict(title="")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add click instruction
    category_select = st.selectbox(
        "Selecione uma categoria para drill-down:",
        [""] + [d['id'] for d in data_sorted],
        format_func=lambda x: next((d['name'] for d in data if d['id'] == x), x) if x else "Escolha...",
        key="bar_select"
    )
    
    if category_select:
        _handle_category_selection(category_select)


def _render_pie_chart(data: List[Dict]):
    """Render pie chart visualization"""
    if not data:
        return
    
    # Prepare data
    labels = [d['name'] for d in data]
    values = [d['value'] for d in data]
    
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        texttemplate='%{label}<br>%{percent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        height=500,
        margin=dict(t=30, b=30, l=30, r=30)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _handle_category_selection(selected_id: str):
    """Handle category selection for drill-down"""
    if selected_id:
        st.session_state.hierarchy_path.append(selected_id)
        st.session_state.hierarchy_level = min(4, st.session_state.hierarchy_level + 1)
        st.session_state.selected_category = selected_id
        st.rerun()


def _render_temporal_analysis(financial_data: Dict, selected_years: List[int]):
    """Render temporal analysis of expenses"""
    st.markdown("### 📈 Análise Temporal")
    
    # Prepare time series data
    time_data = []
    
    for year in sorted(selected_years):
        if year not in financial_data:
            continue
        
        year_data = financial_data[year]
        
        # Get monthly data if available
        if 'monthly_data' in year_data:
            for month, month_data in year_data['monthly_data'].items():
                for cat_key, value in month_data.items():
                    if cat_key in year_data.get('hierarchy', {}):
                        cat_name = year_data['hierarchy'][cat_key].get('name', cat_key)
                        time_data.append({
                            'Ano': year,
                            'Mês': month,
                            'Categoria': cat_name,
                            'Valor': value
                        })
    
    if not time_data:
        st.info("Dados mensais não disponíveis para análise temporal.")
        return
    
    df_time = pd.DataFrame(time_data)
    
    # Create line chart
    fig = px.line(
        df_time.groupby(['Ano', 'Mês', 'Categoria'])['Valor'].sum().reset_index(),
        x='Mês',
        y='Valor',
        color='Categoria',
        facet_col='Ano',
        title='Evolução Mensal por Categoria',
        labels={'Valor': 'Valor (R$)', 'Mês': 'Mês'},
        markers=True
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)



def _render_insights(aggregated_data: Dict):
    """Render insights and analysis"""
    st.markdown("### 💡 Insights Automáticos")
    
    hierarchy = ExpenseHierarchy()
    insights = hierarchy.get_insights(aggregated_data['all_items'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Distribuição de Custos")
        
        # Show distribution
        for cat_name, cat_info in insights['distribution'].items():
            st.progress(cat_info['percentage'] / 100)
            st.write(f"**{cat_name}**: {cat_info['percentage']:.1f}% ({format_currency(cat_info['value'])})")
    
    with col2:
        st.markdown("#### 🎯 Principais Categorias")
        
        # Show top categories
        for i, (cat_key, cat_data) in enumerate(insights['top_categories'].items(), 1):
            st.write(f"{i}. **{cat_data['name']}**: {format_currency(cat_data['value'])} ({cat_data['count']} itens)")
    
    # Show uncategorized items if any
    if insights['uncategorized_items']:
        st.markdown("#### ⚠️ Itens Não Categorizados")
        st.warning(f"Encontrados {len(insights['uncategorized_items'])} itens que precisam de melhor categorização.")
        
        with st.expander("Ver itens não categorizados"):
            for item in insights['uncategorized_items'][:20]:
                st.write(f"- {item['label']}: {format_currency(item.get('value', 0))}")


def _render_detailed_table(aggregated_data: Dict):
    """Render detailed expense table"""
    st.markdown("### 📋 Tabela Detalhada")
    
    # Prepare data for table
    table_data = []
    
    for item in aggregated_data['all_items']:
        if 'parsed' in item:
            parsed = item['parsed']
            table_data.append({
                'Item': item['label'],
                'Categoria Principal': parsed.get('main_category_name', ''),
                'Subcategoria': parsed.get('subcategory_name', ''),
                'Detalhe': parsed.get('detail_category', '').title() if parsed.get('detail_category') else '',
                'Valor': item['annual']
            })
        else:
            table_data.append({
                'Item': item['label'],
                'Categoria Principal': '',
                'Subcategoria': '',
                'Detalhe': '',
                'Valor': item.get('annual', 0)
            })
    
    if not table_data:
        st.info("Nenhum item para exibir.")
        return
    
    df_table = pd.DataFrame(table_data)
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Category filter
        categories = df_table['Categoria Principal'].unique()
        selected_cat = st.selectbox(
            "Filtrar por categoria:",
            ["Todas"] + list(categories),
            key="table_cat_filter"
        )
        
        if selected_cat != "Todas":
            df_table = df_table[df_table['Categoria Principal'] == selected_cat]
    
    with col2:
        # Value filter
        min_value = st.number_input(
            "Valor mínimo:",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="table_min_value"
        )
        
        df_table = df_table[df_table['Valor'] >= min_value]
    
    with col3:
        # Search
        search = st.text_input("🔍 Buscar:", key="table_search")
        if search:
            mask = df_table['Item'].str.contains(search, case=False, na=False)
            df_table = df_table[mask]
    
    # Sort by value
    df_table = df_table.sort_values('Valor', ascending=False)
    
    # Format for display
    df_display = df_table.copy()
    df_display['Valor'] = df_display['Valor'].apply(format_currency)
    
    # Display table
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Item": st.column_config.TextColumn("Item", width="large"),
            "Valor": st.column_config.TextColumn("Valor", width="medium")
        }
    )
    
    # Export button
    if st.button("📥 Exportar para CSV", key="export_table"):
        csv = df_table.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"despesas_hierarquicas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )