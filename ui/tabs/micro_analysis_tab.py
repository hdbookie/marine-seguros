"""
Micro Analysis Tab Module
Provides detailed cost and expense analysis functionality
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.process_manager import process_detailed_monthly_data, apply_filters
from ui.components.filters import (
    render_time_period_filters,
    render_primary_filters,
    render_advanced_filters,
    build_filter_dict
)
from visualizations.micro_charts import (
    create_expense_pareto_chart,
    create_expense_treemap,
    create_expense_sankey,
    create_growth_analysis_chart,
    create_monthly_heatmap
)
from utils import format_currency, get_category_icon, get_category_name


def render_micro_analysis_tab(flexible_data: Dict) -> None:
    """
    Render the micro analysis tab for detailed cost and expense investigation
    
    Args:
        flexible_data: Processed financial data from flexible extractor
    """
    # Header with purpose statement
    st.header("🔬 Análise Micro - Custos e Despesas Detalhados")
    st.markdown("""
    <div style='background-color: #f0f9ff; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <p style='margin: 0; color: #0c5690;'>
            🔎 <strong>Investigue por que alguns anos foram melhores que outros</strong> - Analise linha por linha todos os custos e despesas para identificar onde houve aumentos ou reduções que impactaram os resultados.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if not flexible_data:
        st.info("📊 Carregue dados usando o extrator flexível para acessar a análise micro.")
        return
    
    # Process detailed monthly data
    if 'detailed_monthly_data' not in st.session_state:
        st.session_state.detailed_monthly_data = process_detailed_monthly_data(flexible_data)
    
    detailed_data = st.session_state.detailed_monthly_data
    
    if not detailed_data or not detailed_data['line_items']:
        st.warning("Nenhum dado de custo/despesa encontrado para análise.")
        return
    
    # Get available years
    years = sorted([str(y) for y in flexible_data.keys()])
    current_year = years[-1] if years else None
    
    # Initialize session state for filters
    if 'details_year_filter' not in st.session_state:
        st.session_state.details_year_filter = [current_year] if current_year else []
    if 'details_month_filter' not in st.session_state:
        st.session_state.details_month_filter = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                                                'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    if 'details_search_term' not in st.session_state:
        st.session_state.details_search_term = ""
    
    # Calculate all_items early for use in filters
    all_items = [item for item in detailed_data['line_items'] if item['categoria'] != 'revenue']
    
    # FILTERS SECTION - At the top for better UX
    st.markdown("### 🔍 Filtros")
    
    # Time period quick filters
    render_time_period_filters(years, "details")
    
    # Primary filters
    all_categories = [cat for cat in detailed_data['summary']['total_categories'] if cat != 'revenue']
    selected_years, selected_categories, search_term = render_primary_filters(
        years, all_categories, "details"
    )
    
    # Advanced filters
    advanced_filters = render_advanced_filters(all_items, key_prefix="details")
    
    st.markdown("---")
    
    # Build complete filter dictionary
    filters = build_filter_dict(selected_years, selected_categories, search_term, advanced_filters)
    
    # Apply filters
    filtered_items = apply_filters(detailed_data['line_items'], filters)
    
    # Analysis Mode Selector
    st.markdown("### 🎯 O que você quer analisar?")
    
    analysis_mode = st.radio(
        "Escolha uma análise focada:",
        ["🏆 Maiores Gastos", "📈 Crescimento Rápido", "🔄 Custos Recorrentes", "💡 Oportunidades"],
        horizontal=True,
        key="micro_analysis_mode"
    )
    
    # Quick Summary Cards
    render_summary_cards(filtered_items)
    
    # Render analysis based on selected mode
    if analysis_mode == "🏆 Maiores Gastos":
        render_top_expenses_analysis(filtered_items)
    elif analysis_mode == "📈 Crescimento Rápido":
        render_growth_analysis(filtered_items, detailed_data, selected_years)
    elif analysis_mode == "🔄 Custos Recorrentes":
        render_recurring_expenses_analysis(filtered_items)
    elif analysis_mode == "💡 Oportunidades":
        render_opportunities_analysis(filtered_items)
    
    # Debug info
    if len(filtered_items) == 0 and detailed_data['line_items']:
        with st.expander("🔍 Debug: Por que não há itens?", expanded=False):
            st.write(f"Total de itens antes dos filtros: {len(detailed_data['line_items'])}")
            st.write(f"Anos selecionados: {selected_years}")
            st.write(f"Meses selecionados: {filters.get('months', 'Todos')}")
            st.write(f"Categorias selecionadas: {selected_categories}")
            st.write(f"Termo de busca: '{search_term}'")


