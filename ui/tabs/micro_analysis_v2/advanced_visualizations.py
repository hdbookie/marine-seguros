"""
Advanced Visualizations for Micro Analysis V2
Provides cutting-edge interactive visualizations for expense analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from utils import format_currency
import json


def render_waterfall_drilldown(financial_data: Dict, selected_year: int):
    """
    Render an interactive waterfall chart with drill-down capability
    Shows expense flow from high-level categories to granular items
    """
    st.markdown("### 🌊 Análise Waterfall Interativa")
    
    if selected_year not in financial_data:
        st.warning(f"Dados não disponíveis para {selected_year}")
        return
    
    year_data = financial_data[selected_year]
    
    # Initialize session state for waterfall navigation
    if 'waterfall_level' not in st.session_state:
        st.session_state.waterfall_level = 1
    if 'waterfall_path' not in st.session_state:
        st.session_state.waterfall_path = []
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**Nível atual:** {_get_waterfall_level_name(st.session_state.waterfall_level)}")
        if st.session_state.waterfall_path:
            breadcrumb = " → ".join(st.session_state.waterfall_path)
            st.caption(f"📍 {breadcrumb}")
    
    with col2:
        if st.button("⬆️ Subir Nível") and st.session_state.waterfall_level > 1:
            st.session_state.waterfall_level -= 1
            if st.session_state.waterfall_path:
                st.session_state.waterfall_path.pop()
            st.rerun()
    
    with col3:
        if st.button("🔄 Resetar"):
            st.session_state.waterfall_level = 1
            st.session_state.waterfall_path = []
            st.rerun()
    
    # Get current level data
    waterfall_data = _prepare_waterfall_data(year_data, st.session_state.waterfall_level, st.session_state.waterfall_path)
    
    if not waterfall_data:
        st.warning("Nenhum dado disponível para este nível")
        return
    
    # Create waterfall chart
    fig = _create_waterfall_chart(waterfall_data, st.session_state.waterfall_level)
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Add drill-down buttons for clickable items
    if any(item.get('drillable', False) for item in waterfall_data):
        st.markdown("### 🔍 Explorar Categorias")
        
        # Create columns for buttons
        num_items = len([item for item in waterfall_data if item.get('drillable', False)])
        cols = st.columns(min(3, num_items))
        
        col_idx = 0
        for item in waterfall_data:
            if item.get('drillable', False):
                with cols[col_idx % min(3, num_items)]:
                    if st.button(
                        f"📊 {item['name']}\n{format_currency(item['value'])}",
                        key=f"drill_{st.session_state.waterfall_level}_{item['name']}",
                        use_container_width=True
                    ):
                        st.session_state.waterfall_path.append(item['name'])
                        st.session_state.waterfall_level = min(4, st.session_state.waterfall_level + 1)
                        st.rerun()
                col_idx += 1
    
    # Show summary stats for current level
    _render_waterfall_summary(waterfall_data)


def _prepare_waterfall_data(year_data: Dict, level: int, path: List[str]) -> List[Dict]:
    """Prepare data for waterfall chart based on current level and path"""
    
    if 'sections' not in year_data:
        return []
    
    sections = year_data['sections']
    
    # Revenue categories to exclude from waterfall
    revenue_categories = ['FATURAMENTO', 'RECEITA', 'RECEITAS', 'Outras receitas/creditos']
    
    if level == 1:
        # Level 1: Main sections (costs/expenses only)
        data = []
        for section in sections:
            section_name = section.get('name', '')
            # Skip revenue categories
            if any(rev.upper() in section_name.upper() for rev in revenue_categories):
                continue
            
            if section.get('value', 0) > 0:  # Only positive values
                data.append({
                    'name': section['name'],
                    'value': section['value'],
                    'type': 'section',
                    'drillable': len(section.get('subcategories', [])) > 0
                })
        return sorted(data, key=lambda x: x['value'], reverse=True)
    
    elif level == 2 and len(path) >= 1:
        # Level 2: Subcategories of selected section
        section_name = path[0]
        target_section = None
        
        for section in sections:
            if section['name'] == section_name:
                target_section = section
                break
        
        if not target_section:
            return []
        
        data = []
        for subcat in target_section.get('subcategories', []):
            if subcat.get('value', 0) > 0:
                data.append({
                    'name': subcat['name'],
                    'value': subcat['value'],
                    'type': 'subcategory',
                    'drillable': len(subcat.get('items', [])) > 0
                })
        
        return sorted(data, key=lambda x: x['value'], reverse=True)
    
    elif level == 3 and len(path) >= 2:
        # Level 3: Items of selected subcategory
        section_name, subcat_name = path[0], path[1]
        target_subcat = None
        
        for section in sections:
            if section['name'] == section_name:
                for subcat in section.get('subcategories', []):
                    if subcat['name'] == subcat_name:
                        target_subcat = subcat
                        break
                break
        
        if not target_subcat:
            return []
        
        data = []
        for item in target_subcat.get('items', []):
            if item.get('value', 0) > 0:
                data.append({
                    'name': item['name'],
                    'value': item['value'],
                    'type': 'item',
                    'drillable': False
                })
        
        return sorted(data, key=lambda x: x['value'], reverse=True)
    
    return []


def _create_waterfall_chart(data: List[Dict], level: int) -> go.Figure:
    """Create an interactive waterfall chart"""
    
    if not data:
        return go.Figure()
    
    # Prepare waterfall data
    categories = [item['name'] for item in data]
    values = [item['value'] for item in data]
    drillable = [item.get('drillable', False) for item in data]
    
    # Create cumulative values for waterfall effect
    cumulative = np.cumsum([0] + values[:-1])
    
    # Color scheme based on level and drillability
    color_schemes = {
        1: ['#2E7D32', '#388E3C', '#43A047', '#4CAF50', '#66BB6A'],  # Main sections (green shades)
        2: ['#1565C0', '#1976D2', '#1E88E5', '#2196F3', '#42A5F5'],  # Subcategories (blue shades)
        3: ['#E65100', '#EF6C00', '#F57C00', '#FB8C00', '#FF9800']   # Items (orange shades)
    }
    colors = color_schemes.get(level, color_schemes[1])
    
    # Create figure
    fig = go.Figure()
    
    # Add waterfall bars
    for i, (category, value, cum_val, is_drillable) in enumerate(zip(categories, values, cumulative, drillable)):
        color = colors[i % len(colors)]
        
        # Adjust opacity for drillable items
        bar_opacity = 0.9 if is_drillable else 0.6
        hover_text = f'<b>{category}</b><br>Valor: {format_currency(value)}<br>Acumulado: {format_currency(cum_val + value)}'
        if is_drillable:
            hover_text += '<br><b>📊 Contém subcategorias</b>'
        
        # Main bar (from cumulative to cumulative + value)
        fig.add_trace(go.Bar(
            x=[category],
            y=[value],
            base=[cum_val],
            name=category,
            marker=dict(
                color=color,
                opacity=bar_opacity,
                line=dict(color='white', width=2) if is_drillable else dict(width=0)
            ),
            text=format_currency(value),
            textposition='auto',
            hovertemplate=hover_text + '<extra></extra>',
            showlegend=False
        ))
        
        # Connector line (if not first item)
        if i > 0:
            fig.add_trace(go.Scatter(
                x=[categories[i-1], category],
                y=[cumulative[i], cumulative[i]],
                mode='lines',
                line=dict(color='gray', dash='dot', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Add total line
    total_value = sum(values)
    fig.add_trace(go.Scatter(
        x=[categories[0], categories[-1]],
        y=[total_value, total_value],
        mode='lines',
        line=dict(color='red', dash='dash', width=2),
        name=f'Total: {format_currency(total_value)}',
        hovertemplate=f'<b>Total Geral</b><br>{format_currency(total_value)}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'Análise de Custos - {_get_waterfall_level_name(level)}',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(title='Categorias', tickangle=-45),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        height=500,
        showlegend=True,
        hovermode='closest',
        plot_bgcolor='rgba(250,250,250,0.5)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    return fig


def _get_waterfall_level_name(level: int) -> str:
    """Get human-readable name for waterfall level"""
    names = {
        1: "Categorias de Custos",
        2: "Subcategorias", 
        3: "Itens Detalhados",
        4: "Componentes"
    }
    return names.get(level, f"Nível {level}")


def _render_waterfall_summary(data: List[Dict]):
    """Render summary statistics for current waterfall level"""
    
    if not data:
        return
    
    st.markdown("---")
    st.markdown("#### 📊 Resumo do Nível Atual")
    
    total_value = sum(item['value'] for item in data)
    num_items = len(data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total", format_currency(total_value))
    
    with col2:
        st.metric("Itens", f"{num_items:,}")
    
    with col3:
        if num_items > 0:
            avg_value = total_value / num_items
            st.metric("Valor Médio", format_currency(avg_value))
    
    with col4:
        if data:
            largest_item = max(data, key=lambda x: x['value'])
            percentage = (largest_item['value'] / total_value) * 100
            st.metric("Maior Item", f"{percentage:.1f}%", help=f"{largest_item['name']}")


def render_enhanced_heatmaps(financial_data: Dict, selected_years: List[int]):
    """
    Render multiple advanced heatmaps for different analytical perspectives
    """
    st.markdown("### 🔥 Análise de Heatmaps Avançados")
    
    if len(selected_years) < 2:
        st.warning("Selecione pelo menos 2 anos para análises de heatmap comparativas.")
        return
    
    # Heatmap type selector
    heatmap_type = st.selectbox(
        "Tipo de Análise",
        [
            "🌡️ Intensidade de Gastos",
            "📈 Taxa de Crescimento YoY", 
            "🔍 Variação Mensal",
            "⚖️ Análise de Eficiência",
            "🎯 Concentração de Custos"
        ]
    )
    
    if heatmap_type == "🌡️ Intensidade de Gastos":
        _render_intensity_heatmap(financial_data, selected_years)
    elif heatmap_type == "📈 Taxa de Crescimento YoY":
        _render_growth_heatmap(financial_data, selected_years)
    elif heatmap_type == "🔍 Variação Mensal":
        _render_monthly_variation_heatmap(financial_data, selected_years)
    elif heatmap_type == "⚖️ Análise de Eficiência":
        _render_efficiency_heatmap(financial_data, selected_years)
    elif heatmap_type == "🎯 Concentração de Custos":
        _render_concentration_heatmap(financial_data, selected_years)


def _render_intensity_heatmap(financial_data: Dict, selected_years: List[int]):
    """Render expense intensity heatmap (Category vs Month)"""
    
    st.markdown("#### 🌡️ Mapa de Calor - Intensidade de Gastos")
    st.caption("Mostra a intensidade dos gastos por categoria e mês ao longo dos anos")
    
    # Prepare data
    heatmap_data = []
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    for year in sorted(selected_years):
        if year not in financial_data or 'sections' not in financial_data[year]:
            continue
        
        sections = financial_data[year]['sections']
        
        for section in sections:
            section_name = section['name']
            monthly_data = section.get('monthly', {})
            
            for month in months:
                value = monthly_data.get(month, 0)
                if value > 0:
                    heatmap_data.append({
                        'Categoria': section_name,
                        'Mês': month,
                        'Ano': year,
                        'Valor': value,
                        'Categoria_Mês': f"{section_name}_{month}",
                        'Ano_Mês': f"{year}_{month}"
                    })
    
    if not heatmap_data:
        st.warning("Dados mensais não disponíveis para criar heatmap")
        return
    
    df = pd.DataFrame(heatmap_data)
    
    # Create pivot table for heatmap
    pivot_df = df.pivot_table(
        values='Valor',
        index='Categoria',
        columns='Ano_Mês',
        fill_value=0
    )
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=[col.replace('_', ' ') for col in pivot_df.columns],
        y=pivot_df.index,
        colorscale='RdYlBu_r',
        text=[[f'{format_currency(val)}<br>({val/pivot_df.values.max()*100:.1f}% do máximo)' 
               for val in row] for row in pivot_df.values],
        texttemplate='%{text}',
        textfont={"size": 8},
        hovertemplate='<b>%{y}</b><br>Período: %{x}<br>Valor: %{text}<extra></extra>',
        colorbar=dict(title="Intensidade (R$)", tickformat=',.0f')
    ))
    
    fig.update_layout(
        title='Intensidade de Gastos - Categoria vs Tempo',
        xaxis=dict(title='Período (Ano_Mês)', tickangle=45),
        yaxis=dict(title='Categoria'),
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add insights
    _render_heatmap_insights(df, "intensidade")


def _render_growth_heatmap(financial_data: Dict, selected_years: List[int]):
    """Render year-over-year growth rate heatmap"""
    
    st.markdown("#### 📈 Mapa de Calor - Taxa de Crescimento")
    st.caption("Mostra taxas de crescimento ano-sobre-ano por categoria")
    
    if len(selected_years) < 2:
        st.warning("Necessário pelo menos 2 anos para cálculo de crescimento")
        return
    
    # Calculate growth rates
    growth_data = []
    
    for i in range(1, len(selected_years)):
        current_year = selected_years[i]
        previous_year = selected_years[i-1]
        
        if (current_year not in financial_data or previous_year not in financial_data or
            'sections' not in financial_data[current_year] or 'sections' not in financial_data[previous_year]):
            continue
        
        current_sections = {s['name']: s['value'] for s in financial_data[current_year]['sections']}
        previous_sections = {s['name']: s['value'] for s in financial_data[previous_year]['sections']}
        
        for category in set(current_sections.keys()) & set(previous_sections.keys()):
            current_val = current_sections[category]
            previous_val = previous_sections[category]
            
            if previous_val > 0:
                growth_rate = ((current_val - previous_val) / previous_val) * 100
                growth_data.append({
                    'Categoria': category,
                    'Período': f"{previous_year}-{current_year}",
                    'Crescimento': growth_rate,
                    'Valor_Anterior': previous_val,
                    'Valor_Atual': current_val
                })
    
    if not growth_data:
        st.warning("Dados insuficientes para calcular crescimento")
        return
    
    df = pd.DataFrame(growth_data)
    
    # Create pivot for heatmap
    pivot_df = df.pivot_table(
        values='Crescimento',
        index='Categoria',
        columns='Período',
        fill_value=0
    )
    
    # Create heatmap with diverging color scale
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale='RdBu_r',  # Red for positive growth, Blue for negative
        zmid=0,  # Center at 0%
        text=[[f'{val:.1f}%' for val in row] for row in pivot_df.values],
        texttemplate='%{text}',
        textfont={"size": 10},
        hovertemplate='<b>%{y}</b><br>Período: %{x}<br>Crescimento: %{text}<extra></extra>',
        colorbar=dict(title="Crescimento (%)", ticksuffix='%')
    ))
    
    fig.update_layout(
        title='Taxa de Crescimento - Categoria vs Período',
        xaxis=dict(title='Período'),
        yaxis=dict(title='Categoria'),
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add growth insights
    _render_growth_insights(df)


def _render_heatmap_insights(df: pd.DataFrame, analysis_type: str):
    """Render insights from heatmap analysis"""
    
    st.markdown("#### 🔍 Insights da Análise")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Principais Observações:**")
        
        if analysis_type == "intensidade":
            # Find highest intensity
            max_row = df.loc[df['Valor'].idxmax()]
            st.info(f"📊 Maior intensidade: **{max_row['Categoria']}** em {max_row['Mês']}/{max_row['Ano']} - {format_currency(max_row['Valor'])}")
            
            # Find most consistent category
            category_variance = df.groupby('Categoria')['Valor'].var().sort_values()
            most_consistent = category_variance.index[0]
            st.success(f"🎯 Mais consistente: **{most_consistent}** (menor variação)")
            
    with col2:
        st.markdown("**Recomendações:**")
        
        if analysis_type == "intensidade":
            # Seasonal patterns
            monthly_avg = df.groupby('Mês')['Valor'].mean().sort_values(ascending=False)
            peak_month = monthly_avg.index[0]
            low_month = monthly_avg.index[-1]
            
            st.warning(f"📅 Padrão sazonal detectado: pico em **{peak_month}**, menor em **{low_month}**")
            st.info("💡 Considere planejamento sazonal de despesas")


def _render_growth_insights(df: pd.DataFrame):
    """Render insights from growth analysis"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Análise de Crescimento:**")
        
        # Fastest growing category
        fastest_growth = df.loc[df['Crescimento'].idxmax()]
        st.success(f"🚀 Maior crescimento: **{fastest_growth['Categoria']}** (+{fastest_growth['Crescimento']:.1f}%)")
        
        # Fastest declining category  
        if df['Crescimento'].min() < 0:
            fastest_decline = df.loc[df['Crescimento'].idxmin()]
            st.error(f"📉 Maior declínio: **{fastest_decline['Categoria']}** ({fastest_decline['Crescimento']:.1f}%)")
    
    with col2:
        st.markdown("**Tendências Identificadas:**")
        
        # Overall growth trend
        avg_growth = df['Crescimento'].mean()
        if avg_growth > 5:
            st.warning(f"⚠️ Crescimento médio alto: {avg_growth:.1f}% - monitorar custos")
        elif avg_growth < -5:
            st.info(f"📊 Redução média: {avg_growth:.1f}% - otimização em curso")
        else:
            st.success(f"✅ Crescimento controlado: {avg_growth:.1f}%")


