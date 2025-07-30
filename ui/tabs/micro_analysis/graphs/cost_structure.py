"""
Cost Structure Analysis Graph Module
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from visualizations.charts import (
    create_detailed_cost_structure_chart,
    create_cost_as_percentage_of_revenue_chart,
    create_pareto_chart,
    create_treemap
)
from utils.categories import get_category_name
from ..config import GRAPH_CONFIGS


def render_cost_structure(df, flexible_data, selected_years, config=None):
    """
    Render cost structure analysis charts
    
    Args:
        df: DataFrame with financial data
        flexible_data: Raw flexible data for detailed analysis
        selected_years: List of selected years
        config: Optional configuration overrides
    """
    config = {**GRAPH_CONFIGS['cost_structure'], **(config or {})}
    
    # Detailed cost structure
    st.subheader(config['title'])
    fig_detailed = create_detailed_cost_structure_chart(df)
    fig_detailed.update_layout(height=config['height'])
    st.plotly_chart(fig_detailed, use_container_width=True)
    
    # Costs as percentage of revenue
    st.subheader("Custos como % da Receita")
    fig_percentage = create_cost_as_percentage_of_revenue_chart(df)
    st.plotly_chart(fig_percentage, use_container_width=True)
    
    # Sub-category analysis
    _render_subcategory_analysis(flexible_data, selected_years)
    
    # Pareto analysis
    _render_pareto_analysis(flexible_data, selected_years)


def _render_subcategory_analysis(flexible_data, selected_years):
    """Render sub-category drill-down analysis"""
    st.subheader("Análise de Sub-Categorias")
    
    cost_categories = [
        'variable_costs', 'fixed_costs', 'non_operational_costs', 
        'taxes', 'commissions', 'administrative_expenses', 
        'marketing_expenses', 'financial_expenses'
    ]
    
    # Category selector
    selected_category = st.selectbox(
        "Selecione uma categoria para detalhar",
        [cat.replace('_', ' ').title() for cat in cost_categories],
        key="subcategory_selector"
    )
    
    # Convert back to key format
    category_key = selected_category.lower().replace(' ', '_')
    
    # Collect items for selected category
    all_items = []
    for year in selected_years:
        year_key = int(year)
        if year_key in flexible_data:
            year_data = flexible_data[year_key]
            if isinstance(year_data, dict) and category_key in year_data:
                category_data = year_data[category_key]
                if isinstance(category_data, dict) and 'line_items' in category_data:
                    items = category_data['line_items']
                    if isinstance(items, dict):
                        all_items.extend(items.values())
    
    if all_items:
        # Create treemap
        df_treemap = pd.DataFrame(all_items)
        if 'annual' in df_treemap.columns and 'label' in df_treemap.columns:
            df_treemap['value'] = df_treemap['annual']
            df_treemap['category'] = selected_category
            df_treemap['item'] = df_treemap['label']
            
            fig_treemap = create_treemap(df_treemap, title=f"Detalhes de {selected_category}")
            st.plotly_chart(fig_treemap, use_container_width=True)
    else:
        st.info(f"Nenhum detalhe disponível para {selected_category}")


def _render_pareto_analysis(flexible_data, selected_years):
    """Render Pareto (80/20) analysis"""
    st.subheader("Análise de Pareto (80/20) dos Custos")
    
    # Collect all cost items
    all_costs = []
    cost_types = [
        'variable_costs', 'fixed_costs', 'non_operational_costs',
        'taxes', 'commissions', 'administrative_expenses',
        'marketing_expenses', 'financial_expenses'
    ]
    
    for year in selected_years:
        year_key = int(year)
        if year_key in flexible_data:
            year_data = flexible_data[year_key]
            if isinstance(year_data, dict):
                for cost_type in cost_types:
                    if cost_type in year_data:
                        cost_data = year_data[cost_type]
                        if isinstance(cost_data, dict) and 'line_items' in cost_data:
                            items = cost_data['line_items']
                            if isinstance(items, dict):
                                all_costs.extend(items.values())
    
    if all_costs:
        fig_pareto = create_pareto_chart(all_costs)
        st.plotly_chart(fig_pareto, use_container_width=True)
        
        # Show insights
        _show_pareto_insights(all_costs)
    else:
        st.info("Dados insuficientes para análise de Pareto")


def _show_pareto_insights(all_costs):
    """Show insights from Pareto analysis"""
    # Sort costs by value
    sorted_costs = sorted(all_costs, key=lambda x: x.get('annual', 0), reverse=True)
    total_cost = sum(item.get('annual', 0) for item in sorted_costs)
    
    if total_cost > 0:
        # Find 80% threshold
        cumulative = 0
        count_80 = 0
        for item in sorted_costs:
            cumulative += item.get('annual', 0)
            count_80 += 1
            if cumulative >= total_cost * 0.8:
                break
        
        percentage = (count_80 / len(sorted_costs)) * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Princípio 80/20",
                f"{percentage:.0f}% dos itens",
                help="Percentual de itens que representam 80% dos custos"
            )
        with col2:
            st.metric(
                "Maior custo individual",
                sorted_costs[0].get('label', 'N/A') if sorted_costs else 'N/A',
                help=f"Representa {(sorted_costs[0].get('annual', 0) / total_cost * 100):.1f}% do total"
            )