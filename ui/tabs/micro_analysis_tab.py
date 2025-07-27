"""Micro Analysis Tab - Variable + Fixed Costs Sankey Visualization"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils import format_currency
from utils.categories import get_category_name


def render_micro_analysis_tab(flexible_data):
    """Render the micro analysis tab with Sankey flow diagram"""
    
    st.header("🔬 Análise Micro - Custos Variáveis e Fixos")
    print(f"DEBUG: flexible_data received in micro_analysis_tab: {flexible_data is not None and len(flexible_data)}")
    
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
    elif view_type == "Trimestre Personalizado":
        st.info("🚧 Análise de Trimestre Personalizado em desenvolvimento.")
    elif view_type == "Personalizado":
        st.info("🚧 Análise Personalizada em desenvolvimento.")


def render_filters_section(flexible_data):
    """Render the filters section (matching macro dashboard style)"""
    st.markdown("### 🎛️ Filtros")
    
    # Get available years
    available_years = sorted([str(y) for y in flexible_data.keys()])
    
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
    
    with col_filter1:
        view_type = st.selectbox(
            "Visualização",
            ["Anual", "Mensal", "Trimestral", "Trimestre Personalizado", "Semestral", "Personalizado"],
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
        if st.button("🗓️ Últimos 3 Anos", key="micro_quick_3y", use_container_width=True):
            st.session_state.micro_selected_years = available_years[-3:] if len(available_years) >= 3 else available_years
            st.rerun()
        
        if st.button("📅 Ano Atual", key="micro_quick_current", use_container_width=True):
            current_year = str(datetime.now().year)
            if current_year in available_years:
                st.session_state.micro_selected_years = [current_year]
            else:
                st.session_state.micro_selected_years = [available_years[-1]]
            st.rerun()
    
    return selected_years, view_type, selected_months


def render_annual_sankey(flexible_data, selected_years):
    """Render annual Sankey diagram for selected years"""
    
    
    # Process data for selected years
    all_expense_items = {} # Stores items by their specific category
    
    for year in selected_years:
        # Convert year to int if flexible_data uses int keys
        year_key = int(year) if year.isdigit() else year
        if year_key not in flexible_data:
            continue
            
        year_data = flexible_data[year_key]
        line_items = year_data.get('line_items', {})
        
        for item_key, item_data in line_items.items():
            category = item_data.get('category', 'other')
            label = item_data.get('label', '')
            annual_value = item_data.get('annual', 0)
            is_subtotal = item_data.get('is_subtotal', False)
            
            # Skip calculated items, subtotals, and revenue/margins/results
            if is_subtotal or category in ['calculated_results', 'revenue', 'margins', 'results']:
                continue
            
            if category not in all_expense_items:
                all_expense_items[category] = {}
            
            if label not in all_expense_items[category]:
                all_expense_items[category][label] = 0
            all_expense_items[category][label] += annual_value
    
    # Calculate totals for summary metrics
    total_fixed_costs = sum(sum(all_expense_items.get(cat, {}).values()) for cat in ['fixed_costs', 'admin_expenses', 'operational_expenses', 'marketing_expenses', 'financial_expenses', 'tax_expenses', 'other_expenses', 'other_costs'])
    total_variable_costs = sum(all_expense_items.get('variable_costs', {}).values())
    total_overall_costs = total_fixed_costs + total_variable_costs
    
    if total_overall_costs == 0:
        st.warning("Nenhum custo encontrado para os anos selecionados.")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Geral", format_currency(total_overall_costs))
    with col2:
        st.metric("🔧 Custos Fixos", format_currency(total_fixed_costs), f"{total_fixed_costs/total_overall_costs*100:.1f}%" if total_overall_costs > 0 else "0.0%")
    with col3:
        st.metric("📊 Custos Variáveis", format_currency(total_variable_costs), f"{total_variable_costs/total_overall_costs*100:.1f}%" if total_overall_costs > 0 else "0.0%")
    
    # Create Sankey diagram
    fig = create_sankey_diagram(all_expense_items, total_overall_costs)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    with st.expander("📊 Ver dados detalhados"):
        render_detailed_tables_flexible(all_expense_items)
    
    # Year-over-year comparison if multiple years selected
    if len(selected_years) > 1:
        st.markdown("### 📈 Comparação Anual")
        render_year_comparison(flexible_data, selected_years)
    
    # Top expenses analysis
    st.markdown("### 🏆 Maiores Despesas")
    render_top_expenses_flexible(all_expense_items, total_overall_costs)

def create_sankey_diagram(all_expense_items, total_overall_costs):
    """Create Sankey flow diagram with detailed categories"""
    
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
    
    # Define main categories and their colors
    main_categories = {
        'variable_costs': {"label": "Custos Variáveis", "color": "#10B981"}, # Green
        'fixed_costs': {"label": "Custos Fixos", "color": "#3B82F6"}, # Blue
        'admin_expenses': {"label": "Despesas Administrativas", "color": "#60A5FA"}, # Light Blue
        'operational_expenses': {"label": "Despesas Operacionais", "color": "#93C5FD"}, # Lighter Blue
        'marketing_expenses': {"label": "Despesas de Marketing", "color": "#A78BFA"}, # Purple
        'financial_expenses': {"label": "Despesas Financeiras", "color": "#F87171"}, # Red
        'tax_expenses': {"label": "Impostos e Taxas", "color": "#FBBF24"}, # Amber
        'other_expenses': {"label": "Outras Despesas", "color": "#D1D5DB"}, # Gray
        'other_costs': {"label": "Outros Custos", "color": "#9CA3AF"} # Darker Gray
    }
    
    # Add main category nodes and links from Total Custos
    for cat_key, cat_info in main_categories.items():
        if cat_key in all_expense_items and sum(all_expense_items[cat_key].values()) > 0:
            labels.append(cat_info["label"])
            node_index[cat_info["label"]] = current_index
            colors.append(cat_info["color"])
            current_index += 1
            
            sources.append(node_index["Total Custos"])
            targets.append(node_index[cat_info["label"]])
            values.append(sum(all_expense_items[cat_key].values()))
    
    # Add individual items and links from their respective categories
    for cat_key, items in all_expense_items.items():
        if cat_key in main_categories: # Only process if it's a recognized main category
            parent_node_label = main_categories[cat_key]["label"]
            
            # Sort items by value and take top 15 to avoid clutter
            sorted_items = sorted(items.items(), key=lambda x: x[1], reverse=True)[:15]
            
            for label, value in sorted_items:
                if value > 0:
                    labels.append(label)
                    node_index[label] = current_index
                    # Assign a slightly lighter shade of the parent category's color
                    item_color = main_categories[cat_key]["color"] # Could make this lighter
                    colors.append(item_color) 
                    current_index += 1
                    
                    sources.append(node_index[parent_node_label])
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
        title="Fluxo de Custos Detalhado",
        font_size=14,
        height=800,
        margin=dict(t=50, l=50, r=50, b=50)
    )
    
    return fig


def render_monthly_analysis(flexible_data, selected_years, selected_months):
    """Render monthly analysis view"""
    
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
            category = item_data.get('category', 'other')
            label = item_data.get('label', '')
            monthly_values = item_data.get('monthly', {})
            is_subtotal = item_data.get('is_subtotal', False)
            
            # Skip calculated items and subtotals
            if is_subtotal or category in ['calculated_results', 'revenue', 'margins', 'results']:
                continue
            
            # Only include cost categories
            if category in ['variable_costs', 'fixed_costs', 'admin_expenses', 'operational_expenses', 
                           'marketing_expenses', 'financial_expenses', 'tax_expenses', 
                           'other_expenses', 'other_costs']:
                for month, value in monthly_values.items():
                    if month in selected_months:
                        month_key = f"{year}-{month}"
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {
                                'categories': {},
                                'total': 0
                            }
                        
                        if category not in monthly_data[month_key]['categories']:
                            monthly_data[month_key]['categories'][category] = 0
                        monthly_data[month_key]['categories'][category] += value
                        monthly_data[month_key]['total'] += value
    
    # Create monthly comparison chart
    if monthly_data:
        create_monthly_comparison_chart(monthly_data)
        
        # Add monthly insights
        render_monthly_insights(monthly_data)
    else:
        st.warning("Nenhum dado encontrado para os meses selecionados.")


def render_quarterly_analysis(flexible_data, selected_years):
    """Render quarterly analysis view"""
    
    # Prepare quarterly data
    quarterly_data = {}
    quarters = {
        'Q1': ['JAN', 'FEV', 'MAR'],
        'Q2': ['ABR', 'MAI', 'JUN'],
        'Q3': ['JUL', 'AGO', 'SET'],
        'Q4': ['OUT', 'NOV', 'DEZ']
    }
    
    for year in selected_years:
        year_key = int(year) if year.isdigit() else year
        if year_key not in flexible_data:
            continue
            
        year_data = flexible_data[year_key]
        line_items = year_data.get('line_items', {})
        
        for quarter_name, quarter_months in quarters.items():
            quarter_key = f"{year}-{quarter_name}"
            quarterly_data[quarter_key] = {
                'categories': {},
                'total': 0
            }
            
            for item_key, item_data in line_items.items():
                category = item_data.get('category', 'other')
                monthly_values = item_data.get('monthly', {})
                is_subtotal = item_data.get('is_subtotal', False)
                
                if is_subtotal or category in ['calculated_results', 'revenue', 'margins', 'results']:
                    continue
                
                if category in ['variable_costs', 'fixed_costs', 'admin_expenses', 'operational_expenses', 
                               'marketing_expenses', 'financial_expenses', 'tax_expenses', 
                               'other_expenses', 'other_costs']:
                    quarter_total = sum(monthly_values.get(month, 0) for month in quarter_months)
                    if quarter_total > 0:
                        if category not in quarterly_data[quarter_key]['categories']:
                            quarterly_data[quarter_key]['categories'][category] = 0
                        quarterly_data[quarter_key]['categories'][category] += quarter_total
                        quarterly_data[quarter_key]['total'] += quarter_total
    
    if quarterly_data:
        create_quarterly_chart(quarterly_data)
        render_quarterly_insights(quarterly_data)
    else:
        st.warning("Nenhum dado trimestral encontrado.")


def render_semester_analysis(flexible_data, selected_years):
    """Render semester analysis view"""
    
    # Prepare semester data
    semester_data = {}
    semesters = {
        'S1': ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN'],
        'S2': ['JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    }
    
    for year in selected_years:
        year_key = int(year) if year.isdigit() else year
        if year_key not in flexible_data:
            continue
            
        year_data = flexible_data[year_key]
        line_items = year_data.get('line_items', {})
        
        for semester_name, semester_months in semesters.items():
            semester_key = f"{year}-{semester_name}"
            semester_data[semester_key] = {
                'categories': {},
                'total': 0
            }
            
            for item_key, item_data in line_items.items():
                category = item_data.get('category', 'other')
                monthly_values = item_data.get('monthly', {})
                is_subtotal = item_data.get('is_subtotal', False)
                
                if is_subtotal or category in ['calculated_results', 'revenue', 'margins', 'results']:
                    continue
                
                if category in ['variable_costs', 'fixed_costs', 'admin_expenses', 'operational_expenses', 
                               'marketing_expenses', 'financial_expenses', 'tax_expenses', 
                               'other_expenses', 'other_costs']:
                    semester_total = sum(monthly_values.get(month, 0) for month in semester_months)
                    if semester_total > 0:
                        if category not in semester_data[semester_key]['categories']:
                            semester_data[semester_key]['categories'][category] = 0
                        semester_data[semester_key]['categories'][category] += semester_total
                        semester_data[semester_key]['total'] += semester_total
    
    if semester_data:
        create_semester_chart(semester_data)
        render_semester_insights(semester_data)
    else:
        st.warning("Nenhum dado semestral encontrado.")


def render_detailed_tables_flexible(all_expense_items):
    """Render detailed tables for all expense categories"""
    
    st.subheader("Detalhes por Categoria")
    
    # Define order of categories for display
    category_order = [
        'variable_costs',
        'fixed_costs',
        'admin_expenses',
        'operational_expenses',
        'marketing_expenses',
        'financial_expenses',
        'tax_expenses',
        'other_expenses',
        'other_costs'
    ]
    
    from utils.categories import get_category_name # Import here to avoid circular dependency
    
    for cat_key in category_order:
        if cat_key in all_expense_items and all_expense_items[cat_key]:
            st.markdown(f"#### {get_category_name(cat_key)}")
            df_cat = pd.DataFrame([
                {'Descrição': k, 'Valor': v} 
                for k, v in sorted(all_expense_items[cat_key].items(), key=lambda x: x[1], reverse=True)
            ])
            total_cat = df_cat['Valor'].sum()
            df_cat['% do Total da Categoria'] = (df_cat['Valor'] / total_cat * 100).round(2)
            df_cat['Valor'] = df_cat['Valor'].apply(format_currency)
            df_cat['% do Total da Categoria'] = df_cat['% do Total da Categoria'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(df_cat, use_container_width=True, hide_index=True)

def create_monthly_comparison_chart(monthly_data):
    """Create monthly comparison visualization with detailed categories"""
    
    # Sort months chronologically
    sorted_months = sorted(monthly_data.keys(), key=lambda x: datetime.strptime(x, "%Y-%b")) # Assuming YYYY-MON format
    
    # Prepare data for chart
    months = []
    category_values = {}
    
    # Initialize category_values with all possible categories
    all_categories = set()
    for month_key in sorted_months:
        for cat in monthly_data[month_key]['categories'].keys():
            all_categories.add(cat)
            
    for cat in all_categories:
        category_values[cat] = []

    for month_key in sorted_months:
        months.append(month_key)
        for cat in all_categories:
            category_values[cat].append(monthly_data[month_key]['categories'].get(cat, 0))
    
    # Create stacked bar chart
    fig = go.Figure()
    
    from utils.categories import get_category_name
    
    # Define colors for main categories (matching Sankey if possible)
    category_colors = {
        'variable_costs': '#10B981',
        'fixed_costs': '#3B82F6',
        'admin_expenses': '#60A5FA',
        'operational_expenses': '#93C5FD',
        'marketing_expenses': '#A78BFA',
        'financial_expenses': '#F87171',
        'tax_expenses': '#FBBF24',
        'other_expenses': '#D1D5DB',
        'other_costs': '#9CA3AF'
    }

    for cat in sorted(all_categories):
        fig.add_trace(go.Bar(
            name=get_category_name(cat),
            x=months,
            y=category_values[cat],
            marker_color=category_colors.get(cat, '#CCCCCC')
        ))
    
    fig.update_layout(
        title='Evolução Mensal - Custos por Categoria',
        xaxis_title='Mês',
        yaxis_title='Valor (R$)',
        barmode='stack',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_monthly_insights(monthly_data):
    """Render insights about monthly data"""
    
    # Calculate totals for each month
    month_totals = {}
    for month_key, data in monthly_data.items():
        month_totals[month_key] = data['total']
    
    if not month_totals:
        return
    
    # Calculate statistics
    avg_monthly = sum(month_totals.values()) / len(month_totals)
    max_month = max(month_totals.items(), key=lambda x: x[1])
    min_month = min(month_totals.items(), key=lambda x: x[1])
    
    # Display insights
    st.markdown("### 💡 Insights Mensais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Média Mensal", format_currency(avg_monthly))
    
    with col2:
        st.metric("📈 Mês Mais Alto", format_currency(max_month[1]), max_month[0])
    
    with col3:
        st.metric("📉 Mês Mais Baixo", format_currency(min_month[1]), min_month[0])
    
    with col4:
        variation = ((max_month[1] - min_month[1]) / min_month[1] * 100) if min_month[1] > 0 else 0
        st.metric("📊 Variação", f"{variation:.1f}%", "Max vs Min")
    
    # Month-over-month changes
    if len(month_totals) > 1:
        sorted_months = sorted(month_totals.items())
        mom_changes = []
        
        for i in range(1, len(sorted_months)):
            prev_month = sorted_months[i-1]
            curr_month = sorted_months[i]
            change = ((curr_month[1] - prev_month[1]) / prev_month[1] * 100) if prev_month[1] > 0 else 0
            mom_changes.append({
                'period': f"{prev_month[0]} → {curr_month[0]}",
                'change': change,
                'value': curr_month[1] - prev_month[1]
            })
        
        # Show significant changes
        significant_changes = [c for c in mom_changes if abs(c['change']) > 10]
        if significant_changes:
            st.markdown("#### 🔄 Mudanças Significativas (>10%)")
            for change in significant_changes[:5]:  # Show top 5
                if change['change'] > 0:
                    st.write(f"- {change['period']}: **+{change['change']:.1f}%** (+{format_currency(change['value'])})")
                else:
                    st.write(f"- {change['period']}: **{change['change']:.1f}%** ({format_currency(change['value'])})")


def render_year_comparison(flexible_data, selected_years):
    """Render year-over-year comparison"""
    
    if len(selected_years) < 2:
        return
    
    # Get data for comparison
    comparison_data = {}
    
    for year in selected_years[-2:]:  # Compare last two years
        year_key = int(year) if year.isdigit() else year
        if year_key not in flexible_data:
            continue
            
        year_data = flexible_data[year_key]
        line_items = year_data.get('line_items', {})
        
        fixed_total = 0
        variable_total = 0
        
        for item_key, item_data in line_items.items():
            category = item_data.get('category', '')
            annual_value = item_data.get('annual', 0)
            is_subtotal = item_data.get('is_subtotal', False)
            
            if is_subtotal or category in ['calculated_results', 'revenue', 'margins', 'results']:
                continue
            
            if category == 'variable_costs':
                variable_total += annual_value
            elif category in ['fixed_costs', 'admin_expenses', 'operational_expenses', 
                            'marketing_expenses', 'financial_expenses', 'tax_expenses', 
                            'other_expenses', 'other_costs']:
                fixed_total += annual_value
        
        comparison_data[year] = {
            'fixed': fixed_total,
            'variable': variable_total,
            'total': fixed_total + variable_total
        }
    
    if len(comparison_data) < 2:
        return
    
    # Calculate changes
    years = sorted(comparison_data.keys())
    prev_year = years[0]
    curr_year = years[1]
    
    prev_data = comparison_data[prev_year]
    curr_data = comparison_data[curr_year]
    
    # Display comparison
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_change = ((curr_data['total'] - prev_data['total']) / prev_data['total'] * 100) if prev_data['total'] > 0 else 0
        st.metric(
            f"Total {curr_year} vs {prev_year}",
            format_currency(curr_data['total']),
            f"{total_change:+.1f}%"
        )
    
    with col2:
        fixed_change = ((curr_data['fixed'] - prev_data['fixed']) / prev_data['fixed'] * 100) if prev_data['fixed'] > 0 else 0
        st.metric(
            "Custos Fixos",
            format_currency(curr_data['fixed']),
            f"{fixed_change:+.1f}%"
        )
    
    with col3:
        var_change = ((curr_data['variable'] - prev_data['variable']) / prev_data['variable'] * 100) if prev_data['variable'] > 0 else 0
        st.metric(
            "Custos Variáveis",
            format_currency(curr_data['variable']),
            f"{var_change:+.1f}%"
        )
    
    # Create comparison chart
    fig = go.Figure()
    
    categories = ['Custos Fixos', 'Custos Variáveis', 'Total']
    prev_values = [prev_data['fixed'], prev_data['variable'], prev_data['total']]
    curr_values = [curr_data['fixed'], curr_data['variable'], curr_data['total']]
    
    fig.add_trace(go.Bar(
        name=str(prev_year),
        x=categories,
        y=prev_values,
        text=[format_currency(v) for v in prev_values],
        textposition='auto',
    ))
    
    fig.add_trace(go.Bar(
        name=str(curr_year),
        x=categories,
        y=curr_values,
        text=[format_currency(v) for v in curr_values],
        textposition='auto',
    ))
    
    fig.update_layout(
        title=f'Comparação {prev_year} vs {curr_year}',
        barmode='group',
        height=400,
        yaxis_title="Valor (R$)"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_top_expenses_flexible(all_expense_items, total_overall_costs):
    """Render top expenses analysis across all categories"""
    
    all_items_list = []
    for cat_key, items in all_expense_items.items():
        for label, value in items.items():
            all_items_list.append({
                'Descrição': label,
                'Valor': value,
                'Categoria': cat_key # Keep original category for display
            })
            
    if not all_items_list:
        st.info("Nenhuma despesa detalhada encontrada.")
        return
        
    df_all_items = pd.DataFrame(all_items_list)
    df_all_items = df_all_items.sort_values(by='Valor', ascending=False).reset_index(drop=True)
    
    st.markdown("### 🏆 Maiores Despesas (Geral)")
    
    # Display top 10 overall expenses
    top_10_overall = df_all_items.head(10)
    
    from utils.categories import get_category_name # Import here to avoid circular dependency
    top_10_overall['Categoria'] = top_10_overall['Categoria'].apply(get_category_name)
    top_10_overall['% do Total Geral'] = (top_10_overall['Valor'] / total_overall_costs * 100).round(2)
    top_10_overall['Valor'] = top_10_overall['Valor'].apply(format_currency)
    top_10_overall['% do Total Geral'] = top_10_overall['% do Total Geral'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(top_10_overall, use_container_width=True, hide_index=True)
    
    # Cost structure pie chart
    st.markdown("### 🎯 Estrutura de Custos por Categoria Principal")
    
    # Aggregate values by main category for the pie chart
    main_category_totals = {}
    for cat_key, items in all_expense_items.items():
        main_category_totals[cat_key] = sum(items.values())
        
    # Filter out categories with zero total to avoid issues in pie chart
    main_category_totals = {k: v for k, v in main_category_totals.items() if v > 0}
    
    if not main_category_totals:
        st.info("Nenhuma dado para a estrutura de custos.")
        return
        
    labels = [get_category_name(k) for k in main_category_totals.keys()]
    values = list(main_category_totals.values())
    
    # Define colors for main categories (matching Sankey if possible)
    category_colors = {
        'variable_costs': '#10B981',
        'fixed_costs': '#3B82F6',
        'admin_expenses': '#60A5FA',
        'operational_expenses': '#93C5FD',
        'marketing_expenses': '#A78BFA',
        'financial_expenses': '#F87171',
        'tax_expenses': '#FBBF24',
        'other_expenses': '#D1D5DB',
        'other_costs': '#9CA3AF'
    }
    pie_colors = [category_colors.get(k, '#CCCCCC') for k in main_category_totals.keys()]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        marker_colors=pie_colors
    )])
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.0f}<br>Percentual: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        title="Distribuição de Custos por Categoria Principal",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_quarterly_chart(quarterly_data):
    """Create quarterly comparison visualization with detailed categories"""
    
    # Sort quarters chronologically
    sorted_quarters = sorted(quarterly_data.keys())
    
    # Prepare data for chart
    quarters = []
    category_values = {}
    
    # Initialize category_values with all possible categories
    all_categories = set()
    for quarter_key in sorted_quarters:
        for cat in quarterly_data[quarter_key]['categories'].keys():
            all_categories.add(cat)
            
    for cat in all_categories:
        category_values[cat] = []

    for quarter_key in sorted_quarters:
        quarters.append(quarter_key)
        for cat in all_categories:
            category_values[cat].append(quarterly_data[quarter_key]['categories'].get(cat, 0))
    
    # Create stacked bar chart
    fig = go.Figure()
    
    from utils.categories import get_category_name
    
    # Define colors for main categories (matching Sankey if possible)
    category_colors = {
        'variable_costs': '#10B981',
        'fixed_costs': '#3B82F6',
        'admin_expenses': '#60A5FA',
        'operational_expenses': '#93C5FD',
        'marketing_expenses': '#A78BFA',
        'financial_expenses': '#F87171',
        'tax_expenses': '#FBBF24',
        'other_expenses': '#D1D5DB',
        'other_costs': '#9CA3AF'
    }

    for cat in sorted(all_categories):
        fig.add_trace(go.Bar(
            name=get_category_name(cat),
            x=quarters,
            y=category_values[cat],
            marker_color=category_colors.get(cat, '#CCCCCC')
        ))
    
    fig.update_layout(
        title='Evolução Trimestral - Custos por Categoria',
        xaxis_title='Trimestre',
        yaxis_title='Valor (R$)',
        barmode='stack',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_quarterly_insights(quarterly_data):
    """Render insights about quarterly data"""
    
    # Calculate totals for each quarter
    quarter_totals = {}
    for quarter_key, data in quarterly_data.items():
        quarter_totals[quarter_key] = data['total']
    
    if not quarter_totals:
        return
    
    # Calculate statistics
    avg_quarterly = sum(quarter_totals.values()) / len(quarter_totals)
    max_quarter = max(quarter_totals.items(), key=lambda x: x[1])
    min_quarter = min(quarter_totals.items(), key=lambda x: x[1])
    
    # Display insights
    st.markdown("### 💡 Insights Trimestrais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Média Trimestral", format_currency(avg_quarterly))
    
    with col2:
        st.metric("📈 Trimestre Mais Alto", format_currency(max_quarter[1]), max_quarter[0])
    
    with col3:
        st.metric("📉 Trimestre Mais Baixo", format_currency(min_quarter[1]), min_quarter[0])
    
    with col4:
        variation = ((max_quarter[1] - min_quarter[1]) / min_quarter[1] * 100) if min_quarter[1] > 0 else 0
        st.metric("📊 Variação", f"{variation:.1f}%", "Max vs Min")
    
    # Quarter-over-quarter changes
    if len(quarter_totals) > 1:
        sorted_quarters = sorted(quarter_totals.items())
        qoq_changes = []
        
        for i in range(1, len(sorted_quarters)):
            prev_quarter = sorted_quarters[i-1]
            curr_quarter = sorted_quarters[i]
            change = ((curr_quarter[1] - prev_quarter[1]) / prev_quarter[1] * 100) if prev_quarter[1] > 0 else 0
            qoq_changes.append({
                'period': f"{prev_quarter[0]} → {curr_quarter[0]}",
                'change': change,
                'value': curr_quarter[1] - prev_quarter[1]
            })
        
        # Show significant changes
        significant_changes = [c for c in qoq_changes if abs(c['change']) > 5]
        if significant_changes:
            st.markdown("#### 🔄 Mudanças Significativas (>5%)")
            for change in significant_changes[:5]:  # Show top 5
                if change['change'] > 0:
                    st.write(f"- {change['period']}: **+{change['change']:.1f}%** (+{format_currency(change['value'])})")
                else:
                    st.write(f"- {change['period']}: **{change['change']:.1f}%** ({format_currency(change['value'])})")


def create_semester_chart(semester_data):
    """Create semester comparison visualization with detailed categories"""
    
    # Sort semesters chronologically
    sorted_semesters = sorted(semester_data.keys())
    
    # Prepare data for chart
    semesters = []
    category_values = {}
    
    # Initialize category_values with all possible categories
    all_categories = set()
    for semester_key in sorted_semesters:
        for cat in semester_data[semester_key]['categories'].keys():
            all_categories.add(cat)
            
    for cat in all_categories:
        category_values[cat] = []

    for semester_key in sorted_semesters:
        semesters.append(semester_key)
        for cat in all_categories:
            category_values[cat].append(semester_data[semester_key]['categories'].get(cat, 0))
    
    # Create grouped bar chart for better semester comparison
    fig = go.Figure()
    
    from utils.categories import get_category_name
    
    # Define colors for main categories (matching Sankey if possible)
    category_colors = {
        'variable_costs': '#10B981',
        'fixed_costs': '#3B82F6',
        'admin_expenses': '#60A5FA',
        'operational_expenses': '#93C5FD',
        'marketing_expenses': '#A78BFA',
        'financial_expenses': '#F87171',
        'tax_expenses': '#FBBF24',
        'other_expenses': '#D1D5DB',
        'other_costs': '#9CA3AF'
    }

    for cat in sorted(all_categories):
        fig.add_trace(go.Bar(
            name=get_category_name(cat),
            x=semesters,
            y=category_values[cat],
            marker_color=category_colors.get(cat, '#CCCCCC')
        ))
    
    fig.update_layout(
        title='Comparação Semestral - Custos por Categoria',
        xaxis_title='Semestre',
        yaxis_title='Valor (R$)',
        barmode='stack',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_semester_insights(semester_data):
    """Render insights about semester data"""
    
    # Calculate totals and averages
    semester_totals = {}
    for semester_key, data in semester_data.items():
        semester_totals[semester_key] = {
            'total': data['total'],
            'categories': data['categories']
        }
    
    if not semester_totals:
        return
    
    # Display semester comparison
    st.markdown("### 📊 Análise Semestral")
    
    # Create comparison dataframe
    df_data = []
    from utils.categories import get_category_name
    
    # Get all unique categories across all semesters
    all_categories = set()
    for data in semester_totals.values():
        all_categories.update(data['categories'].keys())
    
    # Sort categories for consistent column order
    sorted_categories = sorted(list(all_categories), key=get_category_name)

    for semester, data in sorted(semester_totals.items()):
        row = {'Semestre': semester, 'Total': format_currency(data['total'])}
        for cat_key in sorted_categories:
            value = data['categories'].get(cat_key, 0)
            row[get_category_name(cat_key)] = format_currency(value)
            if data['total'] > 0:
                row[f'% {get_category_name(cat_key)}'] = f"{(value / data['total'] * 100):.1f}%"
            else:
                row[f'% {get_category_name(cat_key)}'] = "0.0%"
        df_data.append(row)
    
    df_semester = pd.DataFrame(df_data)
    st.dataframe(df_semester, use_container_width=True, hide_index=True)
    
    # Year-over-year semester comparison
    years = {}
    for semester_key in semester_totals:
        year, sem = semester_key.split('-')
        if year not in years:
            years[year] = {}
        years[year][sem] = semester_totals[semester_key]
    
    if len(years) > 1:
        st.markdown("#### 📈 Comparação Ano a Ano por Semestre")
        
        sorted_years = sorted(years.keys())
        for i in range(1, len(sorted_years)):
            prev_year = sorted_years[i-1]
            curr_year = sorted_years[i]
            
            col1, col2 = st.columns(2)
            
            # S1 comparison
            if 'S1' in years[prev_year] and 'S1' in years[curr_year]:
                with col1:
                    prev_s1 = years[prev_year]['S1']['total']
                    curr_s1 = years[curr_year]['S1']['total']
                    change_s1 = ((curr_s1 - prev_s1) / prev_s1 * 100) if prev_s1 > 0 else 0
                    
                    st.metric(
                        f"1º Semestre {curr_year} vs {prev_year}",
                        format_currency(curr_s1),
                        f"{change_s1:+.1f}%"
                    )
            
            # S2 comparison
            if 'S2' in years[prev_year] and 'S2' in years[curr_year]:
                with col2:
                    prev_s2 = years[prev_year]['S2']['total']
                    curr_s2 = years[curr_year]['S2']['total']
                    change_s2 = ((curr_s2 - prev_s2) / prev_s2 * 100) if prev_s2 > 0 else 0
                    
                    st.metric(
                        f"2º Semestre {curr_year} vs {prev_year}",
                        format_currency(curr_s2),
                        f"{change_s2:+.1f}%"
                    )