def render_network_hierarchy_visualizer(financial_data: Dict, selected_year: int):
    """
    Render network-style hierarchy visualization with nodes and edges
    """
    st.markdown("### 🕸️ Visualizador de Rede Hierárquica")
    
    if selected_year not in financial_data:
        st.warning(f"Dados não disponíveis para {selected_year}")
        return
    
    # This is a placeholder for the network visualizer
    # In a full implementation, you'd use libraries like streamlit-agraph or pyvis
    st.info("🚧 Visualizador de rede em desenvolvimento - será implementado com streamlit-agraph")
    
    # For now, show a conceptual description
    st.markdown("""
    **Características do Visualizador de Rede:**
    - 🟢 **Nós**: Representam categorias e itens (tamanho = valor)
    - 🔗 **Arestas**: Mostram relações hierárquicas (espessura = intensidade)
    - 🎨 **Cores**: Codificação por tipo de despesa
    - 🖱️ **Interativo**: Arrastar nós, zoom, filtros
    - 📊 **Métricas**: Centralidade, clustering, densidade
    """)
    
    year_data = financial_data[selected_year]
    if 'sections' in year_data:
        # Show network statistics instead
        _render_network_statistics(year_data)


def _render_network_statistics(year_data: Dict):
    """Render network statistics as a substitute for the visual network"""
    
    st.markdown("#### 📊 Estatísticas da Rede Hierárquica")
    
    sections = year_data['sections']
    
    # Calculate network metrics
    total_nodes = 0
    total_edges = 0
    max_depth = 0
    
    for section in sections:
        total_nodes += 1  # Section node
        subcats = section.get('subcategories', [])
        
        for subcat in subcats:
            total_nodes += 1  # Subcat node
            total_edges += 1  # Section -> Subcat edge
            
            items = subcat.get('items', [])
            if items:
                max_depth = max(max_depth, 3)
                total_nodes += len(items)  # Item nodes
                total_edges += len(items)  # Subcat -> Item edges
            else:
                max_depth = max(max_depth, 2)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🟢 Total de Nós", f"{total_nodes:,}")
    
    with col2:
        st.metric("🔗 Total de Arestas", f"{total_edges:,}")
    
    with col3:
        st.metric("📏 Profundidade Máxima", f"{max_depth}")
    
    with col4:
        density = (2 * total_edges) / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0
        st.metric("🌐 Densidade", f"{density:.3f}")
    
    # Show hierarchy structure summary
    st.markdown("#### 🏗️ Estrutura da Hierarquia")
    
    for section in sections[:5]:  # Show first 5 sections
        with st.expander(f"📁 {section['name']} - {format_currency(section['value'])}"):
            subcats = section.get('subcategories', [])
            st.write(f"**Subcategorias:** {len(subcats)}")
            
            for subcat in subcats[:3]:  # Show first 3 subcategories
                items_count = len(subcat.get('items', []))
                st.write(f"  └─ {subcat['name']}: {items_count} itens - {format_currency(subcat['value'])}")