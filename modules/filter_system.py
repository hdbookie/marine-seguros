import streamlit as st
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
import json
from dataclasses import dataclass, asdict

@dataclass
class FilterState:
    """Represents the current state of all filters"""
    years: Set[int]
    months: Set[str]
    quarters: Set[str]
    metrics: Set[str]
    comparison_mode: str  # 'none', 'yoy', 'mom', 'qoq'
    performance_filter: Optional[str]  # 'top3', 'bottom3', 'above_avg', 'below_avg'
    
    def to_dict(self):
        return {
            'years': list(self.years),
            'months': list(self.months),
            'quarters': list(self.quarters),
            'metrics': list(self.metrics),
            'comparison_mode': self.comparison_mode,
            'performance_filter': self.performance_filter
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            years=set(data.get('years', [])),
            months=set(data.get('months', [])),
            quarters=set(data.get('quarters', [])),
            metrics=set(data.get('metrics', [])),
            comparison_mode=data.get('comparison_mode', 'none'),
            performance_filter=data.get('performance_filter', None)
        )

class FilterSystem:
    """Advanced filtering system with Power BI-style interactions"""
    
    def __init__(self):
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        self.quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        self.metrics = ['Revenue', 'Costs', 'Margins', 'Profit']
        
        # Month groupings
        self.month_groups = {
            'Q1': ['JAN', 'FEV', 'MAR'],
            'Q2': ['ABR', 'MAI', 'JUN'],
            'Q3': ['JUL', 'AGO', 'SET'],
            'Q4': ['OUT', 'NOV', 'DEZ'],
            'Verão': ['DEZ', 'JAN', 'FEV'],  # Brazilian summer
            'Inverno': ['JUN', 'JUL', 'AGO'],  # Brazilian winter
            'Fim de Ano': ['NOV', 'DEZ'],
            'Início de Ano': ['JAN', 'FEV']
        }
        
        # Initialize session state
        if 'filter_state' not in st.session_state:
            st.session_state.filter_state = FilterState(
                years=set(),
                months=set(),
                quarters=set(),
                metrics={'Revenue'},
                comparison_mode='none',
                performance_filter=None
            )
        
        if 'filter_bookmarks' not in st.session_state:
            st.session_state.filter_bookmarks = {}
    
    def render_filter_bar(self, data: Dict) -> FilterState:
        """Render the main filter bar with all controls"""
        
        # Get available years from data
        available_years = sorted(data.keys()) if data else []
        
        # Main filter container
        filter_container = st.container()
        
        with filter_container:
            # Year selector row
            st.markdown("### 📅 Filtros de Período")
            year_cols = st.columns(len(available_years) + 2)
            
            # Year checkboxes
            for i, year in enumerate(available_years):
                with year_cols[i]:
                    if st.checkbox(str(year), 
                                 value=year in st.session_state.filter_state.years,
                                 key=f"year_{year}"):
                        st.session_state.filter_state.years.add(year)
                    else:
                        st.session_state.filter_state.years.discard(year)
            
            # Select all / Clear all buttons
            with year_cols[-2]:
                if st.button("Todos", key="select_all_years"):
                    st.session_state.filter_state.years = set(available_years)
                    st.rerun()
            
            with year_cols[-1]:
                if st.button("Limpar", key="clear_years"):
                    st.session_state.filter_state.years = set()
                    st.rerun()
            
            # Month selector with visual grid
            st.markdown("### 📅 Filtros de Mês")
            self._render_month_grid(data)
            
            # Quick filters row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("#### 🎯 Filtros Rápidos")
                if st.button("Top 3 Meses", key="top3_months"):
                    self._apply_performance_filter(data, 'top3')
                if st.button("Bottom 3 Meses", key="bottom3_months"):
                    self._apply_performance_filter(data, 'bottom3')
            
            with col2:
                st.markdown("#### 🌊 Sazonalidade")
                season = st.selectbox(
                    "Período",
                    ["Nenhum", "Q1", "Q2", "Q3", "Q4", "Verão", "Inverno", "Fim de Ano"],
                    key="season_filter"
                )
                if season != "Nenhum" and season in self.month_groups:
                    st.session_state.filter_state.months = set(self.month_groups[season])
            
            with col3:
                st.markdown("#### 📊 Métricas")
                for metric in self.metrics:
                    if st.checkbox(metric, 
                                 value=metric in st.session_state.filter_state.metrics,
                                 key=f"metric_{metric}"):
                        st.session_state.filter_state.metrics.add(metric)
                    else:
                        st.session_state.filter_state.metrics.discard(metric)
            
            with col4:
                st.markdown("#### 🔖 Favoritos")
                # Bookmark management
                bookmark_name = st.text_input("Nome do filtro", key="bookmark_name")
                if st.button("💾 Salvar", key="save_bookmark") and bookmark_name:
                    self._save_bookmark(bookmark_name)
                
                # Load bookmark
                saved_bookmarks = list(st.session_state.filter_bookmarks.keys())
                if saved_bookmarks:
                    selected_bookmark = st.selectbox(
                        "Carregar filtro",
                        ["Nenhum"] + saved_bookmarks,
                        key="load_bookmark"
                    )
                    if selected_bookmark != "Nenhum":
                        self._load_bookmark(selected_bookmark)
            
            # Active filters summary
            self._render_active_filters_summary()
        
        return st.session_state.filter_state
    
    def _render_month_grid(self, data: Dict):
        """Render interactive month grid with performance indicators"""
        
        # Calculate month performance if data available
        month_performance = self._calculate_month_performance(data) if data else {}
        
        # Create 3x4 grid for months
        for row in range(3):
            cols = st.columns(4)
            for col in range(4):
                month_idx = row * 4 + col
                month = self.months[month_idx]
                
                with cols[col]:
                    # Get performance indicator
                    perf = month_performance.get(month, {})
                    avg_growth = perf.get('avg_growth', 0)
                    
                    # Color coding
                    if avg_growth > 10:
                        indicator = "🟢"
                        color = "green"
                    elif avg_growth > 0:
                        indicator = "🟡"
                        color = "yellow"
                    else:
                        indicator = "🔴"
                        color = "red"
                    
                    # Month button with indicator
                    selected = month in st.session_state.filter_state.months
                    
                    button_label = f"{month} {indicator}"
                    if avg_growth != 0:
                        button_label += f"\n{avg_growth:+.0f}%"
                    
                    if st.button(
                        button_label,
                        key=f"month_{month}",
                        type="primary" if selected else "secondary"
                    ):
                        if selected:
                            st.session_state.filter_state.months.discard(month)
                        else:
                            st.session_state.filter_state.months.add(month)
                        st.rerun()
    
    def _calculate_month_performance(self, data: Dict) -> Dict:
        """Calculate average performance for each month across all years"""
        month_data = {month: {'total_revenue': 0, 'count': 0, 'values': []} 
                     for month in self.months}
        
        for year, year_data in data.items():
            revenue_data = year_data.get('revenue', {})
            for month in self.months:
                if month in revenue_data:
                    value = revenue_data[month]
                    month_data[month]['values'].append(value)
                    month_data[month]['total_revenue'] += value
                    month_data[month]['count'] += 1
        
        # Calculate average and growth
        month_performance = {}
        for month, data in month_data.items():
            if data['count'] > 0:
                avg_revenue = data['total_revenue'] / data['count']
                # Calculate average growth if we have multiple years
                if len(data['values']) > 1:
                    growths = []
                    for i in range(1, len(data['values'])):
                        if data['values'][i-1] > 0:
                            growth = ((data['values'][i] - data['values'][i-1]) / 
                                    data['values'][i-1]) * 100
                            growths.append(growth)
                    avg_growth = sum(growths) / len(growths) if growths else 0
                else:
                    avg_growth = 0
                
                month_performance[month] = {
                    'avg_revenue': avg_revenue,
                    'avg_growth': avg_growth
                }
        
        return month_performance
    
    def _apply_performance_filter(self, data: Dict, filter_type: str):
        """Apply performance-based filters"""
        month_performance = self._calculate_month_performance(data)
        
        # Sort months by performance
        sorted_months = sorted(
            month_performance.items(),
            key=lambda x: x[1]['avg_revenue'],
            reverse=True
        )
        
        if filter_type == 'top3':
            st.session_state.filter_state.months = set([m[0] for m in sorted_months[:3]])
        elif filter_type == 'bottom3':
            st.session_state.filter_state.months = set([m[0] for m in sorted_months[-3:]])
        
        st.session_state.filter_state.performance_filter = filter_type
        st.rerun()
    
    def _render_active_filters_summary(self):
        """Show summary of active filters"""
        active_filters = []
        
        if st.session_state.filter_state.years:
            years_str = ", ".join(map(str, sorted(st.session_state.filter_state.years)))
            active_filters.append(f"Anos: {years_str}")
        
        if st.session_state.filter_state.months:
            months_str = ", ".join(sorted(st.session_state.filter_state.months, 
                                         key=lambda x: self.months.index(x)))
            active_filters.append(f"Meses: {months_str}")
        
        if st.session_state.filter_state.performance_filter:
            active_filters.append(f"Filtro: {st.session_state.filter_state.performance_filter}")
        
        if active_filters:
            st.info(f"🎯 Filtros ativos: {' | '.join(active_filters)}")
    
    def _save_bookmark(self, name: str):
        """Save current filter state as bookmark"""
        st.session_state.filter_bookmarks[name] = st.session_state.filter_state.to_dict()
        st.success(f"✅ Filtro '{name}' salvo!")
    
    def _load_bookmark(self, name: str):
        """Load saved bookmark"""
        if name in st.session_state.filter_bookmarks:
            bookmark_data = st.session_state.filter_bookmarks[name]
            st.session_state.filter_state = FilterState.from_dict(bookmark_data)
            st.rerun()
    
    def apply_filters(self, data: Dict) -> Dict:
        """Apply current filters to data"""
        filtered_data = {}
        
        # Filter by years
        years_to_include = st.session_state.filter_state.years
        if not years_to_include:
            years_to_include = set(data.keys())
        
        for year in years_to_include:
            if year in data:
                year_data = data[year].copy()
                
                # Filter by months if specified
                if st.session_state.filter_state.months:
                    # Filter revenue data
                    if 'revenue' in year_data:
                        filtered_revenue = {}
                        for month in st.session_state.filter_state.months:
                            if month in year_data['revenue']:
                                filtered_revenue[month] = year_data['revenue'][month]
                        year_data['revenue'] = filtered_revenue
                    
                    # Filter other metric data similarly
                    for metric in ['costs', 'profits', 'margins']:
                        if metric in year_data:
                            filtered_metric = {}
                            for month in st.session_state.filter_state.months:
                                if month in year_data[metric]:
                                    filtered_metric[month] = year_data[metric][month]
                            year_data[metric] = filtered_metric
                
                filtered_data[year] = year_data
        
        return filtered_data
    
    def get_filter_context(self) -> str:
        """Get human-readable description of current filters"""
        parts = []
        
        if st.session_state.filter_state.years:
            years = sorted(st.session_state.filter_state.years)
            if len(years) == 1:
                parts.append(f"ano {years[0]}")
            else:
                parts.append(f"anos {min(years)}-{max(years)}")
        
        if st.session_state.filter_state.months:
            months = sorted(st.session_state.filter_state.months, 
                          key=lambda x: self.months.index(x))
            if len(months) <= 3:
                parts.append(f"meses {', '.join(months)}")
            else:
                parts.append(f"{len(months)} meses selecionados")
        
        if st.session_state.filter_state.performance_filter:
            parts.append(st.session_state.filter_state.performance_filter)
        
        return f"Filtrado por: {', '.join(parts)}" if parts else "Sem filtros aplicados"