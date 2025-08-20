"""
Native Hierarchy Renderer for Micro Analysis V2
Displays Excel data in its original 3-level structure
"""

import streamlit as st
import pandas as pd
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
        # Visualization type selector
        visualization_type = st.selectbox(
            "🔧 Visualização",
            [
                "📂 Estrutura Hierárquica",
                "📊 Comparação Entre Anos",
                "🌊 Análise Waterfall",
                "📈 Tendências Temporais", 
                "🎯 Análise de Contribuição",
                "🔥 Mapas de Calor",
                "🌅 Gráfico Sunburst",
                "📋 Tabela Detalhada",
                "💡 Insights Automáticos"
            ],
            index=0,
            key="viz_type_selector",
            help="💡 Para visão mensal dentro de um ano: use 'Estrutura Hierárquica' + 'Mensal'. Para comparar meses entre anos: use 'Comparação Entre Anos'"
        )
    
    with col1:
        # Year selector - support both single and multi-year selection
        available_years = sorted(financial_data.keys())
        
        # Check if this is a comparison visualization
        if visualization_type == "📊 Comparação Entre Anos" and len(available_years) >= 2:
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
    
    elif visualization_type == "📈 Tendências Temporais":
        if time_period != "📅 Anual":
            # Show intra-year trends using period data
            _render_period_trends(period_data, time_period, selected_year)
        elif full_financial_data and len(full_financial_data) >= 2:
            from .time_series_analysis import render_advanced_time_series_analysis
            available_years = sorted(full_financial_data.keys())
            render_advanced_time_series_analysis(full_financial_data, available_years)
        else:
            st.warning("⚠️ Análise temporal requer dados de múltiplos anos ou períodos intra-ano")
            st.info("Mostrando visualizações alternativas...")
            
            # Show alternative visualizations
            col1, col2 = st.columns(2)
            with col1:
                _render_sunburst(period_data)
            with col2:
                _render_treemap(period_data)
    
    elif visualization_type == "💡 Insights Automáticos":
        if time_period != "📅 Anual":
            # Show period-specific insights
            _render_period_insights(period_data, time_period, selected_year)
        elif full_financial_data and len(full_financial_data) >= 2:
            from .insights_engine import render_ai_insights_dashboard
            available_years = sorted(full_financial_data.keys())
            render_ai_insights_dashboard(full_financial_data, available_years)
        else:
            st.warning("⚠️ Insights automáticos requerem dados de múltiplos anos ou análise de períodos")
            st.info("Mostrando análise básica para o ano atual...")
            
            # Show basic single-year insights
            _render_basic_year_insights(period_data, selected_year)
    
    elif visualization_type == "🎯 Análise de Contribuição":
        _render_contribution_analysis(period_data, time_period, selected_year)
    
    elif visualization_type == "🔥 Mapas de Calor":
        if full_financial_data and len(full_financial_data) >= 2:
            _render_heatmap_analysis(full_financial_data, time_period)
        else:
            st.warning("⚠️ Mapas de calor requerem dados de múltiplos anos para comparação")
    
    elif visualization_type == "🌅 Gráfico Sunburst":
        _render_sunburst(period_data)
    
    elif visualization_type == "📋 Tabela Detalhada":
        _render_detailed_table(period_data)
    
    # Calculations section removed for cleaner interface


def _filter_expense_sections(sections: List[Dict]) -> List[Dict]:
    """
    Filter out revenue categories to focus on costs/expenses only
    """
    revenue_categories = ['FATURAMENTO', 'RECEITA', 'RECEITAS', 'Outras receitas/creditos']
    return [
        section for section in sections 
        if section.get('name', '').upper() not in [cat.upper() for cat in revenue_categories]
    ]


