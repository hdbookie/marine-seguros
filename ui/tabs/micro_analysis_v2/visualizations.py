"""
Visualization components for Micro Analysis V2
Focused on year-by-year comparisons and the 3 main cost categories
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional
from utils import format_currency


def render_annual_comparison(aggregated_data: Dict, selected_years: List[int], financial_data: Dict):
    """
    Render year-by-year comparison of the 3 main categories
    """
    st.markdown("### 📊 Comparação Anual - Custos Fixos vs Variáveis vs Não Operacionais")
    
    # Prepare data for visualization
    years_data = []
    
    for year in sorted(selected_years):
        if year not in financial_data:
            continue
            
        year_totals = {
            'Ano': year,
            'Custos Fixos': 0,
            'Custos Variáveis': 0,
            'Custos Não Operacionais': 0
        }
        
        year_data = financial_data[year]
        
        # Try to get from hierarchy first
        if 'hierarchy' in year_data and isinstance(year_data['hierarchy'], dict):
            for cat_key, cat_data in year_data['hierarchy'].items():
                if cat_key == 'custos_fixos':
                    year_totals['Custos Fixos'] = cat_data.get('total', 0)
                elif cat_key == 'custos_variaveis':
                    year_totals['Custos Variáveis'] = cat_data.get('total', 0)
                elif cat_key == 'custos_nao_operacionais':
                    year_totals['Custos Não Operacionais'] = cat_data.get('total', 0)
        else:
            # Fallback to standard categories
            if 'fixed_costs' in year_data:
                if isinstance(year_data['fixed_costs'], dict):
                    year_totals['Custos Fixos'] = year_data['fixed_costs'].get('annual', 0)
                elif isinstance(year_data['fixed_costs'], (int, float)):
                    year_totals['Custos Fixos'] = year_data['fixed_costs']
            
            if 'variable_costs' in year_data:
                if isinstance(year_data['variable_costs'], dict):
                    year_totals['Custos Variáveis'] = year_data['variable_costs'].get('annual', 0)
                elif isinstance(year_data['variable_costs'], (int, float)):
                    year_totals['Custos Variáveis'] = year_data['variable_costs']
            
            if 'non_operational_costs' in year_data:
                if isinstance(year_data['non_operational_costs'], dict):
                    year_totals['Custos Não Operacionais'] = year_data['non_operational_costs'].get('annual', 0)
                elif isinstance(year_data['non_operational_costs'], (int, float)):
                    year_totals['Custos Não Operacionais'] = year_data['non_operational_costs']
        
        years_data.append(year_totals)
    
    if not years_data:
        st.warning("Nenhum dado disponível para os anos selecionados.")
        return
    
    df = pd.DataFrame(years_data)
    
    # Create visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Stacked Bar Chart
        fig_stacked = go.Figure()
        
        fig_stacked.add_trace(go.Bar(
            name='Custos Fixos',
            x=df['Ano'],
            y=df['Custos Fixos'],
            marker_color='#3498db',
            text=[format_currency(v) for v in df['Custos Fixos']],
            textposition='inside',
            hovertemplate='Ano: %{x}<br>Custos Fixos: R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig_stacked.add_trace(go.Bar(
            name='Custos Variáveis',
            x=df['Ano'],
            y=df['Custos Variáveis'],
            marker_color='#2ecc71',
            text=[format_currency(v) for v in df['Custos Variáveis']],
            textposition='inside',
            hovertemplate='Ano: %{x}<br>Custos Variáveis: R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig_stacked.add_trace(go.Bar(
            name='Custos Não Operacionais',
            x=df['Ano'],
            y=df['Custos Não Operacionais'],
            marker_color='#e74c3c',
            text=[format_currency(v) for v in df['Custos Não Operacionais']],
            textposition='inside',
            hovertemplate='Ano: %{x}<br>Custos Não Operacionais: R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig_stacked.update_layout(
            title='Evolução dos Custos por Categoria',
            barmode='stack',
            xaxis=dict(title='Ano', type='category'),
            yaxis=dict(title='Valor (R$)'),
            height=400,
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        st.plotly_chart(fig_stacked, use_container_width=True)
    
    with col2:
        # Line Chart - Trends
        fig_line = go.Figure()
        
        fig_line.add_trace(go.Scatter(
            x=df['Ano'],
            y=df['Custos Fixos'],
            mode='lines+markers',
            name='Custos Fixos',
            line=dict(color='#3498db', width=3),
            marker=dict(size=10),
            hovertemplate='Ano: %{x}<br>Valor: R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig_line.add_trace(go.Scatter(
            x=df['Ano'],
            y=df['Custos Variáveis'],
            mode='lines+markers',
            name='Custos Variáveis',
            line=dict(color='#2ecc71', width=3),
            marker=dict(size=10),
            hovertemplate='Ano: %{x}<br>Valor: R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig_line.add_trace(go.Scatter(
            x=df['Ano'],
            y=df['Custos Não Operacionais'],
            mode='lines+markers',
            name='Custos Não Operacionais',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=10),
            hovertemplate='Ano: %{x}<br>Valor: R$ %{y:,.0f}<extra></extra>'
        ))
        
        fig_line.update_layout(
            title='Tendência dos Custos',
            xaxis=dict(title='Ano', type='category'),
            yaxis=dict(title='Valor (R$)'),
            height=400,
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
    
    # Percentage Distribution Over Years
    st.markdown("#### 📈 Distribuição Percentual ao Longo dos Anos")
    
    # Calculate percentages
    df['Total'] = df['Custos Fixos'] + df['Custos Variáveis'] + df['Custos Não Operacionais']
    df['% Fixos'] = (df['Custos Fixos'] / df['Total'] * 100).round(1)
    df['% Variáveis'] = (df['Custos Variáveis'] / df['Total'] * 100).round(1)
    df['% Não Operacionais'] = (df['Custos Não Operacionais'] / df['Total'] * 100).round(1)
    
    # 100% Stacked Bar
    fig_pct = go.Figure()
    
    fig_pct.add_trace(go.Bar(
        name='Custos Fixos',
        x=df['Ano'],
        y=df['% Fixos'],
        marker_color='#3498db',
        text=df['% Fixos'].apply(lambda x: f'{x:.1f}%'),
        textposition='inside',
        hovertemplate='Ano: %{x}<br>Custos Fixos: %{y:.1f}%<extra></extra>'
    ))
    
    fig_pct.add_trace(go.Bar(
        name='Custos Variáveis',
        x=df['Ano'],
        y=df['% Variáveis'],
        marker_color='#2ecc71',
        text=df['% Variáveis'].apply(lambda x: f'{x:.1f}%'),
        textposition='inside',
        hovertemplate='Ano: %{x}<br>Custos Variáveis: %{y:.1f}%<extra></extra>'
    ))
    
    fig_pct.add_trace(go.Bar(
        name='Custos Não Operacionais',
        x=df['Ano'],
        y=df['% Não Operacionais'],
        marker_color='#e74c3c',
        text=df['% Não Operacionais'].apply(lambda x: f'{x:.1f}%'),
        textposition='inside',
        hovertemplate='Ano: %{x}<br>Custos Não Operacionais: %{y:.1f}%<extra></extra>'
    ))
    
    fig_pct.update_layout(
        title='Distribuição Percentual dos Custos',
        barmode='stack',
        xaxis=dict(title='Ano', type='category'),
        yaxis=dict(title='Percentual (%)', range=[0, 100]),
        height=350,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    st.plotly_chart(fig_pct, use_container_width=True)
    
    # Summary Table
    st.markdown("#### 📋 Tabela Resumo")
    
    # Format for display
    display_df = df[['Ano', 'Custos Fixos', 'Custos Variáveis', 'Custos Não Operacionais', 'Total']].copy()
    for col in ['Custos Fixos', 'Custos Variáveis', 'Custos Não Operacionais', 'Total']:
        display_df[col] = display_df[col].apply(format_currency)
    
    # Add growth rates
    if len(display_df) > 1:
        for col in ['Custos Fixos', 'Custos Variáveis', 'Custos Não Operacionais']:
            growth_col = f'Cresc. {col.split()[1]}'
            display_df[growth_col] = ''
            for i in range(1, len(df)):
                if df.iloc[i-1][col] > 0:
                    growth = ((df.iloc[i][col] - df.iloc[i-1][col]) / df.iloc[i-1][col]) * 100
                    display_df.loc[df.index[i], growth_col] = f'{growth:+.1f}%'
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_cost_breakdown_by_year(aggregated_data: Dict, selected_year: int, financial_data: Dict):
    """
    Render detailed breakdown for a specific year
    """
    st.markdown(f"### 🔍 Detalhamento do Ano {selected_year}")
    
    if selected_year not in financial_data:
        st.warning(f"Dados não disponíveis para o ano {selected_year}")
        return
    
    year_data = financial_data[selected_year]
    
    # Create three columns for the main categories
    col1, col2, col3 = st.columns(3)
    
    categories_data = {}
    
    # Get data for each main category
    if 'hierarchy' in year_data and isinstance(year_data['hierarchy'], dict):
        hierarchy = year_data['hierarchy']
        
        with col1:
            if 'custos_fixos' in hierarchy:
                _render_category_card('📊 Custos Fixos', hierarchy['custos_fixos'], 'blue')
                categories_data['Custos Fixos'] = hierarchy['custos_fixos']
        
        with col2:
            if 'custos_variaveis' in hierarchy:
                _render_category_card('📈 Custos Variáveis', hierarchy['custos_variaveis'], 'green')
                categories_data['Custos Variáveis'] = hierarchy['custos_variaveis']
        
        with col3:
            if 'custos_nao_operacionais' in hierarchy:
                _render_category_card('🔴 Custos Não Operacionais', hierarchy['custos_nao_operacionais'], 'red')
                categories_data['Custos Não Operacionais'] = hierarchy['custos_nao_operacionais']
    
    # Detailed breakdown by subcategory
    if categories_data:
        st.markdown("---")
        st.markdown("#### 📊 Composição por Subcategoria")
        
        # Prepare data for sunburst
        sunburst_data = []
        colors = []
        color_map = {
            'Custos Fixos': '#3498db',
            'Custos Variáveis': '#2ecc71',
            'Custos Não Operacionais': '#e74c3c'
        }
        
        for cat_name, cat_data in categories_data.items():
            # Add main category
            sunburst_data.append({
                'labels': cat_name,
                'parents': '',
                'values': cat_data.get('total', 0),
                'ids': cat_name
            })
            colors.append(color_map.get(cat_name, '#95a5a6'))
            
            # Add subcategories
            if 'subcategories' in cat_data:
                for subcat_key, subcat_data in cat_data['subcategories'].items():
                    sunburst_data.append({
                        'labels': subcat_data.get('name', subcat_key),
                        'parents': cat_name,
                        'values': subcat_data.get('total', 0),
                        'ids': f"{cat_name}.{subcat_key}"
                    })
                    # Lighter shade for subcategories
                    base_color = color_map.get(cat_name, '#95a5a6')
                    colors.append(base_color)
        
        if sunburst_data:
            df_sunburst = pd.DataFrame(sunburst_data)
            
            fig = go.Figure(go.Sunburst(
                labels=df_sunburst['labels'],
                parents=df_sunburst['parents'],
                values=df_sunburst['values'],
                ids=df_sunburst['ids'],
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


def _render_category_card(title: str, category_data: Dict, color: str):
    """
    Render a card for a category with its details
    """
    color_map = {
        'blue': '#3498db',
        'green': '#2ecc71',
        'red': '#e74c3c'
    }
    
    total = category_data.get('total', 0)
    
    st.markdown(f"""
    <div style="background-color: {color_map.get(color, '#95a5a6')}20; 
                padding: 15px; 
                border-radius: 10px; 
                border-left: 4px solid {color_map.get(color, '#95a5a6')};">
        <h4 style="margin: 0;">{title}</h4>
        <h2 style="margin: 10px 0; color: {color_map.get(color, '#95a5a6')};">{format_currency(total)}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Show top subcategories
    if 'subcategories' in category_data and category_data['subcategories']:
        st.markdown("**Top Subcategorias:**")
        sorted_subcats = sorted(
            category_data['subcategories'].items(),
            key=lambda x: x[1].get('total', 0),
            reverse=True
        )
        
        for i, (subcat_key, subcat_data) in enumerate(sorted_subcats[:3]):
            pct = (subcat_data.get('total', 0) / total * 100) if total > 0 else 0
            st.markdown(f"• {subcat_data.get('name', subcat_key)}: {format_currency(subcat_data.get('total', 0))} ({pct:.1f}%)")


