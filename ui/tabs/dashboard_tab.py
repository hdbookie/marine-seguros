"""Dashboard tab implementation"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from utils import format_currency, format_percentage
from visualizations import (
    create_revenue_cost_chart,
    create_margin_evolution_chart,
    create_cost_breakdown_chart,
    create_monthly_trend_chart
)


def render_dashboard_tab(df, monthly_data=None):
    """Render the main dashboard tab"""
    
    if df.empty:
        st.info("👆 Carregue dados na aba 'Upload' primeiro.")
        return
    
    # Header
    st.header("📊 Dashboard Principal")
    
    # KPI Section
    render_kpi_section(df)
    
    # Filters Section
    selected_years, view_type, selected_months = render_filters_section(df)
    
    # Filter data based on selections
    filtered_df = filter_data(df, selected_years, view_type, selected_months)
    
    if filtered_df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return
    
    # Main Charts Section
    render_main_charts(filtered_df, view_type)
    
    # Monthly Analysis (if monthly data available)
    if monthly_data is not None and not monthly_data.empty:
        render_monthly_analysis(monthly_data, selected_years)


def render_kpi_section(df):
    """Render the KPI cards section"""
    st.markdown("### 📈 Indicadores Principais")
    
    # Calculate KPIs
    latest_year = df['year'].max()
    latest_data = df[df['year'] == latest_year].iloc[0]
    
    # Previous year for comparison
    prev_year = latest_year - 1
    prev_data = df[df['year'] == prev_year]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        revenue = latest_data['revenue']
        prev_revenue = prev_data['revenue'].iloc[0] if not prev_data.empty else 0
        revenue_growth = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        st.metric(
            "Receita Total",
            format_currency(revenue),
            f"{revenue_growth:+.1f}% vs {prev_year}" if prev_revenue > 0 else None
        )
    
    with col2:
        profit = latest_data['net_profit']
        prev_profit = prev_data['net_profit'].iloc[0] if not prev_data.empty else 0
        profit_growth = ((profit - prev_profit) / prev_profit * 100) if prev_profit > 0 else 0
        
        st.metric(
            "Lucro Líquido",
            format_currency(profit),
            f"{profit_growth:+.1f}% vs {prev_year}" if prev_profit > 0 else None
        )
    
    with col3:
        margin = latest_data['profit_margin']
        prev_margin = prev_data['profit_margin'].iloc[0] if not prev_data.empty else 0
        margin_change = margin - prev_margin
        
        st.metric(
            "Margem de Lucro",
            format_percentage(margin),
            f"{margin_change:+.1f}pp vs {prev_year}" if prev_margin > 0 else None
        )
    
    with col4:
        costs = latest_data['variable_costs']
        cost_ratio = (costs / revenue * 100) if revenue > 0 else 0
        
        st.metric(
            "Custos Variáveis",
            format_currency(costs),
            f"{cost_ratio:.1f}% da receita"
        )


def render_filters_section(df):
    """Render the filters section"""
    st.markdown("### 🎛️ Filtros")
    
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
    
    with col_filter1:
        view_type = st.selectbox(
            "Visualização",
            ["Anual", "Mensal", "Trimestral", "Semestral"],
            key="view_type"
        )
    
    with col_filter2:
        if view_type != "Anual":
            available_years = sorted(df['year'].unique())
            default_years = available_years[-3:] if len(available_years) >= 3 else available_years
            
            selected_years = st.multiselect(
                "Anos",
                available_years,
                default=default_years,
                key="dashboard_selected_years"
            )
        else:
            selected_years = sorted(df['year'].unique())
    
    with col_filter3:
        if view_type == "Mensal":
            month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                          "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            selected_months = st.multiselect(
                "Meses",
                month_names,
                default=month_names,
                key="selected_months"
            )
        else:
            selected_months = []
    
    with col_filter4:
        # Quick filters
        quick_filter = st.selectbox(
            "Filtro Rápido",
            ["Todos", "Últimos 3 Anos", "Últimos 5 Anos", "Ano Atual"],
            key="quick_filter"
        )
        
        # Apply quick filter
        if quick_filter == "Últimos 3 Anos":
            selected_years = sorted(df['year'].unique())[-3:]
        elif quick_filter == "Últimos 5 Anos":
            selected_years = sorted(df['year'].unique())[-5:]
        elif quick_filter == "Ano Atual":
            current_year = datetime.now().year
            selected_years = [current_year] if current_year in df['year'].values else [df['year'].max()]
    
    return selected_years, view_type, selected_months


def filter_data(df, selected_years, view_type, selected_months):
    """Filter data based on user selections"""
    filtered_df = df[df['year'].isin(selected_years)]
    
    # Additional filtering based on view type
    if view_type == "Mensal" and selected_months:
        # This would require monthly data structure
        pass
    
    return filtered_df


def render_main_charts(df, view_type):
    """Render the main charts section"""
    st.markdown("### 📊 Análise Gráfica")
    
    # Create tabs for different chart views
    chart_tab1, chart_tab2, chart_tab3 = st.tabs([
        "💰 Receitas vs Custos",
        "📈 Margem de Lucro", 
        "🥧 Composição de Custos"
    ])
    
    with chart_tab1:
        fig = create_revenue_cost_chart(df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional insights
        render_revenue_insights(df)
    
    with chart_tab2:
        fig = create_margin_evolution_chart(df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Margin analysis
        render_margin_analysis(df)
    
    with chart_tab3:
        # Prepare cost breakdown data
        latest_data = df.iloc[-1]
        cost_data = {
            'Custos Variáveis': latest_data.get('variable_costs', 0),
            'Custos Fixos': latest_data.get('fixed_costs', 0),
            'Custos Operacionais': latest_data.get('operational_costs', 0)
        }
        
        fig = create_cost_breakdown_chart(cost_data)
        st.plotly_chart(fig, use_container_width=True)


def render_revenue_insights(df):
    """Render revenue insights"""
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue growth analysis
        if len(df) > 1:
            revenue_growth = df['revenue'].pct_change().mean() * 100
            st.info(f"💡 **Crescimento médio da receita**: {revenue_growth:+.1f}% ao ano")
    
    with col2:
        # Best performing year
        best_year = df.loc[df['revenue'].idxmax()]
        st.success(f"🏆 **Melhor ano**: {best_year['year']} com {format_currency(best_year['revenue'])}")


def render_margin_analysis(df):
    """Render margin analysis"""
    col1, col2 = st.columns(2)
    
    with col1:
        avg_margin = df['profit_margin'].mean()
        st.metric("Margem Média", format_percentage(avg_margin))
    
    with col2:
        best_margin_year = df.loc[df['profit_margin'].idxmax()]
        st.metric(
            f"Melhor Margem ({best_margin_year['year']})",
            format_percentage(best_margin_year['profit_margin'])
        )


def render_monthly_analysis(monthly_data, selected_years):
    """Render monthly analysis section"""
    st.markdown("### 📅 Análise Mensal")
    
    # Filter monthly data by selected years
    filtered_monthly = monthly_data[monthly_data['year'].isin(selected_years)]
    
    if filtered_monthly.empty:
        st.info("Dados mensais não disponíveis para os anos selecionados.")
        return
    
    # Monthly trend chart
    fig = create_monthly_trend_chart(filtered_monthly.set_index('date'))
    st.plotly_chart(fig, use_container_width=True)
    
    # Monthly insights
    render_monthly_insights(filtered_monthly)