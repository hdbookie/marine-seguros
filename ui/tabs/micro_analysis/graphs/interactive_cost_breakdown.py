"""
Interactive Cost Breakdown with Drill-Down Functionality
Provides hierarchical exploration of costs with focus on detailed breakdowns
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from utils import format_currency
from utils.expense_categorizer import classify_expense_subcategory, get_expense_subcategories
from ..config import COLORS, CHART_PALETTES


def render_interactive_cost_breakdown(financial_df, flexible_data, full_width=True):
    """
    Render interactive cost breakdown with drill-down capabilities
    
    Args:
        financial_df: DataFrame with financial data
        flexible_data: Dictionary with detailed financial data by year
        full_width: Whether to use full width display
    """
    st.markdown("### 💰 Análise Hierárquica de Custos")
    
    # Initialize session state for navigation
    if 'cost_hierarchy_path' not in st.session_state:
        st.session_state.cost_hierarchy_path = []
    
    # Render breadcrumb navigation
    _render_breadcrumb_navigation()
    
    # Process and categorize all expenses
    categorized_data = _categorize_expenses(financial_df, flexible_data)
    
    if not categorized_data:
        st.warning("Nenhum dado de custo encontrado para análise hierárquica.")
        return
    
    # Get current level data based on navigation path
    current_level_data = _get_current_level_data(categorized_data, st.session_state.cost_hierarchy_path)
    
    # Render summary cards
    _render_summary_cards(current_level_data, flexible_data)
    
    # Create two columns for visualization and details
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Render interactive visualization
        _render_interactive_visualization(current_level_data, full_width)
    
    with col2:
        # Render detail panel
        _render_detail_panel(current_level_data)
    
    # Render detailed table
    st.markdown("---")
    _render_detail_table(current_level_data)
    
    # Debug mode to see uncategorized items
    if st.checkbox("🔍 Ver itens não categorizados", key="show_uncategorized"):
        _show_uncategorized_debug(categorized_data)
    
    # Debug mode to check commission data structure
    if st.checkbox("🔍 Debug: Ver estrutura de comissões", key="debug_commissions"):
        _debug_commission_structure(flexible_data)
    
    # Debug mode to check totals
    if st.checkbox("🔍 Debug: Ver totais por categoria", key="debug_totals"):
        _debug_category_totals(flexible_data, categorized_data)
    
    # Complete line items table
    if st.checkbox("📋 Ver todos os itens de linha", key="show_all_line_items"):
        _show_complete_line_items_table(flexible_data)


def _render_breadcrumb_navigation():
    """Render breadcrumb navigation for hierarchy"""
    if st.session_state.cost_hierarchy_path:
        breadcrumb_parts = ["Custos"] + st.session_state.cost_hierarchy_path
        breadcrumb_str = " > ".join(breadcrumb_parts)
        
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(f"**📍 {breadcrumb_str}**")
        with col2:
            if st.button("↩️ Voltar", key="back_button"):
                st.session_state.cost_hierarchy_path.pop()
                st.rerun()
    else:
        st.markdown("**📍 Custos**")


def _categorize_expenses(financial_df, flexible_data):
    """
    Categorize all expenses using universal data when available
    Returns hierarchical structure of categorized expenses
    """
    categorized_data = {}
    subcategories = get_expense_subcategories()
    
    for year in sorted(financial_df['year'].unique()):
        if year not in flexible_data:
            continue
            
        year_data = flexible_data[year]
        categorized_data[year] = {
            'categories': {},
            'uncategorized': []
        }
        
        # Temporarily skip universal data processing to use main categories only
        # This prevents double counting until universal extractor is fully debugged
        if False and 'universal_data' in year_data and year_data['universal_data']:
            # Use universal data for complete line item capture
            universal = year_data['universal_data']
            
            # Process categorized items from universal data
            for category, items in universal.get('categorized_items', {}).items():
                # Skip revenue items - we only want costs/expenses
                if category == 'revenue':
                    continue
                    
                # Map category names to our display names
                display_category = _map_universal_category(category)
                
                if display_category not in categorized_data[year]['categories']:
                    categorized_data[year]['categories'][display_category] = {
                        'name': _get_category_display_name(display_category),
                        'total': 0,
                        'subcategories': {}
                    }
                
                # Process each item
                for item_key, item_data in items.items():
                    # Add to appropriate subcategory
                    subcat_key = f"{category}_items"
                    if subcat_key not in categorized_data[year]['categories'][display_category]['subcategories']:
                        categorized_data[year]['categories'][display_category]['subcategories'][subcat_key] = {
                            'name': category.replace('_', ' ').title(),
                            'total': 0,
                            'items': []
                        }
                    
                    # Add the item
                    categorized_data[year]['categories'][display_category]['subcategories'][subcat_key]['items'].append({
                        'label': item_data['label'],
                        'value': item_data['annual'],
                        'source_category': category,
                        'sub_items': item_data.get('sub_items', {})
                    })
                    
                    # Update totals
                    categorized_data[year]['categories'][display_category]['subcategories'][subcat_key]['total'] += item_data['annual']
                    categorized_data[year]['categories'][display_category]['total'] += item_data['annual']
            
            # Process uncategorized items
            if universal.get('uncategorized_items'):
                if 'outros' not in categorized_data[year]['categories']:
                    categorized_data[year]['categories']['outros'] = {
                        'name': '❓ Outros/Não Categorizados',
                        'total': 0,
                        'subcategories': {}
                    }
                
                subcat_key = 'uncategorized_items'
                categorized_data[year]['categories']['outros']['subcategories'][subcat_key] = {
                    'name': 'Itens Não Categorizados',
                    'total': 0,
                    'items': []
                }
                
                for item_key, item_data in universal['uncategorized_items'].items():
                    categorized_data[year]['categories']['outros']['subcategories'][subcat_key]['items'].append({
                        'label': item_data['label'],
                        'value': item_data['annual'],
                        'source_category': 'uncategorized',
                        'sub_items': item_data.get('sub_items', {})
                    })
                    
                    categorized_data[year]['categories']['outros']['subcategories'][subcat_key]['total'] += item_data['annual']
                    categorized_data[year]['categories']['outros']['total'] += item_data['annual']
            
            continue  # Skip the old processing if we have universal data
        
        # Process ONLY main expense categories to avoid double counting
        # Note: other categories like administrative_expenses, marketing_expenses, etc. 
        # are already included within fixed_costs
        # Check if commissions are separate or included in variable_costs
        expense_categories = [
            'fixed_costs', 'variable_costs', 'non_operational_costs'
        ]
        
        # Check if commissions need to be added separately
        if 'commissions' in year_data and isinstance(year_data['commissions'], dict):
            comm_data = year_data['commissions']
            if comm_data.get('annual', 0) > 0:
                # Check if commissions are already in variable_costs
                comm_in_variable = False
                if 'variable_costs' in year_data and 'line_items' in year_data['variable_costs']:
                    for item_key, item_data in year_data['variable_costs']['line_items'].items():
                        if isinstance(item_data, dict):
                            label = item_data.get('label', '').upper()
                            if 'REPASSE' in label and 'COMISS' in label:
                                comm_in_variable = True
                                break
                
                if not comm_in_variable:
                    # Add commissions as a separate category
                    expense_categories.append('commissions')
        
        # Check if commissions exist in the data
        if 'commissions' in year_data and isinstance(year_data['commissions'], dict):
            comm_data = year_data['commissions']
        
        for category in expense_categories:
            if category not in year_data or not isinstance(year_data[category], dict):
                continue
                
            cat_data = year_data[category]
            category_total = cat_data.get('annual', 0) if isinstance(cat_data, dict) else 0
            line_items_total = 0
            
            
            if 'line_items' in cat_data and isinstance(cat_data['line_items'], dict):
                for item_key, item_data in cat_data['line_items'].items():
                    if not isinstance(item_data, dict):
                        continue
                        
                    value = item_data.get('annual', 0)
                    label = item_data.get('label', item_key)
                    
                    # Skip aggregate items to avoid double counting
                    skip_terms = ['CUSTOS FIXOS', 'CUSTOS VARIÁVEIS', 'CUSTO FIXO + VARIAVEL', 
                                  'DESPESAS ADMINISTRATIVAS', 'DESPESAS OPERACIONAIS', 
                                  'DESPESAS FINANCEIRAS', 'DESPESAS DE MARKETING']
                    
                    if any(term in label.upper() for term in skip_terms):
                        continue
                    
                    # Check if this item has sub_items (like commission providers)
                    if 'sub_items' in item_data and isinstance(item_data['sub_items'], dict) and len(item_data['sub_items']) > 0:
                        # First, check if we need to include the parent item value
                        # Calculate sum of sub_items
                        sub_items_total = sum(
                            sub_data.get('annual', 0) 
                            for sub_data in item_data['sub_items'].values() 
                            if isinstance(sub_data, dict)
                        )
                        
                        # If parent value is greater than sum of sub_items, add the difference as "Other"
                        parent_value = item_data.get('annual', 0)
                        difference = parent_value - sub_items_total
                        
                        if difference > 0.01:  # Small tolerance for rounding
                            # Add the difference as "Other" sub-item
                            classification = classify_expense_subcategory(label)
                            if classification['main_category'] == 'outros':
                                classification = _classify_by_source_category(category, label)
                            
                            main_cat = classification['main_category']
                            sub_cat = classification['subcategory']
                            
                            # Initialize category structure if needed
                            if main_cat not in categorized_data[year]['categories']:
                                categorized_data[year]['categories'][main_cat] = {
                                    'name': classification['main_category_name'],
                                    'total': 0,
                                    'subcategories': {}
                                }
                            
                            if sub_cat not in categorized_data[year]['categories'][main_cat]['subcategories']:
                                categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat] = {
                                    'name': classification['subcategory_name'],
                                    'total': 0,
                                    'items': []
                                }
                            
                            # Add the difference as "Other/Unspecified"
                            categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat]['items'].append({
                                'label': f"{label} - Outros/Não Especificado",
                                'value': difference,
                                'source_category': category,
                                'provider': 'Outros'
                            })
                            
                            # Update totals
                            categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat]['total'] += difference
                            categorized_data[year]['categories'][main_cat]['total'] += difference
                            line_items_total += difference
                        
                        # Process each sub-item
                        for sub_key, sub_data in item_data['sub_items'].items():
                            if not isinstance(sub_data, dict):
                                continue
                            
                            sub_value = sub_data.get('annual', 0)
                            sub_label = sub_data.get('label', sub_key)
                            
                            if sub_value > 0:
                                # Use parent classification for sub-items
                                classification = classify_expense_subcategory(label)
                                if classification['main_category'] == 'outros':
                                    classification = _classify_by_source_category(category, label)
                                
                                main_cat = classification['main_category']
                                sub_cat = classification['subcategory']
                                
                                # Initialize category structure if needed
                                if main_cat not in categorized_data[year]['categories']:
                                    categorized_data[year]['categories'][main_cat] = {
                                        'name': classification['main_category_name'],
                                        'total': 0,
                                        'subcategories': {}
                                    }
                                
                                if sub_cat not in categorized_data[year]['categories'][main_cat]['subcategories']:
                                    categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat] = {
                                        'name': classification['subcategory_name'],
                                        'total': 0,
                                        'items': []
                                    }
                                
                                # Add sub-item with provider name
                                categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat]['items'].append({
                                    'label': f"{label} - {sub_label}",
                                    'value': sub_value,
                                    'source_category': category,
                                    'provider': sub_label
                                })
                                
                                # Update totals
                                categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat]['total'] += sub_value
                                categorized_data[year]['categories'][main_cat]['total'] += sub_value
                                line_items_total += sub_value
                    
                    # Only process as regular item if it has value and no sub_items
                    elif value > 0:
                        # First try automatic classification
                        classification = classify_expense_subcategory(label)
                        
                        # If it falls into "outros", use source category for better classification
                        if classification['main_category'] == 'outros':
                            classification = _classify_by_source_category(category, label)
                        
                        main_cat = classification['main_category']
                        sub_cat = classification['subcategory']
                        
                        # Initialize category structure if needed
                        if main_cat not in categorized_data[year]['categories']:
                            categorized_data[year]['categories'][main_cat] = {
                                'name': classification['main_category_name'],
                                'total': 0,
                                'subcategories': {}
                            }
                        
                        if sub_cat not in categorized_data[year]['categories'][main_cat]['subcategories']:
                            categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat] = {
                                'name': classification['subcategory_name'],
                                'total': 0,
                                'items': []
                            }
                        
                        # Add item
                        categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat]['items'].append({
                            'label': label,
                            'value': value,
                            'source_category': category
                        })
                        
                        # Update totals
                        categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat]['total'] += value
                        categorized_data[year]['categories'][main_cat]['total'] += value
                        line_items_total += value
            
            # After processing all line items, check if we captured the full category total
            if category_total > line_items_total + 0.01:  # Small tolerance for rounding
                uncaptured_amount = category_total - line_items_total
                
                # Classify the uncaptured amount based on the category
                classification = _classify_by_source_category(category, f"Outros - {category}")
                main_cat = classification['main_category']
                sub_cat = classification['subcategory']
                
                # Initialize category structure if needed
                if main_cat not in categorized_data[year]['categories']:
                    categorized_data[year]['categories'][main_cat] = {
                        'name': classification['main_category_name'],
                        'total': 0,
                        'subcategories': {}
                    }
                
                if sub_cat not in categorized_data[year]['categories'][main_cat]['subcategories']:
                    categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat] = {
                        'name': classification['subcategory_name'],
                        'total': 0,
                        'items': []
                    }
                
                # Add the uncaptured amount
                categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat]['items'].append({
                    'label': f"Outros itens não detalhados - {category.replace('_', ' ').title()}",
                    'value': uncaptured_amount,
                    'source_category': category
                })
                
                # Update totals
                categorized_data[year]['categories'][main_cat]['subcategories'][sub_cat]['total'] += uncaptured_amount
                categorized_data[year]['categories'][main_cat]['total'] += uncaptured_amount
    
    return categorized_data


def _map_universal_category(category):
    """Map universal category names to display categories"""
    mapping = {
        'revenue': 'receita',
        'salaries': 'pessoal',
        'rent_utilities': 'ocupacao',
        'taxes': 'impostos',
        'commissions': 'comercial',
        'professional_services': 'servicos',
        'marketing': 'marketing',
        'administrative': 'administrativo',
        'financial': 'financeiro',
        'insurance': 'seguros',
        'maintenance': 'manutencao',
        'software': 'tecnologia',
        'travel': 'viagens',
        'meals': 'alimentacao',
        'depreciation': 'depreciacao',
        'variable_costs': 'custos_variaveis',
        'fixed_costs': 'custos_fixos',
        'non_operational': 'nao_operacional'
    }
    return mapping.get(category, category)


def _get_category_display_name(category):
    """Get display name for a category"""
    names = {
        'receita': '💰 Receita',
        'pessoal': '👥 Pessoal',
        'ocupacao': '🏢 Ocupação e Utilidades',
        'impostos': '💸 Impostos e Taxas',
        'comercial': '💼 Despesas Comerciais',
        'servicos': '🔧 Serviços Profissionais',
        'marketing': '📢 Marketing e Vendas',
        'administrativo': '📋 Despesas Administrativas',
        'financeiro': '💰 Despesas Financeiras',
        'seguros': '🛡️ Seguros',
        'manutencao': '🔧 Manutenção',
        'tecnologia': '💻 Tecnologia',
        'viagens': '✈️ Viagens',
        'alimentacao': '🍽️ Alimentação',
        'depreciacao': '📉 Depreciação',
        'custos_variaveis': '📊 Custos Variáveis',
        'custos_fixos': '📊 Custos Fixos',
        'nao_operacional': '📊 Despesas Não Operacionais',
        'outros': '❓ Outros'
    }
    return names.get(category, category.replace('_', ' ').title())


def _classify_by_source_category(source_category, label):
    """
    Classify expense based on source category when automatic classification fails
    """
    category_mapping = {
        'taxes': {
            'main_category': 'impostos',
            'main_category_name': '💸 Impostos e Taxas',
            'subcategory': 'impostos_diversos',
            'subcategory_name': 'Impostos Diversos'
        },
        'commissions': {
            'main_category': 'comercial',
            'main_category_name': '💼 Despesas Comerciais',
            'subcategory': 'comissoes',
            'subcategory_name': 'Comissões e Repasses'
        },
        'administrative_expenses': {
            'main_category': 'administrativo',
            'main_category_name': '📋 Despesas Administrativas',
            'subcategory': 'admin_geral',
            'subcategory_name': 'Administrativo Geral'
        },
        'operational_costs': {
            'main_category': 'operacional',
            'main_category_name': '⚙️ Despesas Operacionais',
            'subcategory': 'operacional_geral',
            'subcategory_name': 'Operacional Geral'
        },
        'marketing_expenses': {
            'main_category': 'marketing',
            'main_category_name': '📢 Marketing e Vendas',
            'subcategory': 'marketing_geral',
            'subcategory_name': 'Marketing Geral'
        },
        'financial_expenses': {
            'main_category': 'financeiro',
            'main_category_name': '💰 Despesas Financeiras',
            'subcategory': 'financeiro_geral',
            'subcategory_name': 'Financeiro Geral'
        },
        'non_operational_costs': {
            'main_category': 'nao_operacional',
            'main_category_name': '📊 Despesas Não Operacionais',
            'subcategory': 'nao_op_geral',
            'subcategory_name': 'Não Operacional Geral'
        }
    }
    
    # Default to source category mapping
    if source_category in category_mapping:
        return category_mapping[source_category]
    
    # Last resort - analyze the label for common patterns
    label_lower = label.lower()
    
    # Check for common patterns not caught by the categorizer
    if any(term in label_lower for term in ['despesa', 'gasto', 'custo']):
        if 'administrativ' in label_lower:
            return category_mapping['administrative_expenses']
        elif 'operacional' in label_lower:
            return category_mapping['operational_costs']
        elif 'financ' in label_lower:
            return category_mapping['financial_expenses']
    
    # True fallback - at least categorize by source
    return {
        'main_category': 'despesas_gerais',
        'main_category_name': '💵 Despesas Gerais',
        'subcategory': source_category.replace('_', ' ').title(),
        'subcategory_name': source_category.replace('_', ' ').title()
    }


def _get_current_level_data(categorized_data, path):
    """Get data for the current hierarchy level based on navigation path"""
    if not path:
        # Top level - show main categories
        return _aggregate_main_categories(categorized_data)
    elif len(path) == 1:
        # Second level - show subcategories of selected main category
        return _aggregate_subcategories(categorized_data, path[0])
    elif len(path) == 2:
        # Third level - show individual items of selected subcategory
        return _aggregate_items(categorized_data, path[0], path[1])
    else:
        return {}


def _aggregate_main_categories(categorized_data):
    """Aggregate data at main category level"""
    aggregated = {}
    
    for year, year_data in categorized_data.items():
        for cat_key, cat_data in year_data['categories'].items():
            if cat_key not in aggregated:
                aggregated[cat_key] = {
                    'name': cat_data['name'],
                    'years': {},
                    'total': 0,
                    'item_count': 0
                }
            
            aggregated[cat_key]['years'][year] = cat_data['total']
            aggregated[cat_key]['total'] += cat_data['total']
            
            # Count items
            for subcat in cat_data['subcategories'].values():
                aggregated[cat_key]['item_count'] += len(subcat['items'])
    
    return aggregated


def _aggregate_subcategories(categorized_data, main_category):
    """Aggregate data at subcategory level for a specific main category"""
    aggregated = {}
    
    for year, year_data in categorized_data.items():
        if main_category in year_data['categories']:
            cat_data = year_data['categories'][main_category]
            
            for subcat_key, subcat_data in cat_data['subcategories'].items():
                if subcat_key not in aggregated:
                    aggregated[subcat_key] = {
                        'name': subcat_data['name'],
                        'years': {},
                        'total': 0,
                        'item_count': len(subcat_data['items'])
                    }
                
                aggregated[subcat_key]['years'][year] = subcat_data['total']
                aggregated[subcat_key]['total'] += subcat_data['total']
    
    return aggregated


def _aggregate_items(categorized_data, main_category, subcategory):
    """Aggregate individual items for a specific subcategory"""
    aggregated = {}
    
    for year, year_data in categorized_data.items():
        if main_category in year_data['categories']:
            cat_data = year_data['categories'][main_category]
            
            if subcategory in cat_data['subcategories']:
                subcat_data = cat_data['subcategories'][subcategory]
                
                for item in subcat_data['items']:
                    item_key = item['label']
                    
                    if item_key not in aggregated:
                        aggregated[item_key] = {
                            'name': item['label'],
                            'years': {},
                            'total': 0,
                            'source': item['source_category']
                        }
                    
                    if year not in aggregated[item_key]['years']:
                        aggregated[item_key]['years'][year] = 0
                    
                    aggregated[item_key]['years'][year] += item['value']
                    aggregated[item_key]['total'] += item['value']
    
    return aggregated


def _render_summary_cards(current_level_data, flexible_data):
    """Render summary metric cards"""
    if not current_level_data:
        return
    
    # Calculate metrics
    total_value = sum(item['total'] for item in current_level_data.values())
    latest_year = max(year for item in current_level_data.values() for year in item['years'].keys())
    latest_year_value = sum(
        item['years'].get(latest_year, 0) 
        for item in current_level_data.values()
    )
    
    # Get revenue for percentage calculation
    revenue = 0
    if latest_year in flexible_data:
        year_data = flexible_data[latest_year]
        if 'revenue' in year_data:
            if isinstance(year_data['revenue'], dict):
                revenue = year_data['revenue'].get('annual', 0)
            else:
                revenue = year_data['revenue'] if year_data['revenue'] else 0
    
    # Calculate YoY growth
    prev_year = latest_year - 1
    prev_year_value = sum(
        item['years'].get(prev_year, 0) 
        for item in current_level_data.values()
    )
    yoy_growth = ((latest_year_value - prev_year_value) / prev_year_value * 100) if prev_year_value > 0 else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            f"Total {latest_year}",
            format_currency(latest_year_value),
            help=f"Valor total para o ano {latest_year}"
        )
    
    with col2:
        if revenue > 0:
            pct_revenue = (latest_year_value / revenue) * 100
            st.metric(
                "% da Receita",
                f"{pct_revenue:.1f}%",
                help="Percentual em relação à receita total"
            )
    
    with col3:
        st.metric(
            "Crescimento YoY",
            f"{yoy_growth:+.1f}%",
            help=f"Crescimento {prev_year} → {latest_year}"
        )
    
    with col4:
        item_count = len(current_level_data)
        st.metric(
            "Itens",
            f"{item_count}",
            help="Número de categorias/itens neste nível"
        )


def _render_interactive_visualization(current_level_data, full_width):
    """Render interactive treemap or sunburst chart"""
    st.markdown("#### 📊 Visualização Interativa")
    
    # Prepare data for treemap
    data_for_plot = []
    colors = []
    
    for idx, (key, data) in enumerate(current_level_data.items()):
        latest_year = max(data['years'].keys()) if data['years'] else 0
        value = data['years'].get(latest_year, 0) if latest_year else data['total']
        
        if value > 0:
            data_for_plot.append({
                'labels': data['name'],
                'values': value,
                'ids': key,
                'parents': '',
                'text': f"{data['name']}<br>{format_currency(value)}"
            })
            
            # Assign color from palette
            color_idx = idx % len(CHART_PALETTES['main'])
            colors.append(CHART_PALETTES['main'][color_idx])
    
    if not data_for_plot:
        st.info("Nenhum dado para visualizar neste nível.")
        return
    
    # Create treemap
    df_plot = pd.DataFrame(data_for_plot)
    
    fig = go.Figure(go.Treemap(
        labels=df_plot['labels'],
        values=df_plot['values'],
        ids=df_plot['ids'],
        parents=df_plot['parents'],
        text=df_plot['text'],
        texttemplate='<b>%{label}</b><br>%{value:,.0f}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent} do total<extra></extra>',
        marker=dict(colors=colors),
        textposition="middle center"
    ))
    
    fig.update_layout(
        height=500 if full_width else 400,
        margin=dict(t=30, b=0, l=0, r=0),
        font=dict(size=14 if full_width else 12)
    )
    
    # Add click event handling
    selected = st.plotly_chart(
        fig, 
        use_container_width=True,
        key="treemap_chart",
        on_select="rerun",
        selection_mode="points"
    )
    
    # Handle selection
    if selected and selected["selection"]["points"]:
        selected_id = selected["selection"]["points"][0]["id"]
        st.session_state.cost_hierarchy_path.append(selected_id)
        st.rerun()


def _render_detail_panel(current_level_data):
    """Render detail panel with insights"""
    st.markdown("#### 💡 Insights")
    
    if not current_level_data:
        return
    
    # Find top items
    sorted_items = sorted(
        current_level_data.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )
    
    # Top 3 items
    st.markdown("**Maiores custos:**")
    for i, (key, data) in enumerate(sorted_items[:3]):
        latest_year = max(data['years'].keys()) if data['years'] else 0
        value = data['years'].get(latest_year, 0) if latest_year else data['total']
        st.markdown(f"{i+1}. {data['name']}: {format_currency(value)}")
    
    # Growth analysis
    st.markdown("**Crescimento rápido:**")
    growth_rates = []
    for key, data in current_level_data.items():
        years = sorted(data['years'].keys())
        if len(years) >= 2:
            first_value = data['years'][years[0]]
            last_value = data['years'][years[-1]]
            if first_value > 0:
                growth = ((last_value - first_value) / first_value) * 100
                growth_rates.append((data['name'], growth, last_value))
    
    growth_rates.sort(key=lambda x: x[1], reverse=True)
    for i, (name, growth, value) in enumerate(growth_rates[:3]):
        st.markdown(f"{i+1}. {name}: {growth:+.1f}%")


def _render_detail_table(current_level_data):
    """Render detailed table with all items"""
    st.markdown("#### 📋 Tabela Detalhada")
    
    if not current_level_data:
        return
    
    # Prepare data for table
    table_data = []
    
    for key, data in current_level_data.items():
        row = {'Item': data['name']}
        
        # Add year columns
        years = sorted(set(year for item in current_level_data.values() for year in item['years'].keys()))
        for year in years[-3:]:  # Show last 3 years
            row[str(year)] = data['years'].get(year, 0)
        
        # Add total
        row['Total'] = data['total']
        
        # Add growth
        if len(years) >= 2:
            latest = data['years'].get(years[-1], 0)
            previous = data['years'].get(years[-2], 0)
            if previous > 0:
                row['Cresc. %'] = ((latest - previous) / previous) * 100
            else:
                row['Cresc. %'] = 0
        
        table_data.append(row)
    
    # Create DataFrame
    df_table = pd.DataFrame(table_data)
    
    # Sort by total
    df_table = df_table.sort_values('Total', ascending=False)
    
    # Format columns
    format_dict = {'Total': format_currency}
    for year in years[-3:]:
        format_dict[str(year)] = format_currency
    if 'Cresc. %' in df_table.columns:
        format_dict['Cresc. %'] = '{:.1f}%'
    
    # Display table with click handler
    st.dataframe(
        df_table.style.format(format_dict),
        use_container_width=True,
        hide_index=True,
        key="detail_table"
    )
    
    # Add click instruction if not at bottom level
    if len(st.session_state.cost_hierarchy_path) < 2:
        st.info("💡 Clique em qualquer item no gráfico acima para ver mais detalhes")


def _show_uncategorized_debug(categorized_data):
    """Show items that fell into uncategorized or vague categories for debugging"""
    st.markdown("#### 🔍 Análise de Itens Não Categorizados")
    
    uncategorized_items = []
    vague_items = []
    
    # Collect items from vague categories
    vague_categories = ['outros', 'despesas_gerais', 'nao_operacional']
    
    for year, year_data in categorized_data.items():
        if 'categories' in year_data:
            for cat_key, cat_data in year_data['categories'].items():
                # Check if this is a vague category
                if cat_key in vague_categories:
                    for subcat_key, subcat_data in cat_data['subcategories'].items():
                        for item in subcat_data['items']:
                            vague_items.append({
                                'Ano': year,
                                'Item': item['label'],
                                'Valor': item['value'],
                                'Categoria': cat_data['name'],
                                'Subcategoria': subcat_data['name'],
                                'Origem': item['source_category']
                            })
    
    # Display results
    if vague_items:
        st.markdown("**Itens em categorias genéricas:**")
        
        # Create DataFrame for display
        df_vague = pd.DataFrame(vague_items)
        
        # Group by category to show patterns
        st.markdown("📊 **Resumo por categoria:**")
        category_summary = df_vague.groupby('Categoria').agg({
            'Item': 'count',
            'Valor': 'sum'
        }).rename(columns={'Item': 'Quantidade', 'Valor': 'Valor Total'})
        
        # Format and display
        st.dataframe(
            category_summary.style.format({'Valor Total': format_currency}),
            use_container_width=True
        )
        
        # Show detailed table
        with st.expander("📋 Ver detalhes completos"):
            # Sort by value descending
            df_vague = df_vague.sort_values('Valor', ascending=False)
            
            # Format for display
            format_dict = {'Valor': format_currency}
            
            st.dataframe(
                df_vague.style.format(format_dict),
                use_container_width=True,
                hide_index=True
            )
            
            # Export option
            csv = df_vague.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name=f"itens_nao_categorizados_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
        
        # Suggestions for improvement
        st.markdown("---")
        st.markdown("💡 **Sugestões para melhorar a categorização:**")
        
        # Analyze patterns in uncategorized items
        common_terms = {}
        for item in vague_items:
            words = item['Item'].lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    common_terms[word] = common_terms.get(word, 0) + 1
        
        # Show top common terms
        if common_terms:
            sorted_terms = sorted(common_terms.items(), key=lambda x: x[1], reverse=True)[:10]
            st.markdown("**Termos mais comuns em itens não categorizados:**")
            for term, count in sorted_terms:
                st.markdown(f"- **{term}**: aparece em {count} itens")
    else:
        st.success("✅ Todos os itens foram categorizados adequadamente!")
        st.info("Nenhum item caiu em categorias genéricas como 'Outros' ou 'Despesas Gerais'.")


def _debug_commission_structure(flexible_data):
    """Debug function to check commission data structure"""
    st.markdown("#### 🔍 Debug: Estrutura de Comissões")
    
    for year, year_data in flexible_data.items():
        if isinstance(year_data, dict) and 'commissions' in year_data:
            st.markdown(f"**Ano {year}:**")
            
            comm_data = year_data['commissions']
            if isinstance(comm_data, dict):
                st.write(f"- Total anual: {format_currency(comm_data.get('annual', 0))}")
                
                if 'line_items' in comm_data:
                    st.write("- Line items encontrados:")
                    for item_key, item_data in comm_data['line_items'].items():
                        if isinstance(item_data, dict):
                            st.write(f"  - {item_data.get('label', item_key)}: {format_currency(item_data.get('annual', 0))}")
                            
                            # Check for sub_items
                            if 'sub_items' in item_data and isinstance(item_data['sub_items'], dict):
                                st.write(f"    Sub-items ({len(item_data['sub_items'])}):")
                                for sub_key, sub_data in item_data['sub_items'].items():
                                    if isinstance(sub_data, dict):
                                        st.write(f"      - {sub_data.get('label', sub_key)}: {format_currency(sub_data.get('annual', 0))}")
                            else:
                                st.write("    [Sem sub-items]")
            else:
                st.write("- Formato de dados inesperado")
            
            st.markdown("---")


def _debug_category_totals(flexible_data, categorized_data):
    """Debug function to check category totals"""
    st.markdown("#### 🔍 Debug: Totais por Categoria")
    
    latest_year = max(year for year in flexible_data.keys() if isinstance(flexible_data[year], dict))
    
    st.markdown(f"**Ano: {latest_year}**")
    
    if latest_year in flexible_data:
        year_data = flexible_data[latest_year]
        
        # Show main cost categories
        st.markdown("**Categorias Principais (devem somar R$ 2.53M):**")
        main_categories = ['variable_costs', 'fixed_costs', 'non_operational_costs']
        main_total = 0
        
        for cat in main_categories:
            if cat in year_data and isinstance(year_data[cat], dict):
                value = year_data[cat].get('annual', 0)
                main_total += value
                st.write(f"- {cat}: {format_currency(value)}")
        
        st.write(f"**Total das categorias principais: {format_currency(main_total)}**")
        
        st.markdown("---")
        
        # Show what's actually being included in the visualization
        st.markdown("**O que está sendo incluído na visualização:**")
        
        if latest_year in categorized_data:
            viz_total = 0
            for cat_key, cat_data in categorized_data[latest_year]['categories'].items():
                cat_total = cat_data['total']
                viz_total += cat_total
                st.write(f"- {cat_data['name']}: {format_currency(cat_total)}")
                
                # Show subcategories
                with st.expander(f"Ver subcategorias de {cat_data['name']}"):
                    for subcat_key, subcat_data in cat_data['subcategories'].items():
                        st.write(f"  - {subcat_data['name']}: {format_currency(subcat_data['total'])} ({len(subcat_data['items'])} itens)")
            
            st.write(f"**Total na visualização: {format_currency(viz_total)}**")
            
            # Show the difference
            difference = main_total - viz_total
            if abs(difference) > 1:
                st.error(f"**Diferença: {format_currency(difference)}** - Há valores não capturados!")
            else:
                st.success("✅ Totais coincidem!")
        
        st.markdown("---")
        
        # Show all categories in the data
        st.markdown("**Todas as categorias no flexible_data:**")
        all_categories = [
            'revenue', 'variable_costs', 'fixed_costs', 'non_operational_costs',
            'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses',
            'financial_expenses', 'operational_costs', 'net_profit', 'gross_profit'
        ]
        
        for cat in all_categories:
            if cat in year_data:
                if isinstance(year_data[cat], dict):
                    value = year_data[cat].get('annual', 0)
                    line_items_count = len(year_data[cat].get('line_items', {}))
                    st.write(f"- {cat}: {format_currency(value)} ({line_items_count} line items)")
                else:
                    st.write(f"- {cat}: {format_currency(year_data[cat])}")


def _show_complete_line_items_table(flexible_data):
    """Show complete table of all line items from universal data"""
    st.markdown("#### 📋 Todos os Itens de Linha Extraídos")
    
    # Collect all line items from all years
    all_items = []
    
    for year, year_data in flexible_data.items():
        if isinstance(year_data, dict) and 'universal_data' in year_data:
            universal = year_data['universal_data']
            
            # Add all line items
            for item in universal.get('all_line_items', []):
                all_items.append({
                    'Ano': year,
                    'Item': item['label'],
                    'Valor Anual': item['annual'],
                    'Categoria': item.get('category', 'uncategorized'),
                    'Seção': item.get('section', ''),
                    'É Sub-item': '✓' if item.get('is_sub_item') else '',
                    'Pai': item.get('parent', '')
                })
    
    if not all_items:
        st.info("Nenhum item de linha encontrado. Certifique-se de que os dados foram processados com o extrator universal.")
        return
    
    # Create DataFrame
    df_items = pd.DataFrame(all_items)
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Year filter
        years = sorted(df_items['Ano'].unique())
        selected_year = st.selectbox("Filtrar por ano:", ['Todos'] + [str(y) for y in years])
        
        if selected_year != 'Todos':
            df_filtered = df_items[df_items['Ano'] == int(selected_year)]
        else:
            df_filtered = df_items.copy()
    
    with col2:
        # Category filter
        categories = sorted(df_filtered['Categoria'].unique())
        selected_category = st.selectbox("Filtrar por categoria:", ['Todas'] + categories)
        
        if selected_category != 'Todas':
            df_filtered = df_filtered[df_filtered['Categoria'] == selected_category]
    
    with col3:
        # Value filter
        min_value = st.number_input("Valor mínimo (R$):", min_value=0.0, value=0.0, step=100.0)
        df_filtered = df_filtered[df_filtered['Valor Anual'] >= min_value]
    
    # Search box
    search_term = st.text_input("🔍 Buscar item:", placeholder="Digite para buscar...")
    if search_term:
        mask = df_filtered['Item'].str.contains(search_term, case=False, na=False)
        df_filtered = df_filtered[mask]
    
    # Summary stats
    st.markdown("**Resumo:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Itens", len(df_filtered))
    with col2:
        st.metric("Valor Total", format_currency(df_filtered['Valor Anual'].sum()))
    with col3:
        sub_items_count = len(df_filtered[df_filtered['É Sub-item'] == '✓'])
        st.metric("Sub-itens", sub_items_count)
    with col4:
        categories_count = df_filtered['Categoria'].nunique()
        st.metric("Categorias", categories_count)
    
    # Sort options
    sort_col1, sort_col2 = st.columns(2)
    with sort_col1:
        sort_by = st.selectbox("Ordenar por:", ['Valor Anual', 'Item', 'Categoria', 'Ano'])
    with sort_col2:
        sort_ascending = st.checkbox("Ordem crescente", value=False)
    
    # Sort DataFrame
    sort_column_map = {
        'Valor Anual': 'Valor Anual',
        'Item': 'Item', 
        'Categoria': 'Categoria',
        'Ano': 'Ano'
    }
    
    df_filtered = df_filtered.sort_values(
        sort_column_map[sort_by], 
        ascending=sort_ascending
    )
    
    # Display table with formatting
    st.markdown("---")
    
    # Format the DataFrame for display
    df_display = df_filtered.copy()
    df_display['Valor Anual'] = df_display['Valor Anual'].apply(format_currency)
    
    # Display with pagination
    items_per_page = st.selectbox("Itens por página:", [50, 100, 200, 500], index=1)
    
    total_items = len(df_display)
    total_pages = (total_items - 1) // items_per_page + 1 if total_items > 0 else 1
    
    if total_pages > 1:
        page = st.number_input("Página:", min_value=1, max_value=total_pages, value=1)
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        df_display = df_display.iloc[start_idx:end_idx]
        
        st.info(f"Mostrando itens {start_idx + 1} a {end_idx} de {total_items} (Página {page} de {total_pages})")
    
    # Display the table
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Valor Anual": st.column_config.TextColumn(
                "Valor Anual",
                width="medium"
            )
        }
    )
    
    # Export option
    if len(df_filtered) > 0:
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            # Export filtered data
            csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar dados filtrados (CSV)",
                data=csv,
                file_name=f"itens_linha_filtrados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime='text/csv'
            )
        
        with col2:
            # Quick analysis
            if st.button("📊 Análise rápida"):
                st.markdown("**Análise dos dados filtrados:**")
                
                # Top categories
                cat_summary = df_filtered.groupby('Categoria')['Valor Anual'].agg(['count', 'sum']).reset_index()
                cat_summary.columns = ['Categoria', 'Quantidade', 'Valor Total']
                cat_summary = cat_summary.sort_values('Valor Total', ascending=False)
                
                st.markdown("**Top 5 categorias por valor:**")
                for i, row in cat_summary.head().iterrows():
                    st.write(f"{i+1}. {row['Categoria']}: {format_currency(row['Valor Total'])} ({row['Quantidade']} itens)")
                
                # Average values
                avg_value = df_filtered['Valor Anual'].mean()
                median_value = df_filtered['Valor Anual'].median()
                
                st.markdown(f"**Valor médio:** {format_currency(avg_value)}")
                st.markdown(f"**Valor mediano:** {format_currency(median_value)}")