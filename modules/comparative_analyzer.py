import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import google.generativeai as genai
from datetime import datetime
import json

class ComparativeAnalyzer:
    """Advanced comparative analysis engine for financial data"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def analyze_all_years(self, yearly_data: Dict[int, Dict]) -> Dict:
        """Comprehensive analysis across all years"""
        
        analysis = {
            'year_over_year': self._year_over_year_analysis(yearly_data),
            'best_worst_periods': self._find_best_worst_periods(yearly_data),
            'growth_patterns': self._analyze_growth_patterns(yearly_data),
            'seasonal_trends': self._detect_seasonal_trends(yearly_data),
            'volatility_analysis': self._analyze_volatility(yearly_data),
            'ai_insights': self._generate_ai_insights(yearly_data)
        }
        
        return analysis
    
    def _year_over_year_analysis(self, yearly_data: Dict[int, Dict]) -> Dict:
        """Detailed year-over-year comparison"""
        
        yoy_analysis = {}
        years = sorted(yearly_data.keys())
        
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            
            comparison = {
                'revenue': self._calculate_change(
                    yearly_data[prev_year].get('revenue', {}),
                    yearly_data[curr_year].get('revenue', {})
                ),
                'costs': self._calculate_change(
                    yearly_data[prev_year].get('costs', {}),
                    yearly_data[curr_year].get('costs', {})
                ),
                'margins': self._calculate_margin_change(
                    yearly_data[prev_year].get('margins', {}),
                    yearly_data[curr_year].get('margins', {})
                ),
                'monthly_changes': self._monthly_comparison(
                    yearly_data[prev_year],
                    yearly_data[curr_year]
                )
            }
            
            yoy_analysis[f"{prev_year}_to_{curr_year}"] = comparison
        
        return yoy_analysis
    
    def _calculate_change(self, prev_data: Dict, curr_data: Dict) -> Dict:
        """Calculate percentage and absolute changes"""
        
        # Get annual totals
        prev_total = prev_data.get('ANNUAL', sum(v for k, v in prev_data.items() 
                                                if isinstance(v, (int, float)) and k != 'ANNUAL'))
        curr_total = curr_data.get('ANNUAL', sum(v for k, v in curr_data.items() 
                                                if isinstance(v, (int, float)) and k != 'ANNUAL'))
        
        change = {
            'previous': prev_total,
            'current': curr_total,
            'absolute_change': curr_total - prev_total if prev_total and curr_total else 0,
            'percentage_change': ((curr_total - prev_total) / prev_total * 100) 
                                if prev_total and curr_total and prev_total != 0 else 0
        }
        
        return change
    
    def _calculate_margin_change(self, prev_margins: Dict, curr_margins: Dict) -> Dict:
        """Calculate margin changes in percentage points"""
        
        prev_avg = np.mean([v for v in prev_margins.values() if isinstance(v, (int, float))])
        curr_avg = np.mean([v for v in curr_margins.values() if isinstance(v, (int, float))])
        
        return {
            'previous_avg': prev_avg,
            'current_avg': curr_avg,
            'change_pp': curr_avg - prev_avg,
            'improvement': curr_avg > prev_avg
        }
    
    def _monthly_comparison(self, prev_year: Dict, curr_year: Dict) -> Dict:
        """Compare each month between two years"""
        
        monthly_changes = {}
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        for month in months:
            prev_rev = prev_year.get('revenue', {}).get(month, 0)
            curr_rev = curr_year.get('revenue', {}).get(month, 0)
            
            if prev_rev and curr_rev:
                change_pct = ((curr_rev - prev_rev) / prev_rev) * 100
                monthly_changes[month] = {
                    'revenue_change_pct': round(change_pct, 2),
                    'revenue_change_abs': round(curr_rev - prev_rev, 2),
                    'direction': 'up' if change_pct > 0 else 'down'
                }
        
        return monthly_changes
    
    def _find_best_worst_periods(self, yearly_data: Dict[int, Dict]) -> Dict:
        """Identify best and worst performing periods"""
        
        all_periods = []
        
        # Collect all monthly data points
        for year, data in yearly_data.items():
            revenue_data = data.get('revenue', {})
            margin_data = data.get('margins', {})
            
            for month, revenue in revenue_data.items():
                if month != 'ANNUAL' and isinstance(revenue, (int, float)):
                    all_periods.append({
                        'year': year,
                        'month': month,
                        'revenue': revenue,
                        'margin': margin_data.get(month, 0),
                        'period': f"{month}/{year}"
                    })
        
        # Sort and find extremes
        revenue_sorted = sorted(all_periods, key=lambda x: x['revenue'], reverse=True)
        margin_sorted = sorted(all_periods, key=lambda x: x['margin'], reverse=True)
        
        return {
            'best_revenue_months': revenue_sorted[:5],
            'worst_revenue_months': revenue_sorted[-5:],
            'best_margin_months': margin_sorted[:5],
            'worst_margin_months': margin_sorted[-5:],
            'insights': self._generate_period_insights(revenue_sorted, margin_sorted)
        }
    
    def _analyze_growth_patterns(self, yearly_data: Dict[int, Dict]) -> Dict:
        """Analyze growth acceleration/deceleration patterns"""
        
        years = sorted(yearly_data.keys())
        growth_rates = []
        
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            
            prev_revenue = yearly_data[prev_year].get('revenue', {}).get('ANNUAL', 0)
            curr_revenue = yearly_data[curr_year].get('revenue', {}).get('ANNUAL', 0)
            
            if prev_revenue > 0:
                growth_rate = ((curr_revenue - prev_revenue) / prev_revenue) * 100
                growth_rates.append({
                    'period': f"{prev_year}-{curr_year}",
                    'growth_rate': growth_rate
                })
        
        # Analyze acceleration
        acceleration = []
        for i in range(1, len(growth_rates)):
            accel = growth_rates[i]['growth_rate'] - growth_rates[i-1]['growth_rate']
            acceleration.append({
                'period': growth_rates[i]['period'],
                'acceleration': accel,
                'trend': 'accelerating' if accel > 0 else 'decelerating'
            })
        
        return {
            'growth_rates': growth_rates,
            'acceleration': acceleration,
            'average_growth': np.mean([g['growth_rate'] for g in growth_rates]),
            'growth_volatility': np.std([g['growth_rate'] for g in growth_rates]),
            'trend': self._determine_overall_trend(growth_rates)
        }
    
    def _detect_seasonal_trends(self, yearly_data: Dict[int, Dict]) -> Dict:
        """Detect seasonal patterns across years"""
        
        monthly_aggregates = {}
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        # Aggregate data by month across all years
        for month in months:
            month_values = []
            
            for year, data in yearly_data.items():
                revenue = data.get('revenue', {}).get(month)
                if revenue and isinstance(revenue, (int, float)):
                    month_values.append(revenue)
            
            if month_values:
                monthly_aggregates[month] = {
                    'average': np.mean(month_values),
                    'std': np.std(month_values),
                    'cv': np.std(month_values) / np.mean(month_values) if np.mean(month_values) > 0 else 0,
                    'values': month_values
                }
        
        # Identify seasonal patterns
        avg_by_month = {m: d['average'] for m, d in monthly_aggregates.items()}
        overall_avg = np.mean(list(avg_by_month.values()))
        
        seasonal_index = {
            month: (avg / overall_avg) * 100 
            for month, avg in avg_by_month.items()
        }
        
        # Classify months
        strong_months = [m for m, idx in seasonal_index.items() if idx > 110]
        weak_months = [m for m, idx in seasonal_index.items() if idx < 90]
        
        return {
            'monthly_averages': monthly_aggregates,
            'seasonal_index': seasonal_index,
            'strong_months': strong_months,
            'weak_months': weak_months,
            'quarterly_pattern': self._analyze_quarterly_pattern(seasonal_index)
        }
    
    def _analyze_quarterly_pattern(self, seasonal_index: Dict) -> Dict:
        """Analyze quarterly patterns"""
        
        q1 = np.mean([seasonal_index.get(m, 100) for m in ['JAN', 'FEV', 'MAR']])
        q2 = np.mean([seasonal_index.get(m, 100) for m in ['ABR', 'MAI', 'JUN']])
        q3 = np.mean([seasonal_index.get(m, 100) for m in ['JUL', 'AGO', 'SET']])
        q4 = np.mean([seasonal_index.get(m, 100) for m in ['OUT', 'NOV', 'DEZ']])
        
        quarters = {'Q1': q1, 'Q2': q2, 'Q3': q3, 'Q4': q4}
        best_quarter = max(quarters, key=quarters.get)
        worst_quarter = min(quarters, key=quarters.get)
        
        return {
            'quarter_index': quarters,
            'best_quarter': best_quarter,
            'worst_quarter': worst_quarter,
            'variance': np.std(list(quarters.values()))
        }
    
    def _analyze_volatility(self, yearly_data: Dict[int, Dict]) -> Dict:
        """Analyze revenue and margin volatility"""
        
        volatility_analysis = {}
        
        for year, data in yearly_data.items():
            revenue_data = data.get('revenue', {})
            margin_data = data.get('margins', {})
            
            # Get monthly values (excluding ANNUAL)
            monthly_revenues = [v for k, v in revenue_data.items() 
                              if k != 'ANNUAL' and isinstance(v, (int, float))]
            monthly_margins = [v for k, v in margin_data.items() 
                             if k != 'ANNUAL' and isinstance(v, (int, float))]
            
            if monthly_revenues:
                volatility_analysis[year] = {
                    'revenue_volatility': {
                        'std': np.std(monthly_revenues),
                        'cv': np.std(monthly_revenues) / np.mean(monthly_revenues),
                        'range': max(monthly_revenues) - min(monthly_revenues)
                    },
                    'margin_volatility': {
                        'std': np.std(monthly_margins) if monthly_margins else 0,
                        'range': (max(monthly_margins) - min(monthly_margins)) if monthly_margins else 0
                    }
                }
        
        # Trend in volatility
        years = sorted(volatility_analysis.keys())
        volatility_trend = 'increasing' if len(years) > 1 and \
            volatility_analysis[years[-1]]['revenue_volatility']['cv'] > \
            volatility_analysis[years[0]]['revenue_volatility']['cv'] else 'decreasing'
        
        return {
            'yearly_volatility': volatility_analysis,
            'volatility_trend': volatility_trend
        }
    
    def _generate_ai_insights(self, yearly_data: Dict[int, Dict]) -> str:
        """Generate comprehensive AI insights"""
        
        # Prepare data summary for AI
        data_summary = {
            'years_analyzed': list(yearly_data.keys()),
            'revenue_by_year': {
                year: data.get('revenue', {}).get('ANNUAL', 0) 
                for year, data in yearly_data.items()
            },
            'growth_pattern': self._analyze_growth_patterns(yearly_data),
            'seasonal_trends': self._detect_seasonal_trends(yearly_data)
        }
        
        prompt = f"""
        Analyze this multi-year financial data for Marine Seguros and provide strategic insights:
        
        Data Summary:
        {json.dumps(data_summary, indent=2)}
        
        Please provide:
        1. **Executive Summary**: 2-3 key takeaways
        2. **Growth Analysis**: Is the business healthy? Growing? Declining?
        3. **Seasonal Patterns**: Which months/quarters drive the business?
        4. **Risk Factors**: What concerns do you see in the data?
        5. **Opportunities**: Where can they improve?
        6. **Strategic Recommendations**: 3-5 specific actions
        
        Focus on actionable insights that would help management make decisions.
        Be specific with numbers and percentages.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI insight generation error: {str(e)}"
    
    def _determine_overall_trend(self, growth_rates: List[Dict]) -> str:
        """Determine the overall business trend"""
        
        if not growth_rates:
            return "insufficient_data"
        
        # Simple linear regression on growth rates
        if len(growth_rates) >= 3:
            rates = [g['growth_rate'] for g in growth_rates]
            x = np.arange(len(rates))
            slope = np.polyfit(x, rates, 1)[0]
            
            if slope > 5:
                return "strong_growth"
            elif slope > 0:
                return "moderate_growth"
            elif slope > -5:
                return "stagnating"
            else:
                return "declining"
        else:
            # Simple comparison for fewer data points
            avg_growth = np.mean([g['growth_rate'] for g in growth_rates])
            if avg_growth > 20:
                return "strong_growth"
            elif avg_growth > 5:
                return "moderate_growth"
            elif avg_growth > -5:
                return "stable"
            else:
                return "declining"
    
    def _generate_period_insights(self, revenue_sorted: List, margin_sorted: List) -> str:
        """Generate insights about best/worst periods"""
        
        insights = []
        
        # Best revenue months pattern
        best_months = [p['month'] for p in revenue_sorted[:5]]
        if 'DEZ' in best_months or 'NOV' in best_months:
            insights.append("Strong year-end performance (November/December)")
        
        # Worst revenue months pattern
        worst_months = [p['month'] for p in revenue_sorted[-5:]]
        if any(m in worst_months for m in ['JAN', 'FEV']):
            insights.append("Weak start to the year (January/February)")
        
        # Margin insights
        best_margin_months = [p['month'] for p in margin_sorted[:5]]
        if len(set(best_margin_months)) <= 3:
            insights.append(f"Consistent high margins in {', '.join(set(best_margin_months))}")
        
        return " | ".join(insights)

    def compare_custom_periods(self, period1_data: Dict, period2_data: Dict, 
                              period1_name: str, period2_name: str) -> Dict:
        """Custom period comparison with AI insights"""
        
        comparison = {
            'metrics': {
                'revenue': self._calculate_change(
                    period1_data.get('revenue', {}),
                    period2_data.get('revenue', {})
                ),
                'costs': self._calculate_change(
                    period1_data.get('costs', {}),
                    period2_data.get('costs', {})
                ),
                'margins': self._calculate_margin_change(
                    period1_data.get('margins', {}),
                    period2_data.get('margins', {})
                )
            },
            'monthly_detail': self._monthly_comparison(period1_data, period2_data),
            'ai_analysis': self._generate_comparison_insights(
                period1_data, period2_data, period1_name, period2_name
            )
        }
        
        return comparison
    
    def _generate_comparison_insights(self, data1: Dict, data2: Dict, 
                                    name1: str, name2: str) -> str:
        """Generate AI insights for period comparison"""
        
        prompt = f"""
        Compare these two financial periods and explain the changes:
        
        {name1}: Revenue: R$ {data1.get('revenue', {}).get('ANNUAL', 0):,.2f}
        {name2}: Revenue: R$ {data2.get('revenue', {}).get('ANNUAL', 0):,.2f}
        
        Monthly changes: {self._monthly_comparison(data1, data2)}
        
        Provide:
        1. What changed and why (be specific)
        2. Which months drove the change
        3. What this means for the business
        4. Recommended actions
        
        Keep it concise and actionable.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return "Comparison analysis unavailable"