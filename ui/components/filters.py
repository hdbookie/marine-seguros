"""
Reusable Filter Components
Provides modular filter UI components for the Marine Seguros dashboard
"""

import streamlit as st
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from utils import get_category_icon, get_category_name, get_expense_subcategories


def render_time_period_filters(years: List[str], key_prefix: str = "details") -> None:
    """
    Render quick time period filter buttons
    
    Args:
        years: List of available years
        key_prefix: Prefix for session state keys
    """
    st.markdown("##### ⏱️ Período Rápido")
    time_cols = st.columns(6)
    
    # Get current year for calculations
    today = datetime.now()
    current_year_int = today.year
    current_month = today.month
    
    with time_cols[0]:
        if st.button("Este Ano", key=f"{key_prefix}_this_year", use_container_width=True):
            current_year_str = str(current_year_int)
            if current_year_str in years:
                st.session_state[f'{key_prefix}_year_filter'] = [current_year_str]
            elif years:  # If current year not in data, use most recent
                st.session_state[f'{key_prefix}_year_filter'] = [years[-1]]
            st.session_state[f'{key_prefix}_month_filter'] = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                                   'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            st.rerun()
    
    with time_cols[1]:
        if st.button("Ano Passado", key=f"{key_prefix}_last_year", use_container_width=True):
            last_year = str(current_year_int - 1)
            if last_year in years:
                st.session_state[f'{key_prefix}_year_filter'] = [last_year]
                st.session_state[f'{key_prefix}_month_filter'] = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                                       'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                st.rerun()
    
    with time_cols[2]:
        if st.button("YTD", key=f"{key_prefix}_ytd", use_container_width=True):
            current_year_str = str(current_year_int)
            if current_year_str in years:
                months_ytd = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                             'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'][:current_month]
                st.session_state[f'{key_prefix}_year_filter'] = [current_year_str]
                st.session_state[f'{key_prefix}_month_filter'] = months_ytd
            elif years:  # If current year not in data, use most recent year
                st.session_state[f'{key_prefix}_year_filter'] = [years[-1]]
                st.session_state[f'{key_prefix}_month_filter'] = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                                       'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            st.rerun()
    
    with time_cols[3]:
        if st.button("Últimos 12M", key=f"{key_prefix}_12m", use_container_width=True):
            # Calculate last 12 months
            months_12m = []
            years_12m = []
            
            for i in range(12):
                month_idx = (current_month - 1 - i) % 12
                year_offset = (current_month - 1 - i) // 12
                calc_year = str(current_year_int - year_offset - (1 if month_idx > current_month - 1 else 0))
                
                if calc_year in years:
                    if calc_year not in years_12m:
                        years_12m.append(calc_year)
                    month_name = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'][month_idx]
                    if month_name not in months_12m:
                        months_12m.append(month_name)
            
            st.session_state[f'{key_prefix}_year_filter'] = years_12m
            st.session_state[f'{key_prefix}_month_filter'] = months_12m
            st.rerun()
    
    with time_cols[4]:
        if st.button("Q4", key=f"{key_prefix}_q4", use_container_width=True):
            st.session_state[f'{key_prefix}_month_filter'] = ['OUT', 'NOV', 'DEZ']
            if not st.session_state.get(f'{key_prefix}_year_filter'):
                st.session_state[f'{key_prefix}_year_filter'] = [str(current_year_int)]
            st.rerun()
    
    with time_cols[5]:
        if st.button("Todos", key=f"{key_prefix}_all", use_container_width=True):
            st.session_state[f'{key_prefix}_year_filter'] = years
            st.session_state[f'{key_prefix}_month_filter'] = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                                   'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            st.rerun()


