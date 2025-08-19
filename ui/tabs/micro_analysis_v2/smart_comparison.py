"""
Smart Comparison Dashboard for Micro Analysis V2
Advanced comparison analytics with variance analysis, scenario planning, and benchmarking
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from utils import format_currency
from datetime import datetime, timedelta
import json


def render_smart_comparison_dashboard(financial_data: Dict, selected_years: List[int]):
    """
    Render comprehensive comparison dashboard with multiple analytical perspectives
    """
    st.markdown("### 🔄 Dashboard de Comparação Inteligente")
    st.caption("Análises comparativas avançadas com detecção de variações e cenários")
    
    if len(selected_years) < 2:
        st.warning("Selecione pelo menos 2 anos para análise comparativa")
        return
    
    # Comparison type selector
    comparison_type = st.selectbox(
        "Tipo de Análise Comparativa",
        [
            "📊 Comparação Período-a-Período",
            "📈 Análise de Variação",
            "🎯 Comparação vs Orçamento",
            "🔍 Análise de Performance",
            "🏆 Benchmarking Interno",
            "🎛️ Cenários What-If"
        ]
    )
    
    if comparison_type == "📊 Comparação Período-a-Período":
        _render_period_comparison(financial_data, selected_years)
    elif comparison_type == "📈 Análise de Variação":
        _render_variance_analysis(financial_data, selected_years)
    elif comparison_type == "🎯 Comparação vs Orçamento":
        _render_budget_comparison(financial_data, selected_years)
    elif comparison_type == "🔍 Análise de Performance":
        _render_performance_analysis(financial_data, selected_years)
    elif comparison_type == "🏆 Benchmarking Interno":
        _render_internal_benchmarking(financial_data, selected_years)
    elif comparison_type == "🎛️ Cenários What-If":
        _render_whatif_scenarios(financial_data, selected_years)


def _render_period_comparison(financial_data: Dict, selected_years: List[int]):
    """Render side-by-side period comparison"""
    
    st.markdown("#### 📊 Comparação Período-a-Período")
    
    # Period selection
    col1, col2 = st.columns(2)
    
    with col1:
        period1 = st.selectbox("Período Base", selected_years, index=0, key="period1")
    
    with col2:
        period2 = st.selectbox("Período Comparação", selected_years, index=min(1, len(selected_years)-1), key="period2")
    
    if period1 == period2:
        st.warning("Selecione períodos diferentes para comparação")
        return
    
    # Get data for both periods
    data1 = financial_data.get(period1, {}).get('sections', [])
    data2 = financial_data.get(period2, {}).get('sections', [])
    
    if not data1 or not data2:
        st.warning("Dados insuficientes para os períodos selecionados")
        return
    
    # Prepare comparison data
    comparison_data = _prepare_comparison_data(data1, data2, period1, period2)
    
    # Create side-by-side comparison visualization
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(f'{period1}', f'{period2}'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    categories = [item['category'] for item in comparison_data]
    values1 = [item['value1'] for item in comparison_data]
    values2 = [item['value2'] for item in comparison_data]
    
    # Left chart (Period 1)
    fig.add_trace(
        go.Bar(
            x=values1,
            y=categories,
            orientation='h',
            name=str(period1),
            marker_color='lightblue',
            text=[format_currency(v) for v in values1],
            textposition='outside',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Right chart (Period 2)
    fig.add_trace(
        go.Bar(
            x=values2,
            y=categories,
            orientation='h',
            name=str(period2),
            marker_color='lightcoral',
            text=[format_currency(v) for v in values2],
            textposition='outside',
            showlegend=False
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title=f'Comparação: {period1} vs {period2}',
        height=600,
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Valor (R$)", row=1, col=1, tickformat=',.0f')
    fig.update_xaxes(title_text="Valor (R$)", row=1, col=2, tickformat=',.0f')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show comparison metrics
    _render_comparison_metrics(comparison_data, period1, period2)


def _render_variance_analysis(financial_data: Dict, selected_years: List[int]):
    """Render detailed variance analysis"""
    
    st.markdown("#### 📈 Análise Detalhada de Variações")
    
    # Base year selection
    base_year = st.selectbox("Ano Base para Comparação", selected_years, key="variance_base")
    comparison_years = [y for y in selected_years if y != base_year]
    
    if not comparison_years:
        st.warning("Selecione pelo menos 2 anos para análise de variação")
        return
    
    # Calculate variances
    variance_data = _calculate_variance_analysis(financial_data, base_year, comparison_years)
    
    if not variance_data:
        st.warning("Dados insuficientes para análise de variação")
        return
    
    # Create variance waterfall chart
    _render_variance_waterfall(variance_data, base_year, comparison_years)
    
    # Show variance breakdown
    _render_variance_breakdown(variance_data, base_year, comparison_years)


def _render_variance_waterfall(variance_data: Dict, base_year: int, comparison_years: List[int]):
    """Create waterfall chart showing variance contributions"""
    
    for comp_year in comparison_years:
        st.markdown(f"##### Análise de Variação: {base_year} → {comp_year}")
        
        categories = list(variance_data.keys())
        variances = [variance_data[cat][f'{comp_year}_absolute_change'] for cat in categories]
        cumulative = np.cumsum([0] + variances[:-1])  # Cumulative for waterfall
        
        # Create waterfall chart
        fig = go.Figure()
        
        # Add bars for each category
        for i, (category, variance, cum_val) in enumerate(zip(categories, variances, cumulative)):
            color = 'green' if variance >= 0 else 'red'
            
            fig.add_trace(go.Bar(
                x=[category],
                y=[abs(variance)],
                base=[cum_val + min(0, variance)],
                name=category,
                marker_color=color,
                text=format_currency(variance),
                textposition='outside',
                showlegend=False,
                hovertemplate=f'<b>{category}</b><br>Variação: {format_currency(variance)}<extra></extra>'
            ))
        
        # Add total line
        total_variance = sum(variances)
        fig.add_hline(
            y=total_variance,
            line=dict(color='blue', dash='dash', width=2),
            annotation_text=f"Variação Total: {format_currency(total_variance)}"
        )
        
        fig.update_layout(
            title=f'Waterfall de Variações - {base_year} vs {comp_year}',
            xaxis=dict(title='Categorias', tickangle=45),
            yaxis=dict(title='Variação (R$)', tickformat=',.0f'),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)


def _render_variance_breakdown(variance_data: Dict, base_year: int, comparison_years: List[int]):
    """Show detailed variance breakdown table"""
    
    st.markdown("#### 📋 Detalhamento das Variações")
    
    for comp_year in comparison_years:
        st.markdown(f"##### Variações {base_year} → {comp_year}")
        
        # Create detailed variance table
        variance_table = []
        
        for category, data in variance_data.items():
            absolute_change = data[f'{comp_year}_absolute_change']
            percent_change = data[f'{comp_year}_percent_change']
            base_value = data['base_value']
            comp_value = data[f'{comp_year}_value']
            
            variance_table.append({
                'Categoria': category,
                f'{base_year}': format_currency(base_value),
                f'{comp_year}': format_currency(comp_value),
                'Variação ($)': format_currency(absolute_change),
                'Variação (%)': f"{percent_change:+.1f}%",
                'Impacto': _classify_variance_impact(absolute_change, percent_change)
            })
        
        df_variance = pd.DataFrame(variance_table)
        
        # Style the dataframe
        def style_variance_table(val):
            if 'Alto' in str(val):
                return 'background-color: #ffcccc'
            elif 'Médio' in str(val):
                return 'background-color: #ffffcc'
            else:
                return 'background-color: #ccffcc'
        
        styled_df = df_variance.style.applymap(
            style_variance_table, subset=['Impacto']
        ).format({
            'Variação (%)': '{:+.1f}%'
        })
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)


def _render_budget_comparison(financial_data: Dict, selected_years: List[int]):
    """Render budget vs actual comparison"""
    
    st.markdown("#### 🎯 Comparação vs Orçamento")
    st.info("🚧 Funcionalidade de orçamento em desenvolvimento - requer integração com dados orçamentários")
    
    # Placeholder for budget comparison
    st.markdown("**Recursos Planejados:**")
    st.write("• Importação de dados orçamentários")
    st.write("• Comparação orçado vs realizado")
    st.write("• Análise de desvios orçamentários")
    st.write("• Alertas de ultrapassagem de orçamento")
    st.write("• Projeções com base no histórico")


def _render_performance_analysis(financial_data: Dict, selected_years: List[int]):
    """Render performance analysis across periods"""
    
    st.markdown("#### 🔍 Análise de Performance")
    
    # Calculate performance metrics
    performance_metrics = _calculate_performance_metrics(financial_data, selected_years)
    
    if not performance_metrics:
        st.warning("Dados insuficientes para análise de performance")
        return
    
    # Create performance dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_growth = performance_metrics.get('average_growth_rate', 0)
        st.metric(
            "Crescimento Médio",
            f"{avg_growth:+.1f}%",
            delta=f"{avg_growth:+.1f}%" if abs(avg_growth) > 1 else None
        )
    
    with col2:
        volatility = performance_metrics.get('average_volatility', 0)
        st.metric("Volatilidade Média", f"{volatility:.1f}%")
    
    with col3:
        consistency = performance_metrics.get('consistency_score', 0)
        st.metric("Score Consistência", f"{consistency:.1f}/10")
    
    with col4:
        efficiency = performance_metrics.get('efficiency_trend', 0)
        trend_icon = "📈" if efficiency > 0 else "📉" if efficiency < 0 else "➡️"
        st.metric("Tendência Eficiência", f"{trend_icon} {abs(efficiency):.1f}%")
    
    # Performance by category chart
    _render_category_performance_chart(performance_metrics)


def _render_category_performance_chart(performance_metrics: Dict):
    """Render performance chart by category"""
    
    category_performance = performance_metrics.get('category_performance', {})
    
    if not category_performance:
        return
    
    categories = list(category_performance.keys())
    growth_rates = [category_performance[cat]['growth_rate'] for cat in categories]
    volatilities = [category_performance[cat]['volatility'] for cat in categories]
    mean_values = [category_performance[cat]['mean_value'] for cat in categories]
    
    # Create performance matrix (Growth vs Volatility)
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=volatilities,
        y=growth_rates,
        mode='markers+text',
        text=categories,
        textposition='top center',
        marker=dict(
            size=[v/max(mean_values)*50 + 10 for v in mean_values],
            color=growth_rates,
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Taxa Crescimento (%)")
        ),
        name='Categorias'
    ))
    
    # Add quadrant lines
    avg_growth = np.mean(growth_rates)
    avg_volatility = np.mean(volatilities)
    
    fig.add_hline(y=avg_growth, line=dict(color='gray', dash='dash'), annotation_text="Crescimento Médio")
    fig.add_vline(x=avg_volatility, line=dict(color='gray', dash='dash'), annotation_text="Volatilidade Média")
    
    fig.update_layout(
        title='Matriz de Performance - Crescimento vs Volatilidade',
        xaxis=dict(title='Volatilidade (%)'),
        yaxis=dict(title='Taxa de Crescimento (%)'),
        height=500,
        annotations=[
            dict(x=max(volatilities)*0.8, y=max(growth_rates)*0.8, text="Alto Crescimento<br>Alta Volatilidade", showarrow=False),
            dict(x=min(volatilities)*0.8, y=max(growth_rates)*0.8, text="Alto Crescimento<br>Baixa Volatilidade", showarrow=False),
            dict(x=min(volatilities)*0.8, y=min(growth_rates)*0.8, text="Baixo Crescimento<br>Baixa Volatilidade", showarrow=False),
            dict(x=max(volatilities)*0.8, y=min(growth_rates)*0.8, text="Baixo Crescimento<br>Alta Volatilidade", showarrow=False),
        ]
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_internal_benchmarking(financial_data: Dict, selected_years: List[int]):
    """Render internal benchmarking analysis"""
    
    st.markdown("#### 🏆 Benchmarking Interno")
    
    # Calculate benchmarking metrics
    benchmarking_data = _calculate_internal_benchmarks(financial_data, selected_years)
    
    if not benchmarking_data:
        st.warning("Dados insuficientes para benchmarking")
        return
    
    # Show best and worst performing periods
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🥇 Melhor Performance")
        best_year = benchmarking_data['best_year']
        best_metrics = benchmarking_data['yearly_metrics'][best_year]
        
        st.success(f"**Ano {best_year}**")
        st.metric("Total de Despesas", format_currency(best_metrics['total_expenses']))
        st.metric("Eficiência", f"{best_metrics['efficiency']:.2f}")
        st.metric("Crescimento", f"{best_metrics.get('growth_rate', 0):+.1f}%")
    
    with col2:
        st.markdown("##### 📉 Pior Performance")
        worst_year = benchmarking_data['worst_year']
        worst_metrics = benchmarking_data['yearly_metrics'][worst_year]
        
        st.error(f"**Ano {worst_year}**")
        st.metric("Total de Despesas", format_currency(worst_metrics['total_expenses']))
        st.metric("Eficiência", f"{worst_metrics['efficiency']:.2f}")
        st.metric("Crescimento", f"{worst_metrics.get('growth_rate', 0):+.1f}%")
    
    # Performance ranking chart
    _render_performance_ranking(benchmarking_data)


def _render_performance_ranking(benchmarking_data: Dict):
    """Render performance ranking across years"""
    
    yearly_metrics = benchmarking_data['yearly_metrics']
    years = sorted(yearly_metrics.keys())
    
    efficiency_scores = [yearly_metrics[year]['efficiency'] for year in years]
    total_expenses = [yearly_metrics[year]['total_expenses'] for year in years]
    
    # Create ranking chart
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['Score de Eficiência por Ano', 'Total de Despesas por Ano'],
        vertical_spacing=0.1
    )
    
    # Efficiency ranking
    fig.add_trace(
        go.Bar(
            x=years,
            y=efficiency_scores,
            name='Score Eficiência',
            marker_color='lightblue',
            text=[f'{score:.2f}' for score in efficiency_scores],
            textposition='outside'
        ),
        row=1, col=1
    )
    
    # Total expenses
    fig.add_trace(
        go.Bar(
            x=years,
            y=total_expenses,
            name='Total Despesas',
            marker_color='lightcoral',
            text=[format_currency(expense) for expense in total_expenses],
            textposition='outside'
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=600, showlegend=False)
    fig.update_yaxes(title_text="Score", row=1, col=1)
    fig.update_yaxes(title_text="Valor (R$)", row=2, col=1, tickformat=',.0f')
    
    st.plotly_chart(fig, use_container_width=True)


def _render_whatif_scenarios(financial_data: Dict, selected_years: List[int]):
    """Render what-if scenario analysis"""
    
    st.markdown("#### 🎛️ Análise de Cenários What-If")
    
    # Base scenario selection
    base_year = st.selectbox("Ano Base para Cenários", selected_years, key="scenario_base")
    
    if base_year not in financial_data or 'sections' not in financial_data[base_year]:
        st.warning("Dados insuficientes para o ano selecionado")
        return
    
    base_data = financial_data[base_year]['sections']
    
    st.markdown("##### 🎯 Configure os Cenários")
    st.caption("Ajuste os valores percentuais para simular diferentes cenários")
    
    # Scenario configuration
    scenarios = {}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📈 Cenário Otimista**")
        optimistic_growth = st.slider("Crescimento Geral (%)", -50, 100, 10, key="opt_growth")
        optimistic_efficiency = st.slider("Melhoria Eficiência (%)", 0, 50, 15, key="opt_eff")
        scenarios['Otimista'] = {'growth': optimistic_growth/100, 'efficiency': optimistic_efficiency/100}
    
    with col2:
        st.markdown("**📊 Cenário Realista**")
        realistic_growth = st.slider("Crescimento Geral (%)", -50, 100, 5, key="real_growth")
        realistic_efficiency = st.slider("Melhoria Eficiência (%)", 0, 50, 5, key="real_eff")
        scenarios['Realista'] = {'growth': realistic_growth/100, 'efficiency': realistic_efficiency/100}
    
    with col3:
        st.markdown("**📉 Cenário Pessimista**")
        pessimistic_growth = st.slider("Crescimento Geral (%)", -50, 100, -5, key="pess_growth")
        pessimistic_efficiency = st.slider("Melhoria Eficiência (%)", 0, 50, 0, key="pess_eff")
        scenarios['Pessimista'] = {'growth': pessimistic_growth/100, 'efficiency': pessimistic_efficiency/100}
    
    # Calculate scenario projections
    scenario_results = _calculate_scenario_projections(base_data, scenarios)
    
    # Visualize scenarios
    _render_scenario_comparison(base_data, scenario_results, base_year)


def _render_scenario_comparison(base_data: List[Dict], scenario_results: Dict, base_year: int):
    """Render scenario comparison visualization"""
    
    categories = [section['name'] for section in base_data]
    base_values = [section['value'] for section in base_data]
    
    # Create scenario comparison chart
    fig = go.Figure()
    
    # Base year
    fig.add_trace(go.Bar(
        x=categories,
        y=base_values,
        name=f'Base ({base_year})',
        marker_color='lightgray',
        text=[format_currency(v) for v in base_values],
        textposition='outside'
    ))
    
    # Scenarios
    colors = {'Otimista': 'green', 'Realista': 'blue', 'Pessimista': 'red'}
    
    for scenario_name, results in scenario_results.items():
        values = [results[cat] for cat in categories]
        
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            name=scenario_name,
            marker_color=colors[scenario_name],
            opacity=0.7,
            text=[format_currency(v) for v in values],
            textposition='outside'
        ))
    
    fig.update_layout(
        title='Comparação de Cenários',
        xaxis=dict(title='Categorias', tickangle=45),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        height=600,
        barmode='group'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show scenario summary
    _render_scenario_summary(base_data, scenario_results)


def _render_scenario_summary(base_data: List[Dict], scenario_results: Dict):
    """Render scenario impact summary"""
    
    st.markdown("#### 📊 Resumo de Impacto dos Cenários")
    
    base_total = sum(section['value'] for section in base_data)
    
    col1, col2, col3 = st.columns(3)
    
    for i, (scenario_name, results) in enumerate(scenario_results.items()):
        scenario_total = sum(results.values())
        impact = ((scenario_total - base_total) / base_total) * 100
        absolute_impact = scenario_total - base_total
        
        if i == 0:
            col = col1
        elif i == 1:
            col = col2
        else:
            col = col3
        
        with col:
            st.markdown(f"**{scenario_name}**")
            st.metric(
                "Total Projetado",
                format_currency(scenario_total),
                delta=format_currency(absolute_impact)
            )
            st.metric("Impacto (%)", f"{impact:+.1f}%")


# Helper functions

def _prepare_comparison_data(data1: List[Dict], data2: List[Dict], period1: int, period2: int) -> List[Dict]:
    """Prepare data for period comparison"""
    
    # Create lookup dictionaries
    dict1 = {section['name']: section['value'] for section in data1}
    dict2 = {section['name']: section['value'] for section in data2}
    
    # Find common categories
    common_categories = set(dict1.keys()) & set(dict2.keys())
    
    comparison_data = []
    for category in sorted(common_categories):
        comparison_data.append({
            'category': category,
            'value1': dict1[category],
            'value2': dict2[category],
            'change': dict2[category] - dict1[category],
            'percent_change': ((dict2[category] - dict1[category]) / dict1[category] * 100) if dict1[category] > 0 else 0
        })
    
    return comparison_data


def _render_comparison_metrics(comparison_data: List[Dict], period1: int, period2: int):
    """Render comparison metrics summary"""
    
    st.markdown("#### 📊 Métricas Comparativas")
    
    total1 = sum(item['value1'] for item in comparison_data)
    total2 = sum(item['value2'] for item in comparison_data)
    total_change = total2 - total1
    total_percent_change = (total_change / total1 * 100) if total1 > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(f"Total {period1}", format_currency(total1))
    
    with col2:
        st.metric(f"Total {period2}", format_currency(total2))
    
    with col3:
        st.metric("Variação Absoluta", format_currency(total_change), delta=format_currency(total_change))
    
    with col4:
        st.metric("Variação (%)", f"{total_percent_change:+.1f}%", delta=f"{total_percent_change:+.1f}%")
    
    # Top movers
    biggest_increases = sorted(comparison_data, key=lambda x: x['change'], reverse=True)[:3]
    biggest_decreases = sorted(comparison_data, key=lambda x: x['change'])[:3]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📈 Maiores Aumentos**")
        for item in biggest_increases:
            if item['change'] > 0:
                st.success(f"{item['category']}: +{format_currency(item['change'])} ({item['percent_change']:+.1f}%)")
    
    with col2:
        st.markdown("**📉 Maiores Reduções**")
        for item in biggest_decreases:
            if item['change'] < 0:
                st.error(f"{item['category']}: {format_currency(item['change'])} ({item['percent_change']:+.1f}%)")


def _calculate_variance_analysis(financial_data: Dict, base_year: int, comparison_years: List[int]) -> Dict:
    """Calculate detailed variance analysis"""
    
    if base_year not in financial_data or 'sections' not in financial_data[base_year]:
        return {}
    
    base_data = {section['name']: section['value'] for section in financial_data[base_year]['sections']}
    variance_data = {}
    
    for category, base_value in base_data.items():
        variance_data[category] = {'base_value': base_value}
        
        for comp_year in comparison_years:
            if comp_year in financial_data and 'sections' in financial_data[comp_year]:
                comp_data = {section['name']: section['value'] for section in financial_data[comp_year]['sections']}
                comp_value = comp_data.get(category, 0)
                
                absolute_change = comp_value - base_value
                percent_change = (absolute_change / base_value * 100) if base_value > 0 else 0
                
                variance_data[category][f'{comp_year}_value'] = comp_value
                variance_data[category][f'{comp_year}_absolute_change'] = absolute_change
                variance_data[category][f'{comp_year}_percent_change'] = percent_change
    
    return variance_data


def _classify_variance_impact(absolute_change: float, percent_change: float) -> str:
    """Classify variance impact level"""
    
    if abs(percent_change) > 25 or abs(absolute_change) > 100000:
        return "Alto Impacto"
    elif abs(percent_change) > 10 or abs(absolute_change) > 50000:
        return "Médio Impacto"
    else:
        return "Baixo Impacto"


def _calculate_performance_metrics(financial_data: Dict, selected_years: List[int]) -> Dict:
    """Calculate comprehensive performance metrics"""
    
    if len(selected_years) < 2:
        return {}
    
    # Calculate yearly totals and growth rates
    yearly_totals = []
    growth_rates = []
    
    for year in sorted(selected_years):
        if year in financial_data and 'sections' in financial_data[year]:
            total = sum(section['value'] for section in financial_data[year]['sections'])
            yearly_totals.append(total)
    
    # Calculate growth rates
    for i in range(1, len(yearly_totals)):
        if yearly_totals[i-1] > 0:
            growth_rate = ((yearly_totals[i] - yearly_totals[i-1]) / yearly_totals[i-1]) * 100
            growth_rates.append(growth_rate)
    
    # Calculate metrics
    avg_growth = np.mean(growth_rates) if growth_rates else 0
    avg_volatility = np.std(growth_rates) if growth_rates else 0
    consistency_score = max(0, 10 - avg_volatility/5)  # Simple consistency score
    
    # Category-level performance
    category_performance = {}
    
    # Get common categories across years
    all_categories = set()
    for year in selected_years:
        if year in financial_data and 'sections' in financial_data[year]:
            for section in financial_data[year]['sections']:
                all_categories.add(section['name'])
    
    for category in all_categories:
        category_values = []
        for year in sorted(selected_years):
            if year in financial_data and 'sections' in financial_data[year]:
                for section in financial_data[year]['sections']:
                    if section['name'] == category:
                        category_values.append(section['value'])
                        break
        
        if len(category_values) >= 2:
            cat_growth_rates = []
            for i in range(1, len(category_values)):
                if category_values[i-1] > 0:
                    rate = ((category_values[i] - category_values[i-1]) / category_values[i-1]) * 100
                    cat_growth_rates.append(rate)
            
            category_performance[category] = {
                'growth_rate': np.mean(cat_growth_rates) if cat_growth_rates else 0,
                'volatility': np.std(cat_growth_rates) if cat_growth_rates else 0,
                'mean_value': np.mean(category_values)
            }
    
    return {
        'average_growth_rate': avg_growth,
        'average_volatility': avg_volatility,
        'consistency_score': consistency_score,
        'efficiency_trend': 0,  # Placeholder
        'category_performance': category_performance
    }


def _calculate_internal_benchmarks(financial_data: Dict, selected_years: List[int]) -> Dict:
    """Calculate internal benchmarking metrics"""
    
    yearly_metrics = {}
    
    for year in selected_years:
        if year in financial_data and 'sections' in financial_data[year]:
            sections = financial_data[year]['sections']
            total_expenses = sum(section['value'] for section in sections)
            
            # Simple efficiency metric (could be enhanced with revenue data)
            efficiency = 1 / (total_expenses / 1000000) if total_expenses > 0 else 0
            
            yearly_metrics[year] = {
                'total_expenses': total_expenses,
                'efficiency': efficiency,
                'num_categories': len(sections)
            }
    
    # Calculate growth rates
    sorted_years = sorted(yearly_metrics.keys())
    for i in range(1, len(sorted_years)):
        current_year = sorted_years[i]
        previous_year = sorted_years[i-1]
        
        prev_total = yearly_metrics[previous_year]['total_expenses']
        curr_total = yearly_metrics[current_year]['total_expenses']
        
        if prev_total > 0:
            growth_rate = ((curr_total - prev_total) / prev_total) * 100
            yearly_metrics[current_year]['growth_rate'] = growth_rate
    
    # Find best and worst years
    best_year = max(yearly_metrics.keys(), key=lambda y: yearly_metrics[y]['efficiency'])
    worst_year = min(yearly_metrics.keys(), key=lambda y: yearly_metrics[y]['efficiency'])
    
    return {
        'yearly_metrics': yearly_metrics,
        'best_year': best_year,
        'worst_year': worst_year
    }


def _calculate_scenario_projections(base_data: List[Dict], scenarios: Dict) -> Dict:
    """Calculate projections for different scenarios"""
    
    scenario_results = {}
    
    for scenario_name, params in scenarios.items():
        growth_factor = 1 + params['growth']
        efficiency_factor = 1 - params['efficiency']  # Efficiency reduces costs
        
        scenario_results[scenario_name] = {}
        
        for section in base_data:
            category = section['name']
            base_value = section['value']
            
            # Apply growth and efficiency adjustments
            projected_value = base_value * growth_factor * efficiency_factor
            scenario_results[scenario_name][category] = projected_value
    
    return scenario_results