def _render_hierarchy_tree(sections: List[Dict], time_period: str, expand_all: bool):
    """
    Render the hierarchical structure as an expandable tree with period breakdown
    """
    st.markdown("### 📂 Estrutura Hierárquica")
    
    # Filter out revenue categories to focus on costs/expenses
    expense_sections = _filter_expense_sections(sections)
    
    st.info(f"📊 Mostrando {len(expense_sections)} seções de custos")
    
    for section in expense_sections:
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
        
        # Level 1: Main Section
        with st.expander(
            f"**{section['name']}** - {format_currency(section.get('value', 0))}",
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
            'level': 'Seção'
        })
        
        # Add subcategories
        for subcat in section.get('subcategories', []):
            subcat_value = subcat.get('value', 0)
            subcat_contribution = (subcat_value / total_expenses) * 100 if total_expenses > 0 else 0
            
            if subcat_contribution > 1:  # Only show subcategories with >1% contribution
                contribution_data.append({
                    'category': f"  └─ {subcat['name']}",
                    'value': subcat_value,
                    'contribution': subcat_contribution,
                    'level': 'Subcategoria'
                })
    
    # Sort by contribution descending
    contribution_data.sort(key=lambda x: x['contribution'], reverse=True)
    
    # Show top contributors
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Ranking de Contribuição")
        
        # Create waterfall-style chart
        categories = [item['category'] for item in contribution_data[:10]]  # Top 10
        contributions = [item['contribution'] for item in contribution_data[:10]]
        values = [item['value'] for item in contribution_data[:10]]
        
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
        
        # Top 3 contributors
        top_3 = contribution_data[:3]
        top_3_total = sum(item['contribution'] for item in top_3)
        
        st.metric("Top 3 Concentração", f"{top_3_total:.1f}%")
        
        for i, item in enumerate(top_3, 1):
            st.markdown(f"**{i}º** {item['category']}: {item['contribution']:.1f}%")
        
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
                
                for year in selected_years:
                    if year in section_data:
                        subcats = section_data[year].get('subcategories', [])
                        subcat = next((s for s in subcats if s['name'] == subcat_name), None)
                        if subcat:
                            monthly_data = subcat.get('monthly', {})
                            values = [monthly_data.get(month, 0) for month in months]
                            
                            if any(v > 0 for v in values):
                                # Calculate year-over-year changes if we have multiple years
                                hover_text = []
                                for i, month in enumerate(months):
                                    value = values[i]
                                    text = f"<b>{month} {year}</b><br>"
                                    text += f"<b>Valor:</b> R$ {value:,.2f}<br>"
                                    
                                    # Add percentage of total
                                    total = sum(values)
                                    if total > 0:
                                        pct = (value / total) * 100
                                        text += f"<b>% do Total:</b> {pct:.1f}%<br>"
                                    
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
                # Show annual totals
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
                
                # Add period progression chart for non-monthly time periods
                if time_period in ["📈 Trimestral", "📆 Semestral", "📅 Customizado"]:
                    st.markdown(f"**Evolução {time_period.replace('📈 ', '').replace('📆 ', '').replace('📅 ', '')} - {subcat_name}**")
                    _render_subcategory_period_comparison(section_data, selected_years, subcat_name, year_colors, time_period)
            
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
        # Show annual comparison table for items
        item_comparison = []
        for item_name in sorted(all_items):
            row = {'Item': item_name}
            
            for year in selected_years:
                if year in subcat_data:
                    items = subcat_data[year].get('items', [])
                    item = next((i for i in items if i['name'] == item_name), None)
                    value = item.get('value', 0) if item else 0
                    row[str(year)] = value
                else:
                    row[str(year)] = 0
            
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
    
    # Handle different drill levels for single year
    if drill_level == "📁 Subcategorias" and selected_entities:
        # Render subcategory level for single year
        for section in sections:
            if section['name'] == selected_section:
                for subcat in section.get('subcategories', []):
                    if subcat['name'] in selected_entities:
                        _render_single_year_entity(subcat, months, analysis_year, chart_type, f"📁 {subcat['name']}")
                break
        return
    
    elif drill_level == "📌 Itens Individuais" and selected_entities:
        # Render item level for single year
        for section in sections:
            if section['name'] == selected_section:
                for subcat in section.get('subcategories', []):
                    if subcat['name'] == selected_subcat:
                        for item in subcat.get('items', []):
                            if item['name'] in selected_entities:
                                _render_single_year_entity(item, months, analysis_year, chart_type, f"📌 {item['name']}")
                        break
                break
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
                    showlegend=False
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