def render_primary_filters(
    years: List[str],
    categories: List[str],
    key_prefix: str = "details"
) -> Tuple[List[str], List[str], str]:
    """
    Render primary filter controls (year, category, search)
    
    Args:
        years: List of available years
        categories: List of available categories
        key_prefix: Prefix for session state keys
        
    Returns:
        Tuple of (selected_years, selected_categories, search_term)
    """
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 3])
    
    with filter_col1:
        # Year filter with smart default
        # Ensure default values exist in options
        year_filter_key = f'{key_prefix}_year_filter'
        if year_filter_key not in st.session_state:
            st.session_state[year_filter_key] = [years[-1]] if years else []
            
        valid_defaults = [y for y in st.session_state[year_filter_key] if y in years]
        if not valid_defaults and years:
            valid_defaults = [years[-1]]  # Use most recent year if no valid defaults
        
        selected_years = st.multiselect(
            "📅 Anos",
            options=years,
            default=valid_defaults,
            key=f"{key_prefix}_year_filter_ui"
        )
        st.session_state[year_filter_key] = selected_years
    
    with filter_col2:
        # Category filter
        selected_categories = st.multiselect(
            "📂 Categorias",
            options=categories,
            format_func=lambda x: f"{get_category_icon(x)} {get_category_name(x)}",
            default=categories,
            key=f"{key_prefix}_category_filter"
        )
    
    with filter_col3:
        # Enhanced search with suggestions
        search_key = f'{key_prefix}_search_term'
        if search_key not in st.session_state:
            st.session_state[search_key] = ""
            
        search_term = st.text_input(
            "🔍 Buscar",
            placeholder="Digite para buscar (ex: vale, salário, João)",
            value=st.session_state[search_key],
            key=f"{key_prefix}_search_input"
        )
        st.session_state[search_key] = search_term
        
        # Quick search buttons
        quick_cols = st.columns(4)
        quick_searches = [
            ("👤 Pessoal", "salário"),
            ("🚌 Vale", "vale"),
            ("🍽️ Alimentação", "alimentação"),
            ("🏢 Aluguel", "aluguel")
        ]
        for idx, (label, term) in enumerate(quick_searches):
            with quick_cols[idx]:
                if st.button(label, key=f"{key_prefix}_quick_{idx}"):
                    st.session_state[search_key] = term
                    st.rerun()
    
    return selected_years, selected_categories, search_term


def render_advanced_filters(
    all_items: List[Dict],
    selected_main_categories: Optional[List[str]] = None,
    key_prefix: str = "details"
) -> Dict[str, Any]:
    """
    Render advanced filter controls in an expander
    
    Args:
        all_items: List of all items (for value range calculation)
        selected_main_categories: Pre-selected main categories
        key_prefix: Prefix for session state keys
        
    Returns:
        Dictionary with advanced filter selections
    """
    advanced_filters = {}
    
    with st.expander("Filtros Avançados", expanded=False):
        adv_col1, adv_col2, adv_col3 = st.columns(3)
        
        with adv_col1:
            # Subcategory filter
            subcategories_data = get_expense_subcategories()
            main_categories = list(subcategories_data.keys()) + ['outros']
            
            if selected_main_categories is None:
                selected_main_categories = st.multiselect(
                    "Categorias Principais",
                    options=main_categories,
                    format_func=lambda x: subcategories_data.get(x, {}).get('name', '📌 Outros') if x != 'outros' else '📌 Outros',
                    default=main_categories,
                    key=f"{key_prefix}_main_categories"
                )
            
            advanced_filters['main_categories'] = selected_main_categories
        
        with adv_col2:
            # Month filter
            months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                     'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            
            month_filter_key = f'{key_prefix}_month_filter'
            if month_filter_key not in st.session_state:
                st.session_state[month_filter_key] = months
                
            selected_months = st.multiselect(
                "📅 Meses",
                options=months,
                default=st.session_state[month_filter_key],
                key=f"{key_prefix}_month_filter_ui"
            )
            st.session_state[month_filter_key] = selected_months
            advanced_filters['months'] = selected_months
        
        with adv_col3:
            # Value range
            all_values = [item.get('valor_anual', 0) for item in all_items]
            min_val = min(all_values) if all_values else 0
            max_val = max(all_values) if all_values else 1000000
            
            value_range = st.slider(
                "Faixa de Valores (R$)",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                format="R$ %d",
                key=f"{key_prefix}_value_range"
            )
            advanced_filters['value_range'] = value_range
    
    return advanced_filters


def build_filter_dict(
    selected_years: List[str],
    selected_categories: List[str],
    search_term: str,
    advanced_filters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Build a complete filter dictionary from individual filter components
    
    Args:
        selected_years: Selected years
        selected_categories: Selected categories
        search_term: Search term
        advanced_filters: Advanced filter selections
        
    Returns:
        Complete filter dictionary
    """
    filters = {
        'years': selected_years,
        'categories': selected_categories,
        'search_term': search_term
    }
    
    if advanced_filters:
        if 'months' in advanced_filters:
            filters['months'] = advanced_filters['months']
        
        if 'value_range' in advanced_filters:
            filters['value_range'] = advanced_filters['value_range']
        
        if 'main_categories' in advanced_filters:
            # Build subcategory list from main categories
            subcategories_data = get_expense_subcategories()
            available_subcategories = []
            
            for main_cat in advanced_filters['main_categories']:
                if main_cat in subcategories_data:
                    for sub_cat in subcategories_data[main_cat]['subcategories'].keys():
                        available_subcategories.append(f"{main_cat}_{sub_cat}")
                elif main_cat == 'outros':
                    available_subcategories.append('outros_nao_categorizado')
            
            filters['subcategories'] = available_subcategories
    
    return filters