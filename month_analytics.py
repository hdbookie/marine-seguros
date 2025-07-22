import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import streamlit as st

class MonthAnalytics:
    """Advanced month-level analytics and insights"""
    
    def __init__(self):
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        self.month_names = {
            'JAN': 'Janeiro', 'FEV': 'Fevereiro', 'MAR': 'Março',
            'ABR': 'Abril', 'MAI': 'Maio', 'JUN': 'Junho',
            'JUL': 'Julho', 'AGO': 'Agosto', 'SET': 'Setembro',
            'OUT': 'Outubro', 'NOV': 'Novembro', 'DEZ': 'Dezembro'
        }
        
        self.quarters = {
            'Q1': ['JAN', 'FEV', 'MAR'],
            'Q2': ['ABR', 'MAI', 'JUN'],
            'Q3': ['JUL', 'AGO', 'SET'],
            'Q4': ['OUT', 'NOV', 'DEZ']
        }
    
    def analyze_month_performance(self, data: Dict, month: str) -> Dict:
        """Deep analysis of a specific month across all years"""
        
        analysis = {
            'month': month,
            'month_name': self.month_names[month],
            'yearly_performance': {},
            'statistics': {},
            'trends': {},
            'insights': []
        }
        
        # Collect month data across years
        month_values = []
        month_margins = []
        month_costs = []
        
        for year, year_data in sorted(data.items()):
            revenue = year_data.get('revenue', {}).get(month, 0)
            margin = year_data.get('margins', {}).get(month, 0)
            cost = year_data.get('costs', {}).get(month, 0)
            
            analysis['yearly_performance'][year] = {
                'revenue': revenue,
                'margin': margin,
                'cost': cost
            }
            
            if revenue > 0:
                month_values.append(revenue)
                month_margins.append(margin)
                month_costs.append(cost)
        
        # Calculate statistics
        if month_values:
            analysis['statistics'] = {
                'avg_revenue': np.mean(month_values),
                'median_revenue': np.median(month_values),
                'std_revenue': np.std(month_values),
                'cv_revenue': np.std(month_values) / np.mean(month_values) * 100,
                'min_revenue': min(month_values),
                'max_revenue': max(month_values),
                'avg_margin': np.mean(month_margins) if month_margins else 0,
                'avg_cost': np.mean(month_costs) if month_costs else 0
            }
            
            # Calculate growth trend
            if len(month_values) > 1:
                growths = []
                for i in range(1, len(month_values)):
                    growth = ((month_values[i] - month_values[i-1]) / month_values[i-1] * 100)
                    growths.append(growth)
                
                analysis['trends'] = {
                    'avg_growth': np.mean(growths),
                    'growth_volatility': np.std(growths),
                    'consistent_growth': all(g > 0 for g in growths),
                    'last_growth': growths[-1] if growths else 0
                }
            
            # Generate insights
            analysis['insights'] = self._generate_month_insights(analysis, data)
        
        return analysis
    
    def compare_months(self, data: Dict, months: List[str]) -> Dict:
        """Compare multiple months performance"""
        
        comparison = {
            'months': months,
            'metrics': {},
            'rankings': {},
            'patterns': []
        }
        
        # Calculate metrics for each month
        for month in months:
            month_analysis = self.analyze_month_performance(data, month)
            comparison['metrics'][month] = month_analysis['statistics']
        
        # Rank months by different criteria
        if comparison['metrics']:
            # Revenue ranking
            revenue_rank = sorted(
                [(m, metrics['avg_revenue']) for m, metrics in comparison['metrics'].items()],
                key=lambda x: x[1],
                reverse=True
            )
            comparison['rankings']['revenue'] = revenue_rank
            
            # Margin ranking
            margin_rank = sorted(
                [(m, metrics['avg_margin']) for m, metrics in comparison['metrics'].items()],
                key=lambda x: x[1],
                reverse=True
            )
            comparison['rankings']['margin'] = margin_rank
            
            # Stability ranking (lower CV is better)
            stability_rank = sorted(
                [(m, metrics['cv_revenue']) for m, metrics in comparison['metrics'].items()],
                key=lambda x: x[1]
            )
            comparison['rankings']['stability'] = stability_rank
        
        # Identify patterns
        comparison['patterns'] = self._identify_month_patterns(comparison)
        
        return comparison
    
    def analyze_seasonal_patterns(self, data: Dict) -> Dict:
        """Analyze seasonal patterns in the data"""
        
        seasonal_analysis = {
            'quarterly_performance': {},
            'seasonal_index': {},
            'best_season': None,
            'worst_season': None,
            'holiday_impact': {}
        }
        
        # Analyze by quarters
        for quarter, months in self.quarters.items():
            quarter_revenues = []
            
            for year_data in data.values():
                quarter_total = sum(
                    year_data.get('revenue', {}).get(month, 0) 
                    for month in months
                )
                if quarter_total > 0:
                    quarter_revenues.append(quarter_total)
            
            if quarter_revenues:
                seasonal_analysis['quarterly_performance'][quarter] = {
                    'avg_revenue': np.mean(quarter_revenues),
                    'total_revenue': sum(quarter_revenues),
                    'volatility': np.std(quarter_revenues)
                }
        
        # Calculate seasonal index (100 = average)
        total_monthly_avg = {}
        for month in self.months:
            month_totals = []
            for year_data in data.values():
                value = year_data.get('revenue', {}).get(month, 0)
                if value > 0:
                    month_totals.append(value)
            
            if month_totals:
                total_monthly_avg[month] = np.mean(month_totals)
        
        if total_monthly_avg:
            overall_avg = np.mean(list(total_monthly_avg.values()))
            
            for month, avg in total_monthly_avg.items():
                seasonal_analysis['seasonal_index'][month] = (avg / overall_avg) * 100
        
        # Identify best/worst seasons
        if seasonal_analysis['quarterly_performance']:
            best_q = max(seasonal_analysis['quarterly_performance'].items(), 
                        key=lambda x: x[1]['avg_revenue'])
            worst_q = min(seasonal_analysis['quarterly_performance'].items(), 
                         key=lambda x: x[1]['avg_revenue'])
            
            seasonal_analysis['best_season'] = best_q[0]
            seasonal_analysis['worst_season'] = worst_q[0]
        
        # Analyze holiday impact (Nov-Dec)
        holiday_months = ['NOV', 'DEZ']
        holiday_revenues = []
        non_holiday_revenues = []
        
        for year_data in data.values():
            holiday_total = sum(
                year_data.get('revenue', {}).get(month, 0) 
                for month in holiday_months
            )
            non_holiday_total = sum(
                year_data.get('revenue', {}).get(month, 0) 
                for month in self.months if month not in holiday_months
            )
            
            if holiday_total > 0:
                holiday_revenues.append(holiday_total / len(holiday_months))
            if non_holiday_total > 0:
                non_holiday_revenues.append(non_holiday_total / (len(self.months) - len(holiday_months)))
        
        if holiday_revenues and non_holiday_revenues:
            holiday_avg = np.mean(holiday_revenues)
            non_holiday_avg = np.mean(non_holiday_revenues)
            
            seasonal_analysis['holiday_impact'] = {
                'holiday_avg': holiday_avg,
                'non_holiday_avg': non_holiday_avg,
                'impact_percentage': ((holiday_avg - non_holiday_avg) / non_holiday_avg * 100)
            }
        
        return seasonal_analysis
    
    def find_month_correlations(self, data: Dict) -> Dict:
        """Find correlations between months"""
        
        # Create a matrix of monthly revenues
        years = sorted(data.keys())
        revenue_matrix = []
        
        for year in years:
            year_revenues = []
            for month in self.months:
                revenue = data[year].get('revenue', {}).get(month, 0)
                year_revenues.append(revenue)
            revenue_matrix.append(year_revenues)
        
        # Convert to DataFrame for correlation
        df = pd.DataFrame(revenue_matrix, columns=self.months)
        
        # Calculate correlation matrix
        correlation_matrix = df.corr()
        
        # Find strong correlations
        strong_correlations = []
        for i, month1 in enumerate(self.months):
            for j, month2 in enumerate(self.months):
                if i < j:  # Avoid duplicates
                    corr = correlation_matrix.loc[month1, month2]
                    if abs(corr) > 0.7:  # Strong correlation threshold
                        strong_correlations.append({
                            'month1': month1,
                            'month2': month2,
                            'correlation': corr,
                            'type': 'positive' if corr > 0 else 'negative'
                        })
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'strong_correlations': strong_correlations
        }
    
    def _generate_month_insights(self, analysis: Dict, full_data: Dict) -> List[str]:
        """Generate insights for a specific month"""
        insights = []
        
        stats = analysis['statistics']
        trends = analysis['trends']
        month = analysis['month']
        month_name = analysis['month_name']
        
        # Performance relative to average
        all_revenues = []
        for year_data in full_data.values():
            for m, revenue in year_data.get('revenue', {}).items():
                if m != 'ANNUAL' and revenue > 0:
                    all_revenues.append(revenue)
        
        if all_revenues:
            overall_avg = np.mean(all_revenues)
            month_avg = stats['avg_revenue']
            
            perf_pct = ((month_avg - overall_avg) / overall_avg * 100)
            
            if perf_pct > 20:
                insights.append(f"{month_name} é um mês forte, com receita {perf_pct:.0f}% acima da média geral")
            elif perf_pct < -20:
                insights.append(f"{month_name} é um mês desafiador, com receita {abs(perf_pct):.0f}% abaixo da média")
        
        # Volatility insight
        if stats['cv_revenue'] > 30:
            insights.append(f"{month_name} tem alta volatilidade (CV: {stats['cv_revenue']:.0f}%), indicando inconsistência")
        elif stats['cv_revenue'] < 15:
            insights.append(f"{month_name} é muito consistente (CV: {stats['cv_revenue']:.0f}%)")
        
        # Growth trend
        if trends:
            if trends['consistent_growth']:
                insights.append(f"{month_name} mostra crescimento consistente ano após ano")
            elif trends['avg_growth'] > 10:
                insights.append(f"{month_name} tem crescimento médio forte de {trends['avg_growth']:.0f}% ao ano")
            elif trends['avg_growth'] < -5:
                insights.append(f"{month_name} está em declínio com queda média de {abs(trends['avg_growth']):.0f}% ao ano")
        
        # Margin insight
        if stats['avg_margin'] > 35:
            insights.append(f"{month_name} tem excelente margem média de {stats['avg_margin']:.0f}%")
        elif stats['avg_margin'] < 20:
            insights.append(f"A margem em {month_name} ({stats['avg_margin']:.0f}%) precisa de atenção")
        
        return insights
    
    def _identify_month_patterns(self, comparison: Dict) -> List[str]:
        """Identify patterns in month comparison"""
        patterns = []
        
        # Check for consistent winners/losers
        if comparison['rankings']['revenue']:
            top_month = comparison['rankings']['revenue'][0][0]
            bottom_month = comparison['rankings']['revenue'][-1][0]
            
            patterns.append(f"{self.month_names[top_month]} consistentemente lidera em receita")
            patterns.append(f"{self.month_names[bottom_month]} consistentemente tem menor receita")
        
        # Check for volatility patterns
        if comparison['rankings']['stability']:
            most_stable = comparison['rankings']['stability'][0][0]
            least_stable = comparison['rankings']['stability'][-1][0]
            
            if comparison['metrics'][most_stable]['cv_revenue'] < 20:
                patterns.append(f"{self.month_names[most_stable]} é o mês mais previsível")
            if comparison['metrics'][least_stable]['cv_revenue'] > 40:
                patterns.append(f"{self.month_names[least_stable]} tem alta imprevisibilidade")
        
        return patterns