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
    
    with col1:
        # Year selector
        available_years = sorted(financial_data.keys())
        selected_year = st.selectbox(
            "📅 Ano",
            available_years,
            index=len(available_years) - 1 if available_years else 0
        )
    
    with col2:
        # Time period selector (like macro dashboard)
        time_period = st.selectbox(
            "📊 Período",
            ["📅 Anual", "📊 Mensal", "📈 Trimestral", "📆 Semestral"],
            index=0
        )
    
    with col3:
        # Visualization type selector
        visualization_type = st.selectbox(
            "🔧 Visualização",
            [
                "📂 Estrutura Hierárquica",
                "🌊 Análise Waterfall",
                "📈 Tendências Temporais",
                "💡 Insights Automáticos"
            ],
            index=0
        )
    
    with col4:
        # Show details toggle
        show_details = st.checkbox("🔍 Detalhes", value=False)
    
    if selected_year not in financial_data:
        st.error(f"Dados não encontrados para {selected_year}")
        return
    
    year_data = financial_data[selected_year]
    
    st.markdown("---")
    
    # Get period-aware data
    period_data = _get_period_data(year_data, time_period)
    
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
    
    elif visualization_type == "🌊 Análise Waterfall":
        if time_period == "📅 Anual":
            from .advanced_visualizations import render_waterfall_drilldown
            render_waterfall_drilldown({selected_year: period_data}, selected_year)
        else:
            st.info(f"🚧 Waterfall em desenvolvimento para visualização {time_period}")
            # Fallback: show composition for now
            _render_composition_chart(period_data)
        
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
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors),
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent} do total<extra></extra>'
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
    
    fig = px.treemap(
        df,
        path=['Section', 'Subcategory', 'Item'],
        values='Value',
        title='Mapa de Árvore - Hierarquia de Despesas'
    )
    
    fig.update_traces(
        texttemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percentParent}',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percentParent} do parent<extra></extra>'
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
    
    # Create pie chart
    fig = px.pie(
        df,
        values='value',
        names='name',
        title='Composição das Despesas'
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>%{percent}<extra></extra>'
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
    
    # Define period groupings
    if time_period == "📈 Trimestral":
        periods = {
            'Q1': ['JAN', 'FEV', 'MAR'],
            'Q2': ['ABR', 'MAI', 'JUN'], 
            'Q3': ['JUL', 'AGO', 'SET'],
            'Q4': ['OUT', 'NOV', 'DEZ']
        }
    elif time_period == "📆 Semestral":
        periods = {
            'S1': ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN'],
            'S2': ['JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        }
    elif time_period == "📊 Mensal":
        periods = {month: [month] for month in months}
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
    Render basic insights for single year analysis
    """
    if 'sections' not in year_data:
        st.info("Dados não disponíveis para análise")
        return
    
    st.markdown("#### 💡 Insights Básicos do Ano")
    
    # Filter out revenue categories to focus on costs/expenses
    sections = _filter_expense_sections(year_data['sections'])
    total_expenses = sum(s.get('value', 0) for s in sections)
    
    if total_expenses == 0:
        st.info("Nenhuma despesa registrada para análise")
        return
    
    # Calculate key metrics
    sorted_sections = sorted(sections, key=lambda x: x.get('value', 0), reverse=True)
    
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