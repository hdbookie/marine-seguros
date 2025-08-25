"""
Native Hierarchy Renderer for Micro Analysis V2
Displays Excel data in its original 3-level structure
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
from utils import format_currency
from utils.hierarchy_consolidator import HierarchyConsolidator
from .year_comparison import render_year_comparison


def render_native_hierarchy_tab(financial_data: Dict, full_financial_data: Dict = None):
    """
    Render the native Excel hierarchy preserving the original structure
    
    Args:
        financial_data: Current year's financial data
        full_financial_data: All years' financial data for advanced analytics
    """
    st.header("📊 Estrutura Nativa do Excel")
    
    if not financial_data:
        st.warning("Nenhum dado disponível para exibir.")
        return
    
    # Unified control row with time period selector
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    # First, render visualization type to determine if we need multi-select
    with col3:
        # Visualization type selector - only show implemented options
        visualization_type = st.selectbox(
            "🔧 Visualização",
            [
                "📂 Estrutura Hierárquica",
                "📊 Comparação Entre Anos",
                "📈 Evolução Subcategorias",
                "🔍 Exploração Interativa",
                "🌊 Análise Waterfall"
            ],
            index=0,
            key="viz_type_selector",
            help="💡 Para visão mensal dentro de um ano: use 'Estrutura Hierárquica' + 'Mensal'. Para comparar meses entre anos: use 'Comparação Entre Anos'. Use 'Exploração Interativa' para navegar pelos níveis hierárquicos."
        )
    
    with col1:
        # Year selector - support both single and multi-year selection
        available_years = sorted(financial_data.keys())
        
        # Check if this is a comparison visualization that needs multiple years
        needs_multi_year = visualization_type in ["📊 Comparação Entre Anos", "📈 Evolução Subcategorias"]
        if needs_multi_year and len(available_years) >= 2:
            selected_years = st.multiselect(
                "📅 Anos (Comparação)",
                available_years,
                default=available_years[-2:] if len(available_years) >= 2 else available_years,
                key="year_multiselect"
            )
            if not selected_years:
                selected_years = [available_years[-1]]
            selected_year = selected_years[0]
        else:
            selected_year = st.selectbox(
                "📅 Ano",
                available_years,
                index=len(available_years) - 1 if available_years else 0,
                key="year_selectbox"
            )
            selected_years = [selected_year]
    
    with col2:
        # Enhanced time period selector (matching macro dashboard)
        time_period = st.selectbox(
            "📊 Período",
            ["📅 Anual", "📊 Mensal", "📈 Trimestral", "🗓️ Trimestre Personalizado", "📆 Semestral", "⚙️ Personalizado"],
            index=0,
            key="micro_v2_time_period"
        )
    
    with col4:
        # Show details toggle
        show_details = st.checkbox("🔍 Detalhes", value=False)
    
    # Validate data availability for selected years
    missing_years = [year for year in selected_years if year not in financial_data]
    if missing_years:
        st.error(f"Dados não encontrados para: {', '.join(map(str, missing_years))}")
        return
    
    # Get data for primary year (for single-year visualizations)
    year_data = financial_data[selected_year]
    
    st.markdown("---")
    
    # Get period-aware data
    period_data = _get_period_data(year_data, time_period)
    
    # Apply hierarchy consolidation to fix misplaced items like Energia Elétrica
    consolidator = HierarchyConsolidator()
    period_data = consolidator.consolidate_year_data(period_data)
    
    # Prepare multi-year data for comparison views
    multi_year_data = {year: _get_period_data(financial_data[year], time_period) for year in selected_years}
    
    # Apply hierarchy consolidation to fix misplaced items like Energia Elétrica
    consolidator = HierarchyConsolidator()
    multi_year_data = {year: consolidator.consolidate_year_data(data) for year, data in multi_year_data.items()}
    
    # Render selected visualization
    st.markdown("---")
    
    if visualization_type == "📂 Estrutura Hierárquica":
        expand_all = st.checkbox("Expandir Tudo", value=False) if show_details else False
        if 'sections' in period_data:
            _render_hierarchy_tree(period_data['sections'], time_period, expand_all)
            # Show detailed table if details enabled
            if show_details:
                st.markdown("---")
                _render_detailed_table(period_data)
    
    elif visualization_type == "📊 Comparação Entre Anos":
        if len(selected_years) < 2:
            st.warning("⚠️ Selecione pelo menos 2 anos para comparação.")
            return
        
        # Render monthly comparison between years
        _render_multi_year_comparison(multi_year_data, selected_years, time_period, show_details)
    
    elif visualization_type == "📈 Evolução Subcategorias":
        if len(selected_years) < 2:
            st.warning("⚠️ Selecione pelo menos 2 anos para visualizar a evolução das subcategorias.")
            return
        
        # Render subcategory evolution across years
        _render_subcategory_evolution(multi_year_data, selected_years, time_period)
    
    elif visualization_type == "🔍 Exploração Interativa":
        # Render interactive drill-down visualization
        _render_interactive_drilldown(period_data, selected_year, time_period)
    
    elif visualization_type == "🌊 Análise Waterfall":
        if time_period == "📅 Anual":
            from .advanced_visualizations import render_waterfall_drilldown
            render_waterfall_drilldown({selected_year: period_data}, selected_year)
        elif time_period == "📊 Mensal":
            from .advanced_visualizations import render_monthly_waterfall
            render_monthly_waterfall(period_data, selected_year, time_period)
        else:
            # Handle quarterly, semestral, and other time periods
            from .advanced_visualizations import render_period_waterfall
            render_period_waterfall(period_data, selected_year, time_period)
        
        # Add composition chart for context
        if show_details:
            st.markdown("---")
            st.markdown("### 📊 Composição por Categoria")
            _render_composition_chart(period_data)
    
    else:
        # Fallback for any unhandled visualization type
        st.info("🚧 Esta visualização está em desenvolvimento.")
    
    # Calculations section removed for cleaner interface


def _filter_expense_sections(sections: List[Dict], include_revenue: bool = False) -> List[Dict]:
    """
    Filter sections to optionally include or exclude revenue categories
    
    Args:
        sections: List of section dictionaries
        include_revenue: If True, include revenue categories; if False, filter them out
    """
    if include_revenue:
        # Return all sections including revenue
        return sections
    
    # Filter out revenue categories to focus on costs/expenses only
    revenue_categories = ['FATURAMENTO']
    return [
        section for section in sections 
        if section.get('name', '').upper() not in [cat.upper() for cat in revenue_categories]
    ]


def _render_hierarchy_tree(sections: List[Dict], time_period: str, expand_all: bool):
    """
    Render the hierarchical structure as an expandable tree with period breakdown
    """
    st.markdown("### 📂 Estrutura Hierárquica")
    
    # Show all sections including revenue (Faturamento)
    # We now include revenue as a major category alongside expenses
    
    # Separate revenue and expense sections for better organization
    revenue_sections = [s for s in sections if s.get('name', '').upper() == 'FATURAMENTO']
    expense_sections = [s for s in sections if s.get('name', '').upper() != 'FATURAMENTO']
    
    # Count total sections
    total_sections = len(revenue_sections) + len(expense_sections)
    
    if revenue_sections:
        st.info(f"📊 Mostrando {total_sections} seções ({len(revenue_sections)} de receita e {len(expense_sections)} de custos)")
    else:
        st.info(f"📊 Mostrando {len(expense_sections)} seções de custos")
    
    # Show revenue sections first (if any)
    for section in revenue_sections:
        _render_section_tree(section, time_period, expand_all, is_revenue=True)
    
    # Then show expense sections
    for section in expense_sections:
        _render_section_tree(section, time_period, expand_all, is_revenue=False)


def _render_section_tree(section: Dict, time_period: str, expand_all: bool, is_revenue: bool = False):
    """
    Render a single section of the hierarchy tree
    """
    # Add revenue icon if this is a revenue section
    section_icon = "💰 " if is_revenue else ""
    
    # Calculate max monthly value across all items in this section for consistent scaling
    section_max_monthly = 0
    if time_period == "📊 Mensal":
        # Include section's own monthly data
        section_monthly = section.get('monthly', {})
        if section_monthly:
            section_max = max(section_monthly.values()) if section_monthly.values() else 0
            section_max_monthly = max(section_max_monthly, section_max)
        
        # Check all subcategories and items
        for subcat in section.get('subcategories', []):
            # Check subcategory monthly values
            subcat_monthly = subcat.get('monthly', {})
            if subcat_monthly:
                subcat_max = max(subcat_monthly.values()) if subcat_monthly.values() else 0
                section_max_monthly = max(section_max_monthly, subcat_max)
            
            # Check item monthly values
            for item in subcat.get('items', []):
                item_monthly = item.get('monthly', {})
                if item_monthly:
                    item_max = max(item_monthly.values()) if item_monthly.values() else 0
                    section_max_monthly = max(section_max_monthly, item_max)
    
    # Determine chart type for this section
    if time_period == "📊 Mensal" and section_max_monthly > 0:
        # For monthly view with data, show chart type selector
        chart_type_key = f"chart_type_{section['name']}"
    else:
        # Default chart type for non-monthly views or empty data
        chart_type_key = None
        
    # Default chart type
    chart_type = "📊 Barras" if time_period != "📊 Mensal" else "📈 Linha"
    
    # Level 1: Main Section - Add revenue icon if applicable
    section_name = f"{section_icon}{section['name']}"
    with st.expander(
        f"**{section_name}** - {format_currency(section.get('value', 0))}",
        expanded=expand_all
    ):
        # Show period breakdown if not annual
        if time_period != "📅 Anual" and section.get('period_breakdown'):
            _render_period_breakdown(section['period_breakdown'], section['name'], time_period, chart_type)
        
        # Show scale indicator and chart type selector for monthly view
        if time_period == "📊 Mensal" and section_max_monthly > 0:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📏 Escala dos gráficos mensais: R$ 0 - {format_currency(section_max_monthly)}")
            with col2:
                chart_type = st.radio(
                    "Tipo",
                    ["📈 Linha", "📊 Barras"],
                    horizontal=True,
                    key=chart_type_key
                )
        
        # Group subcategories by type (parent vs standalone)
        parent_subcats = []
        standalone_subcats = []
        
        for subcat in section.get('subcategories', []):
            has_items = len(subcat.get('items', [])) > 0
            if has_items:
                parent_subcats.append(subcat)
            else:
                standalone_subcats.append(subcat)
        
        # First render parent subcategories with their children
        for i, subcat in enumerate(parent_subcats):
            # Calculate max monthly value for this specific subcategory
            subcat_max_monthly = 0
            if time_period == "📊 Mensal":
                # Check subcategory's own monthly values
                subcat_monthly = subcat.get('monthly', {})
                if subcat_monthly:
                    subcat_max = max(subcat_monthly.values()) if subcat_monthly.values() else 0
                    subcat_max_monthly = max(subcat_max_monthly, subcat_max)
                
                # Check all items within this subcategory
                for item in subcat.get('items', []):
                    item_monthly = item.get('monthly', {})
                    if item_monthly:
                        item_max = max(item_monthly.values()) if item_monthly.values() else 0
                        subcat_max_monthly = max(subcat_max_monthly, item_max)
            
            # Parent header with proper tree symbol
            is_last_parent = (i == len(parent_subcats) - 1) and len(standalone_subcats) == 0
            parent_symbol = "└──" if is_last_parent else "├──"
            
            st.markdown(f"\n**{parent_symbol} {subcat['name']}** - {format_currency(subcat.get('value', 0))}")
            
            # Show sum verification
            items_sum = sum(item.get('value', 0) for item in subcat.get('items', []))
            if abs(subcat.get('value', 0) - items_sum) < 100:
                st.caption(f"    ✓ Soma dos filhos: {format_currency(items_sum)}")
            
            # Show subcategory-specific scale indicator for monthly view
            if time_period == "📊 Mensal" and subcat_max_monthly > 0:
                st.caption(f"    📏 Escala desta categoria: R$ 0 - {format_currency(subcat_max_monthly)}")
            
            # Show period breakdown for subcategory if available
            if time_period != "📅 Anual" and subcat.get('period_breakdown'):
                _render_period_sparkline(subcat['period_breakdown'], time_period, chart_type)
            elif time_period == "📊 Mensal" and subcat.get('monthly') and not subcat.get('items'):
                # Show subcategory monthly sparkline if it has no children
                _render_item_monthly_sparkline(subcat['monthly'], subcat_max_monthly, chart_type)
            
            # Render children with proper indentation
            items = subcat.get('items', [])
            for j, item in enumerate(items):
                # Determine tree symbols for children
                is_last_child = j == len(items) - 1
                
                if is_last_parent:
                    # This is the last parent, use clean indentation
                    child_symbol = "    └──" if is_last_child else "    ├──"
                else:
                    # This parent has siblings, use continued indentation
                    child_symbol = "│   └──" if is_last_child else "│   ├──"
                
                st.markdown(f"{child_symbol} {item['name']} - {format_currency(item.get('value', 0))}")
                
                # Show monthly sparkline for item if in monthly view and data exists
                if time_period == "📊 Mensal" and item.get('monthly'):
                    # Use individual item's own scale for better visibility of trends
                    item_monthly = item.get('monthly', {})
                    item_max = max(item_monthly.values()) if item_monthly.values() else 0
                    _render_item_monthly_sparkline(item['monthly'], item_max, chart_type)
        
        # Then render standalone subcategories
        for i, subcat in enumerate(standalone_subcats):
            is_last = i == len(standalone_subcats) - 1
            symbol = "└──" if is_last else "├──"
            st.markdown(f"{symbol} {subcat['name']} - {format_currency(subcat.get('value', 0))}")
            
            # Show period breakdown or monthly sparkline
            if time_period == "📊 Mensal" and subcat.get('monthly'):
                _render_item_monthly_sparkline(subcat['monthly'], section_max_monthly, chart_type)
            elif time_period != "📅 Anual" and subcat.get('period_breakdown'):
                _render_period_sparkline(subcat['period_breakdown'], time_period, chart_type)


def _get_unified_chart_styling(level: str, chart_type: str = "📈 Linha", max_value: float = None):
    """
    Get unified styling parameters for consistent chart formatting across hierarchy levels
    
    Args:
        level: 'section', 'subcategory', or 'item'
        chart_type: '📈 Linha' or '📊 Barras'  
        max_value: Maximum value for Y-axis scaling
    """
    
    # Color scheme by hierarchy level
    colors = {
        'section': '#87CEEB',      # Light blue (matches current section charts)
        'subcategory': '#9370DB',  # Medium purple for subcategories
        'item': '#F08080'          # Light coral for individual items
    }
    
    # Height by hierarchy level  
    heights = {
        'section': 200,      # Taller for main sections
        'subcategory': 120,  # Medium for subcategories
        'item': 100          # Compact for individual items
    }
    
    # Common styling parameters
    base_style = {
        'height': heights[level],
        'color': colors[level],
        'margin': dict(l=20, r=10, t=10, b=20),
        'showlegend': False,
        'plot_bgcolor': 'rgba(250,250,250,0.3)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'xaxis': dict(
            showticklabels=True,
            tickfont=dict(size=9),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=False,
            tickangle=0
        ),
        'yaxis': dict(
            showticklabels=level == 'section',  # Only show Y labels for section level
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=True,
            zerolinecolor='rgba(128,128,128,0.3)',
            range=[0, max_value * 1.05] if max_value and max_value > 0 else None
        )
    }
    
    return base_style


def _render_monthly_bar(monthly_data: Dict, title: str):
    """
    Render a small monthly bar chart
    """
    if not monthly_data:
        return
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    values = [monthly_data.get(m, 0) for m in months]
    
    fig = go.Figure(data=[
        go.Bar(
            x=months,
            y=values,
            text=[format_currency(v) if v > 0 else '' for v in values],
            textposition='auto',
            marker_color='lightblue'
        )
    ])
    
    fig.update_layout(
        title=f"Distribuição Mensal - {title}",
        height=200,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_monthly_sparkline(monthly_data: Dict):
    """
    Render a simple sparkline for monthly data
    """
    if not monthly_data:
        return
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    values = [monthly_data.get(m, 0) for m in months]
    
    # Create a simple line chart
    df = pd.DataFrame({'Mês': months, 'Valor': values})
    st.line_chart(df.set_index('Mês'), height=100)


def _render_period_breakdown(period_data: Dict, title: str, time_period: str, chart_type: str = "📊 Barras"):
    """
    Render period breakdown chart based on selected time period with unified styling
    """
    if not period_data:
        return
    
    periods = list(period_data.keys())
    values = [period_data.get(p, 0) for p in periods]
    max_value = max(values) if values else 0
    
    # Get unified styling for section level
    styling = _get_unified_chart_styling('section', chart_type, max_value)
    
    fig = go.Figure()
    
    # Choose chart type based on selection
    if chart_type == "📊 Barras":
        fig.add_trace(go.Bar(
            x=periods,
            y=values,
            text=[format_currency(v) if v > 0 else '' for v in values],
            textposition='auto',
            marker_color=styling['color'],
            showlegend=False
        ))
    else:
        fig.add_trace(go.Scatter(
            x=periods,
            y=values,
            mode='lines+markers',
            line=dict(color=styling['color'], width=3),
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>',
            showlegend=False
        ))
    
    period_name = {
        "📊 Mensal": "Mensal",
        "📈 Trimestral": "Trimestral", 
        "📆 Semestral": "Semestral"
    }.get(time_period, "Período")
    
    # Apply unified styling
    fig.update_layout(
        title=f"Distribuição {period_name} - {title}",
        height=styling['height'],
        margin=styling['margin'],
        xaxis=styling['xaxis'],
        yaxis=styling['yaxis'],
        plot_bgcolor=styling['plot_bgcolor'],
        paper_bgcolor=styling['paper_bgcolor'],
        showlegend=styling['showlegend']
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_period_sparkline(period_data: Dict, time_period: str, chart_type: str = "📈 Linha"):
    """
    Render a sparkline for period data with unified styling (subcategory level)
    """
    if not period_data:
        return
    
    periods = list(period_data.keys())
    values = [period_data.get(p, 0) for p in periods]
    max_value = max(values) if values else 0
    
    # Get unified styling for subcategory level
    styling = _get_unified_chart_styling('subcategory', chart_type, max_value)
    
    fig = go.Figure()
    
    # Choose chart type based on selection
    if chart_type == "📊 Barras":
        fig.add_trace(go.Bar(
            x=periods,
            y=values,
            marker_color=styling['color'],
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>',
            showlegend=False
        ))
    else:
        fig.add_trace(go.Scatter(
            x=periods,
            y=values,
            mode='lines+markers',
            line=dict(color=styling['color'], width=2),
            marker=dict(size=5),
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>',
            showlegend=False
        ))
    
    # Apply unified styling
    fig.update_layout(
        height=styling['height'],
        margin=styling['margin'],
        xaxis=styling['xaxis'],
        yaxis=styling['yaxis'],
        plot_bgcolor=styling['plot_bgcolor'],
        paper_bgcolor=styling['paper_bgcolor'],
        showlegend=styling['showlegend']
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_item_monthly_sparkline(monthly_data: Dict, max_value: float = None, chart_type: str = "📈 Linha"):
    """
    Render a compact monthly sparkline for individual items with consistent scaling
    """
    if not monthly_data:
        return
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    values = [monthly_data.get(m, 0) for m in months]
    
    # Get unified styling for item level
    styling = _get_unified_chart_styling('item', chart_type, max_value)
    
    # Always show all 12 months, even if some are zero
    fig = go.Figure()
    
    # Choose chart type based on selection
    if chart_type == "📊 Barras":
        # Bar chart for better value comparison
        fig.add_trace(go.Bar(
            x=months,
            y=values,
            marker_color=styling['color'],
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>',
            showlegend=False
        ))
    else:
        # Line chart (default)
        fig.add_trace(go.Scatter(
            x=months,
            y=values,
            mode='lines+markers',
            line=dict(color=styling['color'], width=2),
            marker=dict(size=4),
            hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>',
            showlegend=False
        ))
    
    # Apply unified styling
    fig.update_layout(
        height=styling['height'],
        margin=styling['margin'],
        xaxis=styling['xaxis'],
        yaxis=styling['yaxis'],
        plot_bgcolor=styling['plot_bgcolor'],
        paper_bgcolor=styling['paper_bgcolor'],
        showlegend=styling['showlegend']
    )
    
    # Find peak month for context
    if values and max(values) > 0:
        peak_month_idx = values.index(max(values))
        peak_month = months[peak_month_idx]
        peak_value = max(values)
        
        # Display chart aligned with other levels
        st.plotly_chart(fig, use_container_width=True)
        # Small context label with tree-style indentation
        st.caption(f"        📈 Pico: {peak_month} ({format_currency(peak_value)})")
    else:
        # Show message for empty data with tree-style indentation
        st.caption("        📊 Sem dados mensais")
            




def _render_detailed_table(year_data: Dict):
    """
    Render a detailed table view of the hierarchy
    """
    if 'sections' not in year_data:
        st.info("Dados não disponíveis para visualização")
        return
    
    # Filter out revenue categories to focus on costs/expenses
    expense_sections = _filter_expense_sections(year_data['sections'])
    
    # Build table data
    table_data = []
    
    for section in expense_sections:
        # Add section row
        table_data.append({
            'Nível': '1',
            'Item': f"📁 {section['name']}",
            'Valor': format_currency(section.get('value', 0)),
            'Tipo': 'Seção'
        })
        
        # Add subcategories
        for subcat in section.get('subcategories', []):
            table_data.append({
                'Nível': '2',
                'Item': f"  └─ {subcat['name']}",
                'Valor': format_currency(subcat.get('value', 0)),
                'Tipo': 'Subcategoria'
            })
            
            # Add items
            for item in subcat.get('items', []):
                table_data.append({
                    'Nível': '3',
                    'Item': f"      • {item['name']}",
                    'Valor': format_currency(item.get('value', 0)),
                    'Tipo': 'Item'
                })
    
    if table_data:
        df = pd.DataFrame(table_data)
        # Hide the level column but keep for sorting
        display_df = df[['Item', 'Valor', 'Tipo']]
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=600)
    else:
        st.info("Nenhum dado para exibir")


def _render_contribution_analysis(period_data: Dict, time_period: str, selected_year: int):
    """
    Render contribution analysis showing what contributes most to total expenses
    """
    st.header(f"🎯 Análise de Contribuição - {time_period} {selected_year}")
    
    if 'sections' not in period_data:
        st.info("Dados não disponíveis para análise de contribuição")
        return
    
    sections = period_data['sections']
    expense_sections = _filter_expense_sections(sections)
    
    if not expense_sections:
        st.info("Nenhuma seção de despesas encontrada")
        return
    
    # Calculate total expenses
    total_expenses = sum(section.get('value', 0) for section in expense_sections)
    
    if total_expenses <= 0:
        st.info("Dados insuficientes para análise de contribuição")
        return
    
    # Create contribution data
    contribution_data = []
    
    for section in expense_sections:
        section_value = section.get('value', 0)
        section_contribution = (section_value / total_expenses) * 100 if total_expenses > 0 else 0
        
        contribution_data.append({
            'category': section['name'],
            'value': section_value,
            'contribution': section_contribution,
            'level': 'Seção',
            'parent': None
        })
        
        # Add subcategories
        for subcat in section.get('subcategories', []):
            subcat_value = subcat.get('value', 0)
            subcat_contribution = (subcat_value / total_expenses) * 100 if total_expenses > 0 else 0
            
            contribution_data.append({
                'category': subcat['name'],
                'value': subcat_value,
                'contribution': subcat_contribution,
                'level': 'Subcategoria',
                'parent': section['name']
            })
            
            # Add individual items
            for item in subcat.get('items', []):
                item_value = item.get('value', 0)
                item_contribution = (item_value / total_expenses) * 100 if total_expenses > 0 else 0
                
                if item_contribution > 0.1:  # Only show items with >0.1% contribution
                    contribution_data.append({
                        'category': item['name'],
                        'value': item_value,
                        'contribution': item_contribution,
                        'level': 'Item',
                        'parent': f"{section['name']} > {subcat['name']}"
                    })
    
    # Sort by contribution descending
    contribution_data.sort(key=lambda x: x['contribution'], reverse=True)
    
    # Show top contributors
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Ranking de Contribuição")
        
        # Add selector for hierarchical level
        hierarchy_level = st.radio(
            "Nível de Análise",
            ["📂 Categorias Principais", "📁 Subcategorias", "📌 Itens Individuais"],
            horizontal=True,
            key="contribution_hierarchy_level"
        )
        
        # Filter data based on selected level
        if hierarchy_level == "📂 Categorias Principais":
            filtered_data = [item for item in contribution_data if item['level'] == 'Seção']
        elif hierarchy_level == "📁 Subcategorias":
            # Only show subcategories without their parent sections to avoid double counting
            filtered_data = [item for item in contribution_data if item['level'] == 'Subcategoria']
        else:  # Items Individuais
            # Show individual items
            filtered_data = [item for item in contribution_data if item['level'] == 'Item']
            if not filtered_data:
                st.info("Nenhum item individual encontrado com contribuição significativa")
                filtered_data = []
        
        # Create chart with filtered data
        categories = []
        for item in filtered_data[:10]:  # Top 10
            if item['level'] == 'Item' and item.get('parent'):
                # Show parent context for items
                categories.append(f"{item['category']} ({item['parent'].split(' > ')[-1]})")
            else:
                categories.append(item['category'])
        contributions = [item['contribution'] for item in filtered_data[:10]]
        values = [item['value'] for item in filtered_data[:10]]
        
        fig = go.Figure()
        
        # Color by contribution level
        colors = ['#e74c3c' if c > 20 else '#f39c12' if c > 10 else '#3498db' if c > 5 else '#95a5a6' for c in contributions]
        
        fig.add_trace(go.Bar(
            y=categories,
            x=contributions,
            orientation='h',
            marker_color=colors,
            text=[f"{c:.1f}%" for c in contributions],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>' +
                         'Contribuição: %{x:.1f}%<br>' +
                         f'Valor: R$ %{{customdata:,.0f}}<br>' +
                         '<extra></extra>',
            customdata=values
        ))
        
        fig.update_layout(
            title="Top 10 Contribuições para Despesas Totais",
            xaxis_title="Contribuição (%)",
            yaxis_title="Categoria",
            height=400,
            margin=dict(l=200)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Insights")
        
        # Top 3 contributors from filtered data
        top_3 = filtered_data[:3] if filtered_data else []
        top_3_total = sum(item['contribution'] for item in top_3)
        
        st.metric("Top 3 Concentração", f"{top_3_total:.1f}%")
        
        for i, item in enumerate(top_3, 1):
            if item['level'] == 'Item' and item.get('parent'):
                display_name = f"{item['category']} ({item['parent'].split(' > ')[-1]})"
            else:
                display_name = item['category']
            st.markdown(f"**{i}º** {display_name}: {item['contribution']:.1f}%")
        
        # Show total for verification
        total_shown = sum(item['contribution'] for item in filtered_data)
        if total_shown > 0:
            st.caption(f"Total mostrado: {total_shown:.1f}%")
        
        # Concentration analysis
        if top_3_total > 70:
            st.warning("🔴 Alta concentração - Top 3 categorias representam >70% das despesas")
        elif top_3_total > 50:
            st.info("🟡 Concentração moderada - Top 3 categorias representam >50% das despesas")
        else:
            st.success("🟢 Distribuição equilibrada de despesas")


def _render_heatmap_analysis(full_financial_data: Dict, time_period: str):
    """
    Render heatmap analysis showing changes across years and categories
    """
    st.header(f"🔥 Mapa de Calor - Variações {time_period}")
    
    available_years = sorted(full_financial_data.keys())
    if len(available_years) < 2:
        st.warning("São necessários pelo menos 2 anos de dados para o mapa de calor")
        return
    
    # Build comparison matrix
    categories = set()
    for year_data in full_financial_data.values():
        if 'sections' in year_data:
            for section in year_data['sections']:
                categories.add(section['name'])
                for subcat in section.get('subcategories', []):
                    categories.add(f"{section['name']} > {subcat['name']}")
    
    categories = sorted(list(categories))
    
    # Calculate year-over-year changes
    heatmap_data = []
    for i in range(1, len(available_years)):
        prev_year = available_years[i-1]
        curr_year = available_years[i]
        
        for category in categories:
            prev_value = _get_category_value(full_financial_data[prev_year], category)
            curr_value = _get_category_value(full_financial_data[curr_year], category)
            
            if prev_value > 0:
                change_pct = ((curr_value - prev_value) / prev_value) * 100
            else:
                change_pct = 100 if curr_value > 0 else 0
            
            heatmap_data.append({
                'category': category,
                'period': f"{prev_year}-{curr_year}",
                'change': change_pct,
                'prev_value': prev_value,
                'curr_value': curr_value
            })
    
    if not heatmap_data:
        st.info("Dados insuficientes para o mapa de calor")
        return
    
    # Create heatmap
    df = pd.DataFrame(heatmap_data)
    pivot_df = df.pivot(index='category', columns='period', values='change')
    
    # Create pivot dataframes for prev and curr values to use in hover
    pivot_prev = df.pivot(index='category', columns='period', values='prev_value')
    pivot_curr = df.pivot(index='category', columns='period', values='curr_value')
    
    # Create custom hover text with detailed information
    hover_text = []
    for i, category in enumerate(pivot_df.index):
        row_hover = []
        for j, period in enumerate(pivot_df.columns):
            change = pivot_df.iloc[i, j]
            prev_val = pivot_prev.iloc[i, j]
            curr_val = pivot_curr.iloc[i, j]
            
            text = f"<b>{category}</b><br>"
            text += f"<b>Período:</b> {period}<br>"
            text += f"<b>Valor Anterior:</b> R$ {prev_val:,.2f}<br>"
            text += f"<b>Valor Atual:</b> R$ {curr_val:,.2f}<br>"
            text += f"<b>Diferença:</b> R$ {(curr_val - prev_val):,.2f}<br>"
            text += f"<b>Variação:</b> {change:+.1f}%"
            row_hover.append(text)
        hover_text.append(row_hover)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale='RdYlBu_r',
        text=[[f"{val:.1f}%" for val in row] for row in pivot_df.values],
        texttemplate="%{text}",
        textfont={"size": 10},
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_text
    ))
    
    fig.update_layout(
        title="Mapa de Calor - Variações Percentuais por Categoria",
        height=max(400, len(categories) * 25),
        margin=dict(l=250)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Insights
    st.subheader("💡 Insights do Mapa de Calor")
    
    # Find biggest changes
    max_increase = df.loc[df['change'].idxmax()]
    max_decrease = df.loc[df['change'].idxmin()]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Maior Aumento", 
            max_increase['category'], 
            f"+{max_increase['change']:.1f}%"
        )
    with col2:
        st.metric(
            "Maior Redução", 
            max_decrease['category'], 
            f"{max_decrease['change']:.1f}%"
        )


def _get_category_value(year_data: Dict, category: str) -> float:
    """Helper function to get value for a category (including subcategories)"""
    if 'sections' not in year_data:
        return 0
    
    if " > " in category:
        # Subcategory
        section_name, subcat_name = category.split(" > ", 1)
        for section in year_data['sections']:
            if section['name'] == section_name:
                for subcat in section.get('subcategories', []):
                    if subcat['name'] == subcat_name:
                        return subcat.get('value', 0)
    else:
        # Main section
        for section in year_data['sections']:
            if section['name'] == category:
                return section.get('value', 0)
    
    return 0


def _render_sunburst(year_data: Dict):
    """
    Render a sunburst chart of the hierarchy
    """
    if 'sections' not in year_data:
        st.info("Dados não disponíveis para visualização")
        return
    
    labels = []
    parents = []
    values = []
    colors = []
    
    # Color map for main sections
    color_map = {
        'CUSTOS FIXOS': '#3498db',
        'CUSTOS VARIÁVEIS': '#2ecc71',
        'CUSTOS VARIÁVEIS': '#2ecc71',
        'CUSTOS NÃO OPERACIONAIS': '#e74c3c',
        'CUSTOS NAO OPERACIONAIS': '#e74c3c',
        'FATURAMENTO': '#f39c12',
        'RECEITAS': '#f39c12'
    }
    
    # Add root
    labels.append("Total")
    parents.append("")
    values.append(sum(s.get('value', 0) for s in year_data['sections']))
    colors.append('#95a5a6')
    
    for section in year_data['sections']:
        # Add Level 1
        section_name = section['name']
        labels.append(section_name)
        parents.append("Total")
        values.append(section.get('value', 0))
        colors.append(color_map.get(section_name, '#95a5a6'))
        
        # Add Level 2
        for subcat in section.get('subcategories', []):
            subcat_name = f"{section_name} - {subcat['name']}"
            labels.append(subcat['name'])
            parents.append(section_name)
            values.append(subcat.get('value', 0))
            colors.append(color_map.get(section_name, '#95a5a6'))
            
            # Add Level 3
            for item in subcat.get('items', []):
                labels.append(item['name'])
                parents.append(subcat['name'])
                values.append(item.get('value', 0))
                colors.append(color_map.get(section_name, '#95a5a6'))
    
    # Create custom hover text for more informative tooltips
    hover_texts = []
    for i, label in enumerate(labels):
        parent = parents[i] if i < len(parents) else ""
        value = values[i] if i < len(values) else 0
        
        text = f"<b>{label}</b><br>"
        text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
        
        # Calculate percentage based on parent
        if parent and parent in labels:
            parent_idx = labels.index(parent)
            parent_value = values[parent_idx] if parent_idx < len(values) else 0
            if parent_value > 0:
                pct = (value / parent_value) * 100
                text += f"<b>% de {parent}:</b> {pct:.1f}%<br>"
        
        # Calculate percentage of total
        if len(values) > 0 and values[0] > 0:  # First value is total
            pct_total = (value / values[0]) * 100
            text += f"<b>% do Total:</b> {pct_total:.1f}%"
        
        hover_texts.append(text)
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors),
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts
    ))
    
    fig.update_layout(
        height=500,
        margin=dict(t=30, b=0, l=0, r=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_treemap(year_data: Dict):
    """
    Render a treemap of the hierarchy
    """
    if 'sections' not in year_data:
        st.info("Dados não disponíveis para visualização")
        return
    
    data = []
    
    for section in year_data['sections']:
        section_name = section['name']
        
        for subcat in section.get('subcategories', []):
            subcat_name = subcat['name']
            
            if subcat.get('items'):
                for item in subcat['items']:
                    data.append({
                        'Section': section_name,
                        'Subcategory': subcat_name,
                        'Item': item['name'],
                        'Value': item.get('value', 0)
                    })
            else:
                # Add subcategory itself if no items
                data.append({
                    'Section': section_name,
                    'Subcategory': subcat_name,
                    'Item': subcat_name,
                    'Value': subcat.get('value', 0)
                })
    
    if not data:
        st.info("Nenhum dado para visualizar")
        return
    
    df = pd.DataFrame(data)
    
    # Calculate totals for better hover information
    total_value = df['Value'].sum()
    section_totals = df.groupby('Section')['Value'].sum().to_dict()
    subcat_totals = df.groupby(['Section', 'Subcategory'])['Value'].sum().to_dict()
    
    # Add custom hover data
    hover_data = []
    for _, row in df.iterrows():
        section = row['Section']
        subcat = row['Subcategory']
        item = row['Item']
        value = row['Value']
        
        text = f"<b>{item}</b><br>"
        text += f"<b>Seção:</b> {section}<br>"
        if item != subcat:
            text += f"<b>Subcategoria:</b> {subcat}<br>"
        text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
        
        # Percentage of subcategory
        subcat_total = subcat_totals.get((section, subcat), 0)
        if subcat_total > 0:
            pct_subcat = (value / subcat_total) * 100
            text += f"<b>% da Subcategoria:</b> {pct_subcat:.1f}%<br>"
        
        # Percentage of section
        section_total = section_totals.get(section, 0)
        if section_total > 0:
            pct_section = (value / section_total) * 100
            text += f"<b>% da Seção:</b> {pct_section:.1f}%<br>"
        
        # Percentage of total
        if total_value > 0:
            pct_total = (value / total_value) * 100
            text += f"<b>% do Total:</b> {pct_total:.1f}%"
        
        hover_data.append(text)
    
    df['hover_text'] = hover_data
    
    fig = px.treemap(
        df,
        path=['Section', 'Subcategory', 'Item'],
        values='Value',
        title='Mapa de Árvore - Hierarquia de Despesas',
        custom_data=['hover_text']
    )
    
    fig.update_traces(
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='%{customdata[0]}<extra></extra>'
    )
    
    fig.update_layout(height=500)
    
    st.plotly_chart(fig, use_container_width=True)


def _render_composition_chart(year_data: Dict):
    """
    Render a composition chart showing the breakdown
    """
    if 'sections' not in year_data:
        st.info("Dados não disponíveis para visualização")
        return
    
    # Filter out revenue categories to focus on costs/expenses
    expense_sections = _filter_expense_sections(year_data['sections'])
    
    # Prepare data for pie chart
    section_data = []
    for section in expense_sections:
        if section.get('value', 0) > 0:
            section_data.append({
                'name': section['name'],
                'value': section['value']
            })
    
    if not section_data:
        st.info("Nenhum dado para visualizar")
        return
    
    df = pd.DataFrame(section_data)
    
    # Calculate total and add custom hover data
    total_value = df['value'].sum()
    hover_texts = []
    
    for _, row in df.iterrows():
        name = row['name']
        value = row['value']
        
        text = f"<b>{name}</b><br>"
        text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
        text += f"<b>% do Total:</b> {(value/total_value*100):.1f}%<br>"
        
        # Add ranking
        rank = (df['value'] >= value).sum()
        text += f"<b>Ranking:</b> {rank}º de {len(df)}<br>"
        
        # Add comparison to average
        avg_value = df['value'].mean()
        if avg_value > 0:
            diff_avg = ((value - avg_value) / avg_value) * 100
            text += f"<b>Vs. Média:</b> {diff_avg:+.1f}%"
        
        hover_texts.append(text)
    
    df['hover_text'] = hover_texts
    
    # Create pie chart
    fig = px.pie(
        df,
        values='value',
        names='name',
        title='Composição das Despesas',
        custom_data=['hover_text']
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{customdata[0]}<extra></extra>'
    )
    
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show table breakdown
    # Create summary table below the pie chart
    st.markdown("#### 📋 Resumo por Categoria")
    
    summary_data = []
    total_expenses = sum(s.get('value', 0) for s in expense_sections)
    for section in expense_sections:
        section_total = section.get('value', 0)
        summary_data.append({
            'Categoria': section['name'],
            'Valor': format_currency(section_total),
            'Percentual': f"{(section_total / total_expenses * 100):.1f}%" if section_total > 0 and total_expenses > 0 else "0%"
        })
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)


def _get_period_data(year_data: Dict, time_period: str) -> Dict:
    """
    Transform year data based on selected time period
    """
    if time_period == "📅 Anual":
        return year_data
    
    # For non-annual periods, we need to aggregate monthly data
    period_data = {
        'sections': [],
        'calculations': year_data.get('calculations', {}),
        'monthly_data': year_data.get('monthly_data', {})
    }
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Define period groupings (enhanced to match macro dashboard)
    if time_period == "📈 Trimestral":
        periods = {
            'Q1': ['JAN', 'FEV', 'MAR'],
            'Q2': ['ABR', 'MAI', 'JUN'], 
            'Q3': ['JUL', 'AGO', 'SET'],
            'Q4': ['OUT', 'NOV', 'DEZ']
        }
    elif time_period == "🗓️ Trimestre Personalizado":
        # Brazilian business trimesters (common in Brazilian accounting)
        periods = {
            'T1': ['JAN', 'FEV', 'MAR', 'ABR'],
            'T2': ['MAI', 'JUN', 'JUL', 'AGO'], 
            'T3': ['SET', 'OUT', 'NOV', 'DEZ']
        }
    elif time_period == "📆 Semestral":
        periods = {
            'S1': ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN'],
            'S2': ['JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        }
    elif time_period == "📊 Mensal":
        periods = {month: [month] for month in months}
    elif time_period == "⚙️ Personalizado":
        # For now, default to quarterly - can be enhanced later with custom period selection
        periods = {
            'Q1': ['JAN', 'FEV', 'MAR'],
            'Q2': ['ABR', 'MAI', 'JUN'], 
            'Q3': ['JUL', 'AGO', 'SET'],
            'Q4': ['OUT', 'NOV', 'DEZ']
        }
    else:
        return year_data
    
    # Process each section
    for section in year_data.get('sections', []):
        processed_section = {
            'name': section['name'],
            'value': section.get('value', 0),
            'monthly': section.get('monthly', {}),
            'subcategories': [],
            'period_breakdown': {}
        }
        
        # Calculate period breakdown
        section_monthly = section.get('monthly', {})
        for period_name, period_months in periods.items():
            period_total = sum(section_monthly.get(month, 0) for month in period_months)
            processed_section['period_breakdown'][period_name] = period_total
        
        # Process subcategories
        for subcat in section.get('subcategories', []):
            # Process items to ensure monthly data is preserved
            processed_items = []
            for item in subcat.get('items', []):
                processed_item = {
                    'name': item['name'],
                    'level': item.get('level', 3),
                    'value': item.get('value', 0),
                    'monthly': item.get('monthly', {})  # Preserve monthly data for sparklines
                }
                processed_items.append(processed_item)
            
            processed_subcat = {
                'name': subcat['name'],
                'value': subcat.get('value', 0),
                'monthly': subcat.get('monthly', {}),
                'items': processed_items,
                'period_breakdown': {}
            }
            
            # Calculate period breakdown for subcategory
            subcat_monthly = subcat.get('monthly', {})
            for period_name, period_months in periods.items():
                period_total = sum(subcat_monthly.get(month, 0) for month in period_months)
                processed_subcat['period_breakdown'][period_name] = period_total
            
            processed_section['subcategories'].append(processed_subcat)
        
        period_data['sections'].append(processed_section)
    
    return period_data


def _render_basic_year_insights(year_data: Dict, selected_year: int):
    """
    Render enhanced intelligent insights for single year analysis
    """
    if 'sections' not in year_data:
        st.info("Dados não disponíveis para análise")
        return
    
    st.markdown("#### 🧠 Insights Inteligentes do Ano")
    
    # Filter out revenue categories to focus on costs/expenses
    sections = _filter_expense_sections(year_data['sections'])
    total_expenses = sum(s.get('value', 0) for s in sections)
    
    if total_expenses == 0:
        st.info("Nenhuma despesa registrada para análise")
        return
    
    # Calculate advanced insights
    insights = _generate_intelligent_insights(sections, total_expenses, selected_year)
    
    # Display key insights with smart alerts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**🎯 Principais Descobertas:**")
        for insight in insights['key_findings']:
            if insight['type'] == 'alert':
                st.warning(f"⚠️ {insight['message']}")
            elif insight['type'] == 'success':
                st.success(f"✅ {insight['message']}")
            else:
                st.info(f"💡 {insight['message']}")
        
        # Show expense distribution analysis
        st.markdown("**📊 Distribuição de Despesas:**")
        _render_expense_distribution_insights(sections, total_expenses)
    
    with col2:
        st.markdown("**📈 Métricas Chave:**")
        for metric in insights['metrics']:
            st.metric(
                metric['label'],
                metric['value'],
                delta=metric.get('delta'),
                help=metric.get('help')
            )
        
        # Show anomaly alerts
        if insights['anomalies']:
            st.markdown("**🚨 Anomalias Detectadas:**")
            for anomaly in insights['anomalies']:
                st.error(f"🔴 {anomaly}")


def _generate_intelligent_insights(sections: List[Dict], total_expenses: float, year: int) -> Dict:
    """
    Generate intelligent insights from expense data using advanced analytics
    """
    sorted_sections = sorted(sections, key=lambda x: x.get('value', 0), reverse=True)
    
    insights = {
        'key_findings': [],
        'metrics': [],
        'anomalies': []
    }
    
    # Calculate concentration metrics
    if sorted_sections:
        top_1_pct = (sorted_sections[0].get('value', 0) / total_expenses) * 100
        top_3_values = sum(s.get('value', 0) for s in sorted_sections[:3])
        top_3_pct = (top_3_values / total_expenses) * 100
        
        # Add key metrics
        insights['metrics'].extend([
            {
                'label': 'Total Despesas',
                'value': format_currency(total_expenses),
                'help': 'Soma de todas as categorias de despesas'
            },
            {
                'label': 'Categorias Ativas',
                'value': len([s for s in sections if s.get('value', 0) > 0]),
                'help': 'Número de categorias com despesas registradas'
            },
            {
                'label': 'Concentração Top 3',
                'value': f"{top_3_pct:.1f}%",
                'help': 'Percentual das despesas concentrado nas 3 maiores categorias'
            }
        ])
        
        # Concentration analysis
        if top_1_pct > 50:
            insights['key_findings'].append({
                'type': 'alert',
                'message': f"Alta concentração: {sorted_sections[0]['name']} representa {top_1_pct:.1f}% das despesas"
            })
        elif top_3_pct > 70:
            insights['key_findings'].append({
                'type': 'alert',
                'message': f"Top 3 categorias concentram {top_3_pct:.1f}% das despesas - considere diversificar"
            })
        else:
            insights['key_findings'].append({
                'type': 'success',
                'message': f"Distribuição equilibrada: Top 3 categorias representam {top_3_pct:.1f}% das despesas"
            })
    
    # Seasonal pattern analysis (if monthly data available)
    seasonal_insights = _analyze_seasonal_patterns(sections)
    insights['key_findings'].extend(seasonal_insights)
    
    # Cost efficiency analysis
    efficiency_insights = _analyze_cost_efficiency(sections, total_expenses)
    insights['key_findings'].extend(efficiency_insights)
    
    # Detect unusual patterns or anomalies
    anomalies = _detect_anomalies(sections)
    insights['anomalies'].extend(anomalies)
    
    return insights


def _analyze_seasonal_patterns(sections: List[Dict]) -> List[Dict]:
    """
    Analyze seasonal patterns in expense data
    """
    insights = []
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    for section in sections:
        monthly_data = section.get('monthly', {})
        if monthly_data and len(monthly_data) >= 6:  # Need at least 6 months of data
            
            # Find peak and lowest months
            monthly_values = [(month, monthly_data.get(month, 0)) for month in months]
            monthly_values = [(m, v) for m, v in monthly_values if v > 0]
            
            if len(monthly_values) >= 3:
                monthly_values.sort(key=lambda x: x[1], reverse=True)
                peak_month, peak_value = monthly_values[0]
                low_month, low_value = monthly_values[-1]
                
                # Calculate seasonality ratio
                if low_value > 0:
                    seasonality_ratio = peak_value / low_value
                    
                    if seasonality_ratio > 3:  # High seasonality
                        insights.append({
                            'type': 'info',
                            'message': f"{section['name']}: Alta sazonalidade - pico em {peak_month} ({format_currency(peak_value)})"
                        })
    
    return insights


def _analyze_cost_efficiency(sections: List[Dict], total_expenses: float) -> List[Dict]:
    """
    Analyze cost efficiency and provide optimization suggestions
    """
    insights = []
    
    # Look for categories with many small subcategories
    for section in sections:
        subcategories = section.get('subcategories', [])
        if len(subcategories) >= 5:
            
            # Count subcategories with very small values
            small_subcats = [sub for sub in subcategories if sub.get('value', 0) < (total_expenses * 0.005)]  # < 0.5% of total
            
            if len(small_subcats) >= 3:
                total_small = sum(sub.get('value', 0) for sub in small_subcats)
                insights.append({
                    'type': 'info',
                    'message': f"{section['name']}: {len(small_subcats)} subcategorias pequenas totalizam {format_currency(total_small)} - considere consolidar"
                })
    
    return insights


def _detect_anomalies(sections: List[Dict]) -> List[str]:
    """
    Detect anomalies and unusual patterns in the data
    """
    anomalies = []
    
    for section in sections:
        # Check for sections with value but no subcategories
        if section.get('value', 0) > 0 and not section.get('subcategories'):
            anomalies.append(f"{section['name']}: Tem valor mas não tem subcategorias detalhadas")
        
        # Check for subcategories with zero items
        subcategories = section.get('subcategories', [])
        for subcat in subcategories:
            if subcat.get('value', 0) > 0 and not subcat.get('items'):
                anomalies.append(f"{section['name']} > {subcat['name']}: Tem valor mas não tem itens detalhados")
    
    return anomalies


def _render_expense_distribution_insights(sections: List[Dict], total_expenses: float):
    """
    Render visual insights about expense distribution
    """
    sorted_sections = sorted(sections, key=lambda x: x.get('value', 0), reverse=True)
    
    # Create contribution chart
    categories = [s['name'] for s in sorted_sections[:5]]  # Top 5
    values = [s.get('value', 0) for s in sorted_sections[:5]]
    percentages = [(v / total_expenses) * 100 for v in values]
    
    fig = go.Figure()
    
    # Color coding by size
    colors = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#9b59b6']
    
    fig.add_trace(go.Bar(
        x=categories,
        y=percentages,
        marker_color=colors[:len(categories)],
        text=[f"{p:.1f}%" for p in percentages],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                     'Participação: %{y:.1f}%<br>' +
                     f'Valor: %{{customdata}}<br>' +
                     '<extra></extra>',
        customdata=[format_currency(v) for v in values]
    ))
    
    fig.update_layout(
        title="Top 5 Categorias por Participação",
        yaxis_title="Participação (%)",
        height=300,
        margin=dict(t=50, b=100)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total de Despesas",
            format_currency(total_expenses)
        )
        st.metric(
            "Número de Categorias",
            len(sections)
        )
    
    with col2:
        # Concentration analysis
        if sorted_sections:
            top_category = sorted_sections[0]
            concentration = (top_category.get('value', 0) / total_expenses) * 100
            
            st.metric(
                "Maior Categoria",
                top_category['name']
            )
            st.metric(
                "Concentração",
                f"{concentration:.1f}%"
            )
    
    with col3:
        # Pareto analysis (80/20 rule)
        cumulative = 0
        pareto_count = 0
        for section in sorted_sections:
            cumulative += section.get('value', 0)
            pareto_count += 1
            if cumulative >= total_expenses * 0.8:
                break
        
        st.metric(
            "Top 80% (Pareto)",
            f"{pareto_count} categorias"
        )
        st.metric(
            "Percentual Pareto",
            f"{(pareto_count / len(sections) * 100):.1f}%"
        )
    
    # Top categories
    st.markdown("##### 🔝 Top 5 Categorias")
    for i, section in enumerate(sorted_sections[:5]):
        percentage = (section.get('value', 0) / total_expenses) * 100
        st.write(f"{i+1}. **{section['name']}** - {format_currency(section.get('value', 0))} ({percentage:.1f}%)")
    
    # Risk analysis
    if len(sections) > 1:
        st.markdown("##### ⚠️ Análise de Risco")
        
        if concentration > 60:
            st.error(f"🔴 **Alto risco de concentração**: {top_category['name']} representa {concentration:.1f}% dos custos")
        elif concentration > 40:
            st.warning(f"🟡 **Risco moderado de concentração**: {top_category['name']} representa {concentration:.1f}% dos custos")
        else:
            st.success(f"✅ **Distribuição equilibrada**: Maior categoria representa {concentration:.1f}% dos custos")


def _render_period_trends(period_data: Dict, time_period: str, year: int):
    """
    Render intra-year period trends
    """
    st.markdown(f"#### 📈 Tendências {time_period.replace('📈 ', '').replace('📊 ', '').replace('📆 ', '')} - {year}")
    
    if 'sections' not in period_data:
        st.info("Dados não disponíveis para análise de tendências")
        return
    
    # Create trend chart for each major category
    categories = []
    periods = []
    values = []
    
    # Get period names from first section
    first_section = period_data['sections'][0] if period_data['sections'] else {}
    period_names = list(first_section.get('period_breakdown', {}).keys())
    
    if not period_names:
        st.info("Dados de períodos não disponíveis")
        return
    
    # Filter out revenue categories and collect data for chart  
    expense_sections = _filter_expense_sections(period_data['sections'])
    for section in expense_sections:
        section_name = section['name']
        period_breakdown = section.get('period_breakdown', {})
        
        for period_name in period_names:
            categories.append(section_name)
            periods.append(period_name)
            values.append(period_breakdown.get(period_name, 0))
    
    # Create dataframe
    df = pd.DataFrame({
        'Categoria': categories,
        'Período': periods,
        'Valor': values
    })
    
    # Create line chart showing trends
    fig = px.line(
        df,
        x='Período',
        y='Valor',
        color='Categoria',
        title=f'Evolução {time_period.replace("📈 ", "").replace("📊 ", "").replace("📆 ", "")} por Categoria',
        labels={'Valor': 'Valor (R$)', 'Período': 'Período'},
        markers=True
    )
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Show period comparison table
    st.markdown("#### 📊 Comparação por Período")
    
    # Create pivot table for easy comparison
    pivot_df = df.pivot(index='Categoria', columns='Período', values='Valor').fillna(0)
    
    # Format currency
    for col in pivot_df.columns:
        pivot_df[col] = pivot_df[col].apply(format_currency)
    
    st.dataframe(pivot_df, use_container_width=True)


def _render_period_insights(period_data: Dict, time_period: str, year: int):
    """
    Render insights specific to the selected time period
    """
    st.markdown(f"#### 💡 Insights {time_period.replace('📈 ', '').replace('📊 ', '').replace('📆 ', '')} - {year}")
    
    if 'sections' not in period_data or not period_data['sections']:
        st.info("Dados insuficientes para análise")
        return
    
    # Filter out revenue categories and calculate period insights
    sections = _filter_expense_sections(period_data['sections'])  
    total_annual = sum(s.get('value', 0) for s in sections)
    
    # Get period data
    first_section = sections[0] if sections else {}
    period_names = list(first_section.get('period_breakdown', {}).keys())
    
    if not period_names:
        st.info("Dados de períodos não disponíveis")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            f"Total {time_period.replace('📈 ', '').replace('📊 ', '').replace('📆 ', '')}",
            format_currency(total_annual)
        )
        
        # Find highest period
        period_totals = {}
        for period_name in period_names:
            period_total = sum(s.get('period_breakdown', {}).get(period_name, 0) for s in sections)
            period_totals[period_name] = period_total
        
        highest_period = max(period_totals.keys(), key=lambda k: period_totals[k])
        st.metric(
            "Período Maior",
            highest_period,
            delta=format_currency(period_totals[highest_period])
        )
    
    with col2:
        # Calculate period distribution
        if len(period_totals) > 1:
            values = list(period_totals.values())
            variability = (max(values) - min(values)) / max(values) * 100 if max(values) > 0 else 0
            
            st.metric(
                "Variabilidade",
                f"{variability:.1f}%",
                help="Diferença percentual entre maior e menor período"
            )
            
            avg_period = sum(values) / len(values)
            st.metric(
                "Média por Período", 
                format_currency(avg_period)
            )
    
    with col3:
        # Show period patterns
        if time_period == "📈 Trimestral":
            st.markdown("**📊 Padrão Trimestral**")
            if 'Q4' in period_totals and period_totals['Q4'] == max(period_totals.values()):
                st.info("🎯 Q4 é o trimestre com maiores gastos")
            elif 'Q1' in period_totals and period_totals['Q1'] == max(period_totals.values()):
                st.info("🚀 Q1 inicia com gastos elevados")
        elif time_period == "📆 Semestral":
            st.markdown("**📊 Padrão Semestral**")
            if 'S2' in period_totals and period_totals['S2'] > period_totals.get('S1', 0):
                st.info("📈 Segundo semestre tem gastos maiores")
            else:
                st.info("📊 Primeiro semestre concentra gastos")
    
    # Top categories by period variation
    st.markdown("#### 🔍 Categorias com Maior Variação")
    
    category_variations = []
    for section in sections:
        breakdown = section.get('period_breakdown', {})
        values = [breakdown.get(p, 0) for p in period_names]
        
        if values and max(values) > 0:
            variation = (max(values) - min(values)) / max(values) * 100
            category_variations.append({
                'categoria': section['name'],
                'variacao': variation,
                'maior_periodo': period_names[values.index(max(values))],
                'valor_max': max(values)
            })
    
    # Sort by variation
    category_variations.sort(key=lambda x: x['variacao'], reverse=True)
    
    for i, cat in enumerate(category_variations[:5]):
        if cat['variacao'] > 10:  # Only show significant variations
            st.write(f"{i+1}. **{cat['categoria']}**: {cat['variacao']:.1f}% variação (pico em {cat['maior_periodo']})")
    
    if not any(cat['variacao'] > 10 for cat in category_variations):
        st.success("✅ Gastos estáveis ao longo dos períodos")


def _render_multi_year_comparison(multi_year_data: Dict, selected_years: List[int], time_period: str, show_details: bool):
    """
    Render comparison between multiple years with side-by-side sparklines
    """
    # Dynamic header based on time period
    period_name = time_period.replace('📈 ', '').replace('📊 ', '').replace('📆 ', '')
    st.header(f"📊 Comparação {period_name} Entre Anos")
    
    if len(selected_years) < 2:
        st.warning("Selecione pelo menos 2 anos para comparação.")
        return
    
    # Display year range being compared - ensure chronological order
    sorted_years = sorted(selected_years)
    year_range_text = f"{min(sorted_years)} - {max(sorted_years)}"
    st.info(f"🔍 Comparando: {', '.join(map(str, sorted_years))}")
    
    # Get chart type preference - use line charts for all time periods to show progression
    chart_type = "📈 Linha"
    
    # Filter to expense sections only
    expense_data = {}
    for year, data in multi_year_data.items():
        if 'sections' in data:
            expense_data[year] = _filter_expense_sections(data['sections'])
    
    if not expense_data:
        st.warning("Nenhum dado de despesas encontrado para comparação.")
        return
    
    # Show summary metrics for each year - in chronological order
    st.markdown("### 📈 Resumo Anual")
    cols = st.columns(len(sorted_years))
    
    for i, year in enumerate(sorted_years):
        with cols[i]:
            year_sections = expense_data.get(year, [])
            year_total = sum(section.get('value', 0) for section in year_sections)
            
            # Calculate change from previous year
            if i > 0:
                prev_year = selected_years[i-1]
                prev_sections = expense_data.get(prev_year, [])
                prev_total = sum(section.get('value', 0) for section in prev_sections)
                change_pct = ((year_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
                st.metric(
                    f"Total {year}",
                    format_currency(year_total),
                    f"{change_pct:+.1f}%" if i > 0 else None
                )
            else:
                st.metric(f"Total {year}", format_currency(year_total))
    
    st.markdown("---")
    
    # Get all unique sections across years
    all_sections = set()
    for year_sections in expense_data.values():
        all_sections.update(section['name'] for section in year_sections)
    
    # Comparison type selector
    comparison_type = st.selectbox(
        "📊 Tipo de Comparação",
        [
            "🏢 Por Seção Principal",
            "📈 Sparklines Lado a Lado", 
            "📊 Tabela Comparativa",
            "🔥 Análise de Mudanças",
            "📅 Análise Mês a Mês",
            "🗓️ Comparação Sazonal",
            "📊 Comparar Meses Específicos",
            "📊 Análise de Variância"
        ],
        index=1
    )
    
    if comparison_type == "📈 Sparklines Lado a Lado":
        _render_side_by_side_sparklines(expense_data, sorted_years, time_period, chart_type)
    
    elif comparison_type == "🏢 Por Seção Principal":
        _render_section_comparison(expense_data, sorted_years, all_sections)
    
    elif comparison_type == "📊 Tabela Comparativa":
        _render_multi_year_comparison_table(expense_data, sorted_years)
    
    elif comparison_type == "🔥 Análise de Mudanças":
        _render_change_analysis(expense_data, sorted_years)
    
    elif comparison_type == "📅 Análise Mês a Mês":
        _render_month_to_month_analysis(expense_data, sorted_years)
    
    elif comparison_type == "🗓️ Comparação Sazonal":
        _render_seasonal_month_comparison(expense_data, sorted_years)
    
    elif comparison_type == "📊 Comparar Meses Específicos":
        _render_specific_month_comparison(expense_data, sorted_years)
    
    elif comparison_type == "📊 Análise de Variância":
        _render_month_to_month_variance_analysis(expense_data, sorted_years)


def _render_side_by_side_sparklines(expense_data: Dict, selected_years: List[int], time_period: str, chart_type: str):
    """
    Render side-by-side monthly sparklines for each year
    """
    st.markdown("### 📈 Sparklines Comparativas")
    
    # Year colors for differentiation
    year_colors = {}
    color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Blue, Orange, Green, Red
    
    for i, year in enumerate(selected_years):
        year_colors[year] = color_palette[i % len(color_palette)]
    
    # Process each section across all years
    all_sections = set()
    for year_sections in expense_data.values():
        all_sections.update(section['name'] for section in year_sections)
    
    for section_name in sorted(all_sections):
        st.markdown(f"#### {section_name}")
        
        # Create expandable section
        with st.expander(f"Comparar {section_name} - {', '.join(map(str, selected_years))}", expanded=False):
            # Show section-level comparison
            section_data = {}
            for year in selected_years:
                year_sections = expense_data.get(year, [])
                section = next((s for s in year_sections if s['name'] == section_name), None)
                if section:
                    section_data[year] = section
            
            if not section_data:
                st.info("Nenhum dado disponível para esta seção")
                continue
            
            # Show section totals
            cols = st.columns(len(selected_years))
            for i, year in enumerate(selected_years):
                with cols[i]:
                    if year in section_data:
                        value = section_data[year].get('value', 0)
                        st.metric(f"{year}", format_currency(value))
                    else:
                        st.metric(f"{year}", "R$ 0")
            
            # Period comparison if data available  
            if time_period == "📊 Mensal":
                _render_monthly_section_comparison(section_data, selected_years, year_colors, chart_type)
            elif time_period in ["📈 Trimestral", "📆 Semestral", "📅 Customizado"]:
                _render_period_section_comparison(section_data, selected_years, year_colors, chart_type, time_period)
            elif time_period == "📅 Anual":
                _render_annual_section_comparison(section_data, selected_years, year_colors)
            
            # Show subcategories comparison
            _render_subcategories_comparison(section_data, selected_years, time_period, year_colors)


def _render_monthly_section_comparison(section_data: Dict, selected_years: List[int], year_colors: Dict, chart_type: str):
    """
    Render monthly comparison for a single section across years
    """
    fig = go.Figure()
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Store all year data for year-over-year comparisons
    all_year_data = {}
    
    for year in selected_years:
        if year not in section_data:
            continue
            
        section = section_data[year]
        monthly_data = section.get('monthly', {})
        
        # Prepare monthly values
        values = [monthly_data.get(month, 0) for month in months]
        all_year_data[year] = values
        
        if any(v > 0 for v in values):
            # Create detailed hover text for each month
            hover_text = []
            yearly_total = sum(values)
            
            for i, month in enumerate(months):
                value = values[i]
                text = f"<b>{month} {year}</b><br>"
                text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
                
                # Add percentage of year total
                if yearly_total > 0:
                    pct = (value / yearly_total) * 100
                    text += f"<b>% do Ano:</b> {pct:.1f}%<br>"
                
                # Add month-over-month change
                if i > 0 and values[i-1] > 0:
                    mom_change = ((value - values[i-1]) / values[i-1]) * 100
                    text += f"<b>Var. Mês Anterior:</b> {mom_change:+.1f}%<br>"
                
                # Add year-over-year change if we have previous year data
                prev_year = year - 1
                if prev_year in all_year_data:
                    prev_value = all_year_data[prev_year][i]
                    if prev_value > 0:
                        yoy_change = ((value - prev_value) / prev_value) * 100
                        text += f"<b>Var. {prev_year}:</b> {yoy_change:+.1f}%"
                    elif value > 0:
                        text += f"<b>Var. {prev_year}:</b> Novo"
                
                hover_text.append(text)
            
            if chart_type == "📈 Linha":
                fig.add_trace(go.Scatter(
                    x=months,
                    y=values,
                    mode='lines+markers',
                    name=str(year),
                    line=dict(color=year_colors.get(year, '#1f77b4'), width=2),
                    marker=dict(size=6),
                    hovertemplate='%{customdata}<extra></extra>',
                    customdata=hover_text
                ))
            else:  # Bar chart
                fig.add_trace(go.Bar(
                    x=months,
                    y=values,
                    name=str(year),
                    marker=dict(color=year_colors.get(year, '#1f77b4'), opacity=0.7),
                    hovertemplate='%{customdata}<extra></extra>',
                    customdata=hover_text
                ))
    
    fig.update_layout(
        title=f"Evolução Mensal Comparativa",
        height=300,
        xaxis_title="Mês",
        yaxis_title="Valor (R$)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_period_section_comparison(section_data: Dict, selected_years: List[int], year_colors: Dict, chart_type: str, time_period: str):
    """
    Render period comparison (quarterly, semestral, etc.) for a single section across years
    """
    
    # Define period mappings based on time_period
    if time_period == "📈 Trimestral":
        period_mappings = {
            'Q1': ['JAN', 'FEV', 'MAR'],
            'Q2': ['ABR', 'MAI', 'JUN'], 
            'Q3': ['JUL', 'AGO', 'SET'],
            'Q4': ['OUT', 'NOV', 'DEZ']
        }
        period_labels = ['Q1', 'Q2', 'Q3', 'Q4']
    elif time_period == "📆 Semestral":
        period_mappings = {
            'S1': ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN'],
            'S2': ['JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        }
        period_labels = ['S1', 'S2']
    else:  # Custom periods
        # Default to quarterly for custom
        period_mappings = {
            'T1': ['JAN', 'FEV', 'MAR'],
            'T2': ['ABR', 'MAI', 'JUN'], 
            'T3': ['JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        }
        period_labels = ['T1', 'T2', 'T3']
    
    fig = go.Figure()
    
    # Collect data for each year
    all_year_data = {}
    for year in selected_years:
        if year in section_data:
            section = section_data[year]
            monthly_data = section.get('monthly', {})
            
            # Aggregate monthly data to periods
            period_values = []
            for period in period_labels:
                period_total = 0
                months_in_period = period_mappings.get(period, [])
                for month in months_in_period:
                    period_total += monthly_data.get(month, 0)
                period_values.append(period_total)
            
            all_year_data[year] = period_values
            
            # Create hover text for each period
            hover_text = []
            yearly_total = sum(period_values)
            
            for i, (period, value) in enumerate(zip(period_labels, period_values)):
                text = f"<b>{period} - {year}</b><br>"
                text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
                
                # Add percentage of year total
                if yearly_total > 0:
                    pct = (value / yearly_total) * 100
                    text += f"<b>% do Ano:</b> {pct:.1f}%<br>"
                
                # Add period-over-period change
                if i > 0 and period_values[i-1] > 0:
                    pop_change = ((value - period_values[i-1]) / period_values[i-1]) * 100
                    text += f"<b>Var. Período Anterior:</b> {pop_change:+.1f}%<br>"
                
                # Add year-over-year change if we have previous year data
                prev_year = year - 1
                if prev_year in all_year_data:
                    prev_value = all_year_data[prev_year][i]
                    if prev_value > 0:
                        yoy_change = ((value - prev_value) / prev_value) * 100
                        text += f"<b>Var. {prev_year}:</b> {yoy_change:+.1f}%"
                    elif value > 0:
                        text += f"<b>Var. {prev_year}:</b> Novo"
                
                hover_text.append(text)
            
            if chart_type == "📈 Linha":
                fig.add_trace(go.Scatter(
                    x=period_labels,
                    y=period_values,
                    mode='lines+markers',
                    name=str(year),
                    line=dict(color=year_colors.get(year, '#1f77b4'), width=2),
                    marker=dict(size=8),
                    hovertemplate='%{customdata}<extra></extra>',
                    customdata=hover_text
                ))
            else:  # Bar chart
                fig.add_trace(go.Bar(
                    x=period_labels,
                    y=period_values,
                    name=str(year),
                    marker=dict(color=year_colors.get(year, '#1f77b4')),
                    hovertemplate='%{customdata}<extra></extra>',
                    customdata=hover_text
                ))
    
    # Configure layout
    period_type = time_period.replace('📈 ', '').replace('📆 ', '').replace('📅 ', '')
    fig.update_layout(
        title=f"Evolução {period_type}",
        xaxis_title=f"Períodos {period_type}",
        yaxis_title="Valor (R$)",
        hovermode='x unified',
        showlegend=True,
        height=400,
        yaxis=dict(tickformat=",.0f")
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_annual_section_comparison(section_data: Dict, selected_years: List[int], year_colors: Dict):
    """
    Render annual comparison for a single section across years with visual graph
    """
    fig = go.Figure()
    
    # Collect annual totals for each year
    years = sorted(selected_years)
    values = []
    
    for year in years:
        if year in section_data:
            section = section_data[year]
            annual_value = section.get('value', 0)
            values.append(annual_value)
        else:
            values.append(0)
    
    # Create hover text with details
    hover_texts = []
    for i, (year, value) in enumerate(zip(years, values)):
        text = f"<b>{year}</b><br>"
        text += f"<b>Valor Total:</b> R$ {value:,.2f}<br>"
        
        # Add year-over-year change
        if i > 0 and values[i-1] > 0:
            change = ((value - values[i-1]) / values[i-1]) * 100
            text += f"<b>Variação YoY:</b> {change:+.1f}%<br>"
            diff = value - values[i-1]
            text += f"<b>Diferença:</b> R$ {diff:,.2f}"
        elif i > 0:
            text += f"<b>Variação YoY:</b> Novo"
        
        hover_texts.append(text)
    
    # Add line trace for the trend
    fig.add_trace(go.Scatter(
        x=[str(year) for year in years],
        y=values,
        mode='lines+markers',
        name='Evolução Anual',
        line=dict(color='#3498db', width=3),
        marker=dict(size=10, color='#3498db'),
        text=[f'R$ {v:,.0f}' for v in values],
        textposition='top center',
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts
    ))
    
    fig.update_layout(
        title=f"Comparação Anual",
        height=350,
        xaxis_title="Ano",
        xaxis=dict(
            tickmode='array',
            tickvals=[str(year) for year in years],
            ticktext=[str(year) for year in years]
        ),
        yaxis_title="Valor (R$)",
        yaxis=dict(tickformat=",.0f"),
        showlegend=False,
        hovermode='x unified',
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_subcategory_evolution(multi_year_data: Dict, selected_years: List[int], time_period: str):
    """
    Render evolution of main sections across years
    Including Faturamento, Custos Variáveis, Custos Fixos, and Custos Não Operacionais
    """
    st.header("📈 Evolução das Categorias Principais")
    
    # Show recommendation based on data
    with st.expander("💡 Guia de Visualizações", expanded=False):
        st.markdown("""
        **Escolha a melhor visualização para sua análise:**
        
        🎯 **Recomendado para melhor visibilidade:**
        - **Focar em Custos**: Mostra apenas custos, sem faturamento, com escala otimizada
        - **Área Empilhada**: Visualiza a composição total de custos ao longo do tempo
        - **% Composição**: Mostra a proporção relativa de cada custo
        - **Mini Gráficos**: Um gráfico individual para cada subcategoria
        
        📊 **Outras opções:**
        - **Separar Gráficos**: Faturamento e custos em gráficos independentes
        - **Linear**: Visão padrão com valores absolutos
        - **% do Faturamento**: Quanto cada custo representa do faturamento
        - **Índice Base 100**: Compara taxas de crescimento relativo
        - **Dual Axis**: Duas escalas Y (esquerda para custos, direita para faturamento)
        - **Logarítmica**: Para grandes diferenças de escala
        
        💡 **Dica**: Para melhor visualização dos custos, use "**Focar em Custos**" ou "**Mini Gráficos**".
        """)
    
    # Get all sections including revenue
    all_data = {}
    for year, data in multi_year_data.items():
        if 'sections' in data:
            all_data[year] = data['sections']
    
    if not all_data:
        st.warning("Nenhum dado encontrado para análise.")
        return
    
    # Collect all unique subcategories and revenue
    all_subcategories = {}
    
    # First, add Faturamento (Revenue) as the primary line
    # ONLY accept FATURAMENTO - completely ignore RECEITA
    for year in selected_years:
        if year in all_data:
            for section in all_data[year]:
                section_name = section.get('name', '').upper().strip()
                # STRICTLY only FATURAMENTO - no RECEITA, no other revenue types
                if section_name == 'FATURAMENTO':
                    if 'FATURAMENTO' not in all_subcategories:
                        all_subcategories['FATURAMENTO'] = {}
                    all_subcategories['FATURAMENTO'][year] = section.get('value', 0)
    
    # Then collect ONLY the 3 main expense sections - no other sections
    # We want EXACTLY these 3: Custos Variáveis, Custos Fixos, Custos Não Operacionais
    main_expense_sections = ['CUSTOS VARIÁVEIS', 'CUSTOS VARIAVEIS', 'CUSTOS FIXOS', 'CUSTOS NÃO OPERACIONAIS', 'CUSTOS NAO OPERACIONAIS']
    
    for year in selected_years:
        if year in all_data:
            for section in all_data[year]:
                section_name = section.get('name', '').upper().strip()
                
                # STRICT filtering: ONLY the main cost sections, nothing else
                # Also explicitly exclude RECEITA to make sure it doesn't get through
                if section_name in main_expense_sections and section_name != 'RECEITA':
                    # Use the section name directly
                    display_name = section_name.replace('VARIAVEIS', 'VARIÁVEIS').replace('NAO', 'NÃO')
                    
                    if display_name not in all_subcategories:
                        all_subcategories[display_name] = {}
                    all_subcategories[display_name][year] = section.get('value', 0)
    
    if not all_subcategories:
        st.info("Nenhuma subcategoria encontrada nos dados.")
        return
    
    # Separate Faturamento from other main sections
    faturamento_data = all_subcategories.pop('FATURAMENTO', {})
    
    # Sort main cost sections by total value across all years
    sorted_subcats = sorted(
        all_subcategories.items(),
        key=lambda x: sum(x[1].values()),
        reverse=True
    )
    
    # Color palette for subcategories (excluding green which is for Faturamento)
    colors = [
        '#e74c3c', '#3498db', '#f39c12', '#9b59b6',
        '#e67e22', '#1abc9c', '#34495e', '#95a5a6', '#d35400',
        '#c0392b', '#2980b9', '#f1c40f', '#8e44ad',
        '#16a085', '#2c3e50', '#7f8c8d', '#c0392b'
    ]
    
    # Options for better visualization
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Show all main sections (there are only 3-4 of them)
        max_subcategories = len(sorted_subcats)
        st.info(f"📊 Mostrando as {len(sorted_subcats)} categorias principais + Faturamento")
    
    with col2:
        # Scaling option
        scale_option = st.selectbox(
            "Tipo de Visualização",
            [
                "Auto Scale (Recomendado)",
                "Barras Lado a Lado",
                "Barras Agrupadas",
                "Barras Empilhadas",
                "Focar em Custos",
                "Área Empilhada",
                "% Composição",
                "Mini Gráficos",
                "Separar Gráficos",
                "Linear",
                "% do Faturamento",
                "Índice Base 100",
                "Dual Axis (Faturamento/Custos)",
                "Logarítmica"
            ],
            help="Diferentes formas de visualizar os dados"
        )
    
    with col3:
        # Toggle to show/hide Faturamento
        show_faturamento = st.checkbox(
            "Mostrar Faturamento",
            value=True,
            help="Desmarque para focar apenas nos custos"
        )
    
    # Prepare data for the chart
    years = sorted(selected_years)
    
    # Handle different visualization types
    if scale_option == "Auto Scale (Recomendado)":
        # Analyze data to automatically select best visualization
        # Calculate the scale difference between revenue and expenses
        max_revenue = max([faturamento_data.get(year, 0) for year in years]) if faturamento_data else 0
        max_expense = 0
        for subcat_name, year_values in sorted_subcats[:max_subcategories]:
            for year in years:
                value = year_values.get(year, 0)
                if value > max_expense:
                    max_expense = value
        
        # Determine the scale ratio
        if max_revenue > 0 and max_expense > 0:
            scale_ratio = max_revenue / max_expense
            
            # Choose visualization based on scale difference
            if scale_ratio > 20:
                # Revenue is much larger than expenses (20x or more)
                # Use separate charts or grouped bars for best visibility
                if len(years) <= 3:
                    scale_option = "Barras Agrupadas"
                    st.info("📊 Auto Scale: Usando 'Barras Agrupadas' - ideal para comparação com poucos anos e grande diferença de escala")
                else:
                    scale_option = "Separar Gráficos"
                    st.info("🔍 Auto Scale: Usando 'Separar Gráficos' devido à grande diferença de escala entre Faturamento e Despesas")
            elif scale_ratio > 5:
                # Revenue is significantly larger (5x-20x)
                # Use dual axis or grouped bars for comparison
                if len(years) <= 2:
                    scale_option = "Barras Agrupadas"
                    st.info("📊 Auto Scale: Usando 'Barras Agrupadas' para melhor comparação visual")
                else:
                    scale_option = "Dual Axis (Faturamento/Custos)"
                    st.info("🔍 Auto Scale: Usando 'Dual Axis' para melhor comparação entre Faturamento e Despesas")
            elif show_faturamento and scale_ratio < 0.5:
                # Expenses are larger than revenue - focus on expenses
                scale_option = "Focar em Custos"
                st.info("🔍 Auto Scale: Focando em Custos pois as despesas são maiores que o faturamento")
            else:
                # Similar scales, use linear for direct comparison
                scale_option = "Linear"
                st.info("🔍 Auto Scale: Usando visualização linear padrão")
        elif max_expense > 0:
            # No revenue data, focus on expenses
            scale_option = "Focar em Custos"
            st.info("🔍 Auto Scale: Focando em Custos (sem dados de faturamento)")
        else:
            # Default to linear if no data
            scale_option = "Linear"
    
    # Now handle the actual visualization types
    if scale_option == "Barras Lado a Lado":
        # Side by side bars for better comparison
        fig = go.Figure()
        
    elif scale_option == "Barras Agrupadas":
        # Grouped bar chart
        fig = go.Figure()
        
    elif scale_option == "Barras Empilhadas":
        # Stacked bar chart  
        fig = go.Figure()
        
    elif scale_option == "Focar em Custos":
        # Focus only on expenses, no revenue
        fig = go.Figure()
        
    elif scale_option == "Área Empilhada":
        # Stacked area chart for expense composition
        fig = go.Figure()
        
    elif scale_option == "% Composição":
        # Percentage composition over time
        fig = go.Figure()
        
    elif scale_option == "Mini Gráficos":
        # Create small multiples for each subcategory
        from plotly.subplots import make_subplots
        
        # Calculate grid layout
        n_subcats = min(max_subcategories, len(sorted_subcats))
        n_cols = 3
        n_rows = (n_subcats + n_cols - 1) // n_cols
        
        # Create subplots
        subplot_titles = [name for name, _ in sorted_subcats[:n_subcats]]
        fig = make_subplots(
            rows=n_rows, cols=n_cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
    elif scale_option == "Separar Gráficos":
        # Create two separate charts
        from plotly.subplots import make_subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Faturamento", "Despesas por Subcategoria"),
            vertical_spacing=0.12,
            row_heights=[0.3, 0.7]
        )
        
        # Add Faturamento to top subplot
        if faturamento_data:
            values = [faturamento_data.get(year, 0) for year in years]
            fig.add_trace(go.Scatter(
                x=[str(year) for year in years],
                y=values,
                mode='lines+markers',
                name='📊 FATURAMENTO',
                line=dict(color='#27ae60', width=4),
                marker=dict(size=12, color='#27ae60'),
                showlegend=False
            ), row=1, col=1)
    else:
        # Single chart for other options
        fig = go.Figure()
        
    # Process data based on visualization type
    if scale_option == "% do Faturamento":
        # Convert all values to percentage of revenue
        revenue_values = [faturamento_data.get(year, 1) for year in years]  # Avoid division by zero
        
    elif scale_option == "Índice Base 100":
        # Index all values to 100 at the first year
        base_year = years[0]
        
    # Add Faturamento as the primary line (if exists and enabled)
    if scale_option not in ["Separar Gráficos", "Barras Lado a Lado"] and faturamento_data and show_faturamento:
        values = [faturamento_data.get(year, 0) for year in years]
        
        # Adjust values based on visualization type
        if scale_option == "% do Faturamento":
            values = [100 for _ in years]  # Revenue is always 100% of itself
        elif scale_option == "Índice Base 100":
            base_value = values[0] if values[0] > 0 else 1
            values = [(v / base_value) * 100 for v in values]
        
        # Create hover text for Faturamento
        hover_texts = []
        for j, (year, value) in enumerate(zip(years, values)):
            if scale_option in ["% do Faturamento", "Índice Base 100"]:
                text = f"<b>FATURAMENTO</b><br>"
                text += f"<b>{year}:</b> {value:.1f}{'%' if scale_option == '% do Faturamento' else ''}<br>"
                orig_value = faturamento_data.get(year, 0)
                text += f"<b>Valor:</b> R$ {orig_value:,.2f}"
            else:
                text = f"<b>FATURAMENTO</b><br>"
                text += f"<b>{year}:</b> R$ {value:,.2f}<br>"
                
                # Add year-over-year change
                if j > 0 and values[j-1] > 0:
                    change = ((value - values[j-1]) / values[j-1]) * 100
                    text += f"<b>Variação:</b> {change:+.1f}%"
            
            hover_texts.append(text)
        
        # Add Faturamento with distinctive styling
        # Use secondary y-axis if dual axis is selected
        if scale_option == "Dual Axis (Faturamento/Custos)":
            fig.add_trace(go.Scatter(
                x=[str(year) for year in years],
                y=values,
                mode='lines+markers',
                name='📊 FATURAMENTO',
                line=dict(color='#27ae60', width=4, dash='solid'),
                marker=dict(size=12, color='#27ae60'),
                hovertemplate='%{customdata}<extra></extra>',
                customdata=hover_texts,
                yaxis='y2'  # Use secondary y-axis
            ))
        else:
            fig.add_trace(go.Scatter(
                x=[str(year) for year in years],
                y=values,
                mode='lines+markers',
                name='📊 FATURAMENTO',
                line=dict(color='#27ae60', width=4, dash='solid'),
                marker=dict(size=12, color='#27ae60'),
                hovertemplate='%{customdata}<extra></extra>',
                customdata=hover_texts
            ))
    
    # Add traces for each subcategory based on visualization type
    if scale_option == "Barras Lado a Lado":
        # Add subcategory selection
        st.markdown("#### 📋 Selecione as subcategorias para comparar:")
        
        # Add display options
        display_col1, display_col2, display_col3 = st.columns(3)
        with display_col1:
            show_values = st.checkbox("Mostrar valores", value=True, help="Exibir valores e percentuais nas barras")
        with display_col2:
            min_value_for_text = st.number_input(
                "Valor mínimo para exibir texto (R$)", 
                min_value=0, 
                max_value=100000, 
                value=50000, 
                step=10000,
                help="Apenas mostra texto em barras com valores acima deste limite"
            )
        with display_col3:
            horizontal_bars = st.checkbox(
                "Barras horizontais", 
                value=False, 
                help="Exibir barras na horizontal (melhor para muitas categorias)"
            )
        
        # Create columns for checkboxes
        n_cols = 4
        cols = st.columns(n_cols)
        
        # Get all subcategory names
        all_subcat_names = [name for name, _ in sorted_subcats[:max_subcategories]]
        
        # Default selection - top 10 or all if less than 10
        default_selection = all_subcat_names[:min(10, len(all_subcat_names))]
        
        # Add "Select All/None" buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Selecionar Todas"):
                st.session_state['selected_subcats'] = all_subcat_names
                st.rerun()
        with col2:
            if st.button("Limpar Seleção"):
                st.session_state['selected_subcats'] = []
                st.rerun()
        with col3:
            if st.button("Top 10"):
                st.session_state['selected_subcats'] = default_selection
                st.rerun()
        
        # Initialize session state if not exists
        if 'selected_subcats' not in st.session_state:
            st.session_state['selected_subcats'] = default_selection
        
        # Create checkboxes for each subcategory
        selected_subcats = []
        for idx, subcat_name in enumerate(all_subcat_names):
            col_idx = idx % n_cols
            with cols[col_idx]:
                # Truncate long names for display
                display_name = subcat_name[:25] + "..." if len(subcat_name) > 25 else subcat_name
                if st.checkbox(
                    display_name,
                    value=subcat_name in st.session_state.get('selected_subcats', default_selection),
                    key=f"subcat_{idx}",
                    help=subcat_name  # Show full name on hover
                ):
                    selected_subcats.append(subcat_name)
        
        # Filter sorted_subcats to only selected ones
        filtered_subcats = [(name, values) for name, values in sorted_subcats[:max_subcategories] if name in selected_subcats]
        
        if not filtered_subcats:
            st.warning("⚠️ Selecione pelo menos uma subcategoria para visualizar.")
            return
        
        st.info(f"📊 Mostrando {len(filtered_subcats)} subcategorias selecionadas")
        
        # Side by side comparison - focus on expense subcategories only for better visibility
        x_labels = []
        
        # Only add selected expense subcategories
        for subcat_name, _ in filtered_subcats:
            x_labels.append(subcat_name)
        
        # Get number of categories for sizing
        num_categories = len(filtered_subcats)
        
        # Add a trace for each year
        for year_idx, year in enumerate(years):
            y_values = []
            hover_texts = []
            text_labels = []
            
            # Get revenue for this year for percentage calculations
            revenue_value = faturamento_data.get(year, 1) if faturamento_data else 1
            
            # Add subcategory values
            for subcat_name, year_values in filtered_subcats:
                value = year_values.get(year, 0)
                y_values.append(value)
                
                # Calculate % of revenue
                percent_of_revenue = (value / revenue_value * 100) if revenue_value > 0 else 0
                
                # Calculate year-over-year variation
                prev_year = years[year_idx - 1] if year_idx > 0 else None
                variation_text = ""
                if prev_year and prev_year in year_values:
                    prev_value = year_values.get(prev_year, 0)
                    if prev_value > 0:
                        variation = ((value - prev_value) / prev_value) * 100
                        variation_text = f"<br><b>Variação YoY:</b> {variation:+.1f}%"
                    elif value > 0:
                        variation_text = "<br><b>Variação YoY:</b> Novo"
                
                hover_text = f"<b>{subcat_name}</b><br>"
                hover_text += f"<b>{year}:</b> R$ {value:,.0f}<br>"
                hover_text += f"<b>% da Receita:</b> {percent_of_revenue:.2f}%"
                hover_text += variation_text
                
                hover_texts.append(hover_text)
                
                # Create text label showing value and % of revenue
                # Only show text for values above threshold and if enabled
                if show_values and value > min_value_for_text:
                    if value > 100000:
                        text_labels.append(f"{format_currency(value)}<br>{percent_of_revenue:.1f}%")
                    else:
                        text_labels.append(f"R$ {value/1000:.0f}K<br>{percent_of_revenue:.1f}%")
                else:
                    text_labels.append("")  # Empty text for small values or if disabled
            
            # Create bar trace for this year with better colors
            year_colors = {
                0: '#52c41a',  # Green for 2023
                1: '#1890ff',  # Blue for 2024  
                2: '#722ed1',  # Purple for 2025
                3: '#ff4d4f'   # Red for 2026
            }
            
            # Determine text position based on value size
            text_positions = []
            for v in y_values:
                if v > 100000:
                    text_positions.append('outside')
                else:
                    text_positions.append('inside')  # Inside for smaller values
            
            if horizontal_bars:
                # Horizontal bar chart
                fig.add_trace(go.Bar(
                    y=x_labels,  # Categories on y-axis
                    x=y_values,  # Values on x-axis
                    name=str(year),
                    orientation='h',
                    marker_color=year_colors.get(year_idx, '#95a5a6'),
                    hovertemplate='%{customdata}<extra></extra>',
                    customdata=hover_texts,
                    text=text_labels,
                    textposition='outside',
                    textfont=dict(
                        size=10 if num_categories > 10 else 11,
                        color='rgba(0,0,0,0.7)'
                    ),
                    texttemplate='%{text}'
                ))
            else:
                # Vertical bar chart (default)
                fig.add_trace(go.Bar(
                    x=x_labels,
                    y=y_values,
                    name=str(year),
                    marker_color=year_colors.get(year_idx, '#95a5a6'),
                    hovertemplate='%{customdata}<extra></extra>',
                    customdata=hover_texts,
                    text=text_labels,
                    textposition='outside',
                    textfont=dict(
                        size=10 if num_categories > 10 else 11,
                        color='rgba(0,0,0,0.7)'
                    ),
                    texttemplate='%{text}'
                ))
    
    elif scale_option == "Barras Agrupadas":
        # Grouped bar chart - subcategories side by side for each year
        # Create x-axis categories combining year and subcategory
        x_categories = []
        y_values = []
        bar_colors = []
        hover_texts = []
        
        # First add Faturamento if enabled
        if faturamento_data and show_faturamento:
            for year in years:
                x_categories.append(f"{year}<br>📊 Faturamento")
                y_values.append(faturamento_data.get(year, 0))
                bar_colors.append('#27ae60')
                hover_texts.append(f"<b>FATURAMENTO</b><br>{year}: R$ {faturamento_data.get(year, 0):,.0f}")
        
        # Add each subcategory
        for i, (subcat_name, year_values) in enumerate(sorted_subcats[:max_subcategories]):
            for year in years:
                x_categories.append(f"{year}<br>{subcat_name[:15]}...")
                value = year_values.get(year, 0)
                y_values.append(value)
                bar_colors.append(colors[i % len(colors)])
                hover_texts.append(f"<b>{subcat_name}</b><br>{year}: R$ {value:,.0f}")
        
        # Create single bar trace with all data
        fig.add_trace(go.Bar(
            x=x_categories,
            y=y_values,
            marker_color=bar_colors,
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_texts,
            showlegend=False
        ))
    
    elif scale_option == "Barras Empilhadas":
        # Stacked bar chart - expenses stacked on top of each other
        for i, (subcat_name, year_values) in enumerate(sorted_subcats[:max_subcategories]):
            values = [year_values.get(year, 0) for year in years]
            if any(v > 0 for v in values):
                fig.add_trace(go.Bar(
                    x=[str(year) for year in years],
                    y=values,
                    name=subcat_name,
                    marker_color=colors[i % len(colors)],
                    hovertemplate=f'<b>{subcat_name}</b><br>%{{x}}: %{{y:,.0f}}<extra></extra>'
                ))
        
        # Add Faturamento as a separate trace if enabled
        if faturamento_data and show_faturamento:
            values = [faturamento_data.get(year, 0) for year in years]
            fig.add_trace(go.Bar(
                x=[str(year) for year in years],
                y=values,
                name='📊 FATURAMENTO',
                marker_color='#27ae60',
                marker_pattern_shape='/',
                text=[format_currency(v) for v in values],
                textposition='outside',
                hovertemplate='<b>FATURAMENTO</b><br>%{x}: %{y:,.0f}<extra></extra>'
            ))
    
    elif scale_option == "Área Empilhada":
        # Create stacked area chart
        for i, (subcat_name, year_values) in enumerate(sorted_subcats[:max_subcategories]):
            values = [year_values.get(year, 0) for year in years]
            
            if any(v > 0 for v in values):
                fig.add_trace(go.Scatter(
                    x=[str(year) for year in years],
                    y=values,
                    mode='lines',
                    name=subcat_name,
                    stackgroup='one',
                    fillcolor=colors[i % len(colors)],
                    line=dict(width=0.5, color=colors[i % len(colors)])
                ))
    
    elif scale_option == "% Composição":
        # Calculate total expenses per year
        totals_per_year = {}
        for year in years:
            total = 0
            for subcat_name, year_values in sorted_subcats[:max_subcategories]:
                total += year_values.get(year, 0)
            totals_per_year[year] = total if total > 0 else 1
        
        # Add percentage traces
        for i, (subcat_name, year_values) in enumerate(sorted_subcats[:max_subcategories]):
            values = [year_values.get(year, 0) for year in years]
            percentages = [(v / totals_per_year[y]) * 100 for v, y in zip(values, years)]
            
            if any(v > 0 for v in values):
                fig.add_trace(go.Scatter(
                    x=[str(year) for year in years],
                    y=percentages,
                    mode='lines',
                    name=subcat_name,
                    stackgroup='one',
                    groupnorm='percent',
                    fillcolor=colors[i % len(colors)],
                    line=dict(width=0.5, color=colors[i % len(colors)])
                ))
    
    elif scale_option == "Mini Gráficos":
        # Add individual traces to each subplot
        for i, (subcat_name, year_values) in enumerate(sorted_subcats[:max_subcategories]):
            values = [year_values.get(year, 0) for year in years]
            
            if any(v > 0 for v in values):
                row = (i // 3) + 1
                col = (i % 3) + 1
                
                fig.add_trace(go.Scatter(
                    x=[str(year) for year in years],
                    y=values,
                    mode='lines+markers',
                    name=subcat_name,
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=6),
                    showlegend=False
                ), row=row, col=col)
    
    elif scale_option == "Focar em Custos":
        # Show only expenses with better scale
        for i, (subcat_name, year_values) in enumerate(sorted_subcats[:max_subcategories]):
            values = [year_values.get(year, 0) for year in years]
            
            if any(v > 0 for v in values):
                fig.add_trace(go.Scatter(
                    x=[str(year) for year in years],
                    y=values,
                    mode='lines+markers',
                    name=subcat_name,
                    line=dict(color=colors[i % len(colors)], width=2.5),
                    marker=dict(size=8)
                ))
    
    else:
        # Default handling for other visualization types
        for i, (subcat_name, year_values) in enumerate(sorted_subcats[:max_subcategories]):
            values = [year_values.get(year, 0) for year in years]
            original_values = values.copy()  # Keep original for hover text
            
            # Only show subcategories with some non-zero values
            if any(v > 0 for v in values):
                # Adjust values based on visualization type
                if scale_option == "% do Faturamento":
                    revenue_values = [faturamento_data.get(year, 1) for year in years]
                    values = [(v / rv * 100) if rv > 0 else 0 for v, rv in zip(values, revenue_values)]
                elif scale_option == "Índice Base 100":
                    base_value = values[0] if values[0] > 0 else 1
                    values = [(v / base_value) * 100 for v in values]
                
                # Create hover text with details
                hover_texts = []
                for j, (year, value, orig_value) in enumerate(zip(years, values, original_values)):
                    text = f"<b>{subcat_name}</b><br>"
                    
                    if scale_option == "% do Faturamento":
                        text += f"<b>{year}:</b> {value:.2f}% do Faturamento<br>"
                        text += f"<b>Valor:</b> R$ {orig_value:,.2f}"
                    elif scale_option == "Índice Base 100":
                        text += f"<b>{year}:</b> Índice {value:.1f}<br>"
                        text += f"<b>Valor:</b> R$ {orig_value:,.2f}"
                    else:
                        text += f"<b>{year}:</b> R$ {orig_value:,.2f}<br>"
                    
                    # Add year-over-year change
                    if j > 0 and original_values[j-1] > 0:
                        change = ((orig_value - original_values[j-1]) / original_values[j-1]) * 100
                        text += f"<br><b>Variação:</b> {change:+.1f}%"
                    elif j > 0 and orig_value > 0:
                        text += "<br><b>Variação:</b> Novo"
                    
                    hover_texts.append(text)
                
                # Add to appropriate subplot if using separate charts
                if scale_option == "Separar Gráficos":
                    fig.add_trace(go.Scatter(
                        x=[str(year) for year in years],
                        y=values,
                        mode='lines+markers',
                        name=subcat_name,
                        line=dict(color=colors[i % len(colors)], width=2),
                        marker=dict(size=8),
                        hovertemplate='%{customdata}<extra></extra>',
                        customdata=hover_texts
                    ), row=2, col=1)
                else:
                    fig.add_trace(go.Scatter(
                        x=[str(year) for year in years],
                        y=values,
                        mode='lines+markers',
                        name=subcat_name,
                        line=dict(color=colors[i % len(colors)], width=2),
                        marker=dict(size=8),
                        hovertemplate='%{customdata}<extra></extra>',
                        customdata=hover_texts
                    ))
    
    # Configure layout based on scaling option
    if scale_option == "Barras Lado a Lado":
        # Layout for side by side bars - focus on expenses only
        # Calculate dynamic width based on number of selected categories
        num_categories = len(filtered_subcats) if 'filtered_subcats' in locals() else len(sorted_subcats[:max_subcategories])
        # Adjust bar width based on number of categories
        if num_categories > 15:
            bar_width = 100  # Slightly narrower for many categories
        elif num_categories > 10:
            bar_width = 120  # Standard width
        else:
            bar_width = 150  # Wider bars for fewer categories
        min_width = 1000
        chart_width = max(min_width, num_categories * bar_width)
        
        # Update layout based on orientation
        if horizontal_bars:
            # Horizontal layout - better for many categories
            chart_height = max(600, num_categories * 80)  # Dynamic height based on categories
            fig.update_layout(
                title=f"Comparação de Subcategorias de Custos - {min(years)}-{max(years)}",
                yaxis_title="Subcategorias",
                yaxis=dict(
                    tickfont=dict(size=12),
                    automargin=True  # Auto adjust margin for long labels
                ),
                xaxis_title="Valor (R$)",
                xaxis=dict(
                    tickformat=",.0f",
                    tickfont=dict(size=12)
                ),
                barmode='group',
                bargap=0.2,
                bargroupgap=0.1,
                hovermode='y unified',
                height=chart_height,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    title="Anos",
                    font=dict(size=12)
                ),
                font=dict(size=12)
            )
        else:
            # Vertical layout (default)
            fig.update_layout(
                title=f"Comparação de Subcategorias de Custos - {min(years)}-{max(years)}",
                xaxis_title="Subcategorias",
                xaxis=dict(
                    tickangle=-45,
                    tickfont=dict(size=14 if num_categories <= 10 else 12)
                ),
                yaxis_title="Valor (R$)",
                yaxis=dict(
                    tickformat=",.0f",
                    tickfont=dict(size=12)
                ),
                barmode='group',
                bargap=0.2,  # More space between category groups
                bargroupgap=0.1,  # More space between bars in same group
                hovermode='x unified',
                height=800,  # Taller chart for better label visibility
                width=chart_width,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    title="Anos",
                    font=dict(size=12)
                ),
                font=dict(size=12)
            )
        
        if show_faturamento and faturamento_data:
            # Show Faturamento info separately
            faturamento_2024 = faturamento_data.get(years[0], 0) if len(years) > 0 else 0
            faturamento_2025 = faturamento_data.get(years[-1], 0) if len(years) > 0 else 0
            faturamento_var = ((faturamento_2025 - faturamento_2024) / faturamento_2024 * 100) if faturamento_2024 > 0 else 0
            st.info(f"📊 Faturamento: {years[0] if len(years) > 0 else ''}: {format_currency(faturamento_2024)} | {years[-1] if len(years) > 0 else ''}: {format_currency(faturamento_2025)} | Variação: {faturamento_var:+.1f}%")
    
    elif scale_option == "Barras Agrupadas":
        # Layout for grouped bars
        fig.update_layout(
            title=f"{'Faturamento vs ' if show_faturamento else ''}Top {max_subcategories} Subcategorias - {min(years)}-{max(years)}",
            xaxis_title="Ano",
            xaxis=dict(
                tickmode='array',
                tickvals=[str(year) for year in years],
                ticktext=[str(year) for year in years]
            ),
            yaxis_title="Valor (R$)",
            yaxis=dict(tickformat=",.0f"),
            barmode='group',
            bargap=0.15,
            bargroupgap=0.1,
            hovermode='x unified',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
    
    elif scale_option == "Barras Empilhadas":
        # Layout for stacked bars
        fig.update_layout(
            title=f"Composição de Custos{'+ Faturamento' if show_faturamento else ''} - {min(years)}-{max(years)}",
            xaxis_title="Ano",
            xaxis=dict(
                tickmode='array',
                tickvals=[str(year) for year in years],
                ticktext=[str(year) for year in years]
            ),
            yaxis_title="Valor (R$)",
            yaxis=dict(tickformat=",.0f"),
            barmode='stack',
            hovermode='x unified',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
    
    elif scale_option == "Mini Gráficos":
        # Layout for small multiples
        fig.update_xaxes(
            tickmode='array',
            tickvals=[str(year) for year in years],
            ticktext=[str(year) for year in years]
        )
        fig.update_yaxes(tickformat=",.0f")
        fig.update_layout(
            height=200 * n_rows,
            showlegend=False,
            title_text=f"Evolução Individual das Subcategorias {min(years)}-{max(years)}"
        )
    
    elif scale_option == "Focar em Custos":
        # Layout focused on expenses only
        fig.update_layout(
            title=f"Top {max_subcategories} Subcategorias de Custos - {min(years)}-{max(years)}",
            xaxis_title="Ano",
            xaxis=dict(
                tickmode='array',
                tickvals=[str(year) for year in years],
                ticktext=[str(year) for year in years]
            ),
            yaxis_title="Valor (R$)",
            yaxis=dict(tickformat=",.0f"),
            hovermode='x unified',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
    
    elif scale_option == "Área Empilhada":
        # Layout for stacked area chart
        fig.update_layout(
            title=f"Composição de Custos por Subcategoria - {min(years)}-{max(years)}",
            xaxis_title="Ano",
            xaxis=dict(
                tickmode='array',
                tickvals=[str(year) for year in years],
                ticktext=[str(year) for year in years]
            ),
            yaxis_title="Valor (R$)",
            yaxis=dict(tickformat=",.0f"),
            hovermode='x unified',
            height=600,
            showlegend=True
        )
    
    elif scale_option == "% Composição":
        # Layout for percentage composition
        fig.update_layout(
            title=f"Composição Percentual de Custos - {min(years)}-{max(years)}",
            xaxis_title="Ano",
            xaxis=dict(
                tickmode='array',
                tickvals=[str(year) for year in years],
                ticktext=[str(year) for year in years]
            ),
            yaxis_title="Percentual (%)",
            yaxis=dict(tickformat=".0f", ticksuffix="%", range=[0, 100]),
            hovermode='x unified',
            height=600,
            showlegend=True
        )
    
    elif scale_option == "Separar Gráficos":
        # Layout for separate charts
        fig.update_xaxes(
            tickmode='array',
            tickvals=[str(year) for year in years],
            ticktext=[str(year) for year in years]
        )
        fig.update_yaxes(tickformat=",.0f", row=1, col=1)
        fig.update_yaxes(tickformat=",.0f", row=2, col=1)
        fig.update_layout(
            height=700,
            showlegend=True,
            hovermode='x unified',
            title_text=f"Evolução Financeira {min(years)}-{max(years)}"
        )
    else:
        layout_config = {
            'xaxis_title': "Ano",
            'xaxis': dict(
                tickmode='array',
                tickvals=[str(year) for year in years],
                ticktext=[str(year) for year in years]
            ),
            'hovermode': 'x unified',
            'height': 600,
            'showlegend': True,
            'legend': dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            'margin': dict(l=50, r=250, t=80, b=50)
        }
        
        # Configure title and y-axis based on scale option
        if scale_option == "% do Faturamento":
            layout_config['title'] = f"Custos como % do Faturamento - {min(years)}-{max(years)}"
            layout_config['yaxis'] = dict(
                title="% do Faturamento",
                tickformat=".1f",
                ticksuffix="%"
            )
        elif scale_option == "Índice Base 100":
            layout_config['title'] = f"Evolução Indexada (Base {years[0]}=100) - {min(years)}-{max(years)}"
            layout_config['yaxis'] = dict(
                title=f"Índice (Base {years[0]}=100)",
                tickformat=".0f"
            )
        elif scale_option == "Logarítmica":
            layout_config['title'] = f"{'Faturamento vs ' if show_faturamento else ''}Top {max_subcategories} Subcategorias - Escala Log"
            layout_config['yaxis'] = dict(
                title="Valor (R$) - Escala Log",
                type='log',
                tickformat=",.0f"
            )
        elif scale_option == "Dual Axis (Faturamento/Custos)":
            layout_config['title'] = f"Faturamento vs Top {max_subcategories} Subcategorias - Dual Axis"
            layout_config['yaxis'] = dict(
                title="Custos (R$)",
                tickformat=",.0f",
                side='left'
            )
            layout_config['yaxis2'] = dict(
                title="Faturamento (R$)",
                tickformat=",.0f",
                overlaying='y',
                side='right',
                showgrid=False
            )
        else:  # Linear
            layout_config['title'] = f"{'Faturamento vs ' if show_faturamento else ''}Top {max_subcategories} Subcategorias - {min(years)}-{max(years)}"
            layout_config['yaxis'] = dict(
                title="Valor (R$)",
                tickformat=",.0f"
            )
        
        fig.update_layout(**layout_config)
    
    # Display chart with special handling for wide "Barras Lado a Lado" charts
    if scale_option == "Barras Lado a Lado":
        # Use full width for scrollable chart
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.plotly_chart(fig, use_container_width=True)
    
    # Show summary statistics
    st.markdown("### 📊 Análise de Crescimento")
    
    # Add Faturamento to growth analysis if it exists
    growth_data = []
    
    # First add Faturamento growth
    if faturamento_data and years[0] in faturamento_data and years[-1] in faturamento_data:
        initial_value = faturamento_data[years[0]]
        final_value = faturamento_data[years[-1]]
        if initial_value > 0:
            growth_rate = ((final_value - initial_value) / initial_value) * 100
            growth_data.append({
                'Categoria': '📊 FATURAMENTO',
                f'{years[0]}': format_currency(initial_value),
                f'{years[-1]}': format_currency(final_value),
                'Crescimento %': f"{growth_rate:+.1f}%",
                'Diferença': format_currency(final_value - initial_value)
            })
    
    # Then add subcategories growth
    for subcat_name, year_values in sorted_subcats[:max_subcategories]:
        if years[0] in year_values and years[-1] in year_values:
            initial_value = year_values[years[0]]
            final_value = year_values[years[-1]]
            if initial_value > 0:
                growth_rate = ((final_value - initial_value) / initial_value) * 100
                growth_data.append({
                    'Categoria': subcat_name,
                    f'{years[0]}': format_currency(initial_value),
                    f'{years[-1]}': format_currency(final_value),
                    'Crescimento %': f"{growth_rate:+.1f}%",
                    'Diferença': format_currency(final_value - initial_value)
                })
    
    if growth_data:
        df_growth = pd.DataFrame(growth_data)
        st.dataframe(df_growth, use_container_width=True, hide_index=True)


def _render_subcategories_comparison(section_data: Dict, selected_years: List[int], time_period: str, year_colors: Dict):
    """
    Render subcategories comparison across years
    """
    st.markdown("##### 📂 Subcategorias")
    
    # Get all subcategories across years
    all_subcats = set()
    for section in section_data.values():
        subcats = section.get('subcategories', [])
        all_subcats.update(sub['name'] for sub in subcats)
    
    # Debug: Print what subcategories we found for this section
    section_names = [section.get('name', 'unknown') for section in section_data.values()]
    print(f"DEBUG: Subcategories in section(s) {section_names}: {sorted(all_subcats)}")
    
    if not all_subcats:
        st.info("Nenhuma subcategoria encontrada")
        return
    
    for subcat_name in sorted(all_subcats):
        with st.expander(f"🔹 {subcat_name}", expanded=False):
            # Show subcategory totals or monthly breakdown
            if time_period == "📊 Mensal":
                # Show monthly breakdown for subcategory
                st.markdown(f"**Evolução Mensal - {subcat_name}**")
                
                # Collect monthly data for all years
                fig = go.Figure()
                months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                
                # Dictionary to store most expensive items per month per year
                most_expensive_items = {}
                
                for year in selected_years:
                    if year in section_data:
                        subcats = section_data[year].get('subcategories', [])
                        subcat = next((s for s in subcats if s['name'] == subcat_name), None)
                        if subcat:
                            monthly_data = subcat.get('monthly', {})
                            values = [monthly_data.get(month, 0) for month in months]
                            
                            # Find most expensive item for each month
                            items = subcat.get('items', [])
                            
                            # If no items, check if subcategory itself has children or breakdown
                            if not items and subcat.get('children'):
                                items = subcat.get('children', [])
                            
                            for month in months:
                                max_item_name = None
                                max_item_value = 0
                                
                                # Check all items for this month
                                for item in items:
                                    item_monthly = item.get('monthly', {})
                                    item_value = item_monthly.get(month, 0)
                                    if item_value > max_item_value:
                                        max_item_value = item_value
                                        max_item_name = item.get('name', 'Unknown')
                                
                                # If still no items found but subcategory has monthly data, use subcategory itself
                                if not max_item_name and not items:
                                    subcat_monthly_value = monthly_data.get(month, 0)
                                    if subcat_monthly_value > 0:
                                        max_item_name = f"{subcat_name} (Total)"
                                        max_item_value = subcat_monthly_value
                                
                                if max_item_name and max_item_value > 0:
                                    if year not in most_expensive_items:
                                        most_expensive_items[year] = {}
                                    most_expensive_items[year][month] = {
                                        'name': max_item_name,
                                        'value': max_item_value
                                    }
                            
                            if any(v > 0 for v in values):
                                # Calculate year-over-year changes if we have multiple years
                                hover_text = []
                                for i, month in enumerate(months):
                                    value = values[i]
                                    text = f"<b>{month} {year}</b><br>"
                                    text += f"<b>Valor Total:</b> R$ {value:,.2f}<br>"
                                    
                                    # Add most expensive item info
                                    if year in most_expensive_items and month in most_expensive_items[year]:
                                        item_info = most_expensive_items[year][month]
                                        text += f"<b>Item Mais Caro:</b> {item_info['name']}<br>"
                                        text += f"<b>Valor do Item:</b> R$ {item_info['value']:,.2f}<br>"
                                        if value > 0:
                                            item_pct = (item_info['value'] / value) * 100
                                            text += f"<b>% do Total:</b> {item_pct:.1f}%<br>"
                                    
                                    # Add percentage of total
                                    total = sum(values)
                                    if total > 0:
                                        pct = (value / total) * 100
                                        text += f"<b>% do Ano:</b> {pct:.1f}%<br>"
                                    
                                    # Add month-over-month change
                                    if i > 0 and values[i-1] > 0:
                                        change = ((value - values[i-1]) / values[i-1]) * 100
                                        text += f"<b>Var. Mês Anterior:</b> {change:+.1f}%"
                                    
                                    hover_text.append(text)
                                
                                fig.add_trace(go.Scatter(
                                    x=months,
                                    y=values,
                                    mode='lines+markers',
                                    name=str(year),
                                    line=dict(color=year_colors.get(year, '#808080'), width=2),
                                    marker=dict(size=6),
                                    hovertemplate='%{customdata}<extra></extra>',
                                    customdata=hover_text
                                ))
                
                if fig.data:
                    fig.update_layout(
                        height=250,
                        margin=dict(t=20, b=30, l=30, r=30),
                        xaxis_title="Mês",
                        yaxis_title="Valor (R$)",
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                    )
                    # Create unique key including section name to avoid duplicates
                    section_name = next(iter(section_data.values())).get('name', 'unknown')
                    # Sanitize names for use in keys
                    safe_section = section_name.replace(' ', '_').replace('/', '_')
                    safe_subcat = subcat_name.replace(' ', '_').replace('/', '_')
                    st.plotly_chart(fig, use_container_width=True, key=f"subcat_monthly_{safe_section}_{safe_subcat}")
                else:
                    st.info("Sem dados mensais disponíveis para esta subcategoria")
            else:
                # Show annual totals with graphs
                st.markdown(f"**📊 Comparação Anual - {subcat_name}**")
                
                # First show the metrics
                cols = st.columns(len(selected_years) + 1)  # +1 for comparison
                subcat_values = {}
                
                for i, year in enumerate(selected_years):
                    with cols[i]:
                        if year in section_data:
                            subcats = section_data[year].get('subcategories', [])
                            subcat = next((s for s in subcats if s['name'] == subcat_name), None)
                            value = subcat.get('value', 0) if subcat else 0
                            subcat_values[year] = value
                            st.metric(f"{year}", format_currency(value))
                        else:
                            subcat_values[year] = 0
                            st.metric(f"{year}", "R$ 0")
                
                # Show change analysis in last column (only for annual view)
                with cols[-1]:
                    if len(selected_years) == 2:
                        val1, val2 = subcat_values[selected_years[0]], subcat_values[selected_years[1]]
                        if val1 > 0:
                            change_pct = ((val2 - val1) / val1) * 100
                            st.metric("Variação", f"{change_pct:+.1f}%")
                        else:
                            st.metric("Variação", "Novo" if val2 > 0 else "N/A")
                
                # Add annual comparison line chart
                if subcat_values:
                    fig = go.Figure()
                    
                    # Create line for the trend
                    years = sorted(subcat_values.keys())
                    values = [subcat_values[year] for year in years]
                    
                    # Create hover text with details
                    hover_texts = []
                    for i, (year, value) in enumerate(zip(years, values)):
                        text = f"<b>{year}</b><br>"
                        text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
                        if i > 0:
                            change = ((value - values[i-1]) / values[i-1] * 100) if values[i-1] > 0 else 0
                            text += f"<b>Variação:</b> {change:+.1f}%"
                        hover_texts.append(text)
                    
                    fig.add_trace(go.Scatter(
                        x=[str(year) for year in years],
                        y=values,
                        mode='lines+markers',
                        name=subcat_name,
                        line=dict(color='#e74c3c', width=3),
                        marker=dict(size=8, color='#e74c3c'),
                        text=[f'R$ {v:,.0f}' for v in values],
                        textposition='top center',
                        hovertemplate='%{customdata}<extra></extra>',
                        customdata=hover_texts
                    ))
                    
                    fig.update_layout(
                        height=250,
                        margin=dict(t=10, b=30, l=30, r=30),
                        xaxis_title="Ano",
                        xaxis=dict(
                            tickmode='array',
                            tickvals=[str(year) for year in years],
                            ticktext=[str(year) for year in years]
                        ),
                        yaxis_title="Valor (R$)",
                        yaxis=dict(tickformat=",.0f"),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, key=f"annual_subcat_{subcat_name.replace(' ', '_')}")
                
                # Add period progression chart for non-monthly time periods
                if time_period in ["📈 Trimestral", "📆 Semestral", "📅 Customizado"]:
                    st.markdown(f"**Evolução {time_period.replace('📈 ', '').replace('📆 ', '').replace('📅 ', '')} - {subcat_name}**")
                    _render_subcategory_period_comparison(section_data, selected_years, subcat_name, year_colors, time_period)
            
            # Add new visualization: All items in one chart for comparison
            if time_period == "📊 Mensal":
                st.markdown(f"**📊 Comparação de Itens - {subcat_name}**")
                
                # Let user choose visualization type
                col1, col2 = st.columns([3, 1])
                with col2:
                    chart_type = st.selectbox(
                        "Tipo de Gráfico",
                        ["📈 Linhas", "📊 Barras Agrupadas", "📚 Barras Empilhadas", "🌊 Área Empilhada", "🔥 Heatmap", "📊 Análise de Tendência"],
                        key=f"chart_type_{subcat_name.replace(' ', '_')}"
                    )
                
                _render_items_comparison_chart(section_data, selected_years, subcat_name, chart_type)
            
            # Show individual items if available
            _render_items_comparison(section_data, selected_years, subcat_name, time_period, year_colors)


def _render_subcategory_period_comparison(section_data: Dict, selected_years: List[int], subcat_name: str, year_colors: Dict, time_period: str):
    """
    Render period progression chart for subcategory comparison
    """
    # Define period mappings based on time_period
    if time_period == "📈 Trimestral":
        period_mappings = {
            'Q1': ['JAN', 'FEV', 'MAR'],
            'Q2': ['ABR', 'MAI', 'JUN'], 
            'Q3': ['JUL', 'AGO', 'SET'],
            'Q4': ['OUT', 'NOV', 'DEZ']
        }
        period_labels = ['Q1', 'Q2', 'Q3', 'Q4']
    elif time_period == "📆 Semestral":
        period_mappings = {
            'S1': ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN'],
            'S2': ['JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        }
        period_labels = ['S1', 'S2']
    else:  # Custom periods
        period_mappings = {
            'T1': ['JAN', 'FEV', 'MAR'],
            'T2': ['ABR', 'MAI', 'JUN'], 
            'T3': ['JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        }
        period_labels = ['T1', 'T2', 'T3']
    
    fig = go.Figure()
    
    # Collect data for each year
    for year in selected_years:
        if year in section_data:
            # Find the subcategory in this year's data
            subcats = section_data[year].get('subcategories', [])
            subcat = next((s for s in subcats if s['name'] == subcat_name), None)
            
            if subcat:
                monthly_data = subcat.get('monthly', {})
                
                if monthly_data:
                    # Aggregate monthly data to periods
                    period_values = []
                    for period in period_labels:
                        period_total = 0
                        months_in_period = period_mappings.get(period, [])
                        for month in months_in_period:
                            period_total += monthly_data.get(month, 0)
                        period_values.append(period_total)
                    
                    # Create hover text for each period
                    hover_text = []
                    yearly_total = sum(period_values)
                    
                    for i, (period, value) in enumerate(zip(period_labels, period_values)):
                        text = f"<b>{period} - {year}</b><br>"
                        text += f"<b>{subcat_name}</b><br>"
                        text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
                        
                        # Add percentage of year total
                        if yearly_total > 0:
                            pct = (value / yearly_total) * 100
                            text += f"<b>% do Ano:</b> {pct:.1f}%<br>"
                        
                        # Add period-over-period change
                        if i > 0 and period_values[i-1] > 0:
                            pop_change = ((value - period_values[i-1]) / period_values[i-1]) * 100
                            text += f"<b>Var. Período Anterior:</b> {pop_change:+.1f}%"
                        
                        hover_text.append(text)
                    
                    # Add line trace for this year
                    fig.add_trace(go.Scatter(
                        x=period_labels,
                        y=period_values,
                        mode='lines+markers',
                        name=str(year),
                        line=dict(color=year_colors.get(year, '#1f77b4'), width=2),
                        marker=dict(size=6),
                        hovertemplate='%{customdata}<extra></extra>',
                        customdata=hover_text
                    ))
    
    # Configure layout
    period_type = time_period.replace('📈 ', '').replace('📆 ', '').replace('📅 ', '')
    fig.update_layout(
        title=None,  # No title since we already have the markdown title
        xaxis_title=f"Períodos {period_type}",
        yaxis_title="Valor (R$)",
        hovermode='x unified',
        showlegend=True,
        height=300,
        margin=dict(t=20, b=50, l=50, r=20),
        yaxis=dict(tickformat=",.0f")
    )
    
    # Create unique key for plotly chart to avoid conflicts
    section_name = next(iter(section_data.values())).get('name', 'unknown')
    safe_section = section_name.replace(' ', '_').replace('/', '_')
    safe_subcat = subcat_name.replace(' ', '_').replace('/', '_')
    
    st.plotly_chart(fig, use_container_width=True, key=f"subcat_period_{safe_section}_{safe_subcat}")


def _render_items_comparison(section_data: Dict, selected_years: List[int], subcat_name: str, time_period: str, year_colors: Dict):
    """
    Render individual items comparison within subcategory
    """
    # Get all items for this subcategory across years
    all_items = set()
    subcat_data = {}
    
    for year in selected_years:
        if year in section_data:
            subcats = section_data[year].get('subcategories', [])
            subcat = next((s for s in subcats if s['name'] == subcat_name), None)
            if subcat:
                subcat_data[year] = subcat
                all_items.update(item['name'] for item in subcat.get('items', []))
    
    if not all_items or len(all_items) == 0:
        return
    
    st.markdown("**👥 Itens Individuais:**")
    
    if time_period == "📊 Mensal":
        # Show monthly breakdown for each item
        for item_name in sorted(all_items):
            with st.expander(f"📌 {item_name}", expanded=False):
                fig = go.Figure()
                months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                
                has_data = False
                for year in selected_years:
                    if year in subcat_data:
                        items = subcat_data[year].get('items', [])
                        item = next((i for i in items if i['name'] == item_name), None)
                        if item:
                            monthly_data = item.get('monthly', {})
                            values = [monthly_data.get(month, 0) for month in months]
                            
                            if any(v > 0 for v in values):
                                has_data = True
                                
                                # Create detailed hover text
                                hover_text = []
                                for i, month in enumerate(months):
                                    value = values[i]
                                    text = f"<b>{item_name}</b><br>"
                                    text += f"<b>{month} {year}</b><br>"
                                    text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
                                    
                                    # Add percentage of year total
                                    total = sum(values)
                                    if total > 0:
                                        pct = (value / total) * 100
                                        text += f"<b>% do Ano:</b> {pct:.1f}%<br>"
                                    
                                    # Add month-over-month change
                                    if i > 0 and values[i-1] > 0:
                                        change = ((value - values[i-1]) / values[i-1]) * 100
                                        text += f"<b>Var. Mês Anterior:</b> {change:+.1f}%"
                                    elif i > 0:
                                        text += f"<b>Var. Mês Anterior:</b> Novo"
                                    
                                    hover_text.append(text)
                                
                                fig.add_trace(go.Scatter(
                                    x=months,
                                    y=values,
                                    mode='lines+markers',
                                    name=str(year),
                                    line=dict(color=year_colors.get(year, '#808080'), width=2),
                                    marker=dict(size=5),
                                    hovertemplate='%{customdata}<extra></extra>',
                                    customdata=hover_text
                                ))
                
                if has_data:
                    fig.update_layout(
                        height=200,
                        margin=dict(t=10, b=30, l=30, r=30),
                        xaxis_title="Mês",
                        yaxis_title="Valor (R$)",
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                    )
                    # Create unique key including section and subcategory names to avoid duplicates
                    section_name = next(iter(section_data.values())).get('name', 'unknown')
                    # Sanitize names for use in keys
                    safe_section = section_name.replace(' ', '_').replace('/', '_')
                    safe_subcat = subcat_name.replace(' ', '_').replace('/', '_')
                    safe_item = item_name.replace(' ', '_').replace('/', '_')
                    unique_key = f"item_monthly_{safe_section}_{safe_subcat}_{safe_item}"
                    st.plotly_chart(fig, use_container_width=True, key=unique_key)
                else:
                    st.info("Sem dados mensais disponíveis para este item")
    else:
        # Show annual comparison with bar chart for items
        st.markdown("**📊 Comparação Anual de Itens**")
        
        # Collect data for visualization
        item_data = {}
        for item_name in sorted(all_items):
            item_data[item_name] = {}
            
            for year in selected_years:
                if year in subcat_data:
                    items = subcat_data[year].get('items', [])
                    item = next((i for i in items if i['name'] == item_name), None)
                    value = item.get('value', 0) if item else 0
                    item_data[item_name][year] = value
                else:
                    item_data[item_name][year] = 0
        
        if item_data:
            # Create line chart for items
            fig = go.Figure()
            
            # Define colors for items
            item_colors = {
                'Marketing': '#e74c3c',
                'Publicidade': '#3498db',
                'Tráfego pago': '#2ecc71',
                'Advogados': '#f39c12',
                'Condomínios': '#9b59b6',
                'Energia Elétrica': '#1abc9c',
                'Internet': '#34495e',
                'Manutenção': '#e67e22',
                'Segurança': '#95a5a6',
                'Telefonia': '#d35400'
            }
            default_item_colors = ['#c0392b', '#2980b9', '#27ae60', '#f1c40f', '#8e44ad']
            
            # Add line for each item
            color_idx = 0
            years = sorted(selected_years)
            
            for item_name in sorted(all_items):
                values = [item_data[item_name].get(year, 0) for year in years]
                
                # Only show items with some data
                if any(v > 0 for v in values):
                    # Get color for this item
                    if item_name in item_colors:
                        color = item_colors[item_name]
                    else:
                        color = default_item_colors[color_idx % len(default_item_colors)]
                        color_idx += 1
                    
                    # Create hover text
                    hover_texts = []
                    for i, (year, value) in enumerate(zip(years, values)):
                        text = f"<b>{item_name}</b><br>"
                        text += f"<b>{year}</b><br>"
                        text += f"<b>Valor:</b> R$ {value:,.2f}"
                        if i > 0 and values[i-1] > 0:
                            change = ((value - values[i-1]) / values[i-1] * 100)
                            text += f"<br><b>Variação:</b> {change:+.1f}%"
                        hover_texts.append(text)
                    
                    fig.add_trace(go.Scatter(
                        x=[str(year) for year in years],
                        y=values,
                        mode='lines+markers',
                        name=item_name,
                        line=dict(color=color, width=2),
                        marker=dict(size=6),
                        hovertemplate='%{customdata}<extra></extra>',
                        customdata=hover_texts
                    ))
            
            if fig.data:
                fig.update_layout(
                    height=350,
                    margin=dict(t=20, b=30, l=50, r=20),
                    xaxis_title="Ano",
                    xaxis=dict(
                        tickmode='array',
                        tickvals=[str(year) for year in years],
                        ticktext=[str(year) for year in years]
                    ),
                    yaxis_title="Valor (R$)",
                    yaxis=dict(tickformat=",.0f"),
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True, key=f"annual_items_{subcat_name.replace(' ', '_')}")
            
            # Also show the comparison table
            st.markdown("**📋 Tabela Comparativa**")
            item_comparison = []
            for item_name in sorted(all_items):
                row = {'Item': item_name}
                
                for year in selected_years:
                    value = item_data[item_name].get(year, 0)
                    row[str(year)] = value
                
                # Calculate change if 2 years
                if len(selected_years) == 2:
                    val1, val2 = row[str(selected_years[0])], row[str(selected_years[1])]
                    if val1 > 0:
                        change = ((val2 - val1) / val1) * 100
                        row['Variação %'] = f"{change:+.1f}%"
                    else:
                        row['Variação %'] = "Novo" if val2 > 0 else "0%"
                
                item_comparison.append(row)
            
            if item_comparison:
                # Convert to display format
                df = pd.DataFrame(item_comparison)
                
                # Format currency columns
                for year in selected_years:
                    df[str(year)] = df[str(year)].apply(lambda x: format_currency(x))
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Add period progression charts for individual items in non-monthly periods
            if time_period in ["📈 Trimestral", "📆 Semestral", "📅 Customizado"]:
                st.markdown(f"**📊 Evolução {time_period.replace('📈 ', '').replace('📆 ', '').replace('📅 ', '')} por Item**")
                
                # Create individual charts for items with significant values
                items_with_data = []
                for item_name in sorted(all_items):
                    # Check if item has meaningful data across years
                    total_value = 0
                    for year in selected_years:
                        if year in subcat_data:
                            items = subcat_data[year].get('items', [])
                            item = next((i for i in items if i['name'] == item_name), None)
                            if item:
                                total_value += item.get('value', 0)
                    
                    if total_value > 1000:  # Only show items with meaningful values (> R$ 1000)
                        items_with_data.append(item_name)
                
                # Render period charts for significant items
                for item_name in items_with_data[:5]:  # Limit to top 5 items to avoid clutter
                    with st.expander(f"📈 {item_name} - Evolução {time_period.replace('📈 ', '').replace('📆 ', '').replace('📅 ', '')}", expanded=False):
                        _render_item_period_comparison(subcat_data, selected_years, item_name, year_colors, time_period, section_data, subcat_name)


def _render_items_comparison_chart(section_data: Dict, selected_years: List[int], subcat_name: str, chart_type: str = "📈 Linhas"):
    """
    Render a single chart with all items within a subcategory for easy comparison
    Supports different chart types for better visualization
    """
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Collect all unique items across all selected years
    all_items = set()
    items_data = {}
    
    for year in selected_years:
        if year in section_data:
            subcats = section_data[year].get('subcategories', [])
            subcat = next((s for s in subcats if s['name'] == subcat_name), None)
            
            if subcat:
                items = subcat.get('items', [])
                for item in items:
                    item_name = item.get('name')
                    if item_name:
                        all_items.add(item_name)
                        
                        # Store monthly data for this item and year
                        if item_name not in items_data:
                            items_data[item_name] = {}
                        
                        monthly_data = item.get('monthly', {})
                        if monthly_data:
                            items_data[item_name][year] = monthly_data
    
    if not items_data:
        st.info("Nenhum item com dados mensais encontrado nesta subcategoria")
        return
    
    # Create the comparison chart
    fig = go.Figure()
    
    # Define color palettes
    item_base_colors = {
        'Marketing': '#e74c3c',
        'Publicidade': '#3498db', 
        'Tráfego pago': '#2ecc71',
        'Advogados': '#f39c12',
        'Condomínios': '#9b59b6',
        'Energia Elétrica': '#1abc9c',
        'Internet': '#34495e',
        'Manutenção': '#e67e22',
        'Segurança': '#95a5a6',
        'Telefonia': '#d35400'
    }
    
    # Default colors for items not in the predefined list
    default_colors = ['#c0392b', '#2980b9', '#27ae60', '#f1c40f', '#8e44ad']
    
    # Define consistent year colors
    year_colors_ordered = {
        2021: '#9b59b6',  # Purple
        2022: '#3498db',  # Blue
        2023: '#e74c3c',  # Red
        2024: '#f39c12',  # Orange
        2025: '#2ecc71',  # Green
        2026: '#1abc9c',  # Turquoise
    }
    
    if chart_type == "📊 Barras Agrupadas":
        # Create grouped bar chart - much clearer for comparing items
        # Sort years chronologically
        sorted_years = sorted(selected_years)
        
        for year in sorted_years:
            # Collect data for all items for this year
            year_values = []
            year_items = []
            
            for item_name in sorted(all_items):
                if item_name in items_data and year in items_data[item_name]:
                    monthly_data = items_data[item_name][year]
                    # Calculate average monthly value (excluding zeros)
                    monthly_values = [monthly_data.get(month, 0) for month in months]
                    non_zero_values = [v for v in monthly_values if v > 0]
                    avg_value = sum(non_zero_values) / len(non_zero_values) if non_zero_values else 0
                    
                    if avg_value > 0:
                        year_values.append(avg_value)
                        year_items.append(item_name)
            
            if year_values:
                # Use consistent year color
                year_color = year_colors_ordered.get(year, '#808080')
                
                fig.add_trace(go.Bar(
                    name=str(year),
                    x=year_items,
                    y=year_values,
                    marker_color=year_color,
                    text=[f'R$ {v:,.0f}' for v in year_values],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>' +
                                  f'<b>{year}</b><br>' +
                                  '<b>Média Mensal:</b> R$ %{y:,.2f}<extra></extra>'
                ))
        
        # Focus on showing individual months for better detail
        st.markdown("**📅 Detalhamento Mensal:**")
        
        # Month selector
        selected_month = st.selectbox(
            "Selecione o mês para análise detalhada:",
            months,
            index=0,
            key=f"month_select_{subcat_name.replace(' ', '_')}"
        )
        
        # Create detailed bar chart for selected month
        fig_month = go.Figure()
        
        # Sort years chronologically for consistent ordering
        sorted_years_detail = sorted(selected_years)
        
        for year in sorted_years_detail:
            month_values = []
            month_items = []
            
            for item_name in sorted(all_items):
                if item_name in items_data and year in items_data[item_name]:
                    value = items_data[item_name][year].get(selected_month, 0)
                    if value > 0:
                        month_values.append(value)
                        month_items.append(item_name)
            
            if month_values:
                # Use consistent year color
                year_color = year_colors_ordered.get(year, '#808080')
                
                fig_month.add_trace(go.Bar(
                    name=str(year),
                    x=month_items,
                    y=month_values,
                    marker_color=year_color,
                    text=[f'R$ {v:,.0f}' for v in month_values],
                    textposition='auto'
                ))
        
        if fig_month.data:
            fig_month.update_layout(
                title=f"Comparação de Itens - {selected_month}",
                barmode='group',
                height=300,
                xaxis_title="Item",
                yaxis_title="Valor (R$)",
                yaxis=dict(tickformat=",.0f")
            )
            st.plotly_chart(fig_month, use_container_width=True, key=f"month_detail_{subcat_name.replace(' ', '_')}_{selected_month}")
    
    elif chart_type == "🌊 Área Empilhada":
        # Create stacked area chart showing flow over time (like the drawing)
        # This shows how the composition changes smoothly over time
        
        # Prepare data for each item across all months
        fig = go.Figure()
        
        # Create x-axis with all months
        x_months = []
        for year in sorted(selected_years):
            for month in months:
                x_months.append(f"{month}/{str(year)[-2:]}")
        
        # Add area trace for each item
        for item_name in sorted(all_items):
            if item_name in items_data:
                y_values = []
                
                for year in sorted(selected_years):
                    if year in items_data[item_name]:
                        monthly_data = items_data[item_name][year]
                        for month in months:
                            y_values.append(monthly_data.get(month, 0))
                    else:
                        # Fill with zeros if no data for this year
                        y_values.extend([0] * 12)
                
                # Only add if there's some data
                if any(v > 0 for v in y_values):
                    # Get color for this item
                    if item_name in item_base_colors:
                        color = item_base_colors[item_name]
                    else:
                        color = default_colors[len(fig.data) % len(default_colors)]
                    
                    # Create hover text
                    hover_texts = []
                    for i, (month_label, value) in enumerate(zip(x_months, y_values)):
                        hover_text = f"<b>{item_name}</b><br>"
                        hover_text += f"<b>{month_label}</b><br>"
                        hover_text += f"<b>Valor:</b> R$ {value:,.2f}"
                        hover_texts.append(hover_text)
                    
                    fig.add_trace(go.Scatter(
                        x=x_months,
                        y=y_values,
                        mode='lines',
                        name=item_name,
                        line=dict(width=0.5, color=color),
                        fillcolor=color,
                        stackgroup='one',  # This creates the stacked area effect
                        hovertemplate='%{customdata}<extra></extra>',
                        customdata=hover_texts
                    ))
        
        if fig.data:
            fig.update_layout(
                title="Fluxo de Despesas ao Longo do Tempo",
                height=450,
                xaxis_title="Mês/Ano",
                yaxis_title="Valor Acumulado (R$)",
                yaxis=dict(tickformat=",.0f"),
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
            
            # Adjust x-axis for better readability
            fig.update_xaxes(
                tickangle=-45,
                nticks=len(x_months) // 2  # Show every other month to avoid crowding
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"area_{subcat_name.replace(' ', '_')}")
            
            # Add insights specific to area chart
            st.markdown("**📊 Análise de Composição:**")
            
            # Calculate total for each month
            monthly_totals = []
            for i in range(len(x_months)):
                total = sum(trace.y[i] for trace in fig.data if i < len(trace.y))
                monthly_totals.append(total)
            
            if monthly_totals:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Find month with highest total
                    max_idx = monthly_totals.index(max(monthly_totals))
                    if max_idx < len(x_months):
                        st.metric(
                            "Pico de Gastos",
                            x_months[max_idx],
                            f"R$ {monthly_totals[max_idx]:,.0f}"
                        )
                
                with col2:
                    # Find month with lowest total
                    non_zero_totals = [(i, t) for i, t in enumerate(monthly_totals) if t > 0]
                    if non_zero_totals:
                        min_idx = min(non_zero_totals, key=lambda x: x[1])[0]
                        st.metric(
                            "Menor Gasto",
                            x_months[min_idx],
                            f"R$ {monthly_totals[min_idx]:,.0f}"
                        )
                
                with col3:
                    # Calculate average composition
                    avg_total = sum(monthly_totals) / len([t for t in monthly_totals if t > 0]) if any(monthly_totals) else 0
                    st.metric(
                        "Média Mensal",
                        f"R$ {avg_total:,.0f}",
                        f"{len(fig.data)} itens"
                    )
            
            return  # Exit after rendering area chart
    
    elif chart_type == "🔥 Heatmap":
        # Create heatmap showing patterns across months and items
        import numpy as np
        
        # Prepare data matrix
        all_months_labels = []
        for year in sorted(selected_years):
            for month in months:
                all_months_labels.append(f"{month}/{str(year)[-2:]}")
        
        # Create matrix: items x months
        matrix_data = []
        item_names_list = sorted(list(all_items))
        
        for item_name in item_names_list:
            row = []
            for year in sorted(selected_years):
                if item_name in items_data and year in items_data[item_name]:
                    monthly_data = items_data[item_name][year]
                    for month in months:
                        row.append(monthly_data.get(month, 0))
                else:
                    row.extend([0] * 12)
            matrix_data.append(row)
        
        if matrix_data:
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=matrix_data,
                x=all_months_labels,
                y=item_names_list,
                colorscale='RdYlBu_r',
                hovertemplate='<b>%{y}</b><br>' +
                              '<b>%{x}</b><br>' +
                              '<b>Valor:</b> R$ %{z:,.0f}<extra></extra>',
                colorbar=dict(title="Valor (R$)")
            ))
            
            fig.update_layout(
                title="Padrões de Gastos por Item e Mês",
                height=300 + (len(item_names_list) * 30),
                xaxis_title="Mês/Ano",
                yaxis_title="Item",
                xaxis={'tickangle': -45}
            )
            
            # Show insights below heatmap
            st.plotly_chart(fig, use_container_width=True, key=f"heatmap_{subcat_name.replace(' ', '_')}")
            
            # Identify patterns
            st.markdown("**🔍 Padrões Identificados:**")
            
            # Find highest spending months
            total_by_month = np.sum(matrix_data, axis=0)
            peak_months = np.argsort(total_by_month)[-3:][::-1]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📈 Meses com Maior Gasto:**")
                for idx in peak_months:
                    if idx < len(all_months_labels) and total_by_month[idx] > 0:
                        st.caption(f"• {all_months_labels[idx]}: R$ {total_by_month[idx]:,.0f}")
            
            with col2:
                st.markdown("**💰 Item Mais Consistente:**")
                # Find item with most consistent spending (lowest std dev relative to mean)
                for i, item_name in enumerate(item_names_list):
                    item_values = [v for v in matrix_data[i] if v > 0]
                    if len(item_values) > 3:
                        mean_val = np.mean(item_values)
                        std_val = np.std(item_values)
                        cv = std_val / mean_val if mean_val > 0 else float('inf')
                        if cv < 0.5:  # Low coefficient of variation
                            st.caption(f"• {item_name}: Variação de {cv*100:.1f}%")
                            break
            
            return  # Exit early for heatmap
    
    elif chart_type == "📊 Análise de Tendência":
        # Create trend analysis with growth rates
        fig = go.Figure()
        
        # Calculate growth rates for each item
        growth_data = {}
        
        for item_name in sorted(all_items):
            if item_name in items_data and len(items_data[item_name]) > 1:
                years_with_data = sorted(items_data[item_name].keys())
                if len(years_with_data) >= 2:
                    # Calculate year-over-year growth
                    first_year = years_with_data[0]
                    last_year = years_with_data[-1]
                    
                    first_total = sum(items_data[item_name][first_year].values())
                    last_total = sum(items_data[item_name][last_year].values())
                    
                    if first_total > 0:
                        growth_rate = ((last_total - first_total) / first_total) * 100
                        growth_data[item_name] = {
                            'growth': growth_rate,
                            'first_year': first_year,
                            'last_year': last_year,
                            'first_total': first_total,
                            'last_total': last_total
                        }
        
        if growth_data:
            # Sort by growth rate
            sorted_items = sorted(growth_data.items(), key=lambda x: x[1]['growth'], reverse=True)
            
            # Create waterfall chart showing changes
            item_names_sorted = [item[0] for item in sorted_items]
            growth_rates = [item[1]['growth'] for item in sorted_items]
            
            # Color code by positive/negative growth
            colors = ['green' if g > 0 else 'red' for g in growth_rates]
            
            fig.add_trace(go.Bar(
                x=item_names_sorted,
                y=growth_rates,
                marker_color=colors,
                text=[f"{g:+.1f}%" for g in growth_rates],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>' +
                              '<b>Crescimento:</b> %{y:+.1f}%<br>' +
                              '<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"Taxa de Crescimento ({sorted(selected_years)[0]} → {sorted(selected_years)[-1]})",
                height=400,
                xaxis_title="Item",
                yaxis_title="Taxa de Crescimento (%)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"trend_{subcat_name.replace(' ', '_')}")
            
            # Show detailed insights
            st.markdown("**📊 Análise de Tendências:**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**🚀 Maior Crescimento:**")
                for item, data in sorted_items[:2]:
                    if data['growth'] > 0:
                        st.success(f"{item}: +{data['growth']:.1f}%")
                        st.caption(f"R$ {data['first_total']:,.0f} → R$ {data['last_total']:,.0f}")
            
            with col2:
                st.markdown("**📉 Maior Redução:**")
                for item, data in sorted_items[-2:]:
                    if data['growth'] < 0:
                        st.error(f"{item}: {data['growth']:.1f}%")
                        st.caption(f"R$ {data['first_total']:,.0f} → R$ {data['last_total']:,.0f}")
            
            with col3:
                st.markdown("**📈 Resumo Geral:**")
                total_first = sum(d['first_total'] for d in growth_data.values())
                total_last = sum(d['last_total'] for d in growth_data.values())
                overall_growth = ((total_last - total_first) / total_first * 100) if total_first > 0 else 0
                
                if overall_growth > 0:
                    st.metric("Crescimento Total", f"+{overall_growth:.1f}%", f"R$ {total_last - total_first:,.0f}")
                else:
                    st.metric("Redução Total", f"{overall_growth:.1f}%", f"R$ {total_last - total_first:,.0f}")
            
            return  # Exit early for trend analysis
    
    elif chart_type == "📚 Barras Empilhadas":
        # Create stacked bar chart showing composition over time
        for item_name in sorted(all_items):
            if item_name in items_data:
                # Combine data from all years
                all_values = []
                all_labels = []
                
                for year in selected_years:
                    if year in items_data[item_name]:
                        monthly_data = items_data[item_name][year]
                        values = [monthly_data.get(month, 0) for month in months]
                        all_values.extend(values)
                        all_labels.extend([f"{month}/{str(year)[-2:]}" for month in months])
                
                if any(v > 0 for v in all_values):
                    # Get color for this item
                    if item_name in item_base_colors:
                        color = item_base_colors[item_name]
                    else:
                        color = default_colors[len(fig.data) % len(default_colors)]
                    
                    fig.add_trace(go.Bar(
                        name=item_name,
                        x=all_labels,
                        y=all_values,
                        marker_color=color,
                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                      '<b>%{x}</b><br>' +
                                      '<b>Valor:</b> R$ %{y:,.2f}<extra></extra>'
                    ))
        
        fig.update_layout(barmode='stack')
    
    else:  # Line chart - cleaner version with continuous x-axis
        # Create continuous x-axis with all months from all years
        x_axis_continuous = []
        for year in sorted(selected_years):
            for month in months:
                x_axis_continuous.append(f"{month}/{str(year)[-2:]}")
        
        # Add a trace for each item
        color_idx = 0
        for item_name in sorted(all_items):
            if item_name in items_data:
                # Get base color for this item
                if item_name in item_base_colors:
                    item_color = item_base_colors[item_name]
                else:
                    item_color = default_colors[color_idx % len(default_colors)]
                    color_idx += 1
                
                # Collect all values across years
                all_values = []
                hover_texts = []
                
                for year in sorted(selected_years):
                    if year in items_data[item_name]:
                        monthly_data = items_data[item_name][year]
                        for month in months:
                            value = monthly_data.get(month, 0)
                            all_values.append(value)
                            
                            hover_text = f"<b>{item_name}</b><br>"
                            hover_text += f"<b>{month} {year}</b><br>"
                            hover_text += f"<b>Valor:</b> R$ {value:,.2f}"
                            hover_texts.append(hover_text)
                    else:
                        # Fill with zeros if no data for this year
                        all_values.extend([0] * 12)
                        for month in months:
                            hover_text = f"<b>{item_name}</b><br>"
                            hover_text += f"<b>{month} {year}</b><br>"
                            hover_text += f"<b>Sem dados</b>"
                            hover_texts.append(hover_text)
                
                if any(v > 0 for v in all_values):
                    fig.add_trace(go.Scatter(
                        x=x_axis_continuous,
                        y=all_values,
                        mode='lines+markers',
                        name=item_name,
                        line=dict(color=item_color, width=2),
                        marker=dict(size=4, color=item_color),
                        hovertemplate='%{customdata}<extra></extra>',
                        customdata=hover_texts
                    ))
    
    if fig.data:
        # Different layout configurations based on chart type
        if chart_type == "📊 Barras Agrupadas":
            fig.update_layout(
                title="Média Mensal por Item",
                barmode='group',
                height=350,
                margin=dict(t=40, b=30, l=50, r=20),
                xaxis_title="Item",
                yaxis_title="Valor Médio Mensal (R$)",
                yaxis=dict(tickformat=",.0f"),
                showlegend=True
            )
        elif chart_type == "📚 Barras Empilhadas":
            fig.update_layout(
                height=400,
                margin=dict(t=20, b=50, l=50, r=20),
                xaxis_title="Mês/Ano",
                yaxis_title="Valor (R$)",
                yaxis=dict(tickformat=",.0f"),
                showlegend=True,
                xaxis_tickangle=-45
            )
        else:  # Line chart
            fig.update_layout(
                height=400,
                margin=dict(t=20, b=50, l=50, r=20),
                xaxis_title="Mês/Ano",
                yaxis_title="Valor (R$)",
                yaxis=dict(tickformat=",.0f"),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                ),
                hovermode='x unified'
            )
            # Adjust x-axis to show labels at an angle and skip some for clarity
            fig.update_xaxes(
                tickangle=-45,
                nticks=20  # Limit number of ticks shown
            )
        
        # Create unique key
        section_name = next(iter(section_data.values())).get('name', 'unknown')
        safe_section = section_name.replace(' ', '_').replace('/', '_')
        safe_subcat = subcat_name.replace(' ', '_').replace('/', '_')
        
        st.plotly_chart(fig, use_container_width=True, key=f"items_comparison_{safe_section}_{safe_subcat}")
        
        # Show different tips based on chart type
        if chart_type == "📊 Barras Agrupadas":
            st.caption("💡 **Dica:** O gráfico mostra a média mensal de cada item. Use o seletor abaixo para ver meses específicos.")
        elif chart_type == "📚 Barras Empilhadas":
            st.caption("💡 **Dica:** Veja a composição total das despesas ao longo do tempo. As barras mostram como cada item contribui para o total.")
        else:
            st.caption("💡 **Dica:** Linhas sólidas = 2023, Linhas tracejadas = 2024. Use a legenda para mostrar/ocultar itens.")
        
        # Show top items summary only if not grouped bars (since it shows averages separately)
        if chart_type != "📊 Barras Agrupadas":
            # Show top items by total value
            items_totals = []
            for item_name in sorted(all_items):
                if item_name in items_data:
                    total = 0
                    for year_data in items_data[item_name].values():
                        total += sum(year_data.values())
                    if total > 0:
                        items_totals.append((item_name, total))
            
            if items_totals:
                items_totals.sort(key=lambda x: x[1], reverse=True)
                
                # Show top 3 items
                st.markdown("**🏆 Top 3 Itens por Valor Total:**")
                for i, (item, total) in enumerate(items_totals[:3]):
                    medal = ["🥇", "🥈", "🥉"][i]
                    st.caption(f"{medal} {item}: R$ {total:,.0f}")
    else:
        st.info("Sem dados suficientes para criar o gráfico de comparação")


def _render_subcategory_insights(section_data: Dict, selected_years: List[int], subcat_name: str):
    """
    Render advanced insights for subcategory analysis
    """
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Collect all data for analysis
    all_data = {}
    for year in selected_years:
        if year in section_data:
            subcats = section_data[year].get('subcategories', [])
            subcat = next((s for s in subcats if s['name'] == subcat_name), None)
            if subcat:
                all_data[year] = subcat
    
    if not all_data:
        return
    
    st.markdown("---")
    st.markdown("**🧠 Insights Inteligentes:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📊 Análise de Sazonalidade:**")
        
        # Analyze seasonal patterns
        monthly_totals = {month: 0 for month in months}
        month_counts = {month: 0 for month in months}
        
        for year_data in all_data.values():
            monthly = year_data.get('monthly', {})
            for month, value in monthly.items():
                if value > 0:
                    monthly_totals[month] = monthly_totals.get(month, 0) + value
                    month_counts[month] = month_counts.get(month, 0) + 1
        
        # Calculate averages
        monthly_avg = {}
        for month in months:
            if month_counts.get(month, 0) > 0:
                monthly_avg[month] = monthly_totals[month] / month_counts[month]
        
        if monthly_avg:
            # Find peak and low seasons
            sorted_months = sorted(monthly_avg.items(), key=lambda x: x[1], reverse=True)
            
            if len(sorted_months) >= 3:
                st.success(f"📈 Pico: {sorted_months[0][0]} (R$ {sorted_months[0][1]:,.0f})")
                st.error(f"📉 Baixa: {sorted_months[-1][0]} (R$ {sorted_months[-1][1]:,.0f})")
                
                # Calculate seasonality index
                avg_value = sum(monthly_avg.values()) / len(monthly_avg)
                max_deviation = max(abs(v - avg_value) for v in monthly_avg.values())
                seasonality_index = (max_deviation / avg_value * 100) if avg_value > 0 else 0
                
                if seasonality_index > 50:
                    st.warning(f"⚠️ Alta sazonalidade: {seasonality_index:.0f}%")
                else:
                    st.info(f"✅ Baixa sazonalidade: {seasonality_index:.0f}%")
    
    with col2:
        st.markdown("**💡 Otimização Sugerida:**")
        
        # Find optimization opportunities
        items_analysis = {}
        for year_data in all_data.values():
            items = year_data.get('items', [])
            for item in items:
                item_name = item.get('name')
                if item_name:
                    if item_name not in items_analysis:
                        items_analysis[item_name] = []
                    items_analysis[item_name].append(item.get('value', 0))
        
        # Find items with high variance
        optimization_suggestions = []
        for item_name, values in items_analysis.items():
            if len(values) > 1 and max(values) > 0:
                variance_ratio = (max(values) - min(values)) / max(values)
                if variance_ratio > 0.5:
                    optimization_suggestions.append({
                        'item': item_name,
                        'potential_saving': max(values) - min(values),
                        'variance': variance_ratio * 100
                    })
        
        if optimization_suggestions:
            sorted_suggestions = sorted(optimization_suggestions, key=lambda x: x['potential_saving'], reverse=True)
            for suggestion in sorted_suggestions[:2]:
                st.info(f"💰 {suggestion['item']}")
                st.caption(f"Economia potencial: R$ {suggestion['potential_saving']:,.0f}")
        else:
            st.success("✅ Gastos consistentes")
    
    with col3:
        st.markdown("**🎯 Previsão de Tendência:**")
        
        # Simple trend prediction
        if len(selected_years) >= 2:
            yearly_totals = []
            for year in sorted(selected_years):
                if year in all_data:
                    yearly_totals.append(all_data[year].get('value', 0))
            
            if len(yearly_totals) >= 2:
                # Calculate average growth rate
                growth_rates = []
                for i in range(1, len(yearly_totals)):
                    if yearly_totals[i-1] > 0:
                        growth = ((yearly_totals[i] - yearly_totals[i-1]) / yearly_totals[i-1]) * 100
                        growth_rates.append(growth)
                
                if growth_rates:
                    avg_growth = sum(growth_rates) / len(growth_rates)
                    next_year = sorted(selected_years)[-1] + 1
                    projected_value = yearly_totals[-1] * (1 + avg_growth/100)
                    
                    st.metric(
                        f"Projeção {next_year}",
                        f"R$ {projected_value:,.0f}",
                        f"{avg_growth:+.1f}% a.a."
                    )
                    
                    if avg_growth > 20:
                        st.warning("⚠️ Crescimento acelerado - revisar orçamento")
                    elif avg_growth < -10:
                        st.success("✅ Redução significativa de custos")


def _render_item_period_comparison(subcat_data: Dict, selected_years: List[int], item_name: str, year_colors: Dict, time_period: str, section_data: Dict, subcat_name: str):
    """
    Render period progression chart for individual item comparison
    """
    # Define period mappings based on time_period
    if time_period == "📈 Trimestral":
        period_mappings = {
            'Q1': ['JAN', 'FEV', 'MAR'],
            'Q2': ['ABR', 'MAI', 'JUN'], 
            'Q3': ['JUL', 'AGO', 'SET'],
            'Q4': ['OUT', 'NOV', 'DEZ']
        }
        period_labels = ['Q1', 'Q2', 'Q3', 'Q4']
    elif time_period == "📆 Semestral":
        period_mappings = {
            'S1': ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN'],
            'S2': ['JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        }
        period_labels = ['S1', 'S2']
    else:  # Custom periods
        period_mappings = {
            'T1': ['JAN', 'FEV', 'MAR'],
            'T2': ['ABR', 'MAI', 'JUN'], 
            'T3': ['JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        }
        period_labels = ['T1', 'T2', 'T3']
    
    fig = go.Figure()
    has_data = False
    
    # Collect data for each year
    for year in selected_years:
        if year in subcat_data:
            # Find the item in this year's subcategory data
            items = subcat_data[year].get('items', [])
            item = next((i for i in items if i['name'] == item_name), None)
            
            if item:
                monthly_data = item.get('monthly', {})
                
                if monthly_data:
                    # Aggregate monthly data to periods
                    period_values = []
                    for period in period_labels:
                        period_total = 0
                        months_in_period = period_mappings.get(period, [])
                        for month in months_in_period:
                            period_total += monthly_data.get(month, 0)
                        period_values.append(period_total)
                    
                    if any(v > 0 for v in period_values):
                        has_data = True
                        
                        # Create hover text for each period
                        hover_text = []
                        yearly_total = sum(period_values)
                        
                        for i, (period, value) in enumerate(zip(period_labels, period_values)):
                            text = f"<b>{period} - {year}</b><br>"
                            text += f"<b>{item_name}</b><br>"
                            text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
                            
                            # Add percentage of year total
                            if yearly_total > 0:
                                pct = (value / yearly_total) * 100
                                text += f"<b>% do Ano:</b> {pct:.1f}%<br>"
                            
                            # Add period-over-period change
                            if i > 0 and period_values[i-1] > 0:
                                pop_change = ((value - period_values[i-1]) / period_values[i-1]) * 100
                                text += f"<b>Var. Período Anterior:</b> {pop_change:+.1f}%"
                            
                            hover_text.append(text)
                        
                        # Add line trace for this year
                        fig.add_trace(go.Scatter(
                            x=period_labels,
                            y=period_values,
                            mode='lines+markers',
                            name=str(year),
                            line=dict(color=year_colors.get(year, '#1f77b4'), width=2),
                            marker=dict(size=6),
                            hovertemplate='%{customdata}<extra></extra>',
                            customdata=hover_text
                        ))
    
    if has_data:
        # Configure layout
        period_type = time_period.replace('📈 ', '').replace('📆 ', '').replace('📅 ', '')
        fig.update_layout(
            title=None,  # No title since we already have the expander title
            xaxis_title=f"Períodos {period_type}",
            yaxis_title="Valor (R$)",
            hovermode='x unified',
            showlegend=True,
            height=250,
            margin=dict(t=20, b=40, l=40, r=20),
            yaxis=dict(tickformat=",.0f")
        )
        
        # Create unique key for plotly chart to avoid conflicts
        section_name = next(iter(section_data.values())).get('name', 'unknown')
        safe_section = section_name.replace(' ', '_').replace('/', '_')
        safe_subcat = subcat_name.replace(' ', '_').replace('/', '_')
        safe_item = item_name.replace(' ', '_').replace('/', '_')
        
        st.plotly_chart(fig, use_container_width=True, key=f"item_period_{safe_section}_{safe_subcat}_{safe_item}")
    else:
        st.info(f"Sem dados mensais disponíveis para agregação {time_period.replace('📈 ', '').replace('📆 ', '').replace('📅 ', '')} de {item_name}")


def _render_section_comparison(expense_data: Dict, selected_years: List[int], all_sections: set):
    """
    Render section-level comparison with bar charts
    """
    st.markdown("### 🏢 Comparação por Seção Principal")
    
    # Prepare data for comparison chart
    section_values = {}
    for section_name in sorted(all_sections):
        section_values[section_name] = {}
        for year in selected_years:
            year_sections = expense_data.get(year, [])
            section = next((s for s in year_sections if s['name'] == section_name), None)
            section_values[section_name][year] = section.get('value', 0) if section else 0
    
    # Create grouped bar chart
    fig = go.Figure()
    
    year_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, year in enumerate(selected_years):
        values = [section_values[section][year] for section in sorted(all_sections)]
        fig.add_trace(go.Bar(
            name=str(year),
            x=list(sorted(all_sections)),
            y=values,
            text=[format_currency(v) for v in values],
            textposition='auto',
            marker_color=year_colors[i % len(year_colors)]
        ))
    
    fig.update_layout(
        title="Comparação de Seções Principais",
        barmode='group',
        height=500,
        xaxis_tickangle=-45,
        yaxis_title="Valor (R$)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_multi_year_comparison_table(expense_data: Dict, selected_years: List[int]):
    """
    Render comprehensive comparison table
    """
    st.markdown("### 📊 Tabela Comparativa Detalhada")
    
    # This would use similar logic to the existing year_comparison.py
    # but adapted for the new multi-year structure
    st.info("🚧 Tabela comparativa detalhada em desenvolvimento")
    
    # For now, show a simple summary
    summary_data = []
    all_sections = set()
    for year_sections in expense_data.values():
        all_sections.update(section['name'] for section in year_sections)
    
    for section_name in sorted(all_sections):
        row = {'Seção': section_name}
        for year in selected_years:
            year_sections = expense_data.get(year, [])
            section = next((s for s in year_sections if s['name'] == section_name), None)
            row[str(year)] = format_currency(section.get('value', 0) if section else 0)
        summary_data.append(row)
    
    if summary_data:
        df = pd.DataFrame(summary_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def _render_change_analysis(expense_data: Dict, selected_years: List[int]):
    """
    Render detailed change analysis between years
    """
    st.markdown("### 🔥 Análise Detalhada de Mudanças")
    
    if len(selected_years) != 2:
        st.warning("Análise de mudanças disponível apenas para comparação entre 2 anos.")
        return
    
    year1, year2 = selected_years[0], selected_years[1]
    year1_sections = expense_data.get(year1, [])
    year2_sections = expense_data.get(year2, [])
    
    # Calculate changes
    increases = []
    decreases = []
    new_items = []
    removed_items = []
    
    year1_dict = {s['name']: s for s in year1_sections}
    year2_dict = {s['name']: s for s in year2_sections}
    
    all_sections = set(year1_dict.keys()) | set(year2_dict.keys())
    
    for section_name in all_sections:
        val1 = year1_dict.get(section_name, {}).get('value', 0)
        val2 = year2_dict.get(section_name, {}).get('value', 0)
        
        if val1 == 0 and val2 > 0:
            new_items.append((section_name, val2))
        elif val1 > 0 and val2 == 0:
            removed_items.append((section_name, val1))
        elif val2 > val1:
            change_pct = ((val2 - val1) / val1) * 100
            increases.append((section_name, val2 - val1, change_pct))
        elif val2 < val1:
            change_pct = ((val1 - val2) / val1) * 100
            decreases.append((section_name, val1 - val2, change_pct))
    
    # Display results
    col1, col2 = st.columns(2)
    
    with col1:
        if increases:
            st.markdown("#### 📈 Maiores Aumentos")
            for name, change, pct in sorted(increases, key=lambda x: x[1], reverse=True)[:5]:
                st.write(f"**{name}**: +{format_currency(change)} ({pct:+.1f}%)")
        
        if new_items:
            st.markdown("#### ✨ Novos Custos")
            for name, value in new_items:
                st.write(f"**{name}**: {format_currency(value)}")
    
    with col2:
        if decreases:
            st.markdown("#### 📉 Maiores Reduções")
            for name, change, pct in sorted(decreases, key=lambda x: x[1], reverse=True)[:5]:
                st.write(f"**{name}**: -{format_currency(change)} (-{pct:.1f}%)")
        
        if removed_items:
            st.markdown("#### ❌ Custos Eliminados")
            for name, value in removed_items:
                st.write(f"**{name}**: {format_currency(value)}")
    
    # Summary metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 Aumentos", len(increases))
    with col2:
        st.metric("📉 Reduções", len(decreases))
    with col3:
        st.metric("✨ Novos", len(new_items))
    with col4:
        st.metric("❌ Removidos", len(removed_items))


def _render_month_to_month_analysis(expense_data: Dict, selected_years: List[int]):
    """
    Render month-to-month sequential analysis showing how expenses change from month to month
    """
    st.header("📅 Análise Mês a Mês")
    
    if len(selected_years) < 1:
        st.warning("Selecione pelo menos 1 ano para análise mês a mês.")
        return
    
    # New intuitive tree-based hierarchy selector
    st.markdown("### 🌳 Selecionar Itens para Análise")
    st.markdown("*Expanda as seções para ver subcategorias e itens individuais*")
    
    # Create tree-based selection interface
    selected_entities = _render_tree_selector(expense_data, selected_years)
    
    # Multi-year comparison toggle and chart type selector
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        multi_year_mode = st.checkbox(
            "📊 Comparar Múltiplos Anos",
            value=len(selected_years) > 1,
            key="multi_year_mode"
        )
    
    with col2:
        if multi_year_mode:
            chart_type = st.selectbox(
                "📊 Tipo de Gráfico",
                ["📈 Linhas Multi-Anuais", "📈 Linhas com %", "🔥 Mapa de Calor", "📊 Área Empilhada"],
                key="month_chart_type_multi"
            )
            analysis_year = None  # Not used in multi-year mode
        else:
            analysis_year = st.selectbox(
                "📅 Selecionar Ano",
                selected_years,
                key="month_analysis_year"
            )
    
    with col3:
        if not multi_year_mode:
            chart_type = st.selectbox(
                "📊 Tipo de Gráfico",
                ["💧 Waterfall", "📈 Linha com %", "📊 Combo (Barras + Linha)", "🔥 Mapa de Calor"],
                key="month_chart_type_single"
            )
    
    if not multi_year_mode and analysis_year not in expense_data:
        st.warning(f"Dados não encontrados para {analysis_year}")
        return
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Handle multi-year mode
    if multi_year_mode:
        st.subheader(f"📊 Comparação Mensal - Anos: {', '.join(map(str, selected_years))}")
        
        # Render based on selected entities from tree
        if not selected_entities or not selected_entities.get('items'):
            st.info("📝 Selecione itens na árvore acima para ver a comparação mensal")
            return
        
        entity_type = selected_entities.get('type')
        items = selected_entities.get('items', [])
        
        if entity_type == 'sections':
            # Render section level comparison
            if chart_type == "📈 Linhas Multi-Anuais":
                _render_multi_year_lines(expense_data, selected_years, items, months, show_percentage=False)
            elif chart_type == "📈 Linhas com %":
                _render_multi_year_lines(expense_data, selected_years, items, months, show_percentage=True)
            elif chart_type == "🔥 Mapa de Calor":
                _render_multi_year_heatmap(expense_data, selected_years, items, months)
            elif chart_type == "📊 Área Empilhada":
                _render_stacked_area_chart(expense_data, selected_years, items, months)
        
        elif entity_type == 'subcategories':
            # Render subcategory level comparison
            _render_tree_subcategory_multi_year_lines(expense_data, selected_years, items, months, chart_type)
        
        elif entity_type == 'items':
            # Render item level comparison
            _render_tree_item_multi_year_lines(expense_data, selected_years, items, months, chart_type)
        
        return
    
    # Single year mode (existing code)
    sections = expense_data[analysis_year]
    
    # Calculate month-to-month changes for each section
    st.subheader(f"📊 Variações Mensais em {analysis_year}")
    
    # Handle different entity types for single year based on tree selection
    if selected_entities and selected_entities.get('items'):
        entity_type = selected_entities.get('type')
        items = selected_entities.get('items', [])
        
        if entity_type == 'subcategories':
            # Render subcategory level for single year
            for section in sections:
                for subcat in section.get('subcategories', []):
                    subcat_id = f"{section['name']}_{subcat['name']}"
                    if subcat_id in items:
                        _render_single_year_entity(subcat, months, analysis_year, chart_type, f"📁 {subcat['name']}")
            return
        
        elif entity_type == 'items':
            # Render item level for single year
            for section in sections:
                for subcat in section.get('subcategories', []):
                    for item in subcat.get('items', []):
                        item_id = f"{section['name']}_{subcat['name']}_{item['name']}"
                        if item_id in items:
                            _render_single_year_entity(item, months, analysis_year, chart_type, f"📌 {item['name']}")
            return
    
    # Default: section level rendering
    # Special handling for heat map - render all sections together
    if chart_type == "🔥 Mapa de Calor":
        _render_month_changes_heatmap(sections, months, analysis_year)
        return
    
    # For other chart types, render each section separately
    for section in sections:
        section_name = section['name']
        monthly_data = section.get('monthly', {})
        
        if not monthly_data or len(monthly_data) < 2:
            continue
        
        # Calculate month-over-month changes
        monthly_changes = []
        monthly_values = []
        
        for i, month in enumerate(months):
            current_value = monthly_data.get(month, 0)
            monthly_values.append(current_value)
            
            if i > 0 and current_value > 0:
                prev_month = months[i-1]
                prev_value = monthly_data.get(prev_month, 0)
                
                if prev_value > 0:
                    change_pct = ((current_value - prev_value) / prev_value) * 100
                    change_abs = current_value - prev_value
                    monthly_changes.append({
                        'from_month': prev_month,
                        'to_month': month,
                        'change_pct': change_pct,
                        'change_abs': change_abs,
                        'from_value': prev_value,
                        'to_value': current_value
                    })
        
        if monthly_changes:
            with st.expander(f"**{section_name}** - Mudanças Mês a Mês"):
                # Show month-to-month changes table
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Render different chart types based on selection
                    if chart_type == "💧 Waterfall":
                        _render_month_to_month_waterfall(monthly_changes, section_name, months, monthly_data)
                    elif chart_type == "📈 Linha com %":
                        _render_percentage_line_chart(monthly_changes, section_name, months, monthly_data)
                    elif chart_type == "📊 Combo (Barras + Linha)":
                        _render_combo_chart(monthly_changes, section_name, months, monthly_data)
                    elif chart_type == "🔥 Mapa de Calor":
                        pass  # Heat map will be rendered differently for all sections
                
                with col2:
                    st.markdown("##### 📊 Maiores Variações")
                    # Sort by absolute percentage change
                    sorted_changes = sorted(monthly_changes, key=lambda x: abs(x['change_pct']), reverse=True)
                    
                    for change in sorted_changes[:5]:
                        direction = "📈" if change['change_pct'] > 0 else "📉"
                        st.write(f"{direction} **{change['from_month']}→{change['to_month']}**: {change['change_pct']:+.1f}%")
                
                # Show detailed table
                st.markdown("##### 📋 Detalhamento Completo")
                changes_df = pd.DataFrame([
                    {
                        'Transição': f"{c['from_month']} → {c['to_month']}",
                        'Valor Inicial': format_currency(c['from_value']),
                        'Valor Final': format_currency(c['to_value']),
                        'Variação': format_currency(c['change_abs']),
                        'Variação %': f"{c['change_pct']:+.1f}%"
                    } for c in monthly_changes
                ])
                
                st.dataframe(changes_df, hide_index=True, use_container_width=True)


def _render_single_year_entity(entity: Dict, months: List[str], analysis_year: int, chart_type: str, entity_label: str):
    """Render single year month-to-month analysis for a specific entity (subcategory or item)"""
    monthly_data = entity.get('monthly', {})
    
    if not monthly_data or len(monthly_data) < 2:
        return
    
    # Calculate month-over-month changes
    monthly_changes = []
    monthly_values = []
    
    for i, month in enumerate(months):
        current_value = monthly_data.get(month, 0)
        monthly_values.append(current_value)
        
        if i > 0 and current_value > 0:
            prev_month = months[i-1]
            prev_value = monthly_data.get(prev_month, 0)
            if prev_value > 0:
                change = ((current_value - prev_value) / prev_value) * 100
                monthly_changes.append({'month': month, 'change': change, 'value': current_value})
            else:
                monthly_changes.append({'month': month, 'change': 0, 'value': current_value})
        else:
            monthly_changes.append({'month': month, 'change': 0, 'value': current_value})
    
    # Skip if no significant data
    if sum(monthly_values) == 0:
        return
    
    with st.expander(f"**{entity_label}** - Mudanças Mês a Mês"):
        if chart_type == "💧 Waterfall":
            _render_month_to_month_waterfall(monthly_changes, entity_label, months, monthly_data)
        elif chart_type == "📈 Linha com %":
            _render_percentage_line_chart(monthly_changes, entity_label, months, monthly_data)
        elif chart_type == "📊 Combo (Barras + Linha)":
            _render_combo_chart(monthly_changes, entity_label, months, monthly_data)


def _render_month_to_month_waterfall(monthly_changes: List[Dict], section_name: str, months: List[str], monthly_data: Dict):
    """
    Render a waterfall chart showing month-to-month changes with percentage labels
    """
    # Prepare data for waterfall chart
    x_labels = [months[0]]  # Start with first month
    y_values = [monthly_data.get(months[0], 0)]  # Starting value
    measures = ['absolute']
    text_values = [format_currency(monthly_data.get(months[0], 0))]
    
    # Add each month-to-month change
    for change in monthly_changes:
        x_labels.append(f"{change['from_month']}→{change['to_month']}")
        y_values.append(change['change_abs'])
        measures.append('relative')
        # Show both value and percentage change
        sign = '+' if change['change_abs'] >= 0 else ''
        pct_sign = '+' if change['change_pct'] >= 0 else ''
        text_values.append(f"{sign}{format_currency(change['change_abs'])}<br>({pct_sign}{change['change_pct']:.1f}%)")
    
    # Add final total
    final_month = months[len([m for m in months if monthly_data.get(m, 0) > 0]) - 1]
    x_labels.append(final_month)
    y_values.append(monthly_data.get(final_month, 0))
    measures.append('total')
    text_values.append(format_currency(monthly_data.get(final_month, 0)))
    
    fig = go.Figure(go.Waterfall(
        x=x_labels,
        y=y_values,
        measure=measures,
        text=text_values,
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#d62728"}},
        increasing={"marker": {"color": "#2ca02c"}},
        totals={"marker": {"color": "#1f77b4"}}
    ))
    
    fig.update_layout(
        title=f"Evolução Mensal - {section_name}",
        height=400,
        xaxis_tickangle=-45,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_percentage_line_chart(monthly_changes: List[Dict], section_name: str, months: List[str], monthly_data: Dict):
    """
    Render a line chart with percentage change annotations
    """
    # Prepare data
    x_values = []
    y_values = []
    text_annotations = []
    colors = []
    
    # Add all months with values
    for month in months:
        value = monthly_data.get(month, 0)
        if value > 0:
            x_values.append(month)
            y_values.append(value)
    
    # Calculate percentage changes for annotations
    for i in range(len(x_values)):
        if i == 0:
            text_annotations.append("")  # No change for first month
            colors.append('blue')
        else:
            # Find the corresponding change
            change = next((c for c in monthly_changes if c['to_month'] == x_values[i]), None)
            if change:
                pct = change['change_pct']
                text_annotations.append(f"{pct:+.1f}%")
                colors.append('green' if pct >= 0 else 'red')
            else:
                text_annotations.append("")
                colors.append('blue')
    
    # Create line chart
    fig = go.Figure()
    
    # Add line trace
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers+text',
        name=section_name,
        text=text_annotations,
        textposition="top center",
        textfont=dict(size=12, color=colors),
        line=dict(color='#3498db', width=2),
        marker=dict(size=8, color=colors),
        hovertemplate='<b>%{x}</b><br>Valor: R$ %{y:,.0f}<br>%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Evolução Mensal com % de Mudança - {section_name}",
        xaxis_title="Mês",
        yaxis_title="Valor (R$)",
        height=400,
        showlegend=False,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_combo_chart(monthly_changes: List[Dict], section_name: str, months: List[str], monthly_data: Dict):
    """
    Render a combination chart with bars for values and line for percentage changes
    """
    # Prepare data
    x_values = []
    bar_values = []
    pct_changes = []
    
    # Add all months with values
    for i, month in enumerate(months):
        value = monthly_data.get(month, 0)
        if value > 0:
            x_values.append(month)
            bar_values.append(value)
            
            # Calculate percentage change
            if i == 0 or not any(c['to_month'] == month for c in monthly_changes):
                pct_changes.append(0)  # No change for first month
            else:
                change = next((c for c in monthly_changes if c['to_month'] == month), None)
                if change:
                    pct_changes.append(change['change_pct'])
                else:
                    pct_changes.append(0)
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add bar trace for values
    fig.add_trace(go.Bar(
        x=x_values,
        y=bar_values,
        name='Valor Mensal',
        marker_color='lightblue',
        yaxis='y',
        text=[format_currency(v) for v in bar_values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Valor: %{text}<extra></extra>'
    ))
    
    # Add line trace for percentage changes
    fig.add_trace(go.Scatter(
        x=x_values,
        y=pct_changes,
        mode='lines+markers+text',
        name='% Mudança',
        yaxis='y2',
        line=dict(color='red', width=2),
        marker=dict(size=8),
        text=[f"{pct:+.1f}%" if pct != 0 else "" for pct in pct_changes],
        textposition="top center",
        hovertemplate='<b>%{x}</b><br>Mudança: %{text}<extra></extra>'
    ))
    
    # Update layout with dual y-axes
    fig.update_layout(
        title=f"Valores e % de Mudança - {section_name}",
        xaxis_title="Mês",
        yaxis=dict(
            title="Valor (R$)",
            side='left'
        ),
        yaxis2=dict(
            title="% Mudança",
            overlaying='y',
            side='right',
            tickformat='+.1f'
        ),
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_month_changes_heatmap(sections: List[Dict], months: List[str], year: int):
    """
    Render a heat map showing month-over-month percentage changes for all sections
    """
    # Prepare data matrix
    section_names = []
    z_values = []  # Matrix of percentage changes
    hover_texts = []  # Custom hover text
    
    for section in sections:
        section_name = section['name']
        monthly_data = section.get('monthly', {})
        
        if not monthly_data or len(monthly_data) < 2:
            continue
        
        section_names.append(section_name)
        row_changes = []
        row_hover = []
        
        for i, month in enumerate(months):
            if i == 0:
                # First month has no change
                row_changes.append(0)
                value = monthly_data.get(month, 0)
                row_hover.append(f"{month}: {format_currency(value)}<br>Primeiro mês")
            else:
                current_value = monthly_data.get(month, 0)
                prev_value = monthly_data.get(months[i-1], 0)
                
                if prev_value > 0 and current_value > 0:
                    pct_change = ((current_value - prev_value) / prev_value) * 100
                    row_changes.append(pct_change)
                    row_hover.append(
                        f"{months[i-1]}→{month}<br>"
                        f"{format_currency(prev_value)} → {format_currency(current_value)}<br>"
                        f"Mudança: {pct_change:+.1f}%"
                    )
                else:
                    row_changes.append(0)
                    row_hover.append(f"{month}: Sem dados")
        
        z_values.append(row_changes)
        hover_texts.append(row_hover)
    
    if not z_values:
        st.info("Dados insuficientes para criar o mapa de calor")
        return
    
    # Create heat map
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=months,
        y=section_names,
        colorscale='RdYlGn',  # Red-Yellow-Green scale
        zmid=0,  # Center at 0%
        text=[[f"{val:+.1f}%" if val != 0 else "-" for val in row] for row in z_values],
        texttemplate='%{text}',
        textfont={"size": 10},
        customdata=hover_texts,
        hovertemplate='<b>%{y}</b><br>%{customdata}<extra></extra>',
        colorbar=dict(
            title="% Mudança",
            tickformat="+.0f"
        )
    ))
    
    fig.update_layout(
        title=f"🔥 Mapa de Calor - Mudanças Percentuais Mês a Mês ({year})",
        xaxis_title="Mês",
        yaxis_title="Categoria",
        height=400 + (len(section_names) * 20),  # Dynamic height based on sections
        xaxis={'side': 'bottom'},
        yaxis={'side': 'left', 'autorange': 'reversed'}  # Reverse to show first section at top
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add summary statistics
    col1, col2, col3 = st.columns(3)
    
    # Calculate overall statistics
    all_changes = [val for row in z_values for val in row if val != 0]
    
    if all_changes:
        with col1:
            avg_change = np.mean(all_changes)
            st.metric("📊 Mudança Média", f"{avg_change:+.1f}%")
        
        with col2:
            max_change = max(all_changes)
            st.metric("📈 Maior Aumento", f"{max_change:+.1f}%")
        
        with col3:
            min_change = min(all_changes)
            st.metric("📉 Maior Redução", f"{min_change:+.1f}%")


def _render_subcategory_multi_year_lines(expense_data: Dict, selected_years: List[int], section_name: str, subcategories: List[str], months: List[str], chart_type: str):
    """Render multi-year comparison for subcategories"""
    
    for subcat_name in subcategories:
        # Collect data for this subcategory across years
        subcat_year_data = {}
        
        for year in selected_years:
            if year in expense_data:
                for section in expense_data[year]:
                    if section['name'] == section_name:
                        for subcat in section.get('subcategories', []):
                            if subcat['name'] == subcat_name:
                                monthly_data = subcat.get('monthly', {})
                                if monthly_data:
                                    subcat_year_data[year] = monthly_data
                                break
                        break
        
        if not subcat_year_data:
            continue
        
        with st.expander(f"📁 **{subcat_name}** - Comparação Multi-Anual"):
            _render_multi_year_line_chart(subcat_year_data, months, subcat_name, selected_years, 
                                         show_percentage="com %" in chart_type)


def _render_item_multi_year_lines(expense_data: Dict, selected_years: List[int], section_name: str, subcat_name: str, items: List[str], months: List[str], chart_type: str):
    """Render multi-year comparison for individual items"""
    
    for item_name in items:
        # Collect data for this item across years
        item_year_data = {}
        
        for year in selected_years:
            if year in expense_data:
                for section in expense_data[year]:
                    if section['name'] == section_name:
                        for subcat in section.get('subcategories', []):
                            if subcat['name'] == subcat_name:
                                for item in subcat.get('items', []):
                                    if item['name'] == item_name:
                                        monthly_data = item.get('monthly', {})
                                        if monthly_data:
                                            item_year_data[year] = monthly_data
                                        break
                                break
                        break
        
        if not item_year_data:
            continue
        
        with st.expander(f"📌 **{item_name}** - Comparação Multi-Anual"):
            _render_multi_year_line_chart(item_year_data, months, item_name, selected_years,
                                         show_percentage="com %" in chart_type)


def _render_multi_year_line_chart(year_data: Dict, months: List[str], title: str, selected_years: List[int], show_percentage: bool = False):
    """Helper function to render a multi-year line chart"""
    fig = go.Figure()
    
    # Define colors for years
    year_colors = {
        2018: '#3498db', 2019: '#e74c3c', 2020: '#2ecc71', 2021: '#f39c12',
        2022: '#9b59b6', 2023: '#1abc9c', 2024: '#34495e', 2025: '#e67e22'
    }
    
    # Add a line for each year
    for year in sorted(year_data.keys()):
        monthly_data = year_data[year]
        x_values = []
        y_values = []
        hover_texts = []
        annotations = []
        
        for i, month in enumerate(months):
            value = monthly_data.get(month, 0)
            if value > 0:
                x_values.append(month)
                y_values.append(value)
                
                if show_percentage and i > 0:
                    prev_month = months[i-1]
                    prev_value = monthly_data.get(prev_month, 0)
                    if prev_value > 0:
                        pct_change = ((value - prev_value) / prev_value) * 100
                        annotations.append(f"{pct_change:+.1f}%")
                        hover_texts.append(
                            f"{year} - {month}<br>"
                            f"Valor: {format_currency(value)}<br>"
                            f"Mudança: {pct_change:+.1f}%"
                        )
                    else:
                        annotations.append("")
                        hover_texts.append(f"{year} - {month}<br>Valor: {format_currency(value)}")
                else:
                    annotations.append("")
                    hover_texts.append(f"{year} - {month}<br>Valor: {format_currency(value)}")
        
        # Add line trace for this year
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            name=str(year),
            line=dict(color=year_colors.get(year, '#000000'), width=2),
            marker=dict(size=6),
            text=annotations if show_percentage else None,
            textposition="top center" if show_percentage else None,
            hovertext=hover_texts,
            hoverinfo='text'
        ))
    
    # Update layout
    chart_title = f"Evolução Mensal - {title}"
    if show_percentage:
        chart_title += " (com % de mudança)"
    
    fig.update_layout(
        title=chart_title,
        xaxis_title="Mês",
        yaxis_title="Valor (R$)",
        height=350,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show summary metrics
    col1, col2, col3 = st.columns(3)
    
    # Calculate totals and growth
    totals = {year: sum(data.values()) for year, data in year_data.items()}
    sorted_years = sorted(totals.keys())
    
    with col1:
        if len(sorted_years) > 0:
            st.metric(f"Total {sorted_years[0]}", format_currency(totals[sorted_years[0]]))
    
    with col2:
        if len(sorted_years) > 1:
            st.metric(f"Total {sorted_years[-1]}", format_currency(totals[sorted_years[-1]]))
    
    with col3:
        if len(sorted_years) > 1:
            growth = ((totals[sorted_years[-1]] - totals[sorted_years[0]]) / totals[sorted_years[0]]) * 100
            st.metric("Crescimento Total", f"{growth:+.1f}%")


def _render_multi_year_lines(expense_data: Dict, selected_years: List[int], all_sections: set, months: List[str], show_percentage: bool = False):
    """
    Render multi-year line charts comparing monthly values across years
    """
    # Define colors for each year
    year_colors = {
        2018: '#1f77b4',  # Blue
        2019: '#ff7f0e',  # Orange
        2020: '#2ca02c',  # Green
        2021: '#d62728',  # Red
        2022: '#9467bd',  # Purple
        2023: '#8c564b',  # Brown
        2024: '#e377c2',  # Pink
        2025: '#7f7f7f',  # Gray
    }
    
    for section_name in sorted(all_sections):
        # Collect data for this section across all years
        has_data = False
        section_year_data = {}
        
        for year in selected_years:
            if year in expense_data:
                for section in expense_data[year]:
                    if section['name'] == section_name:
                        monthly_data = section.get('monthly', {})
                        if monthly_data:
                            section_year_data[year] = monthly_data
                            has_data = True
                        break
        
        if not has_data:
            continue
        
        with st.expander(f"**{section_name}** - Comparação Multi-Anual"):
            fig = go.Figure()
            
            # Add a line for each year
            for year in sorted(section_year_data.keys()):
                monthly_data = section_year_data[year]
                x_values = []
                y_values = []
                hover_texts = []
                annotations = []
                
                for i, month in enumerate(months):
                    value = monthly_data.get(month, 0)
                    if value > 0:
                        x_values.append(month)
                        y_values.append(value)
                        
                        # Calculate % change if showing percentages
                        if show_percentage and i > 0:
                            prev_month = months[i-1]
                            prev_value = monthly_data.get(prev_month, 0)
                            if prev_value > 0:
                                pct_change = ((value - prev_value) / prev_value) * 100
                                annotations.append(f"{pct_change:+.1f}%")
                                hover_texts.append(
                                    f"{year} - {month}<br>"
                                    f"Valor: {format_currency(value)}<br>"
                                    f"Mudança: {pct_change:+.1f}%"
                                )
                            else:
                                annotations.append("")
                                hover_texts.append(f"{year} - {month}<br>Valor: {format_currency(value)}")
                        else:
                            annotations.append("")
                            hover_texts.append(f"{year} - {month}<br>Valor: {format_currency(value)}")
                
                # Add line trace for this year
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='lines+markers',
                    name=str(year),
                    line=dict(color=year_colors.get(year, '#000000'), width=2),
                    marker=dict(size=6),
                    text=annotations if show_percentage else None,
                    textposition="top center" if show_percentage else None,
                    hovertext=hover_texts,
                    hoverinfo='text'
                ))
            
            # Update layout
            title = f"Evolução Mensal - {section_name}"
            if show_percentage:
                title += " (com % de mudança)"
            
            fig.update_layout(
                title=title,
                xaxis_title="Mês",
                yaxis_title="Valor (R$)",
                height=400,
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add comparison metrics
            col1, col2, col3 = st.columns(3)
            
            # Calculate year-over-year growth
            if len(section_year_data) >= 2:
                years_sorted = sorted(section_year_data.keys())
                first_year = years_sorted[0]
                last_year = years_sorted[-1]
                
                # Compare December values or last available month
                first_year_total = sum(section_year_data[first_year].values())
                last_year_total = sum(section_year_data[last_year].values())
                
                if first_year_total > 0:
                    total_growth = ((last_year_total - first_year_total) / first_year_total) * 100
                    
                    with col1:
                        st.metric(f"Total {first_year}", format_currency(first_year_total))
                    with col2:
                        st.metric(f"Total {last_year}", format_currency(last_year_total))
                    with col3:
                        st.metric("Crescimento Total", f"{total_growth:+.1f}%")


def _render_multi_year_heatmap(expense_data: Dict, selected_years: List[int], all_sections: set, months: List[str]):
    """
    Render a heat map showing values across multiple years and months
    """
    for section_name in sorted(all_sections):
        # Collect data for this section across all years
        has_data = False
        z_values = []
        y_labels = []
        
        for year in sorted(selected_years):
            if year in expense_data:
                for section in expense_data[year]:
                    if section['name'] == section_name:
                        monthly_data = section.get('monthly', {})
                        if monthly_data:
                            row_values = [monthly_data.get(month, 0) for month in months]
                            z_values.append(row_values)
                            y_labels.append(str(year))
                            has_data = True
                        break
        
        if not has_data:
            continue
        
        with st.expander(f"**{section_name}** - Mapa de Calor Multi-Anual"):
            # Create heat map
            fig = go.Figure(data=go.Heatmap(
                z=z_values,
                x=months,
                y=y_labels,
                colorscale='YlOrRd',
                text=[[format_currency(val) if val > 0 else "-" for val in row] for row in z_values],
                texttemplate='%{text}',
                textfont={"size": 9},
                hovertemplate='%{y} - %{x}<br>Valor: %{text}<extra></extra>',
                colorbar=dict(title="Valor (R$)")
            ))
            
            fig.update_layout(
                title=f"Mapa de Calor - {section_name}",
                xaxis_title="Mês",
                yaxis_title="Ano",
                height=200 + (len(y_labels) * 50)
            )
            
            st.plotly_chart(fig, use_container_width=True)


def _render_stacked_area_chart(expense_data: Dict, selected_years: List[int], all_sections: set, months: List[str]):
    """
    Render stacked area chart showing cumulative values across years
    """
    # Prepare data for all sections combined
    fig = go.Figure()
    
    for section_name in sorted(all_sections):
        for year in sorted(selected_years):
            if year in expense_data:
                for section in expense_data[year]:
                    if section['name'] == section_name:
                        monthly_data = section.get('monthly', {})
                        if monthly_data:
                            x_values = []
                            y_values = []
                            
                            for month in months:
                                value = monthly_data.get(month, 0)
                                x_values.append(f"{month}-{year}")
                                y_values.append(value)
                            
                            fig.add_trace(go.Scatter(
                                x=x_values,
                                y=y_values,
                                mode='lines',
                                name=f"{section_name} ({year})",
                                stackgroup='one',
                                hovertemplate='<b>%{x}</b><br>%{fullData.name}: %{y:,.0f}<extra></extra>'
                            ))
                        break
    
    fig.update_layout(
        title="Área Empilhada - Todas as Categorias",
        xaxis_title="Mês-Ano",
        yaxis_title="Valor Acumulado (R$)",
        height=500,
        hovermode='x unified',
        showlegend=True,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_seasonal_month_comparison(expense_data: Dict, selected_years: List[int]):
    """
    Render seasonal comparison showing same months across different years
    """
    st.header("🗓️ Comparação Sazonal")
    
    if len(selected_years) < 2:
        st.warning("Selecione pelo menos 2 anos para comparação sazonal.")
        return
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Month selector
    selected_month = st.selectbox(
        "📅 Selecionar Mês para Comparação Sazonal",
        months,
        format_func=lambda x: {
            'JAN': 'Janeiro', 'FEV': 'Fevereiro', 'MAR': 'Março', 'ABR': 'Abril',
            'MAI': 'Maio', 'JUN': 'Junho', 'JUL': 'Julho', 'AGO': 'Agosto',
            'SET': 'Setembro', 'OUT': 'Outubro', 'NOV': 'Novembro', 'DEZ': 'Dezembro'
        }[x],
        key="seasonal_month"
    )
    
    st.info(f"🔍 Comparando {selected_month} entre os anos: {', '.join(map(str, selected_years))}")
    
    # Collect all sections across all years
    all_sections = set()
    for year_data in expense_data.values():
        all_sections.update(section['name'] for section in year_data)
    
    # Create comparison data
    for section_name in sorted(all_sections):
        section_data = {}
        has_data = False
        
        for year in selected_years:
            if year in expense_data:
                for section in expense_data[year]:
                    if section['name'] == section_name:
                        monthly_data = section.get('monthly', {})
                        month_value = monthly_data.get(selected_month, 0)
                        section_data[year] = month_value
                        if month_value > 0:
                            has_data = True
        
        if not has_data:
            continue
        
        with st.expander(f"**{section_name}** - {selected_month} por Ano"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Create bar chart comparing the same month across years
                fig = go.Figure()
                
                years = list(section_data.keys())
                values = [section_data.get(year, 0) for year in years]
                
                fig.add_trace(go.Bar(
                    x=[str(year) for year in years],
                    y=values,
                    text=[format_currency(v) for v in values],
                    textposition='auto',
                    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(years)]
                ))
                
                fig.update_layout(
                    title=f"{section_name} - {selected_month}",
                    height=300,
                    showlegend=False,
                    xaxis=dict(
                        tickmode='array',
                        tickvals=[str(year) for year in years],
                        ticktext=[str(year) for year in years]
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("##### 📊 Crescimento Anual")
                # Calculate year-over-year growth
                sorted_years = sorted(years)
                for i in range(1, len(sorted_years)):
                    prev_year = sorted_years[i-1]
                    curr_year = sorted_years[i]
                    prev_val = section_data.get(prev_year, 0)
                    curr_val = section_data.get(curr_year, 0)
                    
                    if prev_val > 0:
                        growth = ((curr_val - prev_val) / prev_val) * 100
                        direction = "📈" if growth > 0 else "📉"
                        st.write(f"{direction} **{prev_year}→{curr_year}**: {growth:+.1f}%")


def _render_specific_month_comparison(expense_data: Dict, selected_years: List[int]):
    """
    Render comparison between any two specific months across any years
    """
    st.header("📊 Comparar Meses Específicos")
    
    if len(selected_years) < 1:
        st.warning("Selecione pelo menos 1 ano.")
        return
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    month_names = {
        'JAN': 'Janeiro', 'FEV': 'Fevereiro', 'MAR': 'Março', 'ABR': 'Abril',
        'MAI': 'Maio', 'JUN': 'Junho', 'JUL': 'Julho', 'AGO': 'Agosto',
        'SET': 'Setembro', 'OUT': 'Outubro', 'NOV': 'Novembro', 'DEZ': 'Dezembro'
    }
    
    # Available years
    available_years = [year for year in selected_years if year in expense_data]
    
    # Month and year selectors
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        month1 = st.selectbox(
            "📅 Primeiro Mês",
            months,
            format_func=lambda x: month_names[x],
            key="specific_month1"
        )
    
    with col2:
        year1 = st.selectbox(
            "📅 Primeiro Ano",
            available_years,
            key="specific_year1"
        )
    
    with col3:
        month2 = st.selectbox(
            "📅 Segundo Mês",
            months,
            format_func=lambda x: month_names[x],
            key="specific_month2",
            index=1 if len(months) > 1 else 0
        )
    
    with col4:
        year2 = st.selectbox(
            "📅 Segundo Ano",
            available_years,
            key="specific_year2",
            index=len(available_years)-1 if len(available_years) > 1 else 0
        )
    
    # Show comparison
    st.info(f"🔍 Comparando: {month_names[month1]} {year1} vs {month_names[month2]} {year2}")
    
    # Collect data for both months
    comparison_data = []
    
    # Get all sections
    all_sections = set()
    if year1 in expense_data:
        all_sections.update(section['name'] for section in expense_data[year1])
    if year2 in expense_data:
        all_sections.update(section['name'] for section in expense_data[year2])
    
    total1 = 0
    total2 = 0
    
    for section_name in sorted(all_sections):
        value1 = 0
        value2 = 0
        
        # Get value for first month/year
        if year1 in expense_data:
            for section in expense_data[year1]:
                if section['name'] == section_name:
                    monthly_data = section.get('monthly', {})
                    value1 = monthly_data.get(month1, 0)
                    break
        
        # Get value for second month/year
        if year2 in expense_data:
            for section in expense_data[year2]:
                if section['name'] == section_name:
                    monthly_data = section.get('monthly', {})
                    value2 = monthly_data.get(month2, 0)
                    break
        
        if value1 > 0 or value2 > 0:
            # Calculate change
            if value1 > 0:
                change_pct = ((value2 - value1) / value1) * 100
            else:
                change_pct = 100 if value2 > 0 else 0
            
            comparison_data.append({
                'section_name': section_name,
                'value1': value1,
                'value2': value2,
                'change': value2 - value1,
                'change_pct': change_pct
            })
            
            total1 += value1
            total2 += value2
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            f"{month_names[month1]} {year1}",
            format_currency(total1)
        )
    
    with col2:
        st.metric(
            f"{month_names[month2]} {year2}",
            format_currency(total2)
        )
    
    with col3:
        total_change_pct = ((total2 - total1) / total1 * 100) if total1 > 0 else (100 if total2 > 0 else 0)
        st.metric(
            "Variação Total",
            format_currency(total2 - total1),
            f"{total_change_pct:+.1f}%"
        )
    
    # Detailed comparison table
    if comparison_data:
        st.subheader("📋 Comparação Detalhada")
        
        df = pd.DataFrame([
            {
                'Categoria': item['section_name'],
                f'{month_names[month1]} {year1}': format_currency(item['value1']),
                f'{month_names[month2]} {year2}': format_currency(item['value2']),
                'Variação': format_currency(item['change']),
                'Variação %': f"{item['change_pct']:+.1f}%"
            } for item in comparison_data
        ])
        
        st.dataframe(df, hide_index=True, use_container_width=True)
        
        # Show biggest changes
        st.subheader("📈 Maiores Variações")
        
        # Sort by absolute percentage change
        sorted_data = sorted(comparison_data, key=lambda x: abs(x['change_pct']), reverse=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📈 Maiores Aumentos")
            increases = [item for item in sorted_data if item['change'] > 0]
            for item in increases[:5]:
                st.write(f"**{item['section_name']}**: +{format_currency(item['change'])} ({item['change_pct']:+.1f}%)")
        
        with col2:
            st.markdown("##### 📉 Maiores Reduções")
            decreases = [item for item in sorted_data if item['change'] < 0]
            for item in decreases[:5]:
                st.write(f"**{item['section_name']}**: {format_currency(item['change'])} ({item['change_pct']:+.1f}%)")
    
    else:
        st.info("Nenhum dado encontrado para comparação.")


def _render_month_to_month_variance_analysis(expense_data: Dict, selected_years: List[int]):
    """
    Render month-to-month variance analysis with outlier detection
    """
    st.header("📊 Análise de Variância Mês a Mês")
    
    if len(selected_years) < 1:
        st.warning("Selecione pelo menos 1 ano para análise de variância.")
        return
    
    # Year selector for variance analysis
    analysis_year = st.selectbox(
        "📅 Selecionar Ano para Análise de Variância",
        selected_years,
        key="variance_analysis_year"
    )
    
    # Get sections for analysis
    sections = expense_data[analysis_year]
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Variance threshold slider
    col1, col2 = st.columns([2, 1])
    with col1:
        outlier_threshold = st.slider(
            "🎯 Limite para Outliers (%)",
            min_value=10,
            max_value=100,
            value=30,
            step=5,
            help="Variações acima deste percentual serão destacadas como outliers"
        )
    
    with col2:
        show_only_outliers = st.checkbox("Mostrar apenas outliers", value=False)
    
    st.subheader(f"🔍 Análise de Variância - {analysis_year}")
    
    # Calculate variance statistics for each section
    variance_data = []
    
    for section in sections:
        section_name = section['name']
        monthly_data = section.get('monthly', {})
        
        # Get monthly values in order
        monthly_values = []
        for month in months:
            value = monthly_data.get(month, 0)
            monthly_values.append(value)
        
        # Calculate month-over-month changes
        monthly_changes = []
        for i in range(1, len(monthly_values)):
            current = monthly_values[i]
            previous = monthly_values[i-1]
            
            if previous > 0:
                pct_change = ((current - previous) / previous) * 100
            else:
                pct_change = 100 if current > 0 else 0
            
            monthly_changes.append({
                'from_month': months[i-1],
                'to_month': months[i],
                'from_value': previous,
                'to_value': current,
                'change_pct': pct_change,
                'change_abs': current - previous
            })
        
        # Calculate variance statistics
        if monthly_changes:
            change_percentages = [abs(c['change_pct']) for c in monthly_changes if c['change_pct'] != 0]
            
            if change_percentages:
                mean_change = np.mean(change_percentages)
                std_change = np.std(change_percentages)
                max_change = max(change_percentages)
                min_change = min(change_percentages)
                
                # Identify outliers (changes beyond threshold)
                outliers = [c for c in monthly_changes if abs(c['change_pct']) > outlier_threshold]
                
                variance_data.append({
                    'section_name': section_name,
                    'mean_variance': mean_change,
                    'std_variance': std_change,
                    'max_variance': max_change,
                    'min_variance': min_change,
                    'monthly_changes': monthly_changes,
                    'outliers': outliers,
                    'volatility_score': std_change / mean_change if mean_change > 0 else 0
                })
    
    # Filter data if showing only outliers
    if show_only_outliers:
        variance_data = [d for d in variance_data if len(d['outliers']) > 0]
    
    if not variance_data:
        st.info("Nenhum dado de variância encontrado para os critérios selecionados.")
        return
    
    # Sort by volatility score (highest first)
    variance_data.sort(key=lambda x: x['volatility_score'], reverse=True)
    
    # Display variance summary
    col1, col2, col3, col4 = st.columns(4)
    
    total_sections = len(variance_data)
    sections_with_outliers = len([d for d in variance_data if len(d['outliers']) > 0])
    avg_volatility = np.mean([d['volatility_score'] for d in variance_data])
    total_outliers = sum(len(d['outliers']) for d in variance_data)
    
    with col1:
        st.metric("📊 Categorias Analisadas", total_sections)
    
    with col2:
        st.metric("⚠️ Com Outliers", sections_with_outliers)
    
    with col3:
        st.metric("📈 Volatilidade Média", f"{avg_volatility:.2f}")
    
    with col4:
        st.metric("🔥 Total de Outliers", total_outliers)
    
    # Render variance analysis for each section
    for section_data in variance_data:
        section_name = section_data['section_name']
        outliers = section_data['outliers']
        
        with st.expander(f"📊 {section_name} - Volatilidade: {section_data['volatility_score']:.2f}", 
                        expanded=len(outliers) > 0):
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Variação Média", f"{section_data['mean_variance']:.1f}%")
                st.metric("Desvio Padrão", f"{section_data['std_variance']:.1f}%")
            
            with col2:
                st.metric("Maior Variação", f"{section_data['max_variance']:.1f}%")
                st.metric("Menor Variação", f"{section_data['min_variance']:.1f}%")
            
            with col3:
                st.metric("Outliers Detectados", len(outliers))
                st.metric("Score de Volatilidade", f"{section_data['volatility_score']:.2f}")
            
            # Show outliers if any
            if outliers:
                st.markdown("##### 🚨 Outliers Detectados:")
                outlier_table = []
                
                for outlier in outliers:
                    outlier_table.append({
                        'Transição': f"{outlier['from_month']} → {outlier['to_month']}",
                        'De': format_currency(outlier['from_value']),
                        'Para': format_currency(outlier['to_value']),
                        'Variação': format_currency(outlier['change_abs']),
                        'Variação %': f"{outlier['change_pct']:+.1f}%"
                    })
                
                outlier_df = pd.DataFrame(outlier_table)
                st.dataframe(outlier_df, hide_index=True, use_container_width=True)
            
            # Create variance chart
            months_for_chart = [c['to_month'] for c in section_data['monthly_changes']]
            changes_for_chart = [c['change_pct'] for c in section_data['monthly_changes']]
            
            # Create bar chart showing month-to-month changes
            fig = go.Figure()
            
            # Color bars based on outlier status
            colors = []
            for change in section_data['monthly_changes']:
                if abs(change['change_pct']) > outlier_threshold:
                    colors.append('#e74c3c')  # Red for outliers
                elif change['change_pct'] > 0:
                    colors.append('#2ecc71')  # Green for increases
                else:
                    colors.append('#3498db')  # Blue for decreases
            
            fig.add_trace(go.Bar(
                x=months_for_chart,
                y=changes_for_chart,
                marker=dict(color=colors),
                text=[f"{change:.1f}%" for change in changes_for_chart],
                textposition='outside'
            ))
            
            # Add threshold lines
            fig.add_hline(y=outlier_threshold, line_dash="dash", 
                         line_color="red", opacity=0.5, 
                         annotation_text=f"Limite Superior ({outlier_threshold}%)")
            fig.add_hline(y=-outlier_threshold, line_dash="dash", 
                         line_color="red", opacity=0.5, 
                         annotation_text=f"Limite Inferior (-{outlier_threshold}%)")
            
            fig.update_layout(
                title=f"Variações Mensais - {section_name}",
                xaxis_title="Transições Mensais",
                yaxis_title="Variação (%)",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Summary insights
    st.markdown("---")
    st.subheader("💡 Insights da Análise")
    
    if variance_data:
        most_volatile = variance_data[0]
        least_volatile = min(variance_data, key=lambda x: x['volatility_score'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🔥 Categoria Mais Volátil")
            st.write(f"**{most_volatile['section_name']}** com score de volatilidade {most_volatile['volatility_score']:.2f}")
            st.write(f"• {len(most_volatile['outliers'])} outliers detectados")
            st.write(f"• Variação média: {most_volatile['mean_variance']:.1f}%")
        
        with col2:
            st.markdown("##### ✅ Categoria Mais Estável")
            st.write(f"**{least_volatile['section_name']}** com score de volatilidade {least_volatile['volatility_score']:.2f}")
            st.write(f"• {len(least_volatile['outliers'])} outliers detectados")
            st.write(f"• Variação média: {least_volatile['mean_variance']:.1f}%")


def _render_tree_selector(expense_data: Dict, selected_years: List[int]):
    """
    Render an intuitive tree-based selector for hierarchy items
    """
    # Initialize session state for tree expansion
    if 'tree_expanded' not in st.session_state:
        st.session_state.tree_expanded = {}
    
    if 'tree_selected' not in st.session_state:
        st.session_state.tree_selected = {
            'sections': [],
            'subcategories': [],
            'items': []
        }
    
    # Build unified hierarchy from all years
    unified_hierarchy = {}
    for year in selected_years:
        if year in expense_data:
            for section in expense_data[year]:
                section_name = section['name']
                section_value = section.get('value', 0)
                
                if section_name not in unified_hierarchy:
                    unified_hierarchy[section_name] = {
                        'value': section_value,
                        'subcategories': {}
                    }
                else:
                    # Update with latest year's value
                    unified_hierarchy[section_name]['value'] = max(
                        unified_hierarchy[section_name]['value'], section_value
                    )
                
                for subcat in section.get('subcategories', []):
                    subcat_name = subcat['name']
                    subcat_value = subcat.get('value', 0)
                    
                    if subcat_name not in unified_hierarchy[section_name]['subcategories']:
                        unified_hierarchy[section_name]['subcategories'][subcat_name] = {
                            'value': subcat_value,
                            'items': {}
                        }
                    else:
                        unified_hierarchy[section_name]['subcategories'][subcat_name]['value'] = max(
                            unified_hierarchy[section_name]['subcategories'][subcat_name]['value'], 
                            subcat_value
                        )
                    
                    for item in subcat.get('items', []):
                        item_name = item['name']
                        item_value = item.get('value', 0)
                        unified_hierarchy[section_name]['subcategories'][subcat_name]['items'][item_name] = max(
                            unified_hierarchy[section_name]['subcategories'][subcat_name]['items'].get(item_name, 0),
                            item_value
                        )
    
    # Render tree interface
    selected_entities = {'type': None, 'section': None, 'subcat': None, 'items': []}
    
    # Main selection controls
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Limpar Tudo", key="clear_all_selections"):
            st.session_state.tree_selected = {
                'sections': [],
                'subcategories': [],
                'items': []
            }
            st.rerun()
    
    # Render sections
    for section_name, section_data in unified_hierarchy.items():
        section_key = f"section_{section_name}"
        
        # Section header with value and expand button
        col_expand, col_check, col_label = st.columns([0.1, 0.1, 0.8])
        
        with col_expand:
            expanded = st.session_state.tree_expanded.get(section_key, False)
            if st.button("▼" if expanded else "▶", key=f"expand_{section_key}"):
                st.session_state.tree_expanded[section_key] = not expanded
                st.rerun()
        
        with col_check:
            section_selected = st.checkbox(
                "",
                value=section_name in st.session_state.tree_selected['sections'],
                key=f"check_{section_key}"
            )
            if section_selected and section_name not in st.session_state.tree_selected['sections']:
                st.session_state.tree_selected['sections'].append(section_name)
            elif not section_selected and section_name in st.session_state.tree_selected['sections']:
                st.session_state.tree_selected['sections'].remove(section_name)
        
        with col_label:
            st.markdown(f"**🏢 {section_name}** - {format_currency(section_data['value'])}")
        
        # Render subcategories if expanded
        if st.session_state.tree_expanded.get(section_key, False):
            for subcat_name, subcat_data in section_data['subcategories'].items():
                subcat_key = f"subcat_{section_name}_{subcat_name}"
                
                # Subcategory with indentation
                col_indent, col_expand2, col_check2, col_label2 = st.columns([0.05, 0.1, 0.1, 0.75])
                
                with col_expand2:
                    subcat_expanded = st.session_state.tree_expanded.get(subcat_key, False)
                    if st.button("▼" if subcat_expanded else "▶", key=f"expand_{subcat_key}"):
                        st.session_state.tree_expanded[subcat_key] = not subcat_expanded
                        st.rerun()
                
                with col_check2:
                    subcat_selected = st.checkbox(
                        "",
                        value=f"{section_name}:{subcat_name}" in st.session_state.tree_selected['subcategories'],
                        key=f"check_{subcat_key}"
                    )
                    subcat_id = f"{section_name}:{subcat_name}"
                    if subcat_selected and subcat_id not in st.session_state.tree_selected['subcategories']:
                        st.session_state.tree_selected['subcategories'].append(subcat_id)
                    elif not subcat_selected and subcat_id in st.session_state.tree_selected['subcategories']:
                        st.session_state.tree_selected['subcategories'].remove(subcat_id)
                
                with col_label2:
                    st.markdown(f"  📁 {subcat_name} - {format_currency(subcat_data['value'])}")
                
                # Render items if subcategory is expanded
                if st.session_state.tree_expanded.get(subcat_key, False):
                    for item_name, item_value in subcat_data['items'].items():
                        item_key = f"item_{section_name}_{subcat_name}_{item_name}"
                        
                        # Item with more indentation
                        col_indent2, col_check3, col_label3 = st.columns([0.2, 0.1, 0.7])
                        
                        with col_check3:
                            item_selected = st.checkbox(
                                "",
                                value=f"{section_name}:{subcat_name}:{item_name}" in st.session_state.tree_selected['items'],
                                key=f"check_{item_key}"
                            )
                            item_id = f"{section_name}:{subcat_name}:{item_name}"
                            if item_selected and item_id not in st.session_state.tree_selected['items']:
                                st.session_state.tree_selected['items'].append(item_id)
                            elif not item_selected and item_id in st.session_state.tree_selected['items']:
                                st.session_state.tree_selected['items'].remove(item_id)
                        
                        with col_label3:
                            st.markdown(f"    📌 {item_name} - {format_currency(item_value)}")
    
    # Determine what to return based on selections
    if st.session_state.tree_selected['items']:
        selected_entities['type'] = 'items'
        selected_entities['items'] = st.session_state.tree_selected['items']
    elif st.session_state.tree_selected['subcategories']:
        selected_entities['type'] = 'subcategories'
        selected_entities['items'] = st.session_state.tree_selected['subcategories']
    elif st.session_state.tree_selected['sections']:
        selected_entities['type'] = 'sections'
        selected_entities['items'] = st.session_state.tree_selected['sections']
    
    return selected_entities


def _render_tree_subcategory_multi_year_lines(expense_data: Dict, selected_years: List[int], subcategory_ids: List[str], months: List[str], chart_type: str):
    """Render multi-year comparison for subcategories selected from tree"""
    
    for subcat_id in subcategory_ids:
        # Parse the ID: "section_name:subcat_name"
        section_name, subcat_name = subcat_id.split(':')
        
        # Collect data for this subcategory across years
        subcat_year_data = {}
        
        for year in selected_years:
            if year in expense_data:
                for section in expense_data[year]:
                    if section['name'] == section_name:
                        for subcat in section.get('subcategories', []):
                            if subcat['name'] == subcat_name:
                                monthly_data = subcat.get('monthly', {})
                                if monthly_data:
                                    subcat_year_data[year] = monthly_data
                                break
                        break
        
        if not subcat_year_data:
            continue
        
        with st.expander(f"📁 **{subcat_name}** ({section_name}) - Comparação Multi-Anual", expanded=True):
            _render_multi_year_line_chart(subcat_year_data, months, subcat_name, selected_years, 
                                         show_percentage="com %" in chart_type)


def _render_tree_item_multi_year_lines(expense_data: Dict, selected_years: List[int], item_ids: List[str], months: List[str], chart_type: str):
    """Render multi-year comparison for individual items selected from tree"""
    
    for item_id in item_ids:
        # Parse the ID: "section_name:subcat_name:item_name"
        section_name, subcat_name, item_name = item_id.split(':')
        
        # Collect data for this item across years
        item_year_data = {}
        
        for year in selected_years:
            if year in expense_data:
                for section in expense_data[year]:
                    if section['name'] == section_name:
                        for subcat in section.get('subcategories', []):
                            if subcat['name'] == subcat_name:
                                for item in subcat.get('items', []):
                                    if item['name'] == item_name:
                                        monthly_data = item.get('monthly', {})
                                        if monthly_data:
                                            item_year_data[year] = monthly_data
                                        break
                                break
                        break
        
        if not item_year_data:
            continue
        
        with st.expander(f"📌 **{item_name}** ({section_name} > {subcat_name}) - Comparação Multi-Anual", expanded=True):
            _render_multi_year_line_chart(item_year_data, months, item_name, selected_years,
                                         show_percentage="com %" in chart_type)

def _render_interactive_drilldown(period_data: Dict, selected_year: int, time_period: str):
    """
    Render interactive drill-down visualization for hierarchical cost exploration
    Users can click through: Main Categories -> Subcategories -> Individual Items
    """
    st.header("🔍 Exploração Interativa dos Custos")
    st.markdown("📋 Navegue pelos níveis hierárquicos clicando nas categorias para explorar em detalhes.")
    
    # Initialize session state for navigation
    if 'drilldown_path' not in st.session_state:
        st.session_state.drilldown_path = []
    
    if 'current_level' not in st.session_state:
        st.session_state.current_level = 'main'  # main, subcategory, items
    
    sections = period_data.get('sections', [])
    if not sections:
        st.warning("Nenhum dado disponível para exploração.")
        return
    
    # Breadcrumb navigation with back button
    breadcrumb_col1, breadcrumb_col2, breadcrumb_col3 = st.columns([3, 1, 1])
    with breadcrumb_col1:
        _render_breadcrumbs()
    with breadcrumb_col2:
        # Back button - only show if not at main level
        if st.session_state.current_level != 'main' and len(st.session_state.drilldown_path) > 0:
            if st.button("⬅️ Voltar", key="back_drilldown"):
                # Go back one level
                st.session_state.drilldown_path.pop()
                if len(st.session_state.drilldown_path) == 0:
                    st.session_state.current_level = 'main'
                elif len(st.session_state.drilldown_path) == 1:
                    st.session_state.current_level = 'subcategory'
                st.rerun()
    with breadcrumb_col3:
        if st.button("🏠 Voltar ao Início", key="reset_drilldown"):
            st.session_state.drilldown_path = []
            st.session_state.current_level = 'main'
            st.rerun()
    
    # Render current level
    if st.session_state.current_level == 'main':
        _render_main_categories(sections, time_period)
    elif st.session_state.current_level == 'subcategory':
        _render_subcategories(sections, time_period)
    elif st.session_state.current_level == 'items':
        _render_individual_items(sections, time_period)


def _render_breadcrumbs():
    """Render breadcrumb navigation with current path"""
    if not st.session_state.drilldown_path:
        st.markdown("📍 **Categorias Principais**")
        return
    
    # Build breadcrumb text
    breadcrumb = "📍 **Início**"
    for i, step in enumerate(st.session_state.drilldown_path):
        breadcrumb += f" › **{step}**"
    st.markdown(breadcrumb)


def _render_main_categories(sections: List[Dict], time_period: str):
    """Render main expense categories for drilling down"""
    st.subheader("📂 Selecione uma Categoria Principal")
    
    # Filter to expense sections only (exclude revenue)
    expense_sections = _filter_expense_sections(sections, include_revenue=False)
    
    if not expense_sections:
        st.info("Nenhuma categoria de despesa encontrada.")
        return
    
    # Create cards for each main category
    cols = st.columns(min(3, len(expense_sections)))
    
    for idx, section in enumerate(expense_sections):
        col_idx = idx % 3
        with cols[col_idx]:
            section_name = section.get('name', 'Categoria')
            section_value = section.get('value', 0)
            subcats_count = len(section.get('subcategories', []))
            
            # Create an interactive card
            with st.container():
                st.markdown(f"""
                <div style='border: 2px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; background: #f9f9f9;'>
                    <h3 style='color: #2c3e50; margin: 0;'>{section_name}</h3>
                    <p style='font-size: 24px; font-weight: bold; color: #e74c3c; margin: 10px 0;'>
                        R$ {section_value:,.2f}
                    </p>
                    <p style='color: #7f8c8d; margin: 0;'>
                        🏷️ {subcats_count} subcategorias
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🔍 Explorar {section_name}", key=f"explore_{idx}"):
                    st.session_state.drilldown_path = [section_name]
                    st.session_state.current_level = 'subcategory'
                    st.rerun()


