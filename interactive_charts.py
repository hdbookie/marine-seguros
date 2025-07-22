import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Callable, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

class InteractiveCharts:
    """Create interactive, clickable charts with Power BI-style interactions"""
    
    def __init__(self, on_click_callback: Optional[Callable] = None):
        self.on_click_callback = on_click_callback
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        # Chart color palette
        self.colors = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'info': '#3b82f6',
            'gradient': ['#667eea', '#764ba2', '#8b5cf6', '#a855f7']
        }
    
    def create_revenue_dashboard(self, data: Dict, filter_state) -> go.Figure:
        """Create main revenue dashboard with multiple interactive charts"""
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Evolução da Receita', 'Distribuição Mensal', 
                          'Comparação Anual', 'Top/Bottom Meses'),
            specs=[[{"type": "scatter"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]],
            row_heights=[0.5, 0.5],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 1. Revenue Evolution (top-left)
        years = sorted(data.keys())
        revenues = []
        for year in years:
            revenue_data = data[year].get('revenue', {})
            total = sum(v for k, v in revenue_data.items() 
                       if k != 'ANNUAL' and isinstance(v, (int, float)))
            revenues.append(total)
        
        fig.add_trace(
            go.Scatter(
                x=years,
                y=revenues,
                mode='lines+markers+text',
                name='Receita Anual',
                line=dict(width=3, color=self.colors['primary']),
                marker=dict(size=12, color=self.colors['primary']),
                text=[f"R$ {r/1e6:.1f}M" for r in revenues],
                textposition='top center',
                customdata=years,
                hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. Monthly Distribution (top-right)
        monthly_totals = self._calculate_monthly_totals(data)
        colors = [self.colors['success'] if v > np.mean(list(monthly_totals.values())) 
                 else self.colors['danger'] for v in monthly_totals.values()]
        
        fig.add_trace(
            go.Bar(
                x=list(monthly_totals.keys()),
                y=list(monthly_totals.values()),
                name='Média Mensal',
                marker_color=colors,
                text=[f"R$ {v/1e3:.0f}K" for v in monthly_totals.values()],
                textposition='outside',
                customdata=list(monthly_totals.keys()),
                hovertemplate='<b>%{x}</b><br>Média: R$ %{y:,.0f}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # 3. Year Comparison (bottom-left)
        if len(years) >= 2:
            recent_years = years[-3:] if len(years) >= 3 else years
            comparison_data = []
            
            for year in recent_years:
                revenue_data = data[year].get('revenue', {})
                total = sum(v for k, v in revenue_data.items() 
                          if k != 'ANNUAL' and isinstance(v, (int, float)))
                comparison_data.append({
                    'Year': str(year),
                    'Revenue': total,
                    'Growth': 0  # Will calculate
                })
            
            # Calculate growth
            for i in range(1, len(comparison_data)):
                if comparison_data[i-1]['Revenue'] > 0:
                    growth = ((comparison_data[i]['Revenue'] - comparison_data[i-1]['Revenue']) 
                             / comparison_data[i-1]['Revenue'] * 100)
                    comparison_data[i]['Growth'] = growth
            
            df_comparison = pd.DataFrame(comparison_data)
            
            fig.add_trace(
                go.Bar(
                    x=df_comparison['Year'],
                    y=df_comparison['Revenue'],
                    name='Receita',
                    marker_color=self.colors['gradient'][:len(recent_years)],
                    text=[f"R$ {r/1e6:.1f}M<br>{g:+.1f}%" 
                         for r, g in zip(df_comparison['Revenue'], df_comparison['Growth'])],
                    textposition='outside',
                    customdata=df_comparison['Year'],
                    hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<br>Crescimento: %{text}<extra></extra>'
                ),
                row=2, col=1
            )
        
        # 4. Top/Bottom Months (bottom-right)
        sorted_months = sorted(monthly_totals.items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_months[:3]
        bottom_3 = sorted_months[-3:]
        
        months_display = [m[0] for m in top_3] + [m[0] for m in bottom_3]
        values_display = [m[1] for m in top_3] + [m[1] for m in bottom_3]
        colors_display = [self.colors['success']] * 3 + [self.colors['danger']] * 3
        
        fig.add_trace(
            go.Bar(
                x=months_display,
                y=values_display,
                marker_color=colors_display,
                text=[f"R$ {v/1e3:.0f}K" for v in values_display],
                textposition='outside',
                showlegend=False,
                customdata=months_display,
                hovertemplate='<b>%{x}</b><br>Média: R$ %{y:,.0f}<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=700,
            showlegend=False,
            title_text="Dashboard Interativo de Receita",
            title_font_size=20,
            hovermode='x unified'
        )
        
        # Update axes
        fig.update_xaxes(tickangle=-45, row=1, col=2)
        fig.update_xaxes(tickangle=-45, row=2, col=2)
        
        # Add click event data
        if self.on_click_callback:
            fig.update_traces(
                on_click=self.on_click_callback
            )
        
        return fig
    
    def create_monthly_heatmap(self, data: Dict) -> go.Figure:
        """Create interactive monthly performance heatmap"""
        
        # Prepare data matrix
        years = sorted(data.keys())
        revenue_matrix = []
        
        for year in years:
            year_revenues = []
            revenue_data = data[year].get('revenue', {})
            
            for month in self.months:
                value = revenue_data.get(month, 0)
                year_revenues.append(value)
            
            revenue_matrix.append(year_revenues)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=revenue_matrix,
            x=self.months,
            y=[str(y) for y in years],
            colorscale='RdYlGn',
            text=[[f"R$ {v/1e3:.0f}K" for v in row] for row in revenue_matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            customdata=[[(year, month) for month in self.months] for year in years],
            hovertemplate='<b>%{y} - %{x}</b><br>Receita: R$ %{z:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Mapa de Calor - Desempenho Mensal',
            xaxis_title='Mês',
            yaxis_title='Ano',
            height=400
        )
        
        return fig
    
    def create_margin_analysis(self, data: Dict) -> go.Figure:
        """Create interactive margin analysis chart"""
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Evolução da Margem', 'Distribuição da Margem'),
            specs=[[{"type": "scatter"}, {"type": "box"}]]
        )
        
        # Prepare margin data
        years = sorted(data.keys())
        avg_margins = []
        all_margins = []
        
        for year in years:
            margin_data = data[year].get('margins', {})
            year_margins = [v for k, v in margin_data.items() 
                          if k != 'ANNUAL' and isinstance(v, (int, float))]
            
            if year_margins:
                avg_margin = sum(year_margins) / len(year_margins)
                avg_margins.append(avg_margin)
                all_margins.extend([(year, m) for m in year_margins])
        
        # Line chart for margin evolution
        fig.add_trace(
            go.Scatter(
                x=years,
                y=avg_margins,
                mode='lines+markers+text',
                name='Margem Média',
                line=dict(width=3, color=self.colors['secondary']),
                marker=dict(size=10),
                text=[f"{m:.1f}%" for m in avg_margins],
                textposition='top center',
                customdata=years,
                hovertemplate='<b>%{x}</b><br>Margem: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add trend line
        if len(years) > 2:
            z = np.polyfit(range(len(years)), avg_margins, 1)
            p = np.poly1d(z)
            trend_line = p(range(len(years)))
            
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=trend_line,
                    mode='lines',
                    name='Tendência',
                    line=dict(dash='dash', color='gray'),
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # Box plot for margin distribution
        for i, year in enumerate(years):
            year_margins = [m for y, m in all_margins if y == year]
            
            fig.add_trace(
                go.Box(
                    y=year_margins,
                    name=str(year),
                    marker_color=self.colors['gradient'][i % len(self.colors['gradient'])],
                    boxpoints='all',
                    jitter=0.3,
                    pointpos=-1.8,
                    customdata=[year] * len(year_margins),
                    hovertemplate='<b>%{customdata}</b><br>Margem: %{y:.1f}%<extra></extra>'
                ),
                row=1, col=2
            )
        
        fig.update_layout(
            height=400,
            showlegend=False,
            title_text="Análise de Margem de Lucro"
        )
        
        fig.update_yaxes(title_text="Margem (%)", row=1, col=1)
        fig.update_yaxes(title_text="Margem (%)", row=1, col=2)
        
        return fig
    
    def create_comparison_chart(self, data: Dict, year1: int, year2: int) -> go.Figure:
        """Create detailed comparison chart between two years"""
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(f'Comparação Mensal: {year1} vs {year2}', 
                          'Variação Percentual'),
            row_heights=[0.6, 0.4],
            vertical_spacing=0.15
        )
        
        # Get data for both years
        data1 = data.get(year1, {}).get('revenue', {})
        data2 = data.get(year2, {}).get('revenue', {})
        
        values1 = [data1.get(month, 0) for month in self.months]
        values2 = [data2.get(month, 0) for month in self.months]
        
        # Calculate variations
        variations = []
        for v1, v2 in zip(values1, values2):
            if v1 > 0:
                var = ((v2 - v1) / v1) * 100
            else:
                var = 0 if v2 == 0 else 100
            variations.append(var)
        
        # Monthly comparison bars
        fig.add_trace(
            go.Bar(
                x=self.months,
                y=values1,
                name=str(year1),
                marker_color=self.colors['primary'],
                customdata=[(year1, m) for m in self.months],
                hovertemplate='<b>%{x} %{customdata[0]}</b><br>R$ %{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=self.months,
                y=values2,
                name=str(year2),
                marker_color=self.colors['secondary'],
                customdata=[(year2, m) for m in self.months],
                hovertemplate='<b>%{x} %{customdata[0]}</b><br>R$ %{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Variation chart
        colors = [self.colors['success'] if v > 0 else self.colors['danger'] 
                 for v in variations]
        
        fig.add_trace(
            go.Bar(
                x=self.months,
                y=variations,
                marker_color=colors,
                text=[f"{v:+.1f}%" for v in variations],
                textposition='outside',
                showlegend=False,
                customdata=self.months,
                hovertemplate='<b>%{x}</b><br>Variação: %{y:+.1f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Add zero line for variation chart
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        
        fig.update_layout(
            height=600,
            barmode='group',
            title_text=f"Análise Comparativa: {year1} vs {year2}"
        )
        
        fig.update_yaxes(title_text="Receita (R$)", row=1, col=1)
        fig.update_yaxes(title_text="Variação (%)", row=2, col=1)
        
        return fig
    
    def create_performance_gauge(self, current_value: float, target_value: float, 
                                title: str = "Performance") -> go.Figure:
        """Create a gauge chart for performance metrics"""
        
        percentage = (current_value / target_value * 100) if target_value > 0 else 0
        
        # Determine color based on performance
        if percentage >= 100:
            color = self.colors['success']
        elif percentage >= 80:
            color = self.colors['warning']
        else:
            color = self.colors['danger']
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=percentage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': 100, 'suffix': '%'},
            gauge={
                'axis': {'range': [None, 120], 'ticksuffix': '%'},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 80], 'color': "lightgray"},
                    {'range': [80, 100], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        
        fig.update_layout(height=250)
        
        return fig
    
    def create_trend_sparkline(self, values: List[float], title: str = "") -> go.Figure:
        """Create a small sparkline chart for trends"""
        
        fig = go.Figure()
        
        # Determine trend color
        if len(values) > 1:
            trend = values[-1] - values[0]
            color = self.colors['success'] if trend > 0 else self.colors['danger']
        else:
            color = self.colors['primary']
        
        fig.add_trace(go.Scatter(
            y=values,
            mode='lines',
            line=dict(color=color, width=2),
            fill='tozeroy',
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.3)",
            showlegend=False,
            hovertemplate='%{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            height=100,
            margin=dict(l=0, r=0, t=20, b=0),
            title=dict(text=title, font=dict(size=12)),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
        )
        
        return fig
    
    def _calculate_monthly_totals(self, data: Dict) -> Dict:
        """Calculate total revenue for each month across all years"""
        monthly_totals = {month: 0 for month in self.months}
        count = {month: 0 for month in self.months}
        
        for year_data in data.values():
            revenue_data = year_data.get('revenue', {})
            for month in self.months:
                if month in revenue_data:
                    monthly_totals[month] += revenue_data[month]
                    count[month] += 1
        
        # Calculate averages
        for month in self.months:
            if count[month] > 0:
                monthly_totals[month] = monthly_totals[month] / count[month]
        
        return monthly_totals
    
    def handle_click_event(self, trace, points, state):
        """Handle click events on charts"""
        if points.point_inds:
            # Get clicked data
            point_index = points.point_inds[0]
            
            # Extract custom data if available
            if hasattr(trace, 'customdata') and trace.customdata:
                clicked_data = trace.customdata[point_index]
                
                # Update filter based on clicked data
                if isinstance(clicked_data, str) and clicked_data in self.months:
                    # Month clicked
                    if clicked_data not in st.session_state.filter_state.months:
                        st.session_state.filter_state.months.add(clicked_data)
                    else:
                        st.session_state.filter_state.months.discard(clicked_data)
                    st.rerun()
                
                elif isinstance(clicked_data, (int, float)):
                    # Year clicked
                    year = int(clicked_data)
                    if year not in st.session_state.filter_state.years:
                        st.session_state.filter_state.years.add(year)
                    else:
                        st.session_state.filter_state.years.discard(year)
                    st.rerun()