def render_summary_cards(items: List[Dict]) -> None:
    """Render summary metric cards"""
    st.markdown("### 📊 Resumo Rápido")
    summary_cols = st.columns(5)
    
    with summary_cols[0]:
        total_annual = sum(item['valor_anual'] for item in items)
        st.metric(
            "💸 Total Custos/Despesas",
            format_currency(total_annual),
            f"{len(items)} itens"
        )
    
    with summary_cols[1]:
        # Biggest single expense
        if items:
            biggest_expense = max(items, key=lambda x: x['valor_anual'])
            st.metric(
                "🔝 Maior Gasto",
                format_currency(biggest_expense['valor_anual']),
                biggest_expense['descricao'][:20] + "..."
            )
        else:
            st.metric("🔝 Maior Gasto", "N/A", "")
    
    with summary_cols[2]:
        # Average expense
        avg_expense = total_annual / len(items) if items else 0
        st.metric(
            "📊 Média",
            format_currency(avg_expense),
            "por item"
        )
    
    with summary_cols[3]:
        # Growth indicator
        years_in_data = list(set(item['ano'] for item in items))
        if len(years_in_data) > 1:
            oldest_year = min(years_in_data)
            newest_year = max(years_in_data)
            old_total = sum(item['valor_anual'] for item in items if item['ano'] == oldest_year)
            new_total = sum(item['valor_anual'] for item in items if item['ano'] == newest_year)
            growth = ((new_total - old_total) / old_total * 100) if old_total > 0 else 0
            st.metric(
                "📈 Crescimento",
                f"{growth:+.1f}%",
                f"{oldest_year} → {newest_year}"
            )
        else:
            st.metric("📈 Crescimento", "N/A", "Selecione 2 anos")
    
    with summary_cols[4]:
        # Concentration
        if items:
            top_10_expenses = sorted(items, key=lambda x: x['valor_anual'], reverse=True)[:10]
            top_10_total = sum(item['valor_anual'] for item in top_10_expenses)
            concentration = (top_10_total / total_annual * 100) if total_annual > 0 else 0
            st.metric(
                "🎯 Concentração",
                f"{concentration:.0f}%",
                "nos top 10 itens"
            )
        else:
            st.metric("🎯 Concentração", "N/A", "")


def render_top_expenses_analysis(items: List[Dict]) -> None:
    """Render analysis of top expenses"""
    st.info("🎯 **Foco:** Seus maiores gastos - onde pequenas otimizações geram grandes economias")
    
    if not items:
        st.warning("Nenhum item encontrado para os filtros selecionados.")
        return
    
    top_expenses = sorted(items, key=lambda x: x['valor_anual'], reverse=True)[:20]
    
    # Create tabs for different visualizations
    viz_tabs = st.tabs(["📊 Pareto", "🌳 Treemap", "🔀 Sankey", "🗓️ Mapa de Calor"])
    
    with viz_tabs[0]:
        fig = create_expense_pareto_chart(top_expenses)
        st.plotly_chart(fig, use_container_width=True)
    
    with viz_tabs[1]:
        fig = create_expense_treemap(items)
        st.plotly_chart(fig, use_container_width=True)
    
    with viz_tabs[2]:
        fig = create_expense_sankey(items[:50])  # Limit for readability
        st.plotly_chart(fig, use_container_width=True)
    
    with viz_tabs[3]:
        fig = create_monthly_heatmap(top_expenses)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    with st.expander("📋 Tabela Detalhada", expanded=False):
        df_display = pd.DataFrame([
            {
                'Descrição': item['descricao'],
                'Categoria': get_category_name(item['categoria']),
                'Subcategoria': item['subcategoria_nome'],
                'Valor Anual': item['valor_anual'],
                'Média Mensal': item['valor_anual'] / 12,
                'Ano': item['ano']
            }
            for item in top_expenses
        ])
        
        # Format currency columns
        for col in ['Valor Anual', 'Média Mensal']:
            df_display[col] = df_display[col].apply(lambda x: format_currency(x))
        
        st.dataframe(df_display, use_container_width=True)


