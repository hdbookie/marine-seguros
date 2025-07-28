"""Chart creation functions for the dashboard"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.formatters import format_currency, format_percentage


def create_revenue_cost_chart(df, title="Evolução de Receitas vs Custos"):
    """Create a revenue vs costs comparison chart"""
    fig = go.Figure()
    
    # Add Revenue bars
    fig.add_trace(go.Bar(
        name='Receitas',
        x=df['year'],
        y=df['revenue'],
        text=[format_currency(v) for v in df['revenue']],
        textposition='outside',
        marker_color='rgba(50, 171, 96, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Receita:</b> %{text}<extra></extra>'
    ))
    
    # Add Costs bars
    fig.add_trace(go.Bar(
        name='Custos',
        x=df['year'],
        y=df['variable_costs'] + df['fixed_costs'] + df['operational_costs'],
        text=[format_currency(v) for v in df['variable_costs'] + df['fixed_costs'] + df['operational_costs']],
        textposition='outside',
        marker_color='rgba(219, 64, 82, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Custos:</b> %{text}<extra></extra>'
    ))
    
    # Add Profit line
    fig.add_trace(go.Scatter(
        name='Lucro',
        x=df['year'],
        y=df['net_profit'],
        text=[format_currency(v) for v in df['net_profit']],
        mode='lines+markers+text',
        textposition='top center',
        line=dict(color='rgb(55, 83, 109)', width=3),
        marker=dict(size=10),
        yaxis='y2',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Lucro:</b> %{text}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis=dict(
            title='Valores (R$)',
            titlefont=dict(color='rgb(55, 83, 109)'),
            tickfont=dict(color='rgb(55, 83, 109)'),
            side='left'
        ),
        yaxis2=dict(
            title='Lucro (R$)',
            titlefont=dict(color='rgb(55, 83, 109)'),
            tickfont=dict(color='rgb(55, 83, 109)'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        barmode='group',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig


def create_margin_evolution_chart(df, title="Evolução da Margem de Lucro"):
    """Create a profit margin evolution chart"""
    fig = go.Figure()
    
    # Add margin line
    fig.add_trace(go.Scatter(
        name='Margem de Lucro',
        x=df['year'],
        y=df['profit_margin'],
        text=[f"{v:.1f}%" for v in df['profit_margin']],
        mode='lines+markers+text',
        textposition='top center',
        line=dict(color='rgb(55, 83, 109)', width=3),
        marker=dict(size=10),
        fill='tonexty',
        fillcolor='rgba(55, 83, 109, 0.1)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Margem:</b> %{text}<extra></extra>'
    ))
    
    # Add reference line at 0%
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break Even")
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis_title='Margem de Lucro (%)',
        hovermode='x',
        template='plotly_white',
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig


def create_cost_breakdown_chart(data, title="Composição de Custos"):
    """Create a cost breakdown pie/donut chart"""
    # Prepare data
    categories = []
    values = []
    
    for category, value in data.items():
        if value > 0:
            categories.append(category)
            values.append(value)
    
    # Create donut chart
    fig = go.Figure(data=[go.Pie(
        labels=categories,
        values=values,
        hole=0.4,
        textinfo='label+percent',
        textposition='outside',
        marker=dict(
            colors=px.colors.qualitative.Set3
        ),
        hovertemplate='<b>%{label}</b><br>Valor: %{value:,.2f}<br>Percentual: %{percent}<extra></extra>'
    )])
    
    # Update layout
    fig.update_layout(
        title=title,
        showlegend=True,
        margin=dict(l=20, r=20, t=80, b=20)
    )
    
    return fig


def create_monthly_trend_chart(monthly_data, title="Tendência Mensal"):
    """Create a monthly trend chart with moving average"""
    fig = go.Figure()
    
    # Main line
    fig.add_trace(go.Scatter(
        name='Valor Mensal',
        x=monthly_data.index,
        y=monthly_data['value'],
        mode='lines+markers',
        line=dict(color='rgb(55, 83, 109)', width=2),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>Valor: R$ %{y:,.2f}<extra></extra>'
    ))
    
    # Add 3-month moving average
    if len(monthly_data) >= 3:
        ma3 = monthly_data['value'].rolling(window=3).mean()
        fig.add_trace(go.Scatter(
            name='Média Móvel (3M)',
            x=monthly_data.index,
            y=ma3,
            mode='lines',
            line=dict(color='rgba(255, 99, 71, 0.7)', width=2, dash='dash'),
            hovertemplate='<b>%{x}</b><br>MM3: R$ %{y:,.2f}<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Período',
        yaxis_title='Valor (R$)',
        hovermode='x unified',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99)
    )
    
    return fig


def create_pareto_chart(items, title="Análise de Pareto"):
    """Create a Pareto chart (80/20 analysis)"""
    # Sort items by value
    sorted_items = sorted(items, key=lambda x: x['value'], reverse=True)[:20]
    
    # Calculate cumulative percentage
    total = sum(item['value'] for item in sorted_items)
    cumulative_pct = []
    cumulative_sum = 0
    
    for item in sorted_items:
        cumulative_sum += item['value']
        cumulative_pct.append((cumulative_sum / total) * 100)
    
    # Create figure
    fig = go.Figure()
    
    # Bar chart
    fig.add_trace(go.Bar(
        name='Valor',
        x=list(range(1, len(sorted_items) + 1)),
        y=[item['value'] for item in sorted_items],
        text=[item['label'][:30] + '...' if len(item['label']) > 30 else item['label'] 
              for item in sorted_items],
        textposition='none',
        marker_color='lightblue',
        yaxis='y',
        hovertemplate='<b>%{text}</b><br>Valor: R$ %{y:,.2f}<extra></extra>'
    ))
    
    # Cumulative line
    fig.add_trace(go.Scatter(
        name='% Acumulado',
        x=list(range(1, len(sorted_items) + 1)),
        y=cumulative_pct,
        mode='lines+markers',
        line=dict(color='red', width=2),
        marker=dict(size=6),
        yaxis='y2',
        hovertemplate='%{y:.1f}% acumulado<extra></extra>'
    ))
    
    # Add 80% reference line
    fig.add_hline(y=80, line_dash="dash", line_color="green", 
                  annotation_text="80%", yref='y2')
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis=dict(title="Ranking", tickmode='linear'),
        yaxis=dict(title="Valor (R$)", side='left'),
        yaxis2=dict(
            title="Percentual Acumulado",
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        hovermode='x unified',
        template='plotly_white',
        showlegend=True,
        margin=dict(b=100)
    )
    
    return fig


def create_treemap(data, title="Visualização Hierárquica"):
    """Create a treemap visualization"""
    fig = px.treemap(
        data,
        path=['category', 'subcategory', 'item'],
        values='value',
        title=title,
        color='value',
        color_continuous_scale='Blues',
        hover_data={'value': ':,.2f'}
    )
    
    fig.update_traces(
        textposition="middle center",
        textfont_size=12,
        hovertemplate='<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>%{percentParent} do total<extra></extra>'
    )
    
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig


def create_sankey_diagram(source, target, value, title="Fluxo de Despesas"):
    """Create a Sankey diagram for expense flow"""
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=source + target,
            color="lightblue"
        ),
        link=dict(
            source=[source.index(s) for s in source],
            target=[len(source) + target.index(t) for t in target],
            value=value,
            color="rgba(0,0,255,0.2)"
        )
    )])
    
    fig.update_layout(
        title=title,
        font_size=10,
        height=600
    )
    
    return fig

def create_cost_structure_chart(df, title="Estrutura de Custos vs. Receita"):
    """Create a stacked bar chart showing cost structure against revenue"""
    fig = go.Figure()

    # Add Fixed Costs
    fig.add_trace(go.Bar(
        name='Custos Fixos',
        x=df['year'],
        y=df['fixed_costs'],
        text=[format_currency(v) for v in df['fixed_costs']],
        textposition='auto',
        marker_color='rgba(255, 159, 64, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Custos Fixos:</b> %{text}<extra></extra>'
    ))

    # Add Variable Costs
    fig.add_trace(go.Bar(
        name='Custos Variáveis',
        x=df['year'],
        y=df['variable_costs'],
        text=[format_currency(v) for v in df['variable_costs']],
        textposition='auto',
        marker_color='rgba(255, 99, 132, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Custos Variáveis:</b> %{text}<extra></extra>'
    ))

    # Add Operational Costs
    fig.add_trace(go.Bar(
        name='Outros Custos',
        x=df['year'],
        y=df['operational_costs'],
        text=[format_currency(v) for v in df['operational_costs']],
        textposition='auto',
        marker_color='rgba(153, 102, 255, 0.7)',
        hovertemplate='<b>Ano:</b> %{x}<br><b>Outros Custos:</b> %{text}<extra></extra>'
    ))

    # Add Revenue as a line on top
    fig.add_trace(go.Scatter(
        name='Receita Total',
        x=df['year'],
        y=df['revenue'],
        mode='lines+markers+text',
        text=[format_currency(v) for v in df['revenue']],
        textposition='top center',
        line=dict(color='rgba(54, 162, 235, 1)', width=3),
        marker=dict(size=10),
        hovertemplate='<b>Ano:</b> %{x}<br><b>Receita:</b> %{text}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis_title='Valores (R$)',
        barmode='stack',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig

def create_detailed_cost_structure_chart(df, title="Estrutura de Custos Detalhada"):
    """Create a detailed stacked bar chart showing cost structure against revenue"""
    fig = go.Figure()

    cost_categories = ['variable_costs', 'fixed_costs', 'non_operational_costs', 'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 'financial_expenses']
    colors = px.colors.qualitative.Plotly

    for i, cost_type in enumerate(cost_categories):
        fig.add_trace(go.Bar(
            name=cost_type.replace('_', ' ').title(),
            x=df['year'],
            y=df[cost_type],
            text=[format_currency(v) for v in df[cost_type]],
            textposition='auto',
            marker_color=colors[i % len(colors)],
            hovertemplate=f"<b>Ano:</b> %{{x}}<br><b>{cost_type.replace('_', ' ').title()}:</b> %{{text}}<extra></extra>"
        ))

    # Add Revenue as a line on top
    fig.add_trace(go.Scatter(
        name='Receita Total',
        x=df['year'],
        y=df['revenue'],
        mode='lines+markers+text',
        text=[format_currency(v) for v in df['revenue']],
        textposition='top center',
        line=dict(color='rgba(54, 162, 235, 1)', width=3),
        marker=dict(size=10),
        hovertemplate='<b>Ano:</b> %{x}<br><b>Receita:</b> %{text}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Ano',
        yaxis_title='Valores (R$)',
        barmode='stack',
        template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig