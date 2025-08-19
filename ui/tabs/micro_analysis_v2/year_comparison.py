"""
Year-over-Year Comparison for Native Excel Hierarchy
Shows how expense items change across years while preserving structure
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
from utils import format_currency


def render_year_comparison(financial_data: Dict):
    """
    Render year-over-year comparison preserving Excel hierarchy
    """
    st.header("📊 Comparação Anual - Estrutura Hierárquica")
    
    if not financial_data or len(financial_data) < 2:
        st.info("São necessários pelo menos 2 anos de dados para comparação.")
        return
    
    # Year selection row
    available_years = sorted(financial_data.keys())
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        base_year = st.selectbox(
            "📅 Ano Base",
            available_years[:-1],
            index=len(available_years) - 2 if len(available_years) > 1 else 0
        )
    with col2:
        compare_year = st.selectbox(
            "📅 Comparar com",
            [y for y in available_years if y > base_year],
            index=0
        )
    with col3:
        # Empty space for alignment
        st.empty()
    
    if not base_year or not compare_year:
        return
    
    # Get data for both years
    base_data = financial_data[base_year]
    compare_data = financial_data[compare_year]
    
    # Visualization selector
    st.markdown("---")
    
    visualization_type = st.selectbox(
        "📈 Tipo de Análise",
        [
            "📋 Tabela Comparativa Hierárquica",
            "📈 Gráfico Waterfall",
            "📊 Comparação Lado a Lado",
            "🔥 Mapa de Calor de Mudanças",
            "📊 Resumo de Mudanças"
        ],
        index=0
    )
    
    st.markdown("---")
    
    # Render selected visualization
    if visualization_type == "📋 Tabela Comparativa Hierárquica":
        # Options for table
        col1, col2, col3 = st.columns(3)
        with col1:
            show_percentages = st.checkbox("Mostrar %", value=True)
        with col2:
            show_only_changes = st.checkbox("Apenas Mudanças", value=False)
        with col3:
            highlight_threshold = st.slider("Destacar >", 0, 100, 20, 5)
        
        # Build and display comparison table
        comparison_df = _build_comparison_dataframe(
            base_data, compare_data, base_year, compare_year,
            show_only_changes, highlight_threshold
        )
        _render_comparison_table(comparison_df, show_percentages, highlight_threshold)
    
    elif visualization_type == "📈 Gráfico Waterfall":
        _render_waterfall_chart(base_data, compare_data, base_year, compare_year)
    
    elif visualization_type == "📊 Comparação Lado a Lado":
        _render_side_by_side_comparison(base_data, compare_data, base_year, compare_year)
    
    elif visualization_type == "🔥 Mapa de Calor de Mudanças":
        _render_change_heatmap(base_data, compare_data, base_year, compare_year)
    
    elif visualization_type == "📊 Resumo de Mudanças":
        _render_change_summary(base_data, compare_data, base_year, compare_year)


def _build_comparison_dataframe(
    base_data: Dict, compare_data: Dict,
    base_year: int, compare_year: int,
    show_only_changes: bool, highlight_threshold: float
) -> pd.DataFrame:
    """
    Build a DataFrame comparing two years of hierarchical data
    """
    rows = []
    
    # Get all sections from both years
    base_sections = {s['name']: s for s in base_data.get('sections', [])}
    compare_sections = {s['name']: s for s in compare_data.get('sections', [])}
    all_sections = set(base_sections.keys()) | set(compare_sections.keys())
    
    for section_name in sorted(all_sections):
        base_section = base_sections.get(section_name, {})
        compare_section = compare_sections.get(section_name, {})
        
        base_value = base_section.get('value', 0)
        compare_value = compare_section.get('value', 0)
        
        # Skip if filtering for changes only
        if show_only_changes and base_value == compare_value:
            continue
        
        # Add Level 1 row
        rows.append({
            'Nível': 1,
            'Item': section_name,
            f'{base_year}': base_value,
            f'{compare_year}': compare_value,
            'Variação': compare_value - base_value,
            'Variação %': ((compare_value - base_value) / base_value * 100) if base_value > 0 else (100 if compare_value > 0 else 0)
        })
        
        # Get all subcategories
        base_subcats = {s['name']: s for s in base_section.get('subcategories', [])}
        compare_subcats = {s['name']: s for s in compare_section.get('subcategories', [])}
        all_subcats = set(base_subcats.keys()) | set(compare_subcats.keys())
        
        for subcat_name in sorted(all_subcats):
            base_subcat = base_subcats.get(subcat_name, {})
            compare_subcat = compare_subcats.get(subcat_name, {})
            
            base_value = base_subcat.get('value', 0)
            compare_value = compare_subcat.get('value', 0)
            
            # Skip if filtering for changes only
            if show_only_changes and base_value == compare_value:
                continue
            
            # Add Level 2 row
            rows.append({
                'Nível': 2,
                'Item': f"  └─ {subcat_name}",
                f'{base_year}': base_value,
                f'{compare_year}': compare_value,
                'Variação': compare_value - base_value,
                'Variação %': ((compare_value - base_value) / base_value * 100) if base_value > 0 else (100 if compare_value > 0 else 0)
            })
            
            # Get all items
            base_items = {i['name']: i for i in base_subcat.get('items', [])}
            compare_items = {i['name']: i for i in compare_subcat.get('items', [])}
            all_items = set(base_items.keys()) | set(compare_items.keys())
            
            for item_name in sorted(all_items):
                base_item = base_items.get(item_name, {})
                compare_item = compare_items.get(item_name, {})
                
                base_value = base_item.get('value', 0)
                compare_value = compare_item.get('value', 0)
                
                # Skip if filtering for changes only
                if show_only_changes and base_value == compare_value:
                    continue
                
                # Add Level 3 row
                rows.append({
                    'Nível': 3,
                    'Item': f"      • {item_name}",
                    f'{base_year}': base_value,
                    f'{compare_year}': compare_value,
                    'Variação': compare_value - base_value,
                    'Variação %': ((compare_value - base_value) / base_value * 100) if base_value > 0 else (100 if compare_value > 0 else 0)
                })
    
    return pd.DataFrame(rows)


def _render_comparison_table(df: pd.DataFrame, show_percentages: bool, highlight_threshold: float):
    """
    Render the comparison table with formatting
    """
    if df.empty:
        st.info("Nenhum dado para comparar.")
        return
    
    st.markdown("### 📋 Tabela Comparativa Hierárquica")
    
    # Format the DataFrame for display
    display_df = df.copy()
    
    # Format currency columns
    year_cols = [col for col in df.columns if col.isdigit() or (isinstance(col, int))]
    for col in year_cols:
        display_df[col] = display_df[col].apply(lambda x: format_currency(x) if pd.notna(x) else '-')
    
    display_df['Variação'] = display_df['Variação'].apply(lambda x: format_currency(x) if pd.notna(x) else '-')
    
    if show_percentages:
        display_df['Variação %'] = display_df['Variação %'].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) and x != 0 else '-'
        )
    else:
        display_df = display_df.drop('Variação %', axis=1)
    
    # Hide the level column for display
    display_df = display_df.drop('Nível', axis=1)
    
    # Apply styling
    def highlight_changes(row):
        styles = [''] * len(row)
        if 'Variação %' in row.index:
            try:
                pct_str = str(row['Variação %'])
                if pct_str != '-' and '%' in pct_str:
                    pct_value = float(pct_str.replace('%', '').replace('+', ''))
                    if abs(pct_value) > highlight_threshold:
                        color = 'background-color: #ffcccc' if pct_value < 0 else 'background-color: #ccffcc'
                        styles = [color if col == 'Variação %' else '' for col in row.index]
            except:
                pass
        return styles
    
    styled_df = display_df.style.apply(highlight_changes, axis=1)
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Quick summary below the table
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            new_items = df[df[list(df.columns)[2]] == 0]['Item'].count()
            st.metric("✨ Novos", new_items)
        
        with col2:
            removed_items = df[df[list(df.columns)[3]] == 0]['Item'].count()
            st.metric("❌ Removidos", removed_items)
        
        with col3:
            increased = df[df['Variação'] > 0]['Item'].count()
            st.metric("📈 Aumentos", increased)
        
        with col4:
            decreased = df[df['Variação'] < 0]['Item'].count()
            st.metric("📉 Reduções", decreased)


def _render_change_summary(base_data: Dict, compare_data: Dict, base_year: int, compare_year: int):
    """
    Render a summary of changes between years
    """
    # Calculate summary statistics
    base_sections = {s['name']: s for s in base_data.get('sections', [])}
    compare_sections = {s['name']: s for s in compare_data.get('sections', [])}
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate totals
    base_total = sum(s.get('value', 0) for s in base_sections.values())
    compare_total = sum(s.get('value', 0) for s in compare_sections.values())
    total_change = compare_total - base_total
    total_change_pct = (total_change / base_total * 100) if base_total > 0 else 0
    
    with col1:
        st.metric(
            f"Total {base_year}",
            format_currency(base_total)
        )
    
    with col2:
        st.metric(
            f"Total {compare_year}",
            format_currency(compare_total)
        )
    
    with col3:
        st.metric(
            "Variação Total",
            format_currency(abs(total_change)),
            f"{total_change_pct:+.1f}%"
        )
    
    with col4:
        # Count changes
        all_sections = set(base_sections.keys()) | set(compare_sections.keys())
        changes = 0
        for section in all_sections:
            base_val = base_sections.get(section, {}).get('value', 0)
            compare_val = compare_sections.get(section, {}).get('value', 0)
            if base_val != compare_val:
                changes += 1
        st.metric("Categorias Alteradas", changes)
    
    # Detailed changes
    st.markdown("---")
    st.markdown("### 📋 Detalhamento das Mudanças")
    
    # Build change analysis
    increases = []
    decreases = []
    new_items = []
    removed_items = []
    
    for section_name in set(base_sections.keys()) | set(compare_sections.keys()):
        base_value = base_sections.get(section_name, {}).get('value', 0)
        compare_value = compare_sections.get(section_name, {}).get('value', 0)
        
        if base_value == 0 and compare_value > 0:
            new_items.append((section_name, compare_value))
        elif compare_value == 0 and base_value > 0:
            removed_items.append((section_name, base_value))
        elif compare_value > base_value:
            increases.append((section_name, compare_value - base_value, (compare_value - base_value) / base_value * 100))
        elif compare_value < base_value:
            decreases.append((section_name, base_value - compare_value, (base_value - compare_value) / base_value * 100))
    
    # Display in columns
    col1, col2 = st.columns(2)
    
    with col1:
        if increases:
            st.markdown("#### 📈 Aumentos")
            for name, change, pct in sorted(increases, key=lambda x: x[1], reverse=True):
                st.markdown(f"**{name}**: +{format_currency(change)} (+{pct:.1f}%)")
        
        if new_items:
            st.markdown("#### ✨ Novos Itens")
            for name, value in new_items:
                st.markdown(f"**{name}**: {format_currency(value)}")
    
    with col2:
        if decreases:
            st.markdown("#### 📉 Reduções")
            for name, change, pct in sorted(decreases, key=lambda x: x[1], reverse=True):
                st.markdown(f"**{name}**: -{format_currency(change)} (-{pct:.1f}%)")
        
        if removed_items:
            st.markdown("#### ❌ Itens Removidos")
            for name, value in removed_items:
                st.markdown(f"**{name}**: {format_currency(value)}")


def _render_waterfall_chart(base_data: Dict, compare_data: Dict, base_year: int, compare_year: int):
    """
    Render a waterfall chart showing changes
    """
    base_sections = {s['name']: s for s in base_data.get('sections', [])}
    compare_sections = {s['name']: s for s in compare_data.get('sections', [])}
    
    # Calculate total changes
    base_total = sum(s.get('value', 0) for s in base_sections.values())
    compare_total = sum(s.get('value', 0) for s in compare_sections.values())
    
    # Build waterfall data
    x = [str(base_year)]
    y = [base_total]
    measure = ['absolute']
    text = [format_currency(base_total)]
    
    # Add changes for each section
    all_sections = set(base_sections.keys()) | set(compare_sections.keys())
    for section_name in sorted(all_sections):
        base_value = base_sections.get(section_name, {}).get('value', 0)
        compare_value = compare_sections.get(section_name, {}).get('value', 0)
        change = compare_value - base_value
        
        if change != 0:
            x.append(section_name)
            y.append(change)
            measure.append('relative')
            text.append(f"{format_currency(abs(change))}<br>{change/base_value*100:+.1f}%" if base_value > 0 else format_currency(change))
    
    # Add final total
    x.append(str(compare_year))
    y.append(compare_total)
    measure.append('total')
    text.append(format_currency(compare_total))
    
    fig = go.Figure(go.Waterfall(
        x=x,
        y=y,
        measure=measure,
        text=text,
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#d62728"}},
        increasing={"marker": {"color": "#2ca02c"}},
        totals={"marker": {"color": "#1f77b4"}}
    ))
    
    fig.update_layout(
        title=f"Waterfall - Mudanças de {base_year} para {compare_year}",
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_side_by_side_comparison(base_data: Dict, compare_data: Dict, base_year: int, compare_year: int):
    """
    Render side-by-side bar comparison
    """
    base_sections = base_data.get('sections', [])
    compare_sections = compare_data.get('sections', [])
    
    # Get all section names
    all_names = list(set([s['name'] for s in base_sections] + [s['name'] for s in compare_sections]))
    
    # Build data
    base_values = []
    compare_values = []
    
    for name in all_names:
        base_value = next((s['value'] for s in base_sections if s['name'] == name), 0)
        compare_value = next((s['value'] for s in compare_sections if s['name'] == name), 0)
        base_values.append(base_value)
        compare_values.append(compare_value)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name=str(base_year),
        x=all_names,
        y=base_values,
        text=[format_currency(v) for v in base_values],
        textposition='auto',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name=str(compare_year),
        x=all_names,
        y=compare_values,
        text=[format_currency(v) for v in compare_values],
        textposition='auto',
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title="Comparação de Categorias Principais",
        barmode='group',
        height=400,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_change_heatmap(base_data: Dict, compare_data: Dict, base_year: int, compare_year: int):
    """
    Render a heatmap showing percentage changes
    """
    # Build matrix of changes
    sections_changes = []
    
    base_sections = {s['name']: s for s in base_data.get('sections', [])}
    compare_sections = {s['name']: s for s in compare_data.get('sections', [])}
    all_sections = set(base_sections.keys()) | set(compare_sections.keys())
    
    for section_name in sorted(all_sections):
        base_section = base_sections.get(section_name, {})
        compare_section = compare_sections.get(section_name, {})
        
        section_row = []
        subcat_names = []
        
        # Get all subcategories
        base_subcats = {s['name']: s for s in base_section.get('subcategories', [])}
        compare_subcats = {s['name']: s for s in compare_section.get('subcategories', [])}
        all_subcats = set(base_subcats.keys()) | set(compare_subcats.keys())
        
        for subcat_name in sorted(all_subcats):
            base_value = base_subcats.get(subcat_name, {}).get('value', 0)
            compare_value = compare_subcats.get(subcat_name, {}).get('value', 0)
            
            if base_value > 0:
                pct_change = ((compare_value - base_value) / base_value) * 100
            elif compare_value > 0:
                pct_change = 100
            else:
                pct_change = 0
            
            section_row.append(pct_change)
            subcat_names.append(subcat_name)
        
        if section_row:
            sections_changes.append({
                'section': section_name,
                'changes': section_row,
                'subcats': subcat_names
            })
    
    if not sections_changes:
        st.info("Dados insuficientes para criar o heatmap")
        return
    
    # Create heatmap
    z = [row['changes'] for row in sections_changes]
    y = [row['section'] for row in sections_changes]
    x = sections_changes[0]['subcats'] if sections_changes else []
    
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x,
        y=y,
        colorscale='RdBu_r',
        zmid=0,
        text=[[f"{val:+.1f}%" for val in row] for row in z],
        texttemplate='%{text}',
        textfont={"size": 10},
        hovertemplate='%{y} - %{x}<br>Variação: %{text}<extra></extra>',
        colorbar=dict(title="Variação %")
    ))
    
    fig.update_layout(
        title=f"Mapa de Calor - Variações % de {base_year} para {compare_year}",
        height=400,
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)