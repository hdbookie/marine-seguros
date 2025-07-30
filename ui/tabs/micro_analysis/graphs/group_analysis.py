"""
Group Analysis Graph Modules
Handles all group-based visualizations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from visualizations.charts import (
    create_group_evolution_chart,
    create_group_comparison_chart,
    create_margin_impact_by_group_chart,
    create_group_treemap
)
from utils import format_currency
from ..config import GRAPH_CONFIGS, COLORS, CHART_PALETTES


def render_group_evolution(group_df, financial_df, flexible_data, config=None):
    """
    Render group evolution analysis with separate fixed and variable costs
    
    Args:
        group_df: DataFrame with group data
        financial_df: DataFrame with financial data
        flexible_data: Raw flexible data for detailed breakdown
        config: Optional configuration overrides
    """
    config = {**GRAPH_CONFIGS['group_evolution'], **(config or {})}
    
    # Quick debug check for commissions
    if st.checkbox("🔍 Debug rápido: Ver estrutura de comissões", key="quick_debug_comm"):
        latest_year = max(flexible_data.keys()) if flexible_data else None
        if latest_year and 'commissions' in flexible_data[latest_year]:
            comm = flexible_data[latest_year]['commissions']
            st.write(f"Comissões {latest_year}:")
            if isinstance(comm, dict) and 'line_items' in comm:
                for k, v in comm['line_items'].items():
                    if isinstance(v, dict):
                        st.write(f"- {v.get('label', k)}: {v.get('annual', 0)}")
                        if 'sub_items' in v:
                            st.write(f"  Sub-items: {len(v['sub_items'])}")
                        else:
                            st.write("  [Sem sub-items]")
    
    # Variable costs in its own row - full width
    st.markdown("### 📈 Custos Variáveis")
    _render_variable_costs_evolution(financial_df, flexible_data, full_width=True)
    
    # Top expenses in its own row - full width
    st.markdown("---")
    _render_top_expenses_evolution(financial_df, flexible_data, full_width=True)
    
    # Fixed costs in its own row - full width
    st.markdown("---")
    st.markdown("### 📊 Custos Fixos")
    _render_fixed_costs_evolution(financial_df, flexible_data, full_width=True)
    
    # Detailed group comparison below
    st.markdown("---")
    st.subheader("📊 Análise Detalhada por Categoria")
    
    if not group_df.empty:
        # Evolution chart
        fig_evolution = create_group_evolution_chart(group_df, title="Evolução dos Grupos de Despesas")
        fig_evolution.update_layout(height=config['height'])
        st.plotly_chart(fig_evolution, use_container_width=True)
        
        # Year-over-year comparison
        if st.checkbox("📊 Mostrar Comparação Ano a Ano", key="group_yoy"):
            _render_yoy_comparison(group_df)
    else:
        st.warning("Nenhum dado de grupo disponível para visualização.")


def render_group_comparison(group_df, financial_df, major_groups, config=None):
    """
    Render group comparison analysis
    
    Args:
        group_df: DataFrame with group data
        financial_df: DataFrame with financial data
        major_groups: Dictionary with major groups data
        config: Optional configuration overrides
    """
    config = {**GRAPH_CONFIGS['group_comparison'], **(config or {})}
    
    st.subheader(f"📊 {config['title']}")
    
    if not group_df.empty and not financial_df.empty:
        # Stacked bar chart
        fig_comparison = create_group_comparison_chart(group_df, financial_df, title=config['title'])
        fig_comparison.update_layout(height=config['height'])
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Treemap for latest year
        st.subheader("🗂️ Composição dos Grupos - Último Ano")
        latest_year = financial_df['year'].max()
        
        fig_treemap = create_group_treemap(major_groups, latest_year)
        st.plotly_chart(fig_treemap, use_container_width=True)
        
        # Summary insights
        _render_group_insights(group_df, latest_year)
    else:
        st.warning("Dados insuficientes para comparação de grupos.")


def render_margin_impact(group_df, financial_df, config=None):
    """
    Render margin impact analysis
    
    Args:
        group_df: DataFrame with group data
        financial_df: DataFrame with financial data
        config: Optional configuration overrides
    """
    config = {**GRAPH_CONFIGS['margin_impact'], **(config or {})}
    
    st.subheader(f"💰 {config['title']}")
    
    if not group_df.empty and not financial_df.empty:
        # Waterfall chart
        fig_waterfall = create_margin_impact_by_group_chart(group_df, financial_df, title=config['title'])
        fig_waterfall.update_layout(height=config['height'])
        st.plotly_chart(fig_waterfall, use_container_width=True)
        
        # Detailed impact analysis
        if st.checkbox("📋 Mostrar Análise Detalhada", key="margin_detail"):
            _render_impact_details(group_df, financial_df)
    else:
        st.warning("Dados insuficientes para análise de impacto na margem.")


def _render_yoy_comparison(group_df):
    """Render year-over-year comparison table"""
    st.subheader("📊 Comparação Ano a Ano")
    
    # Create pivot table
    pivot_df = group_df.pivot(index='Grupo', columns='Ano', values='Valor')
    
    # Calculate YoY changes
    for col in pivot_df.columns[1:]:
        prev_col = pivot_df.columns[pivot_df.columns.get_loc(col) - 1]
        pivot_df[f'Var {col}'] = ((pivot_df[col] - pivot_df[prev_col]) / pivot_df[prev_col] * 100).round(1)
    
    # Format and display
    st.dataframe(
        pivot_df.style.format({
            col: format_currency if 'Var' not in str(col) else '{:.1f}%'
            for col in pivot_df.columns
        }),
        use_container_width=True
    )


def _render_group_insights(group_df, latest_year):
    """Render key insights about groups"""
    st.subheader("💡 Principais Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Largest group
        latest_data = group_df[group_df['Ano'] == latest_year].sort_values('Valor', ascending=False)
        if not latest_data.empty:
            largest = latest_data.iloc[0]
            st.info(f"**Maior grupo ({latest_year}):**\n{largest['Grupo']}: {format_currency(largest['Valor'])}")
    
    with col2:
        # Fastest growing
        growth_rates = {}
        for grupo in group_df['Grupo'].unique():
            grupo_data = group_df[group_df['Grupo'] == grupo].sort_values('Ano')
            if len(grupo_data) > 1:
                first_value = grupo_data.iloc[0]['Valor']
                last_value = grupo_data.iloc[-1]['Valor']
                if first_value > 0:
                    growth_rate = ((last_value - first_value) / first_value) * 100
                    growth_rates[grupo] = growth_rate
        
        if growth_rates:
            fastest = max(growth_rates.items(), key=lambda x: x[1])
            st.warning(f"**Crescimento mais rápido:**\n{fastest[0]}: +{fastest[1]:.1f}%")


def _render_impact_details(group_df, financial_df):
    """Render detailed impact analysis"""
    st.subheader("📋 Análise Detalhada do Impacto")
    
    latest_year = financial_df['year'].max()
    year_groups = group_df[group_df['Ano'] == latest_year]
    year_financials = financial_df[financial_df['year'] == latest_year].iloc[0]
    
    revenue = year_financials['revenue']
    
    impact_data = []
    for _, row in year_groups.iterrows():
        impact_data.append({
            'Grupo': row['Grupo'],
            'Valor': row['Valor'],
            '% da Receita': (row['Valor'] / revenue) * 100,
            'Impacto na Margem': -(row['Valor'] / revenue) * 100
        })
    
    impact_df = pd.DataFrame(impact_data).sort_values('% da Receita', ascending=False)
    
    st.dataframe(
        impact_df.style.format({
            'Valor': format_currency,
            '% da Receita': '{:.1f}%',
            'Impacto na Margem': '{:+.1f}pp'
        }),
        use_container_width=True
    )


def _render_fixed_costs_evolution(financial_df, flexible_data, full_width=False):
    """Render evolution of fixed costs items"""
    # Add granularity toggle
    granularity_mode = st.radio(
        "Nível de detalhe:",
        ["Top 10 Custos Fixos", "Top 5 Custos Fixos", "Todos os Custos Fixos"],
        horizontal=True,
        key="fixed_costs_granularity"
    )
    
    # Collect ALL expense data that could be fixed costs
    years = []
    fixed_costs_data = []
    revenue_by_year = {}
    
    # Define which categories typically contain fixed costs
    fixed_cost_categories = [
        'fixed_costs', 
        'administrative_expenses',
        'operational_costs',
        'marketing_expenses',
        'financial_expenses'
    ]
    
    # Also look for items that are typically fixed costs by name
    fixed_cost_keywords = [
        'salário', 'salario', 'folha', 'funcionário', 'funcionario',
        'aluguel', 'rent', 'telefone', 'internet', 'água', 'agua',
        'luz', 'energia', 'seguro', 'contabilidade', 'juridico',
        'software', 'sistema', 'escritório', 'escritorio',
        'depreciação', 'depreciacao', 'manutenção', 'manutencao'
    ]
    
    for year in sorted(financial_df['year'].unique()):
        if year in flexible_data:
            year_data = flexible_data[year]
            
            # Get revenue for percentage calculation
            revenue_value = 0
            if 'revenue' in year_data:
                if isinstance(year_data['revenue'], dict):
                    revenue_value = year_data['revenue'].get('annual', 0)
                else:
                    revenue_value = year_data['revenue'] if year_data['revenue'] else 0
            revenue_by_year[year] = revenue_value
            
            # Check multiple categories for fixed cost items
            for category in fixed_cost_categories:
                if category in year_data and isinstance(year_data[category], dict):
                    cat_data = year_data[category]
                    if 'line_items' in cat_data and isinstance(cat_data['line_items'], dict):
                        # Get all items
                        for item_key, item_data in cat_data['line_items'].items():
                            value = item_data.get('annual', 0)
                            label = item_data.get('label', item_key)
                            
                            # Skip aggregate items and include specific fixed cost items
                            skip_terms = ['CUSTOS FIXOS', 'FIXED COSTS', 'TOTAL FIXED COSTS', 
                                         'CUSTO FIXO + VARIAVEL', 'CUSTOS FIXOS + VARIÁVEIS']
                            
                            if label.upper() not in skip_terms and value > 0:
                                # Add category prefix for clarity if needed
                                if category == 'administrative_expenses':
                                    display_label = f"{label}"
                                else:
                                    display_label = label
                                    
                                fixed_costs_data.append({
                                    'Ano': year,
                                    'Item': display_label,
                                    'Valor': value,
                                    'Percentual': (value / revenue_value * 100) if revenue_value > 0 else 0,
                                    'Categoria': category
                                })
    
    # If no data found, look through ALL categories for items that match fixed cost patterns
    if not fixed_costs_data:
        for year in sorted(financial_df['year'].unique()):
            if year in flexible_data:
                year_data = flexible_data[year]
                revenue_value = revenue_by_year.get(year, 0)
                
                # Check ALL categories in the data
                for category_key, category_data in year_data.items():
                    if isinstance(category_data, dict) and 'line_items' in category_data:
                        for item_key, item_data in category_data['line_items'].items():
                            if isinstance(item_data, dict):
                                value = item_data.get('annual', 0)
                                label = item_data.get('label', item_key)
                                
                                # Check if this item name suggests it's a fixed cost
                                if value > 0 and any(keyword in label.lower() for keyword in fixed_cost_keywords):
                                    fixed_costs_data.append({
                                        'Ano': year,
                                        'Item': label,
                                        'Valor': value,
                                        'Percentual': (value / revenue_value * 100) if revenue_value > 0 else 0,
                                        'Categoria': category_key
                                    })
    
    if fixed_costs_data:
        # Create DataFrame
        df_fixed = pd.DataFrame(fixed_costs_data)
        
        # Debug: Show unique items found
        unique_items = df_fixed['Item'].unique()
        if len(unique_items) == 0:
            st.warning("Nenhum item de custo fixo encontrado nos dados.")
            return
        
        # Debug info
        with st.expander("🔍 Debug: Dados encontrados", expanded=False):
            st.write(f"Total de itens únicos encontrados: {len(unique_items)}")
            st.write("Itens:", list(unique_items)[:10])  # Show first 10 items
            st.write(f"Total de registros: {len(df_fixed)}")
        
        # Determine number of items to show
        if granularity_mode == "Top 10 Custos Fixos":
            num_items = min(10, len(unique_items))
        elif granularity_mode == "Top 5 Custos Fixos":
            num_items = min(5, len(unique_items))
        else:
            num_items = len(unique_items)
        
        # Get top items by average value
        if num_items > 0:
            item_averages = df_fixed.groupby('Item')['Valor'].mean().sort_values(ascending=False)
            top_items = item_averages.head(num_items).index.tolist()
            df_top = df_fixed[df_fixed['Item'].isin(top_items)]
        else:
            df_top = df_fixed
        
        # Toggle for absolute vs percentage view
        view_mode = st.radio(
            "Visualizar como:",
            ["Valores Absolutos", "% da Receita"],
            horizontal=True,
            key="fixed_costs_view_mode"
        )
        
        # Create line chart
        fig = go.Figure()
        
        if view_mode == "Valores Absolutos":
            for idx, item in enumerate(top_items):
                item_data = df_top[df_top['Item'] == item].sort_values('Ano')
                color = CHART_PALETTES['costs'][idx % len(CHART_PALETTES['costs'])]
                fig.add_trace(go.Scatter(
                    x=item_data['Ano'],
                    y=item_data['Valor'],
                    mode='lines+markers',
                    name=item[:30] + '...' if len(item) > 30 else item,
                    line=dict(width=3, color=color),
                    marker=dict(size=8, color=color),
                    customdata=item_data[['Valor', 'Percentual']],
                    hovertemplate='<b>%{x}</b><br>' +
                                 f'{item}: R$ %{{customdata[0]:,.0f}}<br>' +
                                 '% da Receita: %{customdata[1]:.1f}%<br>' +
                                 '<extra></extra>'
                ))
            
            title_text = f"{granularity_mode}" if granularity_mode != "Todos os Custos Fixos" else "Todos os Custos Fixos Detalhados"
            fig.update_layout(
                title=title_text,
                xaxis_title="Ano",
                yaxis_title="Valor (R$)",
                height=600 if full_width and num_items > 5 else 500 if full_width else 400 if num_items > 5 else 300,
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02,
                    font=dict(size=11 if num_items > 5 else 12)
                ),
                margin=dict(
                    r=250 if num_items > 5 else 180,
                    t=60 if full_width else 50,
                    b=60 if full_width else 50
                ),
                font=dict(size=14 if full_width else 12),
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.8)",
                    font_size=13,
                    font_family="Arial",
                    font_color="white",
                    bordercolor="rgba(255, 255, 255, 0.3)"
                )
            )
        else:
            for idx, item in enumerate(top_items):
                item_data = df_top[df_top['Item'] == item].sort_values('Ano')
                color = CHART_PALETTES['costs'][idx % len(CHART_PALETTES['costs'])]
                fig.add_trace(go.Scatter(
                    x=item_data['Ano'],
                    y=item_data['Percentual'],
                    mode='lines+markers',
                    name=item[:30] + '...' if len(item) > 30 else item,
                    line=dict(width=3, color=color),
                    marker=dict(size=8, color=color),
                    text=[f"{v:.1f}%" for v in item_data['Percentual']],
                    textposition='top center'
                ))
            
            title_text = f"{granularity_mode} (% da Receita)" if granularity_mode != "Todos os Custos Fixos" else "Todos os Custos Fixos (% da Receita)"
            fig.update_layout(
                title=title_text,
                xaxis_title="Ano",
                yaxis_title="% da Receita",
                height=600 if full_width and num_items > 5 else 500 if full_width else 400 if num_items > 5 else 300,
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02,
                    font=dict(size=11 if num_items > 5 else 12)
                ),
                margin=dict(
                    r=250 if num_items > 5 else 180,
                    t=60 if full_width else 50,
                    b=60 if full_width else 50
                ),
                font=dict(size=14 if full_width else 12),
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.8)",
                    font_size=13,
                    font_family="Arial",
                    font_color="white",
                    bordercolor="rgba(255, 255, 255, 0.3)"
                )
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show fixed costs insights
        if st.checkbox("Ver análise detalhada", key="show_fixed_costs_analysis"):
            _show_fixed_costs_analysis(df_fixed, revenue_by_year)
    else:
        # Try to show data from the financial_df as fallback
        if 'fixed_costs' in financial_df.columns and financial_df['fixed_costs'].sum() > 0:
            st.info("Mostrando custos fixos agregados. Dados detalhados não disponíveis.")
            
            # Create simple line chart from aggregated data
            fig = go.Figure()
            
            yearly_data = financial_df.groupby('year')['fixed_costs'].sum().reset_index()
            fig.add_trace(go.Scatter(
                x=yearly_data['year'],
                y=yearly_data['fixed_costs'],
                mode='lines+markers',
                name='Custos Fixos Totais',
                line=dict(color=COLORS['fixed_costs'], width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Evolução dos Custos Fixos Totais",
                xaxis_title="Ano",
                yaxis_title="Valor (R$)",
                height=400,
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.8)",
                    font_size=13,
                    font_family="Arial",
                    font_color="white",
                    bordercolor="rgba(255, 255, 255, 0.3)"
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados de custos fixos não disponíveis")


def _render_variable_costs_evolution(financial_df, flexible_data, full_width=False):
    """Render evolution of commission and taxes (Simples Nacional)"""
    # Collect data
    evolution_data = []
    
    for year in sorted(financial_df['year'].unique()):
        if year in flexible_data:
            year_data = flexible_data[year]
            
            # Get revenue
            revenue_value = 0
            if 'revenue' in year_data:
                if isinstance(year_data['revenue'], dict):
                    revenue_value = year_data['revenue'].get('annual', 0)
                else:
                    revenue_value = year_data['revenue'] if year_data['revenue'] else 0
            
            # Get commission value
            commission_value = 0
            if 'commissions' in year_data and isinstance(year_data['commissions'], dict):
                commission_value = year_data['commissions'].get('annual', 0)
            
            # Get Simples Nacional (taxes) value
            tax_value = 0
            if 'taxes' in year_data and isinstance(year_data['taxes'], dict):
                tax_data = year_data['taxes']
                if 'line_items' in tax_data and isinstance(tax_data['line_items'], dict):
                    # Look for Simples Nacional
                    for item_key, item_data in tax_data['line_items'].items():
                        if 'simples' in item_data.get('label', '').lower():
                            tax_value += item_data.get('annual', 0)
                
                # If not found in line items, use total
                if tax_value == 0:
                    tax_value = tax_data.get('annual', 0)
            
            evolution_data.append({
                'Ano': year,
                'Receita': revenue_value,
                'Repasse de Comissão': commission_value,
                'Simples Nacional': tax_value,
                'Comissão %': (commission_value / revenue_value * 100) if revenue_value > 0 else 0,
                'Impostos %': (tax_value / revenue_value * 100) if revenue_value > 0 else 0
            })
    
    if evolution_data:
        df_var = pd.DataFrame(evolution_data)
        
        # Toggle for absolute vs percentage view
        view_mode = st.radio(
            "Visualizar como:",
            ["Valores Absolutos", "Percentual da Receita"],
            horizontal=True,
            key="var_costs_view_mode"
        )
        
        fig = go.Figure()
        
        if view_mode == "Valores Absolutos":
            # Add revenue line
            fig.add_trace(go.Scatter(
                x=df_var['Ano'],
                y=df_var['Receita'],
                mode='lines+markers',
                name='Receita',
                line=dict(color=COLORS['revenue'], width=3, dash='dash'),
                marker=dict(size=8),
                customdata=df_var[['Receita']],
                hovertemplate='<b>%{x}</b><br>' +
                             'Receita: %{customdata[0]:,.0f}<br>' +
                             '<extra></extra>'
            ))
            
            # Add commission line
            fig.add_trace(go.Scatter(
                x=df_var['Ano'],
                y=df_var['Repasse de Comissão'],
                mode='lines+markers',
                name='Repasse de Comissão',
                line=dict(color=COLORS['commissions'], width=3),
                marker=dict(size=8),
                customdata=df_var[['Repasse de Comissão', 'Comissão %']],
                hovertemplate='<b>%{x}</b><br>' +
                             'Repasse de Comissão: R$ %{customdata[0]:,.0f}<br>' +
                             '% da Receita: %{customdata[1]:.1f}%<br>' +
                             '<extra></extra>'
            ))
            
            # Add taxes line
            fig.add_trace(go.Scatter(
                x=df_var['Ano'],
                y=df_var['Simples Nacional'],
                mode='lines+markers',
                name='Simples Nacional',
                line=dict(color=COLORS['taxes'], width=3),
                marker=dict(size=8),
                customdata=df_var[['Simples Nacional', 'Impostos %']],
                hovertemplate='<b>%{x}</b><br>' +
                             'Simples Nacional: R$ %{customdata[0]:,.0f}<br>' +
                             '% da Receita: %{customdata[1]:.1f}%<br>' +
                             '<extra></extra>'
            ))
            
            fig.update_layout(
                title="Custos Variáveis vs Receita",
                xaxis_title="Ano",
                yaxis_title="Valor (R$)",
                height=500 if full_width else 300,
                hovermode='x unified',
                showlegend=True,
                font=dict(size=14 if full_width else 12),
                margin=dict(t=50, b=50, l=70, r=150) if full_width else None,
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.8)",
                    font_size=13,
                    font_family="Arial",
                    font_color="white",
                    bordercolor="rgba(255, 255, 255, 0.3)"
                )
            )
        else:
            # Percentage view
            fig.add_trace(go.Scatter(
                x=df_var['Ano'],
                y=df_var['Comissão %'],
                mode='lines+markers',
                name='Repasse de Comissão (%)',
                line=dict(color=COLORS['commissions'], width=3),
                marker=dict(size=8),
                text=[f"{v:.1f}%" for v in df_var['Comissão %']],
                textposition='top center'
            ))
            
            fig.add_trace(go.Scatter(
                x=df_var['Ano'],
                y=df_var['Impostos %'],
                mode='lines+markers',
                name='Simples Nacional (%)',
                line=dict(color=COLORS['taxes'], width=3),
                marker=dict(size=8),
                text=[f"{v:.1f}%" for v in df_var['Impostos %']],
                textposition='bottom center'
            ))
            
            fig.update_layout(
                title="Custos Variáveis como % da Receita",
                xaxis_title="Ano",
                yaxis_title="% da Receita",
                height=500 if full_width else 300,
                hovermode='x unified',
                showlegend=True,
                font=dict(size=14 if full_width else 12),
                margin=dict(t=50, b=50, l=70, r=150) if full_width else None,
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.8)",
                    font_size=13,
                    font_family="Arial",
                    font_color="white",
                    bordercolor="rgba(255, 255, 255, 0.3)"
                )
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_revenue = df_var['Receita'].mean()
            st.metric("Receita Média", format_currency(avg_revenue))
        with col2:
            avg_commission_pct = df_var['Comissão %'].mean()
            st.metric("Comissão Média", f"{avg_commission_pct:.1f}% da receita")
        with col3:
            avg_tax_pct = df_var['Impostos %'].mean()
            st.metric("Impostos Médios", f"{avg_tax_pct:.1f}% da receita")
    else:
        st.info("Dados de custos variáveis não disponíveis")


def _render_top_expenses_evolution(financial_df, flexible_data, full_width=False):
    """Render evolution of top expenses across all categories"""
    if full_width:
        st.markdown("### 💰 Maiores Despesas")
    else:
        st.markdown("### 💰 Maiores Despesas")
    
    # Add granularity toggle
    granularity_mode = st.radio(
        "Nível de detalhe:",
        ["Despesas Específicas", "Categorias Principais"],
        horizontal=True,
        key="expense_granularity_mode"
    )
    
    # Collect all expenses
    all_expenses = []
    revenue_by_year = {}
    
    for year in sorted(financial_df['year'].unique()):
        if year in flexible_data:
            year_data = flexible_data[year]
            
            # Get revenue for percentage calculation
            revenue_value = 0
            if 'revenue' in year_data:
                if isinstance(year_data['revenue'], dict):
                    revenue_value = year_data['revenue'].get('annual', 0)
                else:
                    revenue_value = year_data['revenue'] if year_data['revenue'] else 0
            revenue_by_year[year] = revenue_value
            
            # Categories to check
            categories = [
                'variable_costs', 'fixed_costs', 'taxes', 'commissions',
                'administrative_expenses', 'marketing_expenses', 
                'financial_expenses', 'non_operational_costs'
            ]
            
            for category in categories:
                if category in year_data and isinstance(year_data[category], dict):
                    cat_data = year_data[category]
                    
                    if granularity_mode == "Categorias Principais":
                        # Add category total only
                        total_value = cat_data.get('annual', 0)
                        if total_value > 0:
                            all_expenses.append({
                                'Ano': year,
                                'Despesa': category.replace('_', ' ').title(),
                                'Valor': total_value,
                                'Percentual': (total_value / revenue_value * 100) if revenue_value > 0 else 0,
                                'Tipo': 'Total',
                                'Categoria': category
                            })
                    else:
                        # Add individual line items for specific expenses mode
                        if 'line_items' in cat_data and isinstance(cat_data['line_items'], dict):
                            for item_key, item_data in cat_data['line_items'].items():
                                value = item_data.get('annual', 0)
                                if value > 0:
                                    all_expenses.append({
                                        'Ano': year,
                                        'Despesa': item_data.get('label', item_key),
                                        'Valor': value,
                                        'Percentual': (value / revenue_value * 100) if revenue_value > 0 else 0,
                                        'Tipo': 'Item',
                                        'Categoria': category
                                    })
    
    if all_expenses:
        df_expenses = pd.DataFrame(all_expenses)
        
        # Filter out aggregate totals in specific expenses mode
        if granularity_mode == "Despesas Específicas":
            # Exclude items that are aggregate totals
            exclude_terms = ['CUSTOS FIXOS', 'CUSTOS VARIÁVEIS', 'CUSTOS VARIAVEIS', 
                           'Fixed Costs', 'Variable Costs', 'Taxes', 'Commissions',
                           'Administrative Expenses', 'Marketing Expenses', 
                           'Financial Expenses', 'Non Operational Costs',
                           'Custo fixo + variavel', 'CUSTO FIXO + VARIAVEL',
                           'CUSTOS FIXOS + VARIÁVEIS', 'CUSTOS VARIÁVEIS + FIXOS',
                           'CUSTOS NÃO OPERACIONAIS', 'CUSTOS NAO OPERACIONAIS']
            df_expenses = df_expenses[~df_expenses['Despesa'].isin(exclude_terms)]
        
        # Get top expenses by average value (10 for specific items, 5 for categories)
        num_items = 10 if granularity_mode == "Despesas Específicas" else 5
        top_expenses = df_expenses.groupby('Despesa')['Valor'].mean().nlargest(num_items).index.tolist()
        
        # Toggle for absolute vs percentage view
        view_mode = st.radio(
            "Visualizar como:",
            ["Valores Absolutos", "% da Receita"],
            horizontal=True,
            key="top_expenses_view_mode"
        )
        
        # Create stacked bar chart by year
        fig = go.Figure()
        
        if view_mode == "Valores Absolutos":
            for idx, expense in enumerate(top_expenses):
                expense_data = df_expenses[df_expenses['Despesa'] == expense].groupby('Ano').agg({
                    'Valor': 'sum'
                }).reset_index()
                
                color = CHART_PALETTES['main'][idx % len(CHART_PALETTES['main'])]
                fig.add_trace(go.Bar(
                    x=expense_data['Ano'],
                    y=expense_data['Valor'],
                    name=expense[:40] + '...' if len(expense) > 40 else expense,
                    text=[format_currency(v) for v in expense_data['Valor']],
                    textposition='auto',
                    marker_color=color,
                    hovertemplate='<b>%{x}</b><br>' +
                                 f'{expense}: %{{y:,.0f}}<br>' +
                                 '<extra></extra>'
                ))
            
            title_text = f"Top {num_items} Maiores Despesas" + (" Específicas" if granularity_mode == "Despesas Específicas" else "")
            fig.update_layout(
                title=title_text,
                xaxis_title="Ano",
                yaxis_title="Valor (R$)",
                barmode='stack',
                height=600 if full_width and granularity_mode == "Despesas Específicas" else 500 if full_width else 400 if granularity_mode == "Despesas Específicas" else 300,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02,
                    font=dict(size=12 if full_width else 11 if granularity_mode == "Despesas Específicas" else 12)
                ),
                margin=dict(
                    r=250 if full_width and granularity_mode == "Despesas Específicas" else 220 if granularity_mode == "Despesas Específicas" else 180,
                    t=60 if full_width else 50,
                    b=60 if full_width else 50
                ),
                font=dict(size=14 if full_width else 12),
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.8)",
                    font_size=13,
                    font_family="Arial",
                    font_color="white",
                    bordercolor="rgba(255, 255, 255, 0.3)"
                )
            )
        else:
            for idx, expense in enumerate(top_expenses):
                expense_data = df_expenses[df_expenses['Despesa'] == expense].groupby('Ano').agg({
                    'Percentual': 'sum'
                }).reset_index()
                
                color = CHART_PALETTES['main'][idx % len(CHART_PALETTES['main'])]
                fig.add_trace(go.Bar(
                    x=expense_data['Ano'],
                    y=expense_data['Percentual'],
                    name=expense[:40] + '...' if len(expense) > 40 else expense,
                    text=[f"{v:.1f}%" for v in expense_data['Percentual']],
                    textposition='auto',
                    marker_color=color,
                    hovertemplate='<b>%{x}</b><br>' +
                                 f'{expense}: %{{y:.1f}}%<br>' +
                                 '<extra></extra>'
                ))
            
            title_text = f"Top {num_items} Maiores Despesas (% da Receita)" + (" Específicas" if granularity_mode == "Despesas Específicas" else "")
            fig.update_layout(
                title=title_text,
                xaxis_title="Ano",
                yaxis_title="% da Receita",
                barmode='stack',
                height=600 if full_width and granularity_mode == "Despesas Específicas" else 500 if full_width else 400 if granularity_mode == "Despesas Específicas" else 300,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02,
                    font=dict(size=12 if full_width else 11 if granularity_mode == "Despesas Específicas" else 12)
                ),
                margin=dict(
                    r=250 if full_width and granularity_mode == "Despesas Específicas" else 220 if granularity_mode == "Despesas Específicas" else 180,
                    t=60 if full_width else 50,
                    b=60 if full_width else 50
                ),
                font=dict(size=14 if full_width else 12),
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.8)",
                    font_size=13,
                    font_family="Arial",
                    font_color="white",
                    bordercolor="rgba(255, 255, 255, 0.3)"
                )
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add visual separator
        st.markdown("---")
        
        # Show year breakdown selector with info box
        st.info("💡 **Dica**: Selecione um ano abaixo para ver todas as despesas em detalhe, incluindo as menores que são difíceis de visualizar no gráfico acima.")
        
        st.markdown("### 📅 Ver Detalhes por Ano")
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            available_years = sorted(df_expenses['Ano'].unique())
            selected_year = st.selectbox(
                "Selecione um ano:",
                [""] + [str(year) for year in available_years],
                key="year_detail_selector",
                help="Escolha um ano para ver o detalhamento completo de todas as despesas"
            )
        
        if selected_year:
            _show_year_expense_breakdown(df_expenses, int(selected_year), revenue_by_year, granularity_mode, flexible_data)
        
        # Show expense details selector
        if granularity_mode == "Despesas Específicas":
            st.markdown("#### 🔍 Ver Detalhes de Despesa Específica")
            
            # Create a selectbox with expense names
            all_expense_names = sorted(df_expenses['Despesa'].unique())
            selected_expense = st.selectbox(
                "Selecione uma despesa para ver sua evolução:",
                [""] + all_expense_names,
                key="expense_detail_selector"
            )
            
            if selected_expense:
                _show_expense_details(df_expenses, selected_expense, revenue_by_year)
        
        # Show total expenses summary
        if st.checkbox("Ver resumo total", key="show_expense_summary"):
            years = sorted(df_expenses['Ano'].unique())
            summary_data = []
            for year in years:
                year_expenses = df_expenses[df_expenses['Ano'] == year]['Valor'].sum()
                year_revenue = revenue_by_year.get(year, 0)
                summary_data.append({
                    'Ano': year,
                    'Total Despesas': year_expenses,
                    '% da Receita': (year_expenses / year_revenue * 100) if year_revenue > 0 else 0
                })
            
            summary_df = pd.DataFrame(summary_data)
            col1, col2 = st.columns(2)
            with col1:
                avg_expenses = summary_df['Total Despesas'].mean()
                st.metric("Despesas Médias", format_currency(avg_expenses))
            with col2:
                avg_pct = summary_df['% da Receita'].mean()
                st.metric("% Médio da Receita", f"{avg_pct:.1f}%")
    else:
        st.info("Dados de despesas não disponíveis")


def _show_fixed_costs_analysis(df_fixed, revenue_by_year):
    """Show detailed analysis of fixed costs"""
    st.subheader("📊 Análise Detalhada dos Custos Fixos")
    
    # Get latest year data
    latest_year = df_fixed['Ano'].max()
    latest_data = df_fixed[df_fixed['Ano'] == latest_year]
    
    # Calculate metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_fixed = latest_data['Valor'].sum()
        st.metric("Total Custos Fixos", format_currency(total_fixed))
    
    with col2:
        revenue = revenue_by_year.get(latest_year, 0)
        if revenue > 0:
            fixed_pct = (total_fixed / revenue) * 100
            st.metric("% da Receita", f"{fixed_pct:.1f}%")
    
    with col3:
        # Year-over-year growth
        if latest_year - 1 in df_fixed['Ano'].values:
            prev_year_total = df_fixed[df_fixed['Ano'] == latest_year - 1]['Valor'].sum()
            growth = ((total_fixed - prev_year_total) / prev_year_total) * 100
            st.metric("Crescimento YoY", f"{growth:+.1f}%")
    
    # Show breakdown table
    st.markdown("#### Composição dos Custos Fixos")
    breakdown_data = []
    for _, row in latest_data.iterrows():
        breakdown_data.append({
            'Item': row['Item'],
            'Valor': row['Valor'],
            '% do Total': (row['Valor'] / total_fixed * 100) if total_fixed > 0 else 0,
            '% da Receita': row['Percentual']
        })
    
    breakdown_df = pd.DataFrame(breakdown_data).sort_values('Valor', ascending=False)
    
    st.dataframe(
        breakdown_df.style.format({
            'Valor': format_currency,
            '% do Total': '{:.1f}%',
            '% da Receita': '{:.1f}%'
        }),
        use_container_width=True
    )


def _show_year_expense_breakdown(df_expenses, selected_year, revenue_by_year, granularity_mode, flexible_data):
    """Show detailed breakdown of all expenses for a specific year"""
    year_data = df_expenses[df_expenses['Ano'] == selected_year]
    
    if not year_data.empty:
        # Get revenue for the year
        year_revenue = revenue_by_year.get(selected_year, 0)
        
        # Show year summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_expenses = year_data['Valor'].sum()
            st.metric(f"Total de Despesas em {selected_year}", format_currency(total_expenses))
        
        with col2:
            if year_revenue > 0:
                expense_pct = (total_expenses / year_revenue) * 100
                st.metric("% da Receita", f"{expense_pct:.1f}%")
        
        with col3:
            num_expenses = len(year_data)
            st.metric("Número de Despesas", num_expenses)
        
        # Create two columns for visualization
        col_chart, col_table = st.columns([3, 2])
        
        with col_chart:
            # Create a treemap for better visualization of all expenses
            import plotly.express as px
            
            # Prepare data for treemap with proper hierarchy
            treemap_data = []
            
            # If in granular mode, show individual items
            if granularity_mode == "Despesas Específicas":
                for _, row in year_data.iterrows():
                    treemap_data.append({
                        'Despesa': row['Despesa'][:50] + '...' if len(row['Despesa']) > 50 else row['Despesa'],
                        'Categoria': row['Categoria'].replace('_', ' ').title(),
                        'Valor': row['Valor'],
                        'Percentual': row['Percentual'],
                        'ValorFormatado': format_currency(row['Valor'])
                    })
            else:
                # In category mode, show ALL items from flexible_data for better drill-down
                if selected_year in flexible_data:
                    year_flex_data = flexible_data[selected_year]
                    
                    # Process all categories
                    for category_key, category_data in year_flex_data.items():
                        if isinstance(category_data, dict) and 'line_items' in category_data:
                            cat_display_name = category_key.replace('_', ' ').title()
                            
                            # Add all line items for this category
                            for item_key, item_data in category_data['line_items'].items():
                                if isinstance(item_data, dict):
                                    value = item_data.get('annual', 0)
                                    if value > 0:
                                        label = item_data.get('label', item_key)
                                        
                                        # Check if this item has sub_items (like commission providers)
                                        if 'sub_items' in item_data and item_data['sub_items']:
                                            # Add the parent item
                                            parent_label = label[:50] + '...' if len(label) > 50 else label
                                            
                                            # Add each sub-item as a separate entry
                                            for sub_key, sub_data in item_data['sub_items'].items():
                                                if isinstance(sub_data, dict):
                                                    sub_value = sub_data.get('annual', 0)
                                                    if sub_value > 0:
                                                        sub_label = sub_data.get('label', sub_key)
                                                        treemap_data.append({
                                                            'Despesa': sub_label[:40] + '...' if len(sub_label) > 40 else sub_label,
                                                            'Categoria': cat_display_name,
                                                            'SubCategoria': parent_label,
                                                            'Valor': sub_value,
                                                            'Percentual': (sub_value / year_revenue * 100) if year_revenue > 0 else 0,
                                                            'ValorFormatado': format_currency(sub_value)
                                                        })
                                        else:
                                            # Regular item without sub-items
                                            treemap_data.append({
                                                'Despesa': label[:50] + '...' if len(label) > 50 else label,
                                                'Categoria': cat_display_name,
                                                'SubCategoria': cat_display_name,  # Same as category for items without sub-items
                                                'Valor': value,
                                                'Percentual': (value / year_revenue * 100) if year_revenue > 0 else 0,
                                                'ValorFormatado': format_currency(value)
                                            })
                
                # If no detailed data, fallback to aggregated view
                if not treemap_data:
                    category_totals = year_data.groupby('Categoria').agg({
                        'Valor': 'sum',
                        'Percentual': 'sum'
                    }).reset_index()
                    
                    for _, row in category_totals.iterrows():
                        cat_name = row['Categoria'].replace('_', ' ').title()
                        treemap_data.append({
                            'Despesa': cat_name,
                            'Categoria': 'Total',
                            'Valor': row['Valor'],
                            'Percentual': row['Percentual'],
                            'ValorFormatado': format_currency(row['Valor'])
                        })
            
            treemap_df = pd.DataFrame(treemap_data)
            
            # Create treemap with click instructions
            # Determine path based on whether we have sub-categories
            if 'SubCategoria' in treemap_df.columns and treemap_df['SubCategoria'].nunique() > treemap_df['Categoria'].nunique():
                # We have sub-items, use 3-level hierarchy
                path_cols = ['Categoria', 'SubCategoria', 'Despesa']
                max_depth = 3
            else:
                # No sub-items, use 2-level hierarchy
                path_cols = ['Categoria', 'Despesa']
                max_depth = 2
                
            fig = px.treemap(
                treemap_df,
                path=path_cols,
                values='Valor',
                title=f"Composição das Despesas - {selected_year}<br><sub>💡 Clique em uma categoria para dar zoom e ver detalhes</sub>",
                hover_data={
                    'ValorFormatado': True,
                    'Percentual': ':.2f',
                    'Valor': False
                },
                color='Valor',
                color_continuous_scale='RdYlBu_r',
                maxdepth=max_depth
            )
            
            fig.update_traces(
                texttemplate='<b>%{label}</b><br>%{customdata[0]}',
                textposition="middle center",
                hovertemplate='<b>%{label}</b><br>' +
                             'Valor: %{customdata[0]}<br>' +
                             '% da Receita: %{customdata[1]:.2f}%<br>' +
                             '<extra></extra>'
            )
            
            fig.update_layout(
                height=600,
                margin=dict(t=50, l=0, r=0, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col_table:
            # Show top expenses table
            st.markdown(f"##### Top 15 Despesas de {selected_year}")
            
            # Sort by value and get top 15
            top_expenses = year_data.nlargest(15, 'Valor')[['Despesa', 'Valor', 'Percentual']]
            top_expenses['Valor Formatado'] = top_expenses['Valor'].apply(format_currency)
            top_expenses['% Receita'] = top_expenses['Percentual'].apply(lambda x: f"{x:.2f}%")
            
            # Display table
            display_df = top_expenses[['Despesa', 'Valor Formatado', '% Receita']].reset_index(drop=True)
            display_df.index = display_df.index + 1
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=500
            )
        
        # Show all expenses in expandable section
        with st.expander(f"Ver todas as {num_expenses} despesas de {selected_year}"):
            all_expenses = year_data.sort_values('Valor', ascending=False)[['Despesa', 'Valor', 'Percentual', 'Categoria']]
            all_expenses['Valor Formatado'] = all_expenses['Valor'].apply(format_currency)
            all_expenses['% Receita'] = all_expenses['Percentual'].apply(lambda x: f"{x:.2f}%")
            all_expenses['Categoria'] = all_expenses['Categoria'].apply(lambda x: x.replace('_', ' ').title())
            
            st.dataframe(
                all_expenses[['Despesa', 'Valor Formatado', '% Receita', 'Categoria']].reset_index(drop=True),
                use_container_width=True
            )
            
            # Option to export
            csv = all_expenses[['Despesa', 'Valor', 'Percentual', 'Categoria']].to_csv(index=False)
            st.download_button(
                label=f"📥 Baixar despesas de {selected_year} (CSV)",
                data=csv,
                file_name=f"despesas_{selected_year}.csv",
                mime="text/csv"
            )


def _show_expense_details(df_expenses, selected_expense, revenue_by_year):
    """Show detailed information about a selected expense"""
    expense_data = df_expenses[df_expenses['Despesa'] == selected_expense]
    
    if not expense_data.empty:
        # Get category info
        categories = expense_data['Categoria'].unique()
        category_display = ", ".join([cat.replace('_', ' ').title() for cat in categories])
        
        st.info(f"**Categoria:** {category_display}")
        
        # Show metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_value = expense_data['Valor'].sum()
            st.metric("Valor Total", format_currency(total_value))
        
        with col2:
            avg_value = expense_data['Valor'].mean()
            st.metric("Valor Médio Anual", format_currency(avg_value))
        
        with col3:
            # Calculate average percentage of revenue
            avg_pct = expense_data['Percentual'].mean()
            st.metric("% Médio da Receita", f"{avg_pct:.2f}%")
        
        with col4:
            # Year-over-year growth
            if len(expense_data) > 1:
                years_sorted = expense_data.sort_values('Ano')
                first_value = years_sorted.iloc[0]['Valor']
                last_value = years_sorted.iloc[-1]['Valor']
                if first_value > 0:
                    growth = ((last_value - first_value) / first_value) * 100
                    st.metric("Crescimento Total", f"{growth:+.1f}%")
        
        # Show yearly breakdown
        st.markdown("##### Evolução Anual")
        yearly_data = expense_data[['Ano', 'Valor', 'Percentual']].sort_values('Ano')
        yearly_data['Valor Formatado'] = yearly_data['Valor'].apply(format_currency)
        yearly_data['% da Receita'] = yearly_data['Percentual'].apply(lambda x: f"{x:.2f}%")
        
        # Add year-over-year change
        yearly_data['Variação YoY'] = yearly_data['Valor'].pct_change() * 100
        yearly_data['Variação YoY'] = yearly_data['Variação YoY'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
        
        st.dataframe(
            yearly_data[['Ano', 'Valor Formatado', '% da Receita', 'Variação YoY']].set_index('Ano'),
            use_container_width=True
        )
        
        # Create a mini chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=yearly_data['Ano'],
            y=yearly_data['Valor'],
            mode='lines+markers',
            name=selected_expense,
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            text=yearly_data['Valor Formatado'],
            textposition='top center'
        ))
        
        fig.update_layout(
            title=f"Evolução de {selected_expense}",
            xaxis_title="Ano",
            yaxis_title="Valor (R$)",
            height=300,
            showlegend=False,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)


def _show_variable_costs_percentage(df_var, financial_df):
    """Show variable costs as percentage of revenue"""
    # Merge with revenue data
    revenue_by_year = financial_df[['year', 'revenue']].set_index('year')
    
    percentages = []
    for _, row in df_var.iterrows():
        year = row['Ano']
        if year in revenue_by_year.index:
            revenue = revenue_by_year.loc[year, 'revenue']
            if revenue > 0:
                percentages.append({
                    'Ano': year,
                    'Comissão (%)': (row['Repasse de Comissão'] / revenue) * 100,
                    'Impostos (%)': (row['Simples Nacional'] / revenue) * 100
                })
    
    if percentages:
        df_pct = pd.DataFrame(percentages)
        
        col1, col2 = st.columns(2)
        with col1:
            avg_commission = df_pct['Comissão (%)'].mean()
            st.metric("Comissão Média", f"{avg_commission:.1f}% da receita")
        
        with col2:
            avg_tax = df_pct['Impostos (%)'].mean()
            st.metric("Impostos Médios", f"{avg_tax:.1f}% da receita")