def _render_subcategories(sections: List[Dict], time_period: str):
    """Render subcategories for the selected main category"""
    category_name = st.session_state.drilldown_path[0]
    
    # Find the selected category
    selected_section = None
    for section in sections:
        if section.get('name') == category_name:
            selected_section = section
            break
    
    if not selected_section:
        st.error(f"Categoria '{category_name}' não encontrada.")
        return
    
    st.subheader(f"📁 Subcategorias de {category_name}")
    
    subcategories = selected_section.get('subcategories', [])
    if not subcategories:
        st.info("Nenhuma subcategoria encontrada.")
        return
    
    # Find revenue (Faturamento) for percentage calculation
    revenue_value = 0
    for section in sections:
        section_name = section.get('name', '').upper()
        if section_name == 'FATURAMENTO':
            revenue_value = section.get('value', 0)
            break
    
    # Add toggle for showing as percentage of revenue
    col1, col2 = st.columns([1, 3])
    with col1:
        show_percentage = st.checkbox(
            "📊 Mostrar como % do Faturamento", 
            value=False,
            help="Mostra cada subcategoria como percentual do faturamento total"
        )
    
    # Create a chart showing all subcategories
    subcat_names = []
    subcat_values = []
    subcat_percentages = []
    
    for subcat in subcategories:
        subcat_names.append(subcat.get('name', 'Subcategoria'))
        value = subcat.get('value', 0)
        subcat_values.append(value)
        
        # Calculate percentage of revenue
        if revenue_value > 0:
            percentage = (value / revenue_value) * 100
        else:
            percentage = 0
        subcat_percentages.append(percentage)
    
    # Create bar chart
    fig = go.Figure()
    
    if show_percentage and revenue_value > 0:
        # Show as percentage
        fig.add_trace(go.Bar(
            x=subcat_names,
            y=subcat_percentages,
            name=f"{category_name} (% do Faturamento)",
            marker_color='#e74c3c',
            text=[f'{pct:.1f}%' for pct in subcat_percentages],
            textposition='outside',
            customdata=[[val, pct] for val, pct in zip(subcat_values, subcat_percentages)],
            hovertemplate='<b>%{x}</b><br>' +
                         'Valor: R$ %{customdata[0]:,.2f}<br>' +
                         '% do Faturamento: %{customdata[1]:.2f}%<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"Subcategorias de {category_name} (% do Faturamento: R$ {revenue_value:,.0f})",
            xaxis_title="Subcategorias",
            yaxis_title="% do Faturamento",
            height=400,
            showlegend=False
        )
    else:
        # Show as absolute values with percentage in hover
        fig.add_trace(go.Bar(
            x=subcat_names,
            y=subcat_values,
            name=category_name,
            marker_color='#3498db',
            text=[f'R$ {val:,.0f}' for val in subcat_values],
            textposition='outside',
            customdata=subcat_percentages if revenue_value > 0 else None,
            hovertemplate='<b>%{x}</b><br>' +
                         'Valor: R$ %{y:,.2f}<br>' +
                         (f'% do Faturamento: %{{customdata:.2f}}%<br>' if revenue_value > 0 else '') +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"Subcategorias de {category_name}",
            xaxis_title="Subcategorias",
            yaxis_title="Valor (R$)",
            height=400,
            showlegend=False
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Create clickable cards for each subcategory
    st.subheader("🔍 Selecione uma Subcategoria para Ver Detalhes")
    
    cols = st.columns(min(3, len(subcategories)))
    for idx, subcat in enumerate(subcategories):
        col_idx = idx % 3
        with cols[col_idx]:
            subcat_name = subcat.get('name', 'Subcategoria')
            subcat_value = subcat.get('value', 0)
            items_count = len(subcat.get('items', []))
            
            # Calculate percentage for this subcategory
            if revenue_value > 0:
                subcat_percentage = (subcat_value / revenue_value) * 100
            else:
                subcat_percentage = 0
            
            with st.container():
                percentage_text = f"<p style='color: #e74c3c; font-size: 16px; margin: 5px 0;'>📊 {subcat_percentage:.1f}% do Faturamento</p>" if revenue_value > 0 else ""
                
                st.markdown(f"""
                <div style='border: 2px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; background: #f0f8ff;'>
                    <h4 style='color: #2c3e50; margin: 0;'>{subcat_name}</h4>
                    <p style='font-size: 20px; font-weight: bold; color: #3498db; margin: 10px 0;'>
                        R$ {subcat_value:,.2f}
                    </p>
                    {percentage_text}
                    <p style='color: #7f8c8d; margin: 0;'>
                        📋 {items_count} itens
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"📋 Ver Itens de {subcat_name}", key=f"items_{idx}"):
                    st.session_state.drilldown_path = [category_name, subcat_name]
                    st.session_state.current_level = 'items'
                    st.rerun()


def _render_individual_items(sections: List[Dict], time_period: str):
    """Render individual items for the selected subcategory"""
    category_name = st.session_state.drilldown_path[0]
    subcategory_name = st.session_state.drilldown_path[1]
    
    # Find the selected subcategory
    selected_subcategory = None
    for section in sections:
        if section.get('name') == category_name:
            for subcat in section.get('subcategories', []):
                if subcat.get('name') == subcategory_name:
                    selected_subcategory = subcat
                    break
            break
    
    if not selected_subcategory:
        st.error(f"Subcategoria '{subcategory_name}' não encontrada.")
        return
    
    st.subheader(f"📋 Itens Individuais: {category_name} › {subcategory_name}")
    
    items = selected_subcategory.get('items', [])
    if not items:
        st.info("Nenhum item individual encontrado.")
        return
    
    # Find revenue (Faturamento) for percentage calculation
    revenue_value = 0
    for section in sections:
        section_name = section.get('name', '').upper()
        if section_name == 'FATURAMENTO':
            revenue_value = section.get('value', 0)
            break
    
    # Add toggle for showing as percentage of revenue
    col1, col2 = st.columns([1, 3])
    with col1:
        show_percentage = st.checkbox(
            "📊 Mostrar como % do Faturamento", 
            value=False,
            key="items_percentage_toggle",
            help="Mostra cada item como percentual do faturamento total"
        )
    
    # Create detailed table and chart for individual items
    items_data = []
    for item in items:
        item_name = item.get('name', 'Item')
        item_value = item.get('value', 0)
        monthly_data = item.get('monthly', {})
        
        # Calculate percentage of revenue
        if revenue_value > 0:
            item_percentage = (item_value / revenue_value) * 100
        else:
            item_percentage = 0
        
        items_data.append({
            'Item': item_name,
            'Valor Anual': item_value,
            'Percentual': item_percentage,
            'Dados Mensais': len(monthly_data) > 0
        })
    
    # Sort by value
    items_data.sort(key=lambda x: x['Valor Anual'], reverse=True)
    
    # Show top items in a chart
    if len(items_data) > 1:
        top_items = items_data[:min(10, len(items_data))]  # Top 10
        
        fig = go.Figure()
        
        if show_percentage and revenue_value > 0:
            # Show as percentage
            fig.add_trace(go.Bar(
                x=[item['Item'] for item in top_items],
                y=[item['Percentual'] for item in top_items],
                name=f"{subcategory_name} (% do Faturamento)",
                marker_color='#e74c3c',
                text=[f'{item["Percentual"]:.2f}%' for item in top_items],
                textposition='outside',
                customdata=[[item['Valor Anual'], item['Percentual']] for item in top_items],
                hovertemplate='<b>%{x}</b><br>' +
                             'Valor: R$ %{customdata[0]:,.2f}<br>' +
                             '% do Faturamento: %{customdata[1]:.3f}%<br>' +
                             '<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"Principais Itens: {subcategory_name} (% do Faturamento: R$ {revenue_value:,.0f})",
                xaxis_title="Itens",
                yaxis_title="% do Faturamento",
                height=400,
                showlegend=False,
                xaxis_tickangle=-45
            )
        else:
            # Show as absolute values with percentage in hover
            fig.add_trace(go.Bar(
                x=[item['Item'] for item in top_items],
                y=[item['Valor Anual'] for item in top_items],
                name=subcategory_name,
                marker_color='#e74c3c',
                text=[f'R$ {item["Valor Anual"]:,.0f}' for item in top_items],
                textposition='outside',
                customdata=[item['Percentual'] for item in top_items] if revenue_value > 0 else None,
                hovertemplate='<b>%{x}</b><br>' +
                             'Valor: R$ %{y:,.2f}<br>' +
                             (f'% do Faturamento: %{{customdata:.3f}}%<br>' if revenue_value > 0 else '') +
                             '<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"Principais Itens: {subcategory_name}",
                xaxis_title="Itens",
                yaxis_title="Valor (R$)",
                height=400,
                showlegend=False,
                xaxis_tickangle=-45
            )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Show detailed table
    st.subheader("📊 Detalhamento dos Itens")
    
    # Convert to DataFrame for display
    df_items = pd.DataFrame(items_data)
    df_items['Valor Anual'] = df_items['Valor Anual'].apply(lambda x: f"R$ {x:,.2f}")
    
    # Add percentage column if revenue is available
    if revenue_value > 0:
        df_items['% do Faturamento'] = df_items['Percentual'].apply(lambda x: f"{x:.2f}%")
    
    df_items['Dados Mensais'] = df_items['Dados Mensais'].apply(lambda x: "✅ Sim" if x else "❌ Não")
    
    # Remove the raw Percentual column and reorder
    display_columns = ['Item', 'Valor Anual']
    if revenue_value > 0:
        display_columns.append('% do Faturamento')
    display_columns.append('Dados Mensais')
    
    st.dataframe(df_items[display_columns], use_container_width=True, hide_index=True)
    
    # Optional: Show monthly breakdown for items that have monthly data
    monthly_items = [item for item in items if item.get('monthly')]
    if monthly_items and time_period == "📊 Mensal":
        st.subheader("📈 Evolução Mensal dos Principais Itens")
        
        # Create line chart for monthly data
        fig = go.Figure()
        
        colors = ['#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#1abc9c']
        
        for idx, item in enumerate(monthly_items[:5]):  # Top 5 items
            monthly_data = item.get('monthly', {})
            if monthly_data:
                months = list(monthly_data.keys())
                values = list(monthly_data.values())
                
                fig.add_trace(go.Scatter(
                    x=months,
                    y=values,
                    mode='lines+markers',
                    name=item.get('name', f'Item {idx+1}'),
                    line=dict(color=colors[idx % len(colors)], width=3),
                    marker=dict(size=8)
                ))
        
        fig.update_layout(
            title=f"Evolução Mensal - {subcategory_name}",
            xaxis_title="Mês",
            yaxis_title="Valor (R$)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
