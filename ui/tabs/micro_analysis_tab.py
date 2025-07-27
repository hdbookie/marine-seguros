"""Micro Analysis Tab - Variable + Fixed Costs Sankey Visualization"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils import format_currency


def render_micro_analysis_tab(flexible_data):
    """Render the micro analysis tab with Sankey flow diagram"""
    
    st.header("🔬 Análise Micro - Custos Variáveis e Fixos")
    
    if not flexible_data:
        st.info("📊 Carregue dados usando o extrator flexível para acessar a análise micro.")
        return
    
    # Render filters (same as macro dashboard)
    selected_years, view_type, selected_months = render_filters_section(flexible_data)
    
    # Filter and prepare data based on selections
    if view_type == "Anual":
        render_annual_sankey(flexible_data, selected_years)
    elif view_type == "Mensal":
        render_monthly_analysis(flexible_data, selected_years, selected_months)
    elif view_type == "Trimestral":
        render_quarterly_analysis(flexible_data, selected_years)
    elif view_type == "Semestral":
        render_semester_analysis(flexible_data, selected_years)


def render_filters_section(flexible_data):
    """Render the filters section (matching macro dashboard style)"""
    st.markdown("### 🎛️ Filtros")
    
    # Get available years
    available_years = sorted([str(y) for y in flexible_data.keys()])
    
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
    
    with col_filter1:
        view_type = st.selectbox(
            "Visualização",
            ["Anual", "Mensal", "Trimestral", "Semestral"],
            key="micro_view_type"
        )
    
    with col_filter2:
        if view_type != "Anual":
            default_years = available_years[-3:] if len(available_years) >= 3 else available_years
            selected_years = st.multiselect(
                "Anos",
                available_years,
                default=default_years,
                key="micro_selected_years"
            )
        else:
            selected_years = available_years
    
    with col_filter3:
        if view_type == "Mensal":
            month_names = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
                          "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
            selected_months = st.multiselect(
                "Meses",
                month_names,
                default=month_names,
                key="micro_selected_months"
            )
        else:
            selected_months = []
    
    with col_filter4:
        # Quick filters
        quick_filter = st.selectbox(
            "Filtro Rápido",
            ["Todos", "Últimos 3 Anos", "Últimos 5 Anos", "Ano Atual"],
            key="micro_quick_filter"
        )
        
        # Apply quick filter
        if quick_filter == "Últimos 3 Anos":
            selected_years = available_years[-3:] if len(available_years) >= 3 else available_years
        elif quick_filter == "Últimos 5 Anos":
            selected_years = available_years[-5:] if len(available_years) >= 5 else available_years
        elif quick_filter == "Ano Atual":
            current_year = str(datetime.now().year)
            if current_year in available_years:
                selected_years = [current_year]
            else:
                selected_years = [available_years[-1]]
    
    return selected_years, view_type, selected_months


def render_annual_sankey(flexible_data, selected_years):
    """Render annual Sankey diagram for selected years"""
    
    
    # Process data for selected years
    all_fixed_items = {}
    all_variable_items = {}
    
    for year in selected_years:
        # Convert year to int if flexible_data uses int keys
        year_key = int(year) if year.isdigit() else year
        if year_key not in flexible_data:
            continue
            
        year_data = flexible_data[year_key]
        line_items = year_data.get('line_items', {})
        
        # Debug: Show categories and totals
        year_fixed_total = 0
        year_variable_total = 0
        other_categories = {}
        
        for item_key, item_data in line_items.items():
            cat = item_data.get('category', 'unknown')
            annual_val = item_data.get('annual', 0)
            
            if cat == 'variable_costs':
                year_variable_total += annual_val
            elif cat in ['fixed_costs', 'admin_expenses', 'operational_expenses', 
                        'marketing_expenses', 'financial_expenses', 'tax_expenses', 
                        'other_expenses', 'other_costs']:
                year_fixed_total += annual_val
            else:
                if cat not in other_categories:
                    other_categories[cat] = 0
                other_categories[cat] += annual_val
        
        
        for item_key, item_data in line_items.items():
            category = item_data.get('category', '')
            label = item_data.get('label', '')
            annual_value = item_data.get('annual', 0)
            is_subtotal = item_data.get('is_subtotal', False)
            
            # Skip calculated items, subtotals, and revenue
            if is_subtotal or category in ['calculated_results', 'revenue', 'margins', 'results']:
                continue
            
            # Variable costs go to variable category
            if category == 'variable_costs':
                if label not in all_variable_items:
                    all_variable_items[label] = 0
                all_variable_items[label] += annual_value
            # All other cost/expense categories go to fixed costs
            elif category in ['fixed_costs', 'admin_expenses', 'operational_expenses', 
                            'marketing_expenses', 'financial_expenses', 'tax_expenses', 
                            'other_expenses', 'other_costs']:
                if label not in all_fixed_items:
                    all_fixed_items[label] = 0
                all_fixed_items[label] += annual_value
    
    # Calculate totals
    fixed_total = sum(all_fixed_items.values())
    variable_total = sum(all_variable_items.values())
    total = fixed_total + variable_total
    
    if total == 0:
        st.warning("Nenhum custo encontrado para os anos selecionados.")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Geral", format_currency(total))
    with col2:
        st.metric("🔧 Custos Fixos", format_currency(fixed_total), f"{fixed_total/total*100:.1f}%")
    with col3:
        st.metric("📊 Custos Variáveis", format_currency(variable_total), f"{variable_total/total*100:.1f}%")
    
    # Create Sankey diagram
    fig = create_sankey_diagram(all_fixed_items, all_variable_items, fixed_total, variable_total)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    with st.expander("📊 Ver dados detalhados"):
        render_detailed_tables(all_fixed_items, all_variable_items)


def create_sankey_diagram(fixed_items, variable_items, fixed_total, variable_total):
    """Create Sankey flow diagram"""
    
    labels = []
    sources = []
    targets = []
    values = []
    colors = []
    
    # Node indices
    node_index = {}
    current_index = 0
    
    # Add root node
    labels.append("Total Custos")
    node_index["Total Custos"] = current_index
    colors.append("#1F2937")  # Dark gray
    current_index += 1
    
    # Add category nodes
    labels.append("Custos Fixos")
    node_index["Custos Fixos"] = current_index
    colors.append("#3B82F6")  # Blue
    current_index += 1
    
    labels.append("Custos Variáveis")
    node_index["Custos Variáveis"] = current_index
    colors.append("#10B981")  # Green
    current_index += 1
    
    # Add connections from Total to categories
    if fixed_total > 0:
        sources.append(node_index["Total Custos"])
        targets.append(node_index["Custos Fixos"])
        values.append(fixed_total)
    
    if variable_total > 0:
        sources.append(node_index["Total Custos"])
        targets.append(node_index["Custos Variáveis"])
        values.append(variable_total)
    
    # Add individual items (top 15 per category to avoid clutter)
    # Fixed costs
    sorted_fixed = sorted(fixed_items.items(), key=lambda x: x[1], reverse=True)[:15]
    for label, value in sorted_fixed:
        if value > 0:
            labels.append(label)
            node_index[label] = current_index
            colors.append("#60A5FA")  # Light blue
            current_index += 1
            
            sources.append(node_index["Custos Fixos"])
            targets.append(node_index[label])
            values.append(value)
    
    # Variable costs
    sorted_variable = sorted(variable_items.items(), key=lambda x: x[1], reverse=True)[:15]
    for label, value in sorted_variable:
        if value > 0:
            labels.append(label)
            node_index[label] = current_index
            colors.append("#34D399")  # Light green
            current_index += 1
            
            sources.append(node_index["Custos Variáveis"])
            targets.append(node_index[label])
            values.append(value)
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=colors,
            hovertemplate='%{label}<br>Valor: R$ %{value:,.0f}<extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(0,0,0,0.1)"
        )
    )])
    
    fig.update_layout(
        title="Fluxo de Custos - Variáveis e Fixos",
        font_size=14,
        height=800,
        margin=dict(t=50, l=50, r=50, b=50)
    )
    
    return fig


def render_monthly_analysis(flexible_data, selected_years, selected_months):
    """Render monthly analysis view"""
    
    st.info("🔄 Análise mensal em desenvolvimento...")
    
    # Prepare monthly data
    monthly_data = {}
    
    for year in selected_years:
        # Convert year to int if flexible_data uses int keys
        year_key = int(year) if year.isdigit() else year
        if year_key not in flexible_data:
            continue
            
        year_data = flexible_data[year_key]
        line_items = year_data.get('line_items', {})
        
        for item_key, item_data in line_items.items():
            category = item_data.get('category', '')
            label = item_data.get('label', '')
            monthly_values = item_data.get('monthly', {})
            is_subtotal = item_data.get('is_subtotal', False)
            
            # Skip calculated items and subtotals
            if is_subtotal or category in ['calculated_results', 'revenue', 'margins', 'results']:
                continue
            
            # Include all cost categories (variable costs stay as variable, all others as fixed)
            if category in ['variable_costs', 'fixed_costs', 'admin_expenses', 'operational_expenses', 
                           'marketing_expenses', 'financial_expenses', 'tax_expenses', 
                           'other_expenses', 'other_costs']:
                for month, value in monthly_values.items():
                    if month in selected_months:
                        month_key = f"{year}-{month}"
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {
                                'fixed': 0,
                                'variable': 0,
                                'items': []
                            }
                        
                        if category == 'variable_costs':
                            monthly_data[month_key]['variable'] += value
                        else:
                            monthly_data[month_key]['fixed'] += value
                            
                        monthly_data[month_key]['items'].append({
                            'label': label,
                            'value': value,
                            'category': category
                        })
    
    # Create monthly comparison chart
    if monthly_data:
        create_monthly_comparison_chart(monthly_data)


def render_quarterly_analysis(flexible_data, selected_years):
    """Render quarterly analysis view"""
    st.info("📊 Análise trimestral em desenvolvimento...")


def render_semester_analysis(flexible_data, selected_years):
    """Render semester analysis view"""
    st.info("📊 Análise semestral em desenvolvimento...")


def render_detailed_tables(fixed_items, variable_items):
    """Render detailed tables for fixed and variable costs"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Custos Fixos Detalhados")
        if fixed_items:
            df_fixed = pd.DataFrame([
                {'Descrição': k, 'Valor': v} 
                for k, v in sorted(fixed_items.items(), key=lambda x: x[1], reverse=True)
            ])
            df_fixed['% do Total'] = (df_fixed['Valor'] / df_fixed['Valor'].sum() * 100).round(2)
            df_fixed['Valor'] = df_fixed['Valor'].apply(format_currency)
            df_fixed['% do Total'] = df_fixed['% do Total'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(df_fixed, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("📊 Custos Variáveis Detalhados")
        if variable_items:
            df_variable = pd.DataFrame([
                {'Descrição': k, 'Valor': v} 
                for k, v in sorted(variable_items.items(), key=lambda x: x[1], reverse=True)
            ])
            df_variable['% do Total'] = (df_variable['Valor'] / df_variable['Valor'].sum() * 100).round(2)
            df_variable['Valor'] = df_variable['Valor'].apply(format_currency)
            df_variable['% do Total'] = df_variable['% do Total'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(df_variable, use_container_width=True, hide_index=True)


def create_monthly_comparison_chart(monthly_data):
    """Create monthly comparison visualization"""
    
    # Sort months chronologically
    sorted_months = sorted(monthly_data.keys())
    
    # Prepare data for chart
    months = []
    fixed_values = []
    variable_values = []
    
    for month in sorted_months:
        data = monthly_data[month]
        months.append(month)
        fixed_values.append(data['fixed'])
        variable_values.append(data['variable'])
    
    # Create stacked bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Custos Fixos',
        x=months,
        y=fixed_values,
        marker_color='#3B82F6'
    ))
    
    fig.add_trace(go.Bar(
        name='Custos Variáveis',
        x=months,
        y=variable_values,
        marker_color='#10B981'
    ))
    
    fig.update_layout(
        title='Evolução Mensal - Custos Fixos e Variáveis',
        xaxis_title='Mês',
        yaxis_title='Valor (R$)',
        barmode='stack',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)