def render_heatmap_analysis(financial_data: Dict, selected_years: List[int]):
    """
    Render heatmap showing cost intensity by category and month
    """
    st.markdown("### 🔥 Mapa de Calor - Intensidade de Custos")
    
    # Prepare monthly data
    monthly_data = []
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
              'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    for year in sorted(selected_years):
        if year not in financial_data:
            continue
        
        year_data = financial_data[year]
        
        # Check for monthly_data
        if 'monthly_data' in year_data:
            for month in months:
                if month in year_data['monthly_data']:
                    month_data = year_data['monthly_data'][month]
                    row = {
                        'Ano': year,
                        'Mês': month,
                        'Custos Fixos': month_data.get('custos_fixos', 0),
                        'Custos Variáveis': month_data.get('custos_variaveis', 0),
                        'Custos Não Operacionais': month_data.get('custos_nao_operacionais', 0)
                    }
                    monthly_data.append(row)
    
    if not monthly_data:
        st.info("Dados mensais não disponíveis para criar o mapa de calor.")
        return
    
    df = pd.DataFrame(monthly_data)
    
    # Create heatmap for each category
    for category in ['Custos Fixos', 'Custos Variáveis', 'Custos Não Operacionais']:
        if category in df.columns:
            # Pivot data for heatmap
            pivot_df = df.pivot(index='Mês', columns='Ano', values=category)
            
            # Reorder months
            pivot_df = pivot_df.reindex(months)
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                colorscale='RdYlBu_r',
                text=[[format_currency(val) for val in row] for row in pivot_df.values],
                texttemplate='%{text}',
                textfont={"size": 10},
                hovertemplate='Ano: %{x}<br>Mês: %{y}<br>Valor: %{text}<extra></extra>'
            ))
            
            fig.update_layout(
                title=f'Mapa de Calor - {category}',
                xaxis=dict(title='Ano', type='category'),
                yaxis=dict(title='Mês'),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)