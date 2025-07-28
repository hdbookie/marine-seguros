"""Micro Analysis Tab - Variable + Fixed Costs Sankey Visualization"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils import format_currency
from utils.categories import get_category_name
from visualizations.charts import create_pnl_evolution_chart, create_detailed_cost_structure_chart, create_pnl_waterfall_chart, create_pareto_chart, create_treemap, create_cost_as_percentage_of_revenue_chart, create_margin_comparison_chart

def render_micro_analysis_tab(flexible_data):
    """Render the micro analysis tab with Sankey flow diagram"""
    
    st.header("🔬 Análise Micro - Custos Variáveis e Fixos")
    
    if not flexible_data:
        st.info("📊 Carregue dados usando o extrator flexível para acessar a análise micro.")
        return
    
    # Render filters (same as macro dashboard)
    selected_years, view_type, selected_months = render_filters_section(flexible_data)
    
    # Flatten the data for the DataFrame
    flat_data = []
    for year, year_data in flexible_data.items():
        if str(year) in selected_years:
            row = {'year': year}
            for key, value in year_data.items():
                if isinstance(value, dict) and 'annual' in value:
                    row[key] = value['annual']
                else:
                    row[key] = value
            flat_data.append(row)

    df = pd.DataFrame(flat_data)

    if df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # KPI Section
    render_kpi_section(df)

    # Tabbed Interface
    tab1, tab2, tab3 = st.tabs(["Visão Geral P&L", "Análise de Custos", "Análise de Margem"])

    with tab1:
        render_pnl_evolution_tab(df)

    with tab2:
        st.subheader("Estrutura de Custos Detalhada")
        fig_detailed_cost = create_detailed_cost_structure_chart(df)
        st.plotly_chart(fig_detailed_cost, use_container_width=True)

        st.subheader("Custos como % da Receita")
        fig_cost_percentage = create_cost_as_percentage_of_revenue_chart(df)
        st.plotly_chart(fig_cost_percentage, use_container_width=True)

        st.subheader("Análise de Sub-Categorias")
        cost_categories = ['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']
        selected_category = st.selectbox("Selecione uma categoria de custo para detalhar", [cat.replace('_', ' ').title() for cat in cost_categories])

        # Create treemap for the selected category
        all_items = []
        for year in selected_years:
            year_key = int(year)
            if year_key in flexible_data:
                all_items.extend(flexible_data[year_key].get(selected_category.lower().replace(' ', '_'), {}).get('line_items', {}).values())
        
        if all_items:
            df_treemap = pd.DataFrame(all_items)
            df_treemap['value'] = df_treemap['annual']
            df_treemap['category'] = selected_category
            df_treemap['item'] = df_treemap['label']
            fig_treemap = create_treemap(df_treemap, title=f"Detalhes de {selected_category}")
            st.plotly_chart(fig_treemap, use_container_width=True)

        st.subheader("Análise de Pareto (80/20) dos Custos")
        all_costs = []
        for year in selected_years:
            year_key = int(year)
            if year_key in flexible_data:
                for cost_type in ['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']:
                    all_costs.extend(flexible_data[year_key].get(cost_type, {}).get('line_items', {}).values())
        
        if all_costs:
            fig_pareto = create_pareto_chart(all_costs)
            st.plotly_chart(fig_pareto, use_container_width=True)

    with tab3:
        st.subheader("Análise da Margem")
        fig_margin_comparison = create_margin_comparison_chart(df)
        st.plotly_chart(fig_margin_comparison, use_container_width=True)

    with st.expander("Explore os Dados Detalhados"):
        st.dataframe(df)

def render_pnl_evolution_tab(df):
    st.subheader("Evolução do Demonstrativo de Resultados")
    print(df)
    fig_pnl_evolution = create_pnl_evolution_chart(df)
    st.plotly_chart(fig_pnl_evolution, use_container_width=True)

    st.subheader("Demonstrativo de Resultados (Cascata) - Último Ano")
    fig_pnl_waterfall = create_pnl_waterfall_chart(df)
    st.plotly_chart(fig_pnl_waterfall, use_container_width=True)

def render_kpi_section(df):
    """Render the KPI cards section"""
    st.markdown("### 📈 Indicadores Principais")
    
    latest_year_data = df.iloc[-1]
    previous_year_data = df.iloc[-2] if len(df) > 1 else None

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        revenue = latest_year_data['revenue']
        delta = revenue - previous_year_data['revenue'] if previous_year_data is not None else None
        st.metric("Receita", format_currency(revenue), f"{format_currency(delta)} vs ano anterior" if delta is not None else None)

    with col2:
        total_costs = latest_year_data[['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']].sum()
        prev_total_costs = previous_year_data[['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']].sum() if previous_year_data is not None else None
        delta = total_costs - prev_total_costs if prev_total_costs is not None else None
        st.metric("Custos Totais", format_currency(total_costs), f"{format_currency(delta)} vs ano anterior" if delta is not None else None)

    with col3:
        net_profit = latest_year_data['net_profit']
        delta = net_profit - previous_year_data['net_profit'] if previous_year_data is not None else None
        st.metric("Lucro Líquido", format_currency(net_profit), f"{format_currency(delta)} vs ano anterior" if delta is not None else None)

    with col4:
        profit_margin = latest_year_data['profit_margin']
        delta = profit_margin - previous_year_data['profit_margin'] if previous_year_data is not None else None
        st.metric("Margem de Lucro", f"{profit_margin:.2f}%", f"{delta:.2f}pp vs ano anterior" if delta is not None else None)

def render_filters_section(flexible_data):
    """Render the filters section (matching macro dashboard style)"""
    st.markdown("### 🎛️ Filtros")
    
    # Get available years
    available_years = sorted([str(y) for y in flexible_data.keys()])
    
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
    
    with col_filter1:
        view_type = st.selectbox(
            "Visualização",
            ["Anual", "Mensal", "Trimestral", "Semestral"],
            key="micro_view_type"
        )
    
    with col_filter2:
        if view_type != "Anual":
            default_years = available_years[-3:] if len(available_years) >= 3 else available_years
            selected_years = st.multiselect(
                "Anos",
                available_years,
                default=default_years,
                key="micro_selected_years"
            )
        else:
            selected_years = available_years
    
    with col_filter3:
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
    
    with col_filter4:
        # Quick filters
        if st.button("🗓️ Últimos 3 Anos", key="micro_quick_3y", use_container_width=True):
            st.session_state.micro_selected_years = available_years[-3:] if len(available_years) >= 3 else available_years
            st.rerun()
        
        if st.button("📅 Ano Atual", key="micro_quick_current", use_container_width=True):
            current_year = str(datetime.now().year)
            if current_year in available_years:
                st.session_state.micro_selected_years = [current_year]
            else:
                st.session_state.micro_selected_years = [available_years[-1]]
            st.rerun()
    
    return selected_years, view_type, selected_months