def render_growth_analysis(items: List[Dict], detailed_data: Dict, selected_years: List[str]) -> None:
    """Render growth analysis of expenses"""
    st.info("📈 **Foco:** Despesas com maior variação - identifique tendências preocupantes")
    
    if len(selected_years) < 2:
        st.warning("Selecione pelo menos 2 anos para análise de crescimento.")
        return
    
    # Group items by year
    items_by_year = {}
    for year in selected_years:
        year_int = int(year)
        items_by_year[year_int] = [
            item for item in items if str(item['ano']) == year
        ]
    
    # Create growth chart
    fig = create_growth_analysis_chart(items_by_year)
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate and show top growers/shrinkers
    growth_analysis = []
    
    # Get unique descriptions
    all_descriptions = set()
    for year_items in items_by_year.values():
        for item in year_items:
            all_descriptions.add(item['descricao'])
    
    for desc in all_descriptions:
        values_by_year = {}
        for year, year_items in items_by_year.items():
            for item in year_items:
                if item['descricao'] == desc:
                    values_by_year[year] = item['valor_anual']
                    break
        
        if len(values_by_year) >= 2:
            years_sorted = sorted(values_by_year.keys())
            old_value = values_by_year.get(years_sorted[0], 0)
            new_value = values_by_year.get(years_sorted[-1], 0)
            
            if old_value > 0:
                growth = ((new_value - old_value) / old_value) * 100
                growth_analysis.append({
                    'description': desc,
                    'old_value': old_value,
                    'new_value': new_value,
                    'growth': growth,
                    'absolute_change': new_value - old_value
                })
    
    # Show top growers and shrinkers
    if growth_analysis:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🚀 Maiores Aumentos")
            top_growers = sorted(growth_analysis, key=lambda x: x['growth'], reverse=True)[:10]
            for item in top_growers:
                if item['growth'] > 0:
                    st.write(f"**{item['description'][:40]}...**")
                    st.write(f"↗️ {item['growth']:.1f}% ({format_currency(item['old_value'])} → {format_currency(item['new_value'])})")
                    st.write("---")
        
        with col2:
            st.markdown("#### 📉 Maiores Reduções")
            top_shrinkers = sorted(growth_analysis, key=lambda x: x['growth'])[:10]
            for item in top_shrinkers:
                if item['growth'] < 0:
                    st.write(f"**{item['description'][:40]}...**")
                    st.write(f"↘️ {item['growth']:.1f}% ({format_currency(item['old_value'])} → {format_currency(item['new_value'])})")
                    st.write("---")


def render_recurring_expenses_analysis(items: List[Dict]) -> None:
    """Render analysis of recurring expenses"""
    st.info("🔄 **Foco:** Custos fixos e recorrentes - base da sua estrutura de custos")
    
    if not items:
        st.warning("Nenhum item encontrado para os filtros selecionados.")
        return
    
    # Find recurring expenses (present in 10+ months)
    recurring_expenses = []
    for item in items:
        months_with_value = sum(1 for v in item['valores_mensais'].values() if v > 0)
        if months_with_value >= 10:
            monthly_avg = item['valor_anual'] / 12
            recurring_expenses.append({
                'item': item,
                'months_active': months_with_value,
                'monthly_avg': monthly_avg
            })
    
    if not recurring_expenses:
        st.warning("Nenhuma despesa recorrente encontrada (presente em 10+ meses).")
        return
    
    # Sort by monthly average
    recurring_sorted = sorted(recurring_expenses, key=lambda x: x['monthly_avg'], reverse=True)
    
    # Group by type
    recurring_groups = {
        "Folha de Pagamento": [],
        "Infraestrutura": [],
        "Serviços": [],
        "Benefícios": [],
        "Outros": []
    }
    
    for rec in recurring_sorted:
        item = rec['item']
        desc_lower = item['descricao'].lower()
        
        if any(word in desc_lower for word in ['salário', 'funcionário', 'folha']):
            recurring_groups["Folha de Pagamento"].append(rec)
        elif any(word in desc_lower for word in ['aluguel', 'energia', 'água', 'condomínio']):
            recurring_groups["Infraestrutura"].append(rec)
        elif any(word in desc_lower for word in ['internet', 'telefone', 'software', 'sistema']):
            recurring_groups["Serviços"].append(rec)
        elif any(word in desc_lower for word in ['vale', 'benefício', 'plano']):
            recurring_groups["Benefícios"].append(rec)
        else:
            recurring_groups["Outros"].append(rec)
    
    # Show groups
    for group_name, group_items in recurring_groups.items():
        if group_items:
            group_monthly = sum(item['monthly_avg'] for item in group_items)
            group_annual = sum(item['item']['valor_anual'] for item in group_items)
            
            with st.expander(f"**{group_name}** - {format_currency(group_monthly)}/mês ({len(group_items)} itens)", expanded=True):
                st.caption(f"Total anual: {format_currency(group_annual)}")
                
                for rec in group_items[:10]:  # Show top 10
                    item = rec['item']
                    col1, col2, col3 = st.columns([4, 2, 2])
                    with col1:
                        st.write(f"• {item['descricao']}")
                    with col2:
                        st.write(f"{format_currency(rec['monthly_avg'])}/mês")
                    with col3:
                        st.write(f"✓ {rec['months_active']} meses")


def render_opportunities_analysis(items: List[Dict]) -> None:
    """Render analysis of cost-saving opportunities"""
    st.info("💡 **Foco:** Oportunidades de economia identificadas automaticamente")
    
    if not items:
        st.warning("Nenhum item encontrado para os filtros selecionados.")
        return
    
    opportunities = []
    
    # 1. Duplicate or similar expenses
    descriptions = {}
    for item in items:
        # Normalize description
        key_words = sorted(item['descricao'].lower().split()[:3])  # First 3 words
        key = ' '.join(key_words)
        if key not in descriptions:
            descriptions[key] = []
        descriptions[key].append(item)
    
    # Find potential duplicates
    for key, similar_items in descriptions.items():
        if len(similar_items) > 1:
            total = sum(item['valor_anual'] for item in similar_items)
            opportunities.append({
                'type': 'Possível Duplicação',
                'description': f"{len(similar_items)} despesas similares: {similar_items[0]['descricao'][:30]}...",
                'saving': total * 0.1,  # Assume 10% saving potential
                'items': similar_items
            })
    
    # 2. Expenses that vary significantly month to month
    for item in items:
        monthly_values = [v for v in item['valores_mensais'].values() if v > 0]
        if len(monthly_values) >= 6:
            avg = sum(monthly_values) / len(monthly_values)
            std_dev = (sum((v - avg) ** 2 for v in monthly_values) / len(monthly_values)) ** 0.5
            cv = std_dev / avg if avg > 0 else 0  # Coefficient of variation
            
            if cv > 0.5:  # High variation
                opportunities.append({
                    'type': 'Alta Variação',
                    'description': f"{item['descricao']} - varia muito mês a mês",
                    'saving': item['valor_anual'] * 0.15,
                    'items': [item]
                })
    
    # 3. Small recurring expenses that add up
    small_recurring = [item for item in items 
                      if item['valor_anual'] < 5000 and 
                      sum(1 for v in item['valores_mensais'].values() if v > 0) >= 10]
    
    if len(small_recurring) > 5:
        total_small = sum(item['valor_anual'] for item in small_recurring)
        opportunities.append({
            'type': 'Pequenas Despesas',
            'description': f"{len(small_recurring)} pequenas despesas recorrentes",
            'saving': total_small * 0.2,
            'items': small_recurring
        })
    
    # Sort opportunities by saving potential
    opportunities_sorted = sorted(opportunities, key=lambda x: x['saving'], reverse=True)[:10]
    
    total_saving_potential = sum(opp['saving'] for opp in opportunities_sorted)
    
    if opportunities_sorted:
        st.success(f"🎯 **Potencial de economia identificado: {format_currency(total_saving_potential)}/ano**")
        
        for i, opp in enumerate(opportunities_sorted, 1):
            with st.expander(f"{i}. {opp['type']} - Economia potencial: {format_currency(opp['saving'])}", expanded=(i <= 3)):
                st.write(f"**{opp['description']}**")
                
                # Show items
                for item in opp['items'][:5]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"• {item['descricao']}")
                    with col2:
                        st.write(format_currency(item['valor_anual']))
                
                if len(opp['items']) > 5:
                    st.caption(f"... e {len(opp['items']) - 5} mais")
                
                # Action suggestion
                if opp['type'] == 'Possível Duplicação':
                    st.info("💡 **Ação:** Revisar se são realmente necessárias todas essas despesas similares")
                elif opp['type'] == 'Alta Variação':
                    st.info("💡 **Ação:** Negociar contrato fixo ou investigar causas da variação")
                elif opp['type'] == 'Pequenas Despesas':
                    st.info("💡 **Ação:** Consolidar fornecedores ou cancelar serviços não essenciais")
    else:
        st.success("✅ Estrutura de custos otimizada - poucas oportunidades óbvias de economia")