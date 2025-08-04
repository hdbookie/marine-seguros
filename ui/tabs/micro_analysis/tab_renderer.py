"""
Main Tab Renderer for Micro Analysis
Orchestrates all the modular components
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import configuration
from .config import TAB_CONFIGS, TIME_PERIOD_CONFIGS

# Import modules
from .kpi_section import render_kpi_section
from .graphs import (
    render_pnl_evolution,
    render_cost_structure,
    render_group_evolution,
    render_group_comparison,
    render_margin_impact,
    render_margin_analysis,
    render_financial_notes,
    render_interactive_cost_breakdown
)

# Import processors
from core.group_hierarchy_processor import GroupHierarchyProcessor


def render_micro_analysis_tab(flexible_data):
    """
    Main entry point for the micro analysis tab
    
    Args:
        flexible_data: Dictionary with financial data by year
    """
    st.header("🔬 Análise Micro - Análise Detalhada de Despesas")
    
    if not flexible_data:
        st.info("📊 Carregue dados usando o extrator flexível para acessar a análise micro.")
        return
    
    # Render filters
    selected_years, view_type, selected_months = _render_filters_section(flexible_data)
    
    # Process data based on view type
    df = _process_data_for_view(flexible_data, selected_years, view_type, selected_months)
    
    if df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return
    
    # Process group data
    processor = GroupHierarchyProcessor()
    processed_data = processor.process_data(flexible_data)
    major_groups = processor.get_major_groups(processed_data)
    group_df = processor.create_group_comparison_df(major_groups) if major_groups else pd.DataFrame()
    
    # Render KPI section
    render_kpi_section(df, view_type)
    
    # Render tabs based on configuration
    tab_names = [f"{config['icon']} {config['name']}" for config in TAB_CONFIGS.values()]
    tabs = st.tabs(tab_names)
    
    # Render each tab
    for idx, (tab_key, tab_config) in enumerate(TAB_CONFIGS.items()):
        with tabs[idx]:
            _render_tab_content(
                tab_key, 
                df, 
                flexible_data, 
                group_df, 
                major_groups,
                selected_years,
                view_type
            )


def _render_filters_section(flexible_data):
    """Render the filters section"""
    st.markdown("### 🎛️ Filtros")
    
    # Get available years
    available_years = sorted([str(y) for y in flexible_data.keys()])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        view_type = st.selectbox(
            "Visualização",
            list(TIME_PERIOD_CONFIGS.keys()),
            key="micro_view_type"
        )
    
    with col2:
        if view_type == "Anual":
            selected_years = st.multiselect(
                "Anos Selecionados",
                available_years,
                default=available_years,
                key="micro_selected_years_annual",
                help="Selecione os anos que deseja visualizar"
            )
        else:
            default_years = available_years[-3:] if len(available_years) >= 3 else available_years
            selected_years = st.multiselect(
                "Anos",
                available_years,
                default=default_years,
                key="micro_selected_years"
            )
    
    with col3:
        if view_type == "Mensal":
            month_names = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
                          "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
            selected_months = st.multiselect(
                "Meses",
                month_names,
                default=month_names,
                key="micro_selected_months"
            )
        else:
            selected_months = []
    
    with col4:
        # Quick filters
        col4_1, col4_2 = st.columns(2)
        with col4_1:
            if st.button("🗓️ Últimos 3 Anos", use_container_width=True):
                st.session_state.micro_selected_years = available_years[-3:] if len(available_years) >= 3 else available_years
                st.rerun()
        
        with col4_2:
            if st.button("📅 Ano Atual", use_container_width=True):
                current_year = str(datetime.now().year)
                if current_year in available_years:
                    st.session_state.micro_selected_years_annual = [current_year]
                else:
                    st.session_state.micro_selected_years_annual = [available_years[-1]]
                st.rerun()
    
    return selected_years, view_type, selected_months


def _process_data_for_view(flexible_data, selected_years, view_type, selected_months):
    """Process data based on the selected view type"""
    time_config = TIME_PERIOD_CONFIGS.get(view_type, TIME_PERIOD_CONFIGS['Anual'])
    
    if view_type == "Anual":
        return _process_annual_data(flexible_data, selected_years)
    else:
        return _process_periodic_data(flexible_data, selected_years, view_type, selected_months)


def _process_annual_data(flexible_data, selected_years):
    """Process annual data"""
    flat_data = []
    for year, year_data in flexible_data.items():
        if str(year) in selected_years and isinstance(year_data, dict):
            row = {'year': year}
            
            # List of all cost fields
            cost_fields = [
                'revenue', 'variable_costs', 'fixed_costs', 'non_operational_costs', 
                'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 
                'financial_expenses', 'operational_costs', 'net_profit', 'gross_profit'
            ]
            
            # Flatten each field
            for field in cost_fields:
                if field in year_data:
                    value = year_data[field]
                    if isinstance(value, dict):
                        row[field] = value.get('annual', 0)
                    else:
                        row[field] = value if value is not None else 0
                else:
                    row[field] = 0
            
            # Add profit margin
            if 'profit_margin' not in row and row.get('revenue', 0) > 0:
                row['profit_margin'] = (row.get('net_profit', 0) / row['revenue']) * 100
            
            flat_data.append(row)
    
    return pd.DataFrame(flat_data)


def _process_periodic_data(flexible_data, selected_years, view_type, selected_months):
    """Process monthly/quarterly/semester data"""
    monthly_data = []
    month_names = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                  'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Extract monthly data
    for year, year_data in flexible_data.items():
        if str(year) in selected_years and isinstance(year_data, dict):
            for month_idx, month in enumerate(month_names):
                if view_type == "Mensal" and month not in selected_months:
                    continue
                
                row = {
                    'year': year,
                    'month': month,
                    'month_num': month_idx + 1,
                    'period': f"{year}-{month}"
                }
                
                # Extract monthly values
                for field in ['revenue', 'variable_costs', 'fixed_costs', 'non_operational_costs', 
                             'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 
                             'financial_expenses', 'net_profit']:
                    if field in year_data and isinstance(year_data[field], dict):
                        monthly_values = year_data[field].get('monthly', {})
                        row[field] = monthly_values.get(month, 0)
                    else:
                        row[field] = 0
                
                # Calculate profit margin
                if row['revenue'] > 0:
                    row['profit_margin'] = (row['net_profit'] / row['revenue']) * 100
                else:
                    row['profit_margin'] = 0
                
                monthly_data.append(row)
    
    monthly_df = pd.DataFrame(monthly_data)
    
    # Aggregate based on view type
    if view_type == "Mensal":
        return monthly_df
    elif view_type == "Trimestral":
        return _aggregate_quarterly(monthly_df)
    elif view_type == "Semestral":
        return _aggregate_semester(monthly_df)
    
    return monthly_df


def _aggregate_quarterly(monthly_df):
    """Aggregate monthly data to quarters"""
    monthly_df['quarter'] = (monthly_df['month_num'] - 1) // 3 + 1
    
    df = monthly_df.groupby(['year', 'quarter']).agg({
        'revenue': 'sum',
        'variable_costs': 'sum',
        'fixed_costs': 'sum',
        'non_operational_costs': 'sum',
        'taxes': 'sum',
        'commissions': 'sum',
        'administrative_expenses': 'sum',
        'marketing_expenses': 'sum',
        'financial_expenses': 'sum',
        'net_profit': 'sum'
    }).reset_index()
    
    df['period'] = df.apply(lambda x: f"{int(x['year'])}-Q{int(x['quarter'])}", axis=1)
    df['profit_margin'] = (df['net_profit'] / df['revenue'] * 100).fillna(0)
    
    return df


def _aggregate_semester(monthly_df):
    """Aggregate monthly data to semesters"""
    monthly_df['semester'] = (monthly_df['month_num'] - 1) // 6 + 1
    
    df = monthly_df.groupby(['year', 'semester']).agg({
        'revenue': 'sum',
        'variable_costs': 'sum',
        'fixed_costs': 'sum',
        'non_operational_costs': 'sum',
        'taxes': 'sum',
        'commissions': 'sum',
        'administrative_expenses': 'sum',
        'marketing_expenses': 'sum',
        'financial_expenses': 'sum',
        'net_profit': 'sum'
    }).reset_index()
    
    df['period'] = df.apply(lambda x: f"{int(x['year'])}-S{int(x['semester'])}", axis=1)
    df['profit_margin'] = (df['net_profit'] / df['revenue'] * 100).fillna(0)
    
    return df


def _render_tab_content(tab_key, df, flexible_data, group_df, major_groups, selected_years, view_type):
    """Render content for a specific tab"""
    if tab_key == 'overview':
        # Overview tab - Interactive cost breakdown first
        st.markdown("---")
        render_interactive_cost_breakdown(df, flexible_data, full_width=True)
        
        # Then the regular group evolution
        st.markdown("---")
        if not group_df.empty:
            render_group_evolution(group_df, df, flexible_data)
        else:
            st.info("Carregue dados para visualizar análise de grupos")
    
    elif tab_key == 'groups':
        # Group analysis tab
        if not group_df.empty:
            render_group_comparison(group_df, df, major_groups)
            render_margin_impact(group_df, df)
        else:
            st.info("Dados de grupos não disponíveis. Processando...")
    
    elif tab_key == 'detailed':
        # Detailed analysis tab
        render_cost_structure(df, flexible_data, selected_years)
        render_margin_analysis(df)
    
    elif tab_key == 'insights':
        # Insights tab
        render_financial_notes(flexible_data)
    
    # Add export button at the bottom of each tab
    if st.button(f"📥 Exportar {TAB_CONFIGS[tab_key]['name']}", key=f"export_{tab_key}"):
        st.info("Funcionalidade de exportação em desenvolvimento...")