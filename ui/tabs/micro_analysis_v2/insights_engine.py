"""
AI-Powered Insights Engine for Micro Analysis V2
Generates intelligent insights and recommendations from expense data
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from utils import format_currency
from datetime import datetime
import json


class ExpenseInsightsEngine:
    """
    Advanced insights engine that analyzes expense patterns and generates
    actionable business intelligence
    """
    
    def __init__(self):
        self.insights_cache = {}
        self.threshold_configs = {
            'high_growth': 0.15,  # 15% growth threshold
            'high_variance': 0.30,  # 30% coefficient of variation
            'concentration_risk': 0.60,  # 60% of total in single category
            'seasonal_significance': 0.20  # 20% above/below seasonal average
        }
    
    def generate_comprehensive_insights(self, financial_data: Dict, selected_years: List[int]) -> Dict:
        """
        Generate comprehensive insights across multiple dimensions
        """
        insights = {
            'growth_insights': self._analyze_growth_patterns(financial_data, selected_years),
            'risk_insights': self._analyze_risk_patterns(financial_data, selected_years),
            'efficiency_insights': self._analyze_efficiency_patterns(financial_data, selected_years),
            'seasonal_insights': self._analyze_seasonal_patterns(financial_data, selected_years),
            'anomaly_insights': self._detect_anomalies(financial_data, selected_years),
            'optimization_recommendations': self._generate_optimization_recommendations(financial_data, selected_years),
            'key_metrics': self._calculate_key_metrics(financial_data, selected_years)
        }
        
        return insights
    
    def _analyze_growth_patterns(self, financial_data: Dict, selected_years: List[int]) -> Dict:
        """Analyze growth patterns and trends"""
        
        if len(selected_years) < 2:
            return {'error': 'Insufficient data for growth analysis'}
        
        growth_analysis = {
            'fastest_growing': [],
            'declining_categories': [],
            'volatile_categories': [],
            'stable_categories': []
        }
        
        # Calculate year-over-year growth for each category
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
                    growth_rate = ((current_val - previous_val) / previous_val)
                    
                    category_data = {
                        'category': category,
                        'growth_rate': growth_rate,
                        'period': f"{previous_year}-{current_year}",
                        'previous_value': previous_val,
                        'current_value': current_val,
                        'absolute_change': current_val - previous_val
                    }
                    
                    if growth_rate > self.threshold_configs['high_growth']:
                        growth_analysis['fastest_growing'].append(category_data)
                    elif growth_rate < -0.05:  # 5% decline
                        growth_analysis['declining_categories'].append(category_data)
                    elif abs(growth_rate) < 0.05:  # Within 5%
                        growth_analysis['stable_categories'].append(category_data)
        
        # Sort by growth rate
        growth_analysis['fastest_growing'].sort(key=lambda x: x['growth_rate'], reverse=True)
        growth_analysis['declining_categories'].sort(key=lambda x: x['growth_rate'])
        
        return growth_analysis
    
    def _analyze_risk_patterns(self, financial_data: Dict, selected_years: List[int]) -> Dict:
        """Analyze risk patterns in expense data"""
        
        risk_analysis = {
            'concentration_risks': [],
            'volatility_risks': [],
            'dependency_risks': [],
            'budget_risks': []
        }
        
        # Analyze concentration risk
        for year in selected_years:
            if year not in financial_data or 'sections' not in financial_data[year]:
                continue
            
            sections = financial_data[year]['sections']
            total_expenses = sum(s.get('value', 0) for s in sections)
            
            if total_expenses > 0:
                for section in sections:
                    concentration = (section.get('value', 0) / total_expenses)
                    
                    if concentration > self.threshold_configs['concentration_risk']:
                        risk_analysis['concentration_risks'].append({
                            'category': section['name'],
                            'year': year,
                            'concentration': concentration,
                            'value': section.get('value', 0),
                            'total': total_expenses
                        })
        
        # Analyze volatility risk across years
        category_values = {}
        
        for year in selected_years:
            if year not in financial_data or 'sections' not in financial_data[year]:
                continue
            
            for section in financial_data[year]['sections']:
                category = section['name']
                value = section.get('value', 0)
                
                if category not in category_values:
                    category_values[category] = []
                category_values[category].append(value)
        
        for category, values in category_values.items():
            if len(values) > 1:
                mean_val = np.mean(values)
                std_val = np.std(values)
                cv = (std_val / mean_val) if mean_val > 0 else 0
                
                if cv > self.threshold_configs['high_variance']:
                    risk_analysis['volatility_risks'].append({
                        'category': category,
                        'coefficient_of_variation': cv,
                        'mean_value': mean_val,
                        'std_deviation': std_val,
                        'values': values
                    })
        
        # Sort by risk level
        risk_analysis['volatility_risks'].sort(key=lambda x: x['coefficient_of_variation'], reverse=True)
        risk_analysis['concentration_risks'].sort(key=lambda x: x['concentration'], reverse=True)
        
        return risk_analysis
    
    def _analyze_efficiency_patterns(self, financial_data: Dict, selected_years: List[int]) -> Dict:
        """Analyze efficiency patterns and opportunities"""
        
        efficiency_analysis = {
            'cost_per_unit_trends': [],
            'efficiency_improvements': [],
            'benchmark_comparisons': [],
            'optimization_opportunities': []
        }
        
        # Calculate efficiency trends
        category_efficiency = {}
        
        for year in selected_years:
            if year not in financial_data or 'sections' not in financial_data[year]:
                continue
            
            sections = financial_data[year]['sections']
            total_revenue = 0
            
            # Try to find revenue data
            if 'calculations' in financial_data[year]:
                revenue_items = ['FATURAMENTO', 'RECEITA', 'RECEITAS']
                for revenue_key in revenue_items:
                    if revenue_key in financial_data[year]['calculations']:
                        total_revenue = financial_data[year]['calculations'][revenue_key].get('value', 0)
                        break
            
            if total_revenue > 0:
                for section in sections:
                    category = section['name']
                    value = section.get('value', 0)
                    efficiency_ratio = (value / total_revenue) * 100
                    
                    if category not in category_efficiency:
                        category_efficiency[category] = []
                    
                    category_efficiency[category].append({
                        'year': year,
                        'efficiency_ratio': efficiency_ratio,
                        'absolute_value': value,
                        'revenue': total_revenue
                    })
        
        # Identify efficiency trends
        for category, data_points in category_efficiency.items():
            if len(data_points) > 1:
                ratios = [dp['efficiency_ratio'] for dp in data_points]
                trend = np.polyfit(range(len(ratios)), ratios, 1)[0]
                
                efficiency_analysis['cost_per_unit_trends'].append({
                    'category': category,
                    'trend': trend,
                    'current_ratio': ratios[-1],
                    'historical_data': data_points
                })
                
                # Identify improvements (decreasing cost ratios)
                if trend < -0.5:  # Improving efficiency by 0.5% per year
                    efficiency_analysis['efficiency_improvements'].append({
                        'category': category,
                        'improvement_rate': -trend,
                        'data': data_points
                    })
        
        return efficiency_analysis
    
    def _analyze_seasonal_patterns(self, financial_data: Dict, selected_years: List[int]) -> Dict:
        """Analyze seasonal patterns and their business implications"""
        
        seasonal_analysis = {
            'strong_seasonal_patterns': [],
            'counter_seasonal_opportunities': [],
            'cash_flow_implications': [],
            'planning_recommendations': []
        }
        
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        # Collect monthly data across years
        category_monthly_data = {}
        
        for year in selected_years:
            if year not in financial_data or 'sections' not in financial_data[year]:
                continue
            
            for section in financial_data[year]['sections']:
                category = section['name']
                monthly_data = section.get('monthly', {})
                
                if category not in category_monthly_data:
                    category_monthly_data[category] = {month: [] for month in months}
                
                for month in months:
                    value = monthly_data.get(month, 0)
                    if value > 0:
                        category_monthly_data[category][month].append(value)
        
        # Calculate seasonal patterns
        for category, monthly_data in category_monthly_data.items():
            monthly_averages = {}
            for month, values in monthly_data.items():
                if values:
                    monthly_averages[month] = np.mean(values)
            
            if len(monthly_averages) >= 6:  # Need data for at least half the months
                overall_average = np.mean(list(monthly_averages.values()))
                
                # Calculate seasonal indices
                seasonal_indices = {}
                for month, avg in monthly_averages.items():
                    seasonal_indices[month] = avg / overall_average if overall_average > 0 else 1
                
                # Check for strong seasonality
                max_index = max(seasonal_indices.values())
                min_index = min(seasonal_indices.values())
                seasonal_strength = max_index - min_index
                
                if seasonal_strength > self.threshold_configs['seasonal_significance']:
                    peak_month = max(seasonal_indices.keys(), key=lambda k: seasonal_indices[k])
                    low_month = min(seasonal_indices.keys(), key=lambda k: seasonal_indices[k])
                    
                    seasonal_analysis['strong_seasonal_patterns'].append({
                        'category': category,
                        'seasonal_strength': seasonal_strength,
                        'peak_month': peak_month,
                        'low_month': low_month,
                        'peak_index': max_index,
                        'low_index': min_index,
                        'seasonal_indices': seasonal_indices
                    })
        
        return seasonal_analysis
    
    def _detect_anomalies(self, financial_data: Dict, selected_years: List[int]) -> Dict:
        """Detect anomalies and unusual patterns in expense data"""
        
        anomalies = {
            'expense_spikes': [],
            'unexpected_drops': [],
            'unusual_patterns': [],
            'data_quality_issues': []
        }
        
        for year in selected_years:
            if year not in financial_data or 'sections' not in financial_data[year]:
                continue
            
            sections = financial_data[year]['sections']
            
            for section in sections:
                category = section['name']
                annual_value = section.get('value', 0)
                monthly_data = section.get('monthly', {})
                
                if monthly_data:
                    monthly_values = [v for v in monthly_data.values() if v > 0]
                    
                    if len(monthly_values) > 3:
                        monthly_mean = np.mean(monthly_values)
                        monthly_std = np.std(monthly_values)
                        
                        # Detect spikes (values > mean + 2*std)
                        threshold_high = monthly_mean + 2 * monthly_std
                        threshold_low = max(0, monthly_mean - 2 * monthly_std)
                        
                        for month, value in monthly_data.items():
                            if value > threshold_high:
                                anomalies['expense_spikes'].append({
                                    'category': category,
                                    'year': year,
                                    'month': month,
                                    'value': value,
                                    'expected_range': (monthly_mean - monthly_std, monthly_mean + monthly_std),
                                    'severity': (value - threshold_high) / monthly_std
                                })
                            elif value > 0 and value < threshold_low:
                                anomalies['unexpected_drops'].append({
                                    'category': category,
                                    'year': year,
                                    'month': month,
                                    'value': value,
                                    'expected_range': (monthly_mean - monthly_std, monthly_mean + monthly_std),
                                    'severity': (threshold_low - value) / monthly_std
                                })
        
        # Sort by severity
        anomalies['expense_spikes'].sort(key=lambda x: x['severity'], reverse=True)
        anomalies['unexpected_drops'].sort(key=lambda x: x['severity'], reverse=True)
        
        return anomalies
    
    def _generate_optimization_recommendations(self, financial_data: Dict, selected_years: List[int]) -> List[Dict]:
        """Generate actionable optimization recommendations"""
        
        recommendations = []
        
        # Analyze the data first
        growth_insights = self._analyze_growth_patterns(financial_data, selected_years)
        risk_insights = self._analyze_risk_patterns(financial_data, selected_years)
        efficiency_insights = self._analyze_efficiency_patterns(financial_data, selected_years)
        
        # High growth categories recommendations
        if growth_insights.get('fastest_growing'):
            for item in growth_insights['fastest_growing'][:3]:
                recommendations.append({
                    'type': 'growth_control',
                    'priority': 'high',
                    'category': item['category'],
                    'title': f"Controlar crescimento em {item['category']}",
                    'description': f"Esta categoria cresceu {item['growth_rate']:.1%} no período {item['period']}. "
                                 f"Valor atual: {format_currency(item['current_value'])}. "
                                 f"Considere revisar contratos e processos para otimizar custos.",
                    'impact': 'cost_reduction',
                    'effort': 'medium',
                    'savings_potential': item['current_value'] * 0.10  # 10% potential savings
                })
        
        # Concentration risk recommendations
        if risk_insights.get('concentration_risks'):
            for item in risk_insights['concentration_risks'][:2]:
                recommendations.append({
                    'type': 'diversification',
                    'priority': 'high',
                    'category': item['category'],
                    'title': f"Diversificar dependência de {item['category']}",
                    'description': f"Esta categoria representa {item['concentration']:.1%} dos custos totais "
                                 f"em {item['year']}, criando risco de concentração. "
                                 f"Considere diversificar fornecedores ou reavaliar a estrutura de custos.",
                    'impact': 'risk_reduction',
                    'effort': 'high',
                    'risk_mitigation': item['concentration'] - 0.4  # Target 40% max concentration
                })
        
        # Volatility risk recommendations
        if risk_insights.get('volatility_risks'):
            for item in risk_insights['volatility_risks'][:2]:
                recommendations.append({
                    'type': 'volatility_control',
                    'priority': 'medium',
                    'category': item['category'],
                    'title': f"Estabilizar custos em {item['category']}",
                    'description': f"Esta categoria apresenta alta volatilidade "
                                 f"(CV: {item['coefficient_of_variation']:.1%}). "
                                 f"Considere contratos com preços fixos ou revisão de processos.",
                    'impact': 'predictability',
                    'effort': 'medium',
                    'volatility_reduction': item['coefficient_of_variation'] - 0.2  # Target 20% CV
                })
        
        # Efficiency improvement recommendations
        if efficiency_insights.get('cost_per_unit_trends'):
            declining_efficiency = [t for t in efficiency_insights['cost_per_unit_trends'] if t['trend'] > 0.5]
            
            for item in declining_efficiency[:2]:
                recommendations.append({
                    'type': 'efficiency_improvement',
                    'priority': 'medium',
                    'category': item['category'],
                    'title': f"Melhorar eficiência em {item['category']}",
                    'description': f"A relação custo/receita está aumentando "
                                 f"({item['trend']:+.2f}% ao ano). "
                                 f"Ratio atual: {item['current_ratio']:.2f}%. "
                                 f"Revisar processos e benchmarks de mercado.",
                    'impact': 'efficiency_gain',
                    'effort': 'medium',
                    'efficiency_potential': item['trend'] * -1  # Reverse the trend
                })
        
        # Sort recommendations by priority and impact
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return recommendations
    
    def _calculate_key_metrics(self, financial_data: Dict, selected_years: List[int]) -> Dict:
        """Calculate key performance metrics"""
        
        metrics = {
            'total_expenses_trend': 0,
            'expense_growth_rate': 0,
            'cost_concentration_index': 0,
            'expense_volatility_index': 0,
            'seasonal_impact_score': 0
        }
        
        if len(selected_years) < 2:
            return metrics
        
        # Calculate total expenses for each year
        yearly_totals = []
        for year in selected_years:
            if year in financial_data and 'sections' in financial_data[year]:
                total = sum(s.get('value', 0) for s in financial_data[year]['sections'])
                yearly_totals.append(total)
        
        if len(yearly_totals) >= 2:
            # Calculate growth trend
            if yearly_totals[0] > 0:
                metrics['expense_growth_rate'] = ((yearly_totals[-1] - yearly_totals[0]) / yearly_totals[0])
            
            # Calculate trend coefficient
            metrics['total_expenses_trend'] = np.polyfit(range(len(yearly_totals)), yearly_totals, 1)[0]
        
        # Calculate concentration index (Herfindahl-Hirschman Index)
        if selected_years:
            latest_year = selected_years[-1]
            if latest_year in financial_data and 'sections' in financial_data[latest_year]:
                sections = financial_data[latest_year]['sections']
                total_expenses = sum(s.get('value', 0) for s in sections)
                
                if total_expenses > 0:
                    hhi = sum((s.get('value', 0) / total_expenses) ** 2 for s in sections)
                    metrics['cost_concentration_index'] = hhi
        
        return metrics


def render_ai_insights_dashboard(financial_data: Dict, selected_years: List[int]):
    """
    Render the main AI insights dashboard
    """
    st.markdown("### 🤖 Insights Inteligentes")
    st.caption("Análise automatizada com recomendações acionáveis")
    
    if len(selected_years) < 2:
        st.warning("⚠️ Selecione pelo menos 2 anos para análise completa de insights")
        return
    
    # Initialize insights engine
    engine = ExpenseInsightsEngine()
    
    # Generate comprehensive insights
    with st.spinner("🔍 Analisando padrões e gerando insights..."):
        insights = engine.generate_comprehensive_insights(financial_data, selected_years)
    
    # Create tabs for different insight categories
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Crescimento", 
        "⚠️ Riscos", 
        "⚡ Eficiência", 
        "🔔 Anomalias", 
        "💡 Recomendações"
    ])
    
    with tab1:
        _render_growth_insights_tab(insights['growth_insights'])
    
    with tab2:
        _render_risk_insights_tab(insights['risk_insights'])
    
    with tab3:
        _render_efficiency_insights_tab(insights['efficiency_insights'])
    
    with tab4:
        _render_anomaly_insights_tab(insights['anomaly_insights'])
    
    with tab5:
        _render_recommendations_tab(insights['optimization_recommendations'])
    
    # Show key metrics summary
    _render_key_metrics_summary(insights['key_metrics'])


def _render_growth_insights_tab(growth_insights: Dict):
    """Render growth insights tab"""
    
    st.markdown("#### 📈 Análise de Padrões de Crescimento")
    
    if 'error' in growth_insights:
        st.warning(growth_insights['error'])
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🚀 Categorias de Maior Crescimento**")
        
        fastest_growing = growth_insights.get('fastest_growing', [])
        if fastest_growing:
            for item in fastest_growing[:5]:
                with st.container():
                    st.success(f"**{item['category']}**")
                    st.write(f"📊 Crescimento: {item['growth_rate']:+.1%}")
                    st.write(f"💰 {format_currency(item['previous_value'])} → {format_currency(item['current_value'])}")
                    st.write(f"📅 Período: {item['period']}")
                    st.markdown("---")
        else:
            st.info("Nenhuma categoria com crescimento significativo detectada")
    
    with col2:
        st.markdown("**📉 Categorias em Declínio**")
        
        declining = growth_insights.get('declining_categories', [])
        if declining:
            for item in declining[:5]:
                with st.container():
                    st.error(f"**{item['category']}**")
                    st.write(f"📊 Variação: {item['growth_rate']:+.1%}")
                    st.write(f"💰 {format_currency(item['previous_value'])} → {format_currency(item['current_value'])}")
                    st.write(f"📅 Período: {item['period']}")
                    st.markdown("---")
        else:
            st.info("Nenhuma categoria em declínio significativo detectada")


def _render_risk_insights_tab(risk_insights: Dict):
    """Render risk insights tab"""
    
    st.markdown("#### ⚠️ Análise de Riscos Identificados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 Riscos de Concentração**")
        
        concentration_risks = risk_insights.get('concentration_risks', [])
        if concentration_risks:
            for risk in concentration_risks[:3]:
                with st.container():
                    st.warning(f"**{risk['category']}** ({risk['year']})")
                    st.write(f"📊 Concentração: {risk['concentration']:.1%}")
                    st.write(f"💰 Valor: {format_currency(risk['value'])}")
                    st.write(f"🎯 % do Total: {risk['concentration']:.1%}")
                    
                    if risk['concentration'] > 0.7:
                        st.error("🔴 Risco ALTO - Dependência excessiva")
                    elif risk['concentration'] > 0.5:
                        st.warning("🟡 Risco MÉDIO - Monitorar de perto")
                    
                    st.markdown("---")
        else:
            st.success("✅ Nenhum risco de concentração crítico detectado")
    
    with col2:
        st.markdown("**📊 Riscos de Volatilidade**")
        
        volatility_risks = risk_insights.get('volatility_risks', [])
        if volatility_risks:
            for risk in volatility_risks[:3]:
                with st.container():
                    st.warning(f"**{risk['category']}**")
                    st.write(f"📊 Coeficiente de Variação: {risk['coefficient_of_variation']:.1%}")
                    st.write(f"💰 Valor Médio: {format_currency(risk['mean_value'])}")
                    st.write(f"📏 Desvio Padrão: {format_currency(risk['std_deviation'])}")
                    
                    if risk['coefficient_of_variation'] > 0.5:
                        st.error("🔴 Volatilidade ALTA - Requer atenção")
                    elif risk['coefficient_of_variation'] > 0.3:
                        st.warning("🟡 Volatilidade MÉDIA - Monitorar")
                    
                    st.markdown("---")
        else:
            st.success("✅ Volatilidade dentro de parâmetros aceitáveis")


def _render_efficiency_insights_tab(efficiency_insights: Dict):
    """Render efficiency insights tab"""
    
    st.markdown("#### ⚡ Análise de Eficiência")
    
    cost_trends = efficiency_insights.get('cost_per_unit_trends', [])
    improvements = efficiency_insights.get('efficiency_improvements', [])
    
    if cost_trends:
        st.markdown("**📊 Tendências de Eficiência de Custos**")
        
        # Separate improving vs deteriorating trends
        improving = [t for t in cost_trends if t['trend'] < -0.1]
        deteriorating = [t for t in cost_trends if t['trend'] > 0.1]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**✅ Melhorando**")
            for item in improving[:3]:
                st.success(f"**{item['category']}**")
                st.write(f"📈 Tendência: {item['trend']:+.2f}%/ano")
                st.write(f"📊 Ratio Atual: {item['current_ratio']:.2f}%")
        
        with col2:
            st.markdown("**⚠️ Deteriorando**")
            for item in deteriorating[:3]:
                st.warning(f"**{item['category']}**")
                st.write(f"📉 Tendência: {item['trend']:+.2f}%/ano")
                st.write(f"📊 Ratio Atual: {item['current_ratio']:.2f}%")
    
    else:
        st.info("Dados insuficientes para análise de eficiência")


def _render_anomaly_insights_tab(anomaly_insights: Dict):
    """Render anomaly detection results"""
    
    st.markdown("#### 🔔 Detecção de Anomalias")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📈 Picos de Despesas Detectados**")
        
        spikes = anomaly_insights.get('expense_spikes', [])
        if spikes:
            for spike in spikes[:5]:
                with st.container():
                    st.error(f"**{spike['category']}**")
                    st.write(f"📅 {spike['month']}/{spike['year']}")
                    st.write(f"💰 Valor: {format_currency(spike['value'])}")
                    st.write(f"⚠️ Severidade: {spike['severity']:.1f}σ")
                    
                    expected_min, expected_max = spike['expected_range']
                    st.write(f"📊 Faixa esperada: {format_currency(expected_min)} - {format_currency(expected_max)}")
                    st.markdown("---")
        else:
            st.success("✅ Nenhum pico anômalo detectado")
    
    with col2:
        st.markdown("**📉 Quedas Inesperadas Detectadas**")
        
        drops = anomaly_insights.get('unexpected_drops', [])
        if drops:
            for drop in drops[:5]:
                with st.container():
                    st.warning(f"**{drop['category']}**")
                    st.write(f"📅 {drop['month']}/{drop['year']}")
                    st.write(f"💰 Valor: {format_currency(drop['value'])}")
                    st.write(f"⚠️ Severidade: {drop['severity']:.1f}σ")
                    
                    expected_min, expected_max = drop['expected_range']
                    st.write(f"📊 Faixa esperada: {format_currency(expected_min)} - {format_currency(expected_max)}")
                    st.markdown("---")
        else:
            st.success("✅ Nenhuma queda anômala detectada")


def _render_recommendations_tab(recommendations: List[Dict]):
    """Render optimization recommendations"""
    
    st.markdown("#### 💡 Recomendações de Otimização")
    
    if not recommendations:
        st.info("Nenhuma recomendação específica identificada com base nos dados atuais")
        return
    
    # Group recommendations by priority
    high_priority = [r for r in recommendations if r['priority'] == 'high']
    medium_priority = [r for r in recommendations if r['priority'] == 'medium']
    low_priority = [r for r in recommendations if r['priority'] == 'low']
    
    if high_priority:
        st.markdown("### 🔴 Alta Prioridade")
        for rec in high_priority:
            with st.expander(f"🎯 {rec['title']}", expanded=True):
                st.write(rec['description'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Impacto", rec['impact'].replace('_', ' ').title())
                with col2:
                    st.metric("Esforço", rec['effort'].title())
                with col3:
                    if 'savings_potential' in rec:
                        st.metric("Economia Potencial", format_currency(rec['savings_potential']))
    
    if medium_priority:
        st.markdown("### 🟡 Prioridade Média")
        for rec in medium_priority:
            with st.expander(f"📊 {rec['title']}"):
                st.write(rec['description'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Impacto:** {rec['impact'].replace('_', ' ').title()}")
                with col2:
                    st.write(f"**Esforço:** {rec['effort'].title()}")


def _render_key_metrics_summary(key_metrics: Dict):
    """Render key metrics summary"""
    
    st.markdown("---")
    st.markdown("### 📊 Métricas-Chave Resumo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        growth_rate = key_metrics.get('expense_growth_rate', 0)
        st.metric(
            "Taxa de Crescimento",
            f"{growth_rate:+.1%}",
            delta=f"{growth_rate:+.1%}" if abs(growth_rate) > 0.05 else None
        )
    
    with col2:
        trend = key_metrics.get('total_expenses_trend', 0)
        trend_direction = "↗️" if trend > 0 else "↘️" if trend < 0 else "➡️"
        st.metric("Tendência Anual", f"{trend_direction} {format_currency(abs(trend))}")
    
    with col3:
        concentration = key_metrics.get('cost_concentration_index', 0)
        concentration_level = "Alta" if concentration > 0.3 else "Média" if concentration > 0.15 else "Baixa"
        st.metric("Concentração", f"{concentration:.3f}", help=f"Nível: {concentration_level}")
    
    with col4:
        volatility = key_metrics.get('expense_volatility_index', 0)
        st.metric("Índice Volatilidade", f"{volatility:.3f}")