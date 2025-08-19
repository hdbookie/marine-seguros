"""
Enhanced Dashboard Tab - Unified Macro + Micro Analysis
Combines macro-level overview with drill-down capabilities to micro analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Import existing dashboard functionality
from .dashboard_legacy_tab import render_dashboard_tab
from .micro_analysis_v2.native_hierarchy_renderer import render_native_hierarchy_tab

# Import utilities
from utils.legacy_helpers import format_currency, calculate_percentage_change
from components.charts import (
    create_receita_chart,
    create_custos_fixos_chart,
    create_custos_variaveis_chart,
    create_margem_contribuicao_chart,
    create_despesas_operacionais_chart,
    create_resultado_chart
)
from components.unified_comparison import UnifiedComparisonEngine, render_unified_comparison_section
from components.navigation_helper import get_navigation_manager, render_enhanced_navigation


def render_enhanced_dashboard_tab(db, use_unified_extractor=True):
    """
    Render enhanced dashboard that combines macro overview with micro drill-down
    """
    st.header("📊 Dashboard Integrado - Macro + Micro")
    
    # Check if we have both macro and micro data
    has_macro_data = (
        hasattr(st.session_state, 'processed_data') and 
        st.session_state.processed_data is not None
    )
    
    has_micro_data = (
        hasattr(st.session_state, 'unified_data') and 
        st.session_state.unified_data is not None
    )
    
    # Create navigation options
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        view_mode = st.selectbox(
            "🔍 Modo de Visualização",
            [
                "📊 Visão Macro (Resumo Executivo)",
                "🔬 Visão Micro (Análise Detalhada)", 
                "🔄 Visão Integrada (Macro + Micro)"
            ],
            key="enhanced_view_mode"
        )
    
    with col2:
        if view_mode == "🔄 Visão Integrada (Macro + Micro)":
            drill_down_section = st.selectbox(
                "🎯 Seção para Detalhamento",
                [
                    "Todos", 
                    "CUSTOS FIXOS", 
                    "CUSTOS VARIÁVEIS", 
                    "CUSTOS NÃO OPERACIONAIS",
                    "RECEITA"
                ],
                key="drill_down_section"
            )
        else:
            drill_down_section = "Todos"
    
    with col3:
        show_comparison_mode = st.checkbox(
            "📈 Modo Comparação",
            value=True,
            help="Exibir comparações lado a lado entre anos"
        )
    
    # Enhanced navigation with context preservation
    nav_manager = get_navigation_manager()
    nav_manager.update_context(
        current_view=view_mode,
        section=drill_down_section,
        comparison_mode=show_comparison_mode
    )
    
    # Render enhanced navigation
    render_enhanced_navigation()
    
    st.markdown("---")
    
    # Render content based on view mode
    if view_mode == "📊 Visão Macro (Resumo Executivo)":
        _render_macro_view(db, use_unified_extractor, show_comparison_mode)
        
    elif view_mode == "🔬 Visão Micro (Análise Detalhada)":
        _render_micro_view()
        
    elif view_mode == "🔄 Visão Integrada (Macro + Micro)":
        _render_integrated_view(db, use_unified_extractor, drill_down_section, show_comparison_mode)


def _render_breadcrumb_navigation(view_mode: str, drill_down_section: str):
    """Render breadcrumb navigation"""
    breadcrumbs = ["🏠 Dashboard"]
    
    if view_mode == "📊 Visão Macro (Resumo Executivo)":
        breadcrumbs.append("📊 Macro")
    elif view_mode == "🔬 Visão Micro (Análise Detalhada)":
        breadcrumbs.append("🔬 Micro")
    elif view_mode == "🔄 Visão Integrada (Macro + Micro)":
        breadcrumbs.extend(["🔄 Integrada", f"🎯 {drill_down_section}"])
    
    st.markdown(
        f"**Navegação:** {' → '.join(breadcrumbs)}",
        help="Use os controles acima para navegar entre diferentes níveis de análise"
    )


def _render_macro_view(db, use_unified_extractor: bool, show_comparison_mode: bool):
    """Render the macro-level view with enhanced comparison charts"""
    st.subheader("📊 Visão Macro - Resumo Executivo")
    
    # Add enhanced macro overview with click-to-drill functionality
    if show_comparison_mode:
        _render_enhanced_macro_comparison()
    
    # Render original dashboard content with unique key prefix
    render_dashboard_tab(db, use_unified_extractor, key_prefix="enhanced_")
    
    # Add quick navigation using navigation helper
    st.markdown("---")
    st.markdown("### 🔗 Drill-Down por Seção")
    
    nav_manager = get_navigation_manager()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nav_manager.create_drill_down_button("CUSTOS FIXOS", "🔬 Análise de Custos Fixos", key_suffix="_macro")
    
    with col2:
        nav_manager.create_drill_down_button("CUSTOS VARIÁVEIS", "🔬 Análise de Custos Variáveis", key_suffix="_macro")
    
    with col3:
        nav_manager.create_drill_down_button("RECEITA", "🔬 Análise de Receita", key_suffix="_macro")


def _render_micro_view():
    """Render the micro-level detailed analysis"""
    st.subheader("🔬 Visão Micro - Análise Detalhada")
    
    if hasattr(st.session_state, 'unified_data') and st.session_state.unified_data is not None:
        # Render the micro analysis with the new tree selector
        render_native_hierarchy_tab(st.session_state.unified_data)
        
        # Navigation is already handled by the enhanced navigation component
    else:
        st.info("👆 Carregue dados na aba 'Upload' primeiro para acessar a análise micro detalhada.")


def _render_integrated_view(db, use_unified_extractor: bool, drill_down_section: str, show_comparison_mode: bool):
    """Render the integrated macro + micro view"""
    st.subheader(f"🔄 Visão Integrada - {drill_down_section}")
    
    # Show macro overview first
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📊 Resumo Macro")
        _render_macro_summary_card(drill_down_section)
    
    with col2:
        st.markdown("#### 🔬 Análise Micro")
        _render_micro_drill_down(drill_down_section)
    
    # Show detailed comparison if comparison mode is enabled
    if show_comparison_mode:
        st.markdown("---")
        st.markdown("#### 📈 Comparação Detalhada")
        _render_detailed_comparison(drill_down_section)


def _render_enhanced_macro_comparison():
    """Render enhanced macro comparison with drill-down hints"""
    if not hasattr(st.session_state, 'processed_data') or st.session_state.processed_data is None:
        return
    
    data = st.session_state.processed_data
    df = data.get('consolidated', pd.DataFrame())
    
    if df.empty:
        return
    
    st.markdown("#### 📊 Comparação Macro - Clique para Detalhamento")
    
    # Create enhanced comparison chart with clickable elements
    if 'year' in df.columns and len(df) >= 2:
        # Get the last two years for comparison
        years = sorted(df['year'].unique())[-2:]
        comparison_df = df[df['year'].isin(years)]
        
        # Create side-by-side comparison
        _render_side_by_side_comparison(comparison_df, years)


def _render_side_by_side_comparison(df: pd.DataFrame, years: List[int]):
    """Render side-by-side comparison chart similar to the user's image"""
    categories = [
        ("CUSTOS FIXOS", "fixed_costs", "#1f77b4"),
        ("CUSTOS VARIÁVEIS", "variable_costs", "#ff7f0e"), 
        ("CUSTOS NÃO OPERACIONAIS", "non_operational_costs", "#2ca02c"),
        ("RECEITA", "revenue", "#d62728")
    ]
    
    fig = go.Figure()
    
    year_1, year_2 = years
    df_year_1 = df[df['year'] == year_1].iloc[0] if not df[df['year'] == year_1].empty else None
    df_year_2 = df[df['year'] == year_2].iloc[0] if not df[df['year'] == year_2].empty else None
    
    if df_year_1 is None or df_year_2 is None:
        st.warning("Dados insuficientes para comparação")
        return
    
    # Create grouped bar chart
    x_categories = []
    y_year_1 = []
    y_year_2 = []
    colors = []
    
    for cat_name, col_name, color in categories:
        if col_name in df.columns:
            x_categories.append(cat_name)
            
            val_1 = df_year_1[col_name] if col_name in df_year_1 else 0
            val_2 = df_year_2[col_name] if col_name in df_year_2 else 0
            
            # Convert dict to float if needed
            if isinstance(val_1, dict):
                val_1 = val_1.get('ANNUAL', 0)
            if isinstance(val_2, dict):
                val_2 = val_2.get('ANNUAL', 0)
            
            y_year_1.append(val_1)
            y_year_2.append(val_2)
            colors.append(color)
    
    # Add bars for each year
    fig.add_trace(go.Bar(
        name=str(year_1),
        x=x_categories,
        y=y_year_1,
        text=[format_currency(v) for v in y_year_1],
        textposition='outside',
        marker_color=['rgba(31,119,180,0.5)' if i < 4 else 'rgba(128,128,128,0.5)' for i in range(len(x_categories))],
        hovertemplate='<b>%{x}</b><br>' +
                      f'{year_1}: R$ %{{y:,.0f}}<br>' +
                      '<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        name=str(year_2),
        x=x_categories,
        y=y_year_2,
        text=[format_currency(v) for v in y_year_2],
        textposition='outside',
        marker_color=['#1f77b4' if i == 0 else '#ff7f0e' if i == 1 else '#2ca02c' if i == 2 else '#d62728' if i == 3 else '#808080' for i in range(len(x_categories))],
        hovertemplate='<b>%{x}</b><br>' +
                      f'{year_2}: R$ %{{y:,.0f}}<br>' +
                      '<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Comparação de Categorias Principais - {year_1} vs {year_2}',
        yaxis_title="Valores (R$)",
        xaxis_title="Categorias",
        barmode='group',
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add drill-down buttons below the chart
    st.markdown("**🎯 Clique para análise detalhada:**")
    cols = st.columns(len(x_categories))
    
    nav_manager = get_navigation_manager()
    
    for i, category in enumerate(x_categories):
        with cols[i]:
            nav_manager.create_drill_down_button(
                category, 
                f"🔍 {category}",
                key_suffix=f"_chart_{i}"
            )


def _render_macro_summary_card(section: str):
    """Render macro summary card for specific section"""
    if not hasattr(st.session_state, 'processed_data') or st.session_state.processed_data is None:
        st.info("Dados macro não disponíveis")
        return
    
    data = st.session_state.processed_data
    df = data.get('consolidated', pd.DataFrame())
    
    if df.empty:
        st.info("Dados não encontrados")
        return
    
    # Get column mapping
    section_mapping = {
        "CUSTOS FIXOS": "fixed_costs",
        "CUSTOS VARIÁVEIS": "variable_costs", 
        "CUSTOS NÃO OPERACIONAIS": "non_operational_costs",
        "RECEITA": "revenue"
    }
    
    if section == "Todos":
        st.metric("Total de Categorias", len(section_mapping))
        return
    
    col_name = section_mapping.get(section)
    if not col_name or col_name not in df.columns:
        st.warning(f"Dados não encontrados para {section}")
        return
    
    # Calculate summary metrics
    total_value = df[col_name].sum()
    if isinstance(total_value, dict):
        total_value = total_value.get('ANNUAL', 0)
    
    # Calculate year-over-year change if we have multiple years
    if len(df) >= 2:
        years = sorted(df['year'].unique())
        if len(years) >= 2:
            current_year = df[df['year'] == years[-1]].iloc[0][col_name]
            previous_year = df[df['year'] == years[-2]].iloc[0][col_name]
            
            if isinstance(current_year, dict):
                current_year = current_year.get('ANNUAL', 0)
            if isinstance(previous_year, dict):
                previous_year = previous_year.get('ANNUAL', 0)
            
            if previous_year > 0:
                yoy_change = ((current_year - previous_year) / previous_year) * 100
                delta = f"{yoy_change:+.1f}% vs {years[-2]}"
            else:
                delta = "Novo"
        else:
            delta = None
    else:
        delta = None
    
    st.metric(
        section,
        format_currency(total_value),
        delta=delta
    )
    
    # Add chart for this section
    section_df = df[['year', col_name]].copy()
    
    fig = px.line(
        section_df,
        x='year',
        y=col_name,
        title=f"Evolução - {section}",
        markers=True
    )
    
    fig.update_layout(
        height=200,
        margin=dict(t=30, b=30, l=30, r=30),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_micro_drill_down(section: str):
    """Render micro-level drill-down for specific section"""
    if not hasattr(st.session_state, 'unified_data') or st.session_state.unified_data is None:
        st.info("Dados micro não disponíveis")
        return
    
    unified_data = st.session_state.unified_data
    
    if section == "Todos":
        st.write("Selecione uma seção específica para ver o detalhamento micro")
        return
    
    # Map sections to their categories in the unified data
    section_keywords = {
        "CUSTOS FIXOS": ["CUSTOS FIXOS", "FIXOS"],
        "CUSTOS VARIÁVEIS": ["CUSTOS VARIÁVEIS", "VARIÁVEIS"], 
        "CUSTOS NÃO OPERACIONAIS": ["CUSTOS NÃO OPERACIONAIS", "NÃO OPERACIONAIS"],
        "RECEITA": ["RECEITA", "FATURAMENTO"]
    }
    
    keywords = section_keywords.get(section, [section])
    
    # Find matching sections in unified data
    found_items = []
    for year, year_data in unified_data.items():
        if isinstance(year_data, dict) and 'sections' in year_data:
            for section_data in year_data['sections']:
                section_name = section_data.get('name', '').upper()
                if any(keyword.upper() in section_name for keyword in keywords):
                    # Extract subcategories
                    subcategories = section_data.get('subcategories', [])
                    for subcat in subcategories[:5]:  # Show top 5
                        found_items.append({
                            'year': year,
                            'section': section_data.get('name'),
                            'subcategory': subcat.get('name'),
                            'value': subcat.get('value', 0)
                        })
    
    if found_items:
        # Create summary
        df_items = pd.DataFrame(found_items)
        
        # Show top subcategories
        st.markdown("**🔍 Principais Subcategorias:**")
        top_subcats = df_items.groupby('subcategory')['value'].sum().sort_values(ascending=False).head(5)
        
        for subcat, value in top_subcats.items():
            st.markdown(f"• **{subcat}**: {format_currency(value)}")
        
        # Button to go to full micro analysis
        if st.button(f"🔬 Análise Completa de {section}", key=f"full_micro_{section}"):
            st.session_state.enhanced_view_mode = "🔬 Visão Micro (Análise Detalhada)"
            st.rerun()
    else:
        st.info(f"Nenhum dado detalhado encontrado para {section}")


def _render_detailed_comparison(section: str):
    """Render detailed comparison between macro and micro data"""
    # Get data for unified comparison
    macro_data = getattr(st.session_state, 'processed_data', None)
    micro_data = getattr(st.session_state, 'unified_data', None)
    
    if macro_data and micro_data:
        # Use the unified comparison engine
        render_unified_comparison_section(macro_data, micro_data, section)
    else:
        # Fallback to separate views
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📊 Dados Macro")
            _render_macro_breakdown(section)
        
        with col2:
            st.markdown("##### 🔬 Dados Micro")
            _render_micro_breakdown(section)


def _render_macro_breakdown(section: str):
    """Render macro-level breakdown"""
    # This would show the macro-level data for the section
    st.info("Implementação de breakdown macro em desenvolvimento")


def _render_micro_breakdown(section: str):
    """Render micro-level breakdown"""
    # This would show the detailed micro-level data for the section
    st.info("Implementação de breakdown micro em desenvolvimento")