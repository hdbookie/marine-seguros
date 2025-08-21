"""
Formatter for structured insights output with cards and visualizations
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import json

class InsightsFormatter:
    """
    Format and display AI insights in a structured, visually appealing way
    """
    
    def __init__(self):
        self.color_scheme = {
            'positive': '#10b981',  # Green
            'negative': '#ef4444',  # Red
            'neutral': '#6b7280',   # Gray
            'warning': '#f59e0b',   # Amber
            'info': '#3b82f6'       # Blue
        }
    
    def render_insights_dashboard(self, insights: Dict[str, Any]):
        """
        Render complete insights dashboard with all sections
        
        Args:
            insights: Dictionary containing all insight sections
        """
        # Executive Summary at the top
        if 'executive_summary' in insights:
            self.render_executive_summary(insights['executive_summary'])
        
        # Health Score Card
        if 'health_score' in insights:
            self.render_health_score_card(insights['health_score'])
        
        # Key Metrics Row
        if 'key_metrics' in insights:
            self.render_key_metrics(insights['key_metrics'])
        
        # Main content tabs
        tabs = []
        tab_content = []
        
        if 'financial_analysis' in insights:
            tabs.append("📊 Análise Financeira")
            tab_content.append(('financial_analysis', insights['financial_analysis']))
        
        if 'cost_optimization' in insights:
            tabs.append("💰 Otimização de Custos")
            tab_content.append(('cost_optimization', insights['cost_optimization']))
        
        if 'revenue_growth' in insights:
            tabs.append("📈 Crescimento de Receita")
            tab_content.append(('revenue_growth', insights['revenue_growth']))
        
        if 'risk_assessment' in insights:
            tabs.append("⚠️ Avaliação de Riscos")
            tab_content.append(('risk_assessment', insights['risk_assessment']))
        
        if 'predictions' in insights:
            tabs.append("🔮 Previsões")
            tab_content.append(('predictions', insights['predictions']))
        
        if 'anomalies' in insights:
            tabs.append("🔍 Anomalias")
            tab_content.append(('anomalies', insights['anomalies']))
        
        if tabs:
            tab_objects = st.tabs(tabs)
            for tab, (key, content) in zip(tab_objects, tab_content):
                with tab:
                    self._render_tab_content(key, content)
        
        # Action items at the bottom
        if 'action_items' in insights:
            self.render_action_items(insights['action_items'])
    
    def render_executive_summary(self, summary: Dict):
        """Render executive summary section"""
        st.markdown("## 📋 Resumo Executivo")
        
        # Create columns for key highlights
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'snapshot' in summary:
                st.markdown("### 🎯 Snapshot")
                for item in summary['snapshot']:
                    st.markdown(f"• {item}")
        
        with col2:
            if 'performance' in summary:
                st.markdown("### 📊 Performance")
                for key, value in summary['performance'].items():
                    st.markdown(f"**{key}**: {value}")
        
        with col3:
            if 'outlook' in summary:
                st.markdown("### 🔮 Outlook")
                outlook = summary['outlook']
                if isinstance(outlook, dict):
                    # Format structured outlook data properly
                    if 'projecao_receita' in outlook:
                        st.markdown(f"**Projeção:** {outlook['projecao_receita']}")
                    if 'riscos_quantificados' in outlook:
                        st.markdown(f"**Riscos:** {outlook['riscos_quantificados']}")
                    if 'oportunidades_quantificadas' in outlook:
                        st.markdown(f"**Oportunidades:** {outlook['oportunidades_quantificadas']}")
                    if 'cenario_provavel' in outlook:
                        st.markdown(f"**Cenário:** {outlook['cenario_provavel']}")
                elif isinstance(outlook, str):
                    st.markdown(outlook)
                else:
                    st.markdown("Análise em processamento...")
        
        st.markdown("---")
    
    def render_health_score_card(self, health_data: Dict):
        """Render financial health score card"""
        score = health_data.get('overall_score', 0)
        
        # Determine color based on score
        if score >= 80:
            color = self.color_scheme['positive']
            status = "Excelente"
            icon = "✅"
        elif score >= 60:
            color = self.color_scheme['warning']
            status = "Bom"
            icon = "⚠️"
        else:
            color = self.color_scheme['negative']
            status = "Atenção Necessária"
            icon = "❌"
        
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            title={'text': "Score de Saúde Financeira"},
            delta={'reference': health_data.get('previous_score', score)},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 40], 'color': '#fee2e2'},
                    {'range': [40, 60], 'color': '#fef3c7'},
                    {'range': [60, 80], 'color': '#fef9c3'},
                    {'range': [80, 100], 'color': '#d1fae5'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown(f"### {icon} Status: {status}")
            
            if 'breakdown' in health_data:
                st.markdown("**Breakdown por Categoria:**")
                for category, score_val in health_data['breakdown'].items():
                    progress = score_val / 100
                    st.progress(progress)
                    st.caption(f"{category}: {score_val}/100")
    
    def render_key_metrics(self, metrics: List[Dict]):
        """Render key metrics in cards"""
        cols = st.columns(len(metrics))
        
        for col, metric in zip(cols, metrics):
            with col:
                # Determine delta color
                delta_color = "normal"
                if metric.get('delta_type'):
                    if metric['delta_type'] == 'positive':
                        delta_color = "normal"
                    elif metric['delta_type'] == 'negative':
                        delta_color = "inverse"
                
                st.metric(
                    label=metric['label'],
                    value=metric['value'],
                    delta=metric.get('delta'),
                    delta_color=delta_color,
                    help=metric.get('help')
                )
    
    def _render_tab_content(self, tab_key: str, content: Dict):
        """Render content for specific tab"""
        if tab_key == 'financial_analysis':
            self._render_financial_analysis(content)
        elif tab_key == 'cost_optimization':
            self._render_cost_optimization(content)
        elif tab_key == 'revenue_growth':
            self._render_revenue_growth(content)
        elif tab_key == 'risk_assessment':
            self._render_risk_assessment(content)
        elif tab_key == 'predictions':
            self._render_predictions(content)
        elif tab_key == 'anomalies':
            self._render_anomalies(content)
    
    def _render_financial_analysis(self, analysis: Dict):
        """Render financial analysis section"""
        # Trends
        if 'trends' in analysis:
            st.markdown("### 📈 Tendências Identificadas")
            for trend in analysis['trends']:
                icon = "📈" if trend.get('direction') == 'up' else "📉"
                st.markdown(f"{icon} **{trend['name']}**: {trend['description']}")
        
        # Strengths and Weaknesses
        col1, col2 = st.columns(2)
        
        with col1:
            if 'strengths' in analysis:
                st.markdown("### 💪 Pontos Fortes")
                for strength in analysis['strengths']:
                    st.success(f"✅ {strength}")
        
        with col2:
            if 'weaknesses' in analysis:
                st.markdown("### ⚠️ Pontos de Atenção")
                for weakness in analysis['weaknesses']:
                    st.warning(f"⚠️ {weakness}")
        
        # Charts
        if 'charts' in analysis:
            for chart_data in analysis['charts']:
                self._render_chart(chart_data)
    
    def _render_cost_optimization(self, optimization: Dict):
        """Render cost optimization section"""
        # Quick Wins
        if 'quick_wins' in optimization:
            st.markdown("### 🎯 Quick Wins (< 30 dias)")
            
            quick_wins_df = pd.DataFrame(optimization['quick_wins'])
            
            # Create styled dataframe
            st.dataframe(
                quick_wins_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "action": st.column_config.TextColumn("Ação", width="large"),
                    "savings": st.column_config.NumberColumn("Economia Estimada", format="R$ %.2f"),
                    "complexity": st.column_config.TextColumn("Complexidade"),
                    "risk": st.column_config.TextColumn("Risco")
                }
            )
        
        # Strategic Optimizations
        if 'strategic' in optimization:
            st.markdown("### 🚀 Otimizações Estratégicas (3-6 meses)")
            
            for strategy in optimization['strategic']:
                with st.expander(strategy['name']):
                    st.markdown(f"**ROI Esperado**: {strategy['roi']}")
                    st.markdown(f"**Investimento**: {strategy['investment']}")
                    st.markdown(f"**Descrição**: {strategy['description']}")
                    
                    if 'risks' in strategy:
                        st.markdown("**Riscos**:")
                        for risk in strategy['risks']:
                            st.markdown(f"• {risk}")
        
        # Savings Potential Chart
        if 'savings_potential' in optimization:
            self._render_savings_chart(optimization['savings_potential'])
    
    def _render_revenue_growth(self, growth: Dict):
        """Render revenue growth analysis"""
        # Growth Opportunities
        if 'opportunities' in growth:
            st.markdown("### 🚀 Oportunidades de Crescimento")
            
            opportunities_df = pd.DataFrame(growth['opportunities'])
            
            # Create bubble chart
            fig = px.scatter(
                opportunities_df,
                x='effort',
                y='impact',
                size='potential_revenue',
                color='category',
                hover_name='name',
                title="Matriz de Oportunidades (Esforço vs Impacto)",
                labels={'effort': 'Esforço Necessário', 'impact': 'Impacto Potencial'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Portfolio Analysis
        if 'portfolio' in growth:
            self._render_portfolio_matrix(growth['portfolio'])
        
        # Growth Roadmap
        if 'roadmap' in growth:
            st.markdown("### 📅 Roadmap de Crescimento")
            
            for quarter, actions in growth['roadmap'].items():
                with st.expander(quarter):
                    for action in actions:
                        st.markdown(f"• {action}")
    
    def _render_risk_assessment(self, risks: Dict):
        """Render risk assessment section"""
        # Risk Matrix
        if 'risk_matrix' in risks:
            st.markdown("### 🎯 Matriz de Riscos")
            self._render_risk_matrix(risks['risk_matrix'])
        
        # Risk Categories
        if 'categories' in risks:
            tabs = st.tabs([cat['name'] for cat in risks['categories']])
            
            for tab, category in zip(tabs, risks['categories']):
                with tab:
                    for risk in category['risks']:
                        severity_color = {
                            'Critical': '🔴',
                            'High': '🟠',
                            'Medium': '🟡',
                            'Low': '🟢'
                        }.get(risk['severity'], '⚪')
                        
                        with st.expander(f"{severity_color} {risk['name']}"):
                            st.markdown(f"**Probabilidade**: {risk['probability']}")
                            st.markdown(f"**Impacto**: {risk['impact']}")
                            st.markdown(f"**Descrição**: {risk['description']}")
                            
                            if 'mitigation' in risk:
                                st.markdown(f"**Mitigação**: {risk['mitigation']}")
        
        # Early Warning Indicators
        if 'kris' in risks:
            st.markdown("### 📊 Indicadores de Risco (KRIs)")
            
            kri_df = pd.DataFrame(risks['kris'])
            st.dataframe(kri_df, use_container_width=True, hide_index=True)
    
    def _render_predictions(self, predictions: Dict):
        """Render predictions and forecasts"""
        # Forecast Chart
        if 'forecast' in predictions:
            st.markdown("### 📈 Previsões")
            self._render_forecast_chart(predictions['forecast'])
        
        # Scenarios
        if 'scenarios' in predictions:
            st.markdown("### 🎭 Cenários")
            
            scenario_tabs = st.tabs(['Otimista', 'Base', 'Pessimista'])
            
            for tab, (scenario_name, scenario_data) in zip(scenario_tabs, predictions['scenarios'].items()):
                with tab:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Receita Projetada", scenario_data['revenue'])
                    with col2:
                        st.metric("Margem Esperada", scenario_data['margin'])
                    with col3:
                        st.metric("Probabilidade", scenario_data['probability'])
                    
                    if 'assumptions' in scenario_data:
                        st.markdown("**Premissas**:")
                        for assumption in scenario_data['assumptions']:
                            st.markdown(f"• {assumption}")
        
        # Confidence Levels
        if 'confidence' in predictions:
            st.markdown("### 🎯 Níveis de Confiança")
            
            for prediction, confidence in predictions['confidence'].items():
                st.progress(confidence / 100)
                st.caption(f"{prediction}: {confidence}%")
    
    def _render_anomalies(self, anomalies: Dict):
        """Render anomalies section"""
        if 'detected' in anomalies:
            st.markdown("### 🔍 Anomalias Detectadas")
            
            # Group by severity
            critical = [a for a in anomalies['detected'] if a['severity'] == 'Critical']
            high = [a for a in anomalies['detected'] if a['severity'] == 'High']
            medium = [a for a in anomalies['detected'] if a['severity'] == 'Medium']
            low = [a for a in anomalies['detected'] if a['severity'] == 'Low']
            
            if critical:
                st.error(f"**{len(critical)} Anomalias Críticas**")
                for anomaly in critical:
                    with st.expander(f"🔴 {anomaly['name']}"):
                        st.markdown(f"**Descrição**: {anomaly['description']}")
                        st.markdown(f"**Impacto**: {anomaly['impact']}")
                        st.markdown(f"**Ação Recomendada**: {anomaly['action']}")
            
            if high:
                st.warning(f"**{len(high)} Anomalias de Alta Prioridade**")
                for anomaly in high:
                    with st.expander(f"🟠 {anomaly['name']}"):
                        st.markdown(f"**Descrição**: {anomaly['description']}")
                        st.markdown(f"**Impacto**: {anomaly['impact']}")
                        st.markdown(f"**Ação Recomendada**: {anomaly['action']}")
            
            if medium or low:
                with st.expander(f"Ver {len(medium) + len(low)} anomalias de menor prioridade"):
                    for anomaly in medium + low:
                        icon = "🟡" if anomaly['severity'] == 'Medium' else "🟢"
                        st.markdown(f"{icon} **{anomaly['name']}**: {anomaly['description']}")
    
    def render_action_items(self, actions: List[Dict]):
        """Render prioritized action items"""
        st.markdown("## 🎯 Plano de Ação")
        
        # Group by priority
        high_priority = [a for a in actions if a.get('priority') == 'Alta']
        medium_priority = [a for a in actions if a.get('priority') == 'Média']
        low_priority = [a for a in actions if a.get('priority') == 'Baixa']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🔴 Alta Prioridade")
            for action in high_priority[:3]:  # Limit to top 3
                st.markdown(f"**• {action['action']}**")
                if 'impact' in action and action['impact']:
                    st.caption(f"💡 {action['impact']}")
                if 'deadline' in action:
                    st.caption(f"⏰ Prazo: {action['deadline']}")
                st.markdown("")  # Add spacing
        
        with col2:
            st.markdown("### 🟡 Média Prioridade")
            for action in medium_priority[:3]:  # Limit to top 3
                st.markdown(f"**• {action['action']}**")
                if 'impact' in action and action['impact']:
                    st.caption(f"💡 {action['impact']}")
                if 'deadline' in action:
                    st.caption(f"⏰ Prazo: {action['deadline']}")
                st.markdown("")  # Add spacing
        
        with col3:
            st.markdown("### 🟢 Baixa Prioridade")
            for action in low_priority[:3]:  # Limit to top 3
                st.markdown(f"**• {action['action']}**")
                if 'impact' in action and action['impact']:
                    st.caption(f"💡 {action['impact']}")
                if 'deadline' in action:
                    st.caption(f"⏰ Prazo: {action['deadline']}")
                st.markdown("")  # Add spacing
    
    def _render_chart(self, chart_data: Dict):
        """Render a chart based on type and data"""
        chart_type = chart_data.get('type', 'line')
        
        if chart_type == 'line':
            fig = px.line(
                chart_data['data'],
                x=chart_data['x'],
                y=chart_data['y'],
                title=chart_data.get('title', ''),
                color=chart_data.get('color')
            )
        elif chart_type == 'bar':
            fig = px.bar(
                chart_data['data'],
                x=chart_data['x'],
                y=chart_data['y'],
                title=chart_data.get('title', ''),
                color=chart_data.get('color')
            )
        elif chart_type == 'scatter':
            fig = px.scatter(
                chart_data['data'],
                x=chart_data['x'],
                y=chart_data['y'],
                title=chart_data.get('title', ''),
                size=chart_data.get('size'),
                color=chart_data.get('color')
            )
        else:
            return
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_savings_chart(self, savings_data: Dict):
        """Render savings potential chart"""
        categories = list(savings_data.keys())
        values = list(savings_data.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color=self.color_scheme['positive'],
                text=[f"R$ {v:,.0f}" for v in values],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Potencial de Economia por Categoria",
            xaxis_title="Categoria",
            yaxis_title="Economia Potencial (R$)",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_portfolio_matrix(self, portfolio: Dict):
        """Render BCG portfolio matrix"""
        st.markdown("### 📊 Análise de Portfólio")
        
        # Create scatter plot for BCG matrix
        data = []
        for category, items in portfolio.items():
            for item in items:
                data.append({
                    'name': item['name'],
                    'growth': item['growth'],
                    'market_share': item['market_share'],
                    'revenue': item['revenue'],
                    'category': category
                })
        
        df = pd.DataFrame(data)
        
        fig = px.scatter(
            df,
            x='market_share',
            y='growth',
            size='revenue',
            color='category',
            hover_name='name',
            title="Matriz BCG - Portfólio de Produtos",
            labels={'market_share': 'Participação de Mercado (%)', 'growth': 'Taxa de Crescimento (%)'}
        )
        
        # Add quadrant lines
        fig.add_hline(y=10, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Add quadrant labels
        fig.add_annotation(x=25, y=20, text="Question Marks", showarrow=False, font=dict(size=12, color="gray"))
        fig.add_annotation(x=75, y=20, text="Stars", showarrow=False, font=dict(size=12, color="gray"))
        fig.add_annotation(x=25, y=5, text="Dogs", showarrow=False, font=dict(size=12, color="gray"))
        fig.add_annotation(x=75, y=5, text="Cash Cows", showarrow=False, font=dict(size=12, color="gray"))
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_risk_matrix(self, risks: List[Dict]):
        """Render risk matrix visualization"""
        # Create risk matrix data
        data = []
        for risk in risks:
            data.append({
                'name': risk['name'],
                'probability': risk['probability_score'],
                'impact': risk['impact_score'],
                'severity': risk['severity']
            })
        
        df = pd.DataFrame(data)
        
        # Color mapping for severity
        color_map = {
            'Critical': self.color_scheme['negative'],
            'High': self.color_scheme['warning'],
            'Medium': '#fbbf24',
            'Low': self.color_scheme['positive']
        }
        
        fig = px.scatter(
            df,
            x='probability',
            y='impact',
            color='severity',
            color_discrete_map=color_map,
            hover_name='name',
            title="Matriz de Riscos",
            labels={'probability': 'Probabilidade', 'impact': 'Impacto'},
            size_max=20
        )
        
        # Add quadrant backgrounds
        fig.add_shape(type="rect", x0=0, y0=0, x1=50, y1=50,
                     fillcolor="lightgreen", opacity=0.2, line_width=0)
        fig.add_shape(type="rect", x0=50, y0=0, x1=100, y1=50,
                     fillcolor="yellow", opacity=0.2, line_width=0)
        fig.add_shape(type="rect", x0=0, y0=50, x1=50, y1=100,
                     fillcolor="orange", opacity=0.2, line_width=0)
        fig.add_shape(type="rect", x0=50, y0=50, x1=100, y1=100,
                     fillcolor="red", opacity=0.2, line_width=0)
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_forecast_chart(self, forecast_data: Dict):
        """Render forecast chart with confidence intervals"""
        # Prepare data
        dates = forecast_data['dates']
        actual = forecast_data.get('actual', [])
        predicted = forecast_data['predicted']
        upper_bound = forecast_data.get('upper_bound', [])
        lower_bound = forecast_data.get('lower_bound', [])
        
        fig = go.Figure()
        
        # Add actual data
        if actual:
            fig.add_trace(go.Scatter(
                x=dates[:len(actual)],
                y=actual,
                mode='lines+markers',
                name='Realizado',
                line=dict(color=self.color_scheme['info'], width=2)
            ))
        
        # Add predictions
        fig.add_trace(go.Scatter(
            x=dates[len(actual):] if actual else dates,
            y=predicted,
            mode='lines+markers',
            name='Previsão',
            line=dict(color=self.color_scheme['positive'], width=2, dash='dash')
        ))
        
        # Add confidence interval
        if upper_bound and lower_bound:
            fig.add_trace(go.Scatter(
                x=dates[len(actual):] if actual else dates,
                y=upper_bound,
                mode='lines',
                name='Limite Superior',
                line=dict(width=0),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=dates[len(actual):] if actual else dates,
                y=lower_bound,
                mode='lines',
                name='Limite Inferior',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(68, 68, 68, 0.1)',
                showlegend=False
            ))
        
        fig.update_layout(
            title="Previsão com Intervalo de Confiança",
            xaxis_title="Período",
            yaxis_title="Valor",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def export_to_markdown(self, insights: Dict) -> str:
        """
        Export insights to Markdown format
        
        Args:
            insights: Dictionary containing all insights
        
        Returns:
            Markdown formatted string
        """
        md = f"# Relatório de Insights Financeiros\n"
        md += f"*Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n\n"
        
        # Executive Summary
        if 'executive_summary' in insights:
            md += "## Resumo Executivo\n\n"
            summary = insights['executive_summary']
            
            if 'snapshot' in summary:
                md += "### Snapshot\n"
                for item in summary['snapshot']:
                    md += f"- {item}\n"
                md += "\n"
            
            if 'performance' in summary:
                md += "### Performance\n"
                for key, value in summary['performance'].items():
                    md += f"- **{key}**: {value}\n"
                md += "\n"
        
        # Health Score
        if 'health_score' in insights:
            md += "## Score de Saúde Financeira\n\n"
            md += f"**Score Geral**: {insights['health_score'].get('overall_score', 'N/A')}/100\n\n"
            
            if 'breakdown' in insights['health_score']:
                md += "### Breakdown por Categoria\n"
                for cat, score in insights['health_score']['breakdown'].items():
                    md += f"- {cat}: {score}/100\n"
                md += "\n"
        
        # Key Metrics
        if 'key_metrics' in insights:
            md += "## Métricas Principais\n\n"
            for metric in insights['key_metrics']:
                md += f"- **{metric['label']}**: {metric['value']}"
                if 'delta' in metric:
                    md += f" ({metric['delta']})"
                md += "\n"
            md += "\n"
        
        # Action Items
        if 'action_items' in insights:
            md += "## Plano de Ação\n\n"
            
            # Group by priority
            high = [a for a in insights['action_items'] if a.get('priority') == 'Alta']
            medium = [a for a in insights['action_items'] if a.get('priority') == 'Média']
            low = [a for a in insights['action_items'] if a.get('priority') == 'Baixa']
            
            if high:
                md += "### Alta Prioridade\n"
                for action in high:
                    md += f"- [ ] {action['action']}"
                    if 'deadline' in action:
                        md += f" (Prazo: {action['deadline']})"
                    md += "\n"
                md += "\n"
            
            if medium:
                md += "### Média Prioridade\n"
                for action in medium:
                    md += f"- [ ] {action['action']}"
                    if 'deadline' in action:
                        md += f" (Prazo: {action['deadline']})"
                    md += "\n"
                md += "\n"
            
            if low:
                md += "### Baixa Prioridade\n"
                for action in low:
                    md += f"- [ ] {action['action']}"
                    if 'deadline' in action:
                        md += f" (Prazo: {action['deadline']})"
                    md += "\n"
                md += "\n"
        
        return md
    
    def export_to_json(self, insights: Dict) -> str:
        """
        Export insights to JSON format
        
        Args:
            insights: Dictionary containing all insights
        
        Returns:
            JSON formatted string
        """
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'insights': insights
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)