"""
Unified Comparison Component
Bridges macro-level dashboard data with micro-level hierarchical analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple, Any
from utils.legacy_helpers import format_currency


class UnifiedComparisonEngine:
    """
    Engine for creating unified comparisons between macro and micro data
    """
    
    def __init__(self, macro_data: Dict, micro_data: Dict):
        """
        Initialize with both macro and micro data
        
        Args:
            macro_data: Processed macro-level data from dashboard
            micro_data: Unified micro-level data from hierarchy extractor
        """
        self.macro_data = macro_data
        self.micro_data = micro_data
        
    def create_unified_comparison_chart(
        self, 
        section: str = "CUSTOS FIXOS",
        years: List[int] = None,
        chart_type: str = "side_by_side"
    ) -> Optional[go.Figure]:
        """
        Create a unified comparison chart that shows both macro totals and micro breakdowns
        
        Args:
            section: Section to focus on (e.g., "CUSTOS FIXOS")
            years: Years to compare
            chart_type: Type of chart ("side_by_side", "stacked", "waterfall")
            
        Returns:
            Plotly figure or None
        """
        if not years:
            years = self._get_common_years()
        
        if len(years) < 2:
            return None
            
        if chart_type == "side_by_side":
            return self._create_side_by_side_comparison(section, years)
        elif chart_type == "stacked":
            return self._create_stacked_comparison(section, years)
        elif chart_type == "waterfall":
            return self._create_waterfall_comparison(section, years)
        
        return None
    
    def _get_common_years(self) -> List[int]:
        """Get years that exist in both macro and micro data"""
        macro_years = set()
        micro_years = set()
        
        # Get macro years
        if self.macro_data and 'consolidated' in self.macro_data:
            df = self.macro_data['consolidated']
            if isinstance(df, pd.DataFrame) and 'year' in df.columns:
                macro_years = set(df['year'].unique())
        
        # Get micro years
        if self.micro_data:
            micro_years = set(self.micro_data.keys())
        
        # Return intersection, sorted
        common_years = sorted(list(macro_years & micro_years))
        return common_years[-3:]  # Last 3 years
    
    def _create_side_by_side_comparison(self, section: str, years: List[int]) -> go.Figure:
        """Create side-by-side comparison chart"""
        fig = go.Figure()
        
        # Get macro data for this section
        macro_totals = self._get_macro_totals_by_section(section, years)
        
        # Get micro breakdown for this section
        micro_breakdown = self._get_micro_breakdown_by_section(section, years)
        
        # Create grouped bars
        x_positions = []
        bar_width = 0.35
        
        for i, year in enumerate(years):
            # Macro bar
            x_macro = i - bar_width/2
            macro_value = macro_totals.get(year, 0)
            
            fig.add_trace(go.Bar(
                name=f'Total {year}' if i == 0 else '',
                x=[x_macro],
                y=[macro_value],
                width=bar_width,
                marker_color='rgba(55, 128, 191, 0.7)',
                text=format_currency(macro_value),
                textposition='outside',
                legendgroup='macro',
                showlegend=(i == 0),
                hovertemplate=f'<b>{section} - {year}</b><br>' +
                             f'Total Macro: {format_currency(macro_value)}<br>' +
                             '<extra></extra>'
            ))
            
            # Micro stacked bars
            x_micro = i + bar_width/2
            micro_data_year = micro_breakdown.get(year, [])
            
            if micro_data_year:
                # Create stacked bars for subcategories
                bottom = 0
                colors = px.colors.qualitative.Set3
                
                for j, (subcat_name, subcat_value) in enumerate(micro_data_year[:5]):  # Top 5
                    color = colors[j % len(colors)]
                    
                    fig.add_trace(go.Bar(
                        name=subcat_name if i == 0 else '',
                        x=[x_micro],
                        y=[subcat_value],
                        width=bar_width,
                        marker_color=color,
                        base=bottom,
                        legendgroup=f'micro_{j}',
                        showlegend=(i == 0),
                        hovertemplate=f'<b>{subcat_name} - {year}</b><br>' +
                                     f'Valor: {format_currency(subcat_value)}<br>' +
                                     '<extra></extra>'
                    ))
                    bottom += subcat_value
            
            x_positions.append(str(year))
        
        # Update layout
        fig.update_layout(
            title=f'Comparação Macro vs Micro - {section}',
            xaxis_title='Anos',
            yaxis_title='Valores (R$)',
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(len(years))),
                ticktext=[str(year) for year in years]
            ),
            barmode='group',
            height=600,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            ),
            margin=dict(r=150)
        )
        
        return fig
    
    def _create_stacked_comparison(self, section: str, years: List[int]) -> go.Figure:
        """Create stacked comparison showing macro total with micro breakdown"""
        fig = go.Figure()
        
        # Get micro breakdown for this section
        micro_breakdown = self._get_micro_breakdown_by_section(section, years)
        
        # Create stacked bars for each year
        colors = px.colors.qualitative.Set3
        all_subcategories = set()
        
        # Collect all subcategories across years
        for year_data in micro_breakdown.values():
            for subcat_name, _ in year_data:
                all_subcategories.add(subcat_name)
        
        all_subcategories = sorted(list(all_subcategories))
        
        # Create traces for each subcategory
        for i, subcat_name in enumerate(all_subcategories):
            y_values = []
            
            for year in years:
                year_data = micro_breakdown.get(year, [])
                # Find value for this subcategory in this year
                subcat_value = 0
                for name, value in year_data:
                    if name == subcat_name:
                        subcat_value = value
                        break
                y_values.append(subcat_value)
            
            fig.add_trace(go.Bar(
                name=subcat_name,
                x=[str(year) for year in years],
                y=y_values,
                marker_color=colors[i % len(colors)],
                hovertemplate=f'<b>{subcat_name}</b><br>' +
                             'Ano: %{x}<br>' +
                             'Valor: R$ %{y:,.0f}<br>' +
                             '<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title=f'Estrutura Detalhada - {section}',
            xaxis_title='Anos',
            yaxis_title='Valores (R$)',
            barmode='stack',
            height=600,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            ),
            margin=dict(r=150)
        )
        
        return fig
    
    def _create_waterfall_comparison(self, section: str, years: List[int]) -> go.Figure:
        """Create waterfall chart showing changes between years"""
        if len(years) < 2:
            return None
        
        # Get macro totals for comparison
        macro_totals = self._get_macro_totals_by_section(section, years)
        
        # Create waterfall chart
        fig = go.Figure()
        
        year_1, year_2 = years[0], years[-1]
        value_1 = macro_totals.get(year_1, 0)
        value_2 = macro_totals.get(year_2, 0)
        change = value_2 - value_1
        
        # Waterfall components
        fig.add_trace(go.Waterfall(
            name="",
            orientation="v",
            measure=["absolute", "relative", "absolute"],
            x=[str(year_1), f"Variação", str(year_2)],
            y=[value_1, change, value_2],
            text=[format_currency(value_1), 
                  format_currency(change), 
                  format_currency(value_2)],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            increasing={"marker": {"color": "#2E8B57"}},
            decreasing={"marker": {"color": "#DC143C"}},
            totals={"marker": {"color": "#1f77b4"}}
        ))
        
        fig.update_layout(
            title=f'Análise de Variação - {section} ({year_1} → {year_2})',
            yaxis_title='Valores (R$)',
            height=500
        )
        
        return fig
    
    def _get_macro_totals_by_section(self, section: str, years: List[int]) -> Dict[int, float]:
        """Get macro-level totals for a specific section"""
        section_mapping = {
            "CUSTOS FIXOS": "fixed_costs",
            "CUSTOS VARIÁVEIS": "variable_costs",
            "CUSTOS NÃO OPERACIONAIS": "non_operational_costs",
            "RECEITA": "revenue"
        }
        
        col_name = section_mapping.get(section)
        if not col_name or not self.macro_data or 'consolidated' not in self.macro_data:
            return {}
        
        df = self.macro_data['consolidated']
        if not isinstance(df, pd.DataFrame) or col_name not in df.columns:
            return {}
        
        totals = {}
        for year in years:
            year_data = df[df['year'] == year]
            if not year_data.empty:
                value = year_data.iloc[0][col_name]
                if isinstance(value, dict):
                    value = value.get('ANNUAL', 0)
                totals[year] = float(value)
        
        return totals
    
    def _get_micro_breakdown_by_section(self, section: str, years: List[int]) -> Dict[int, List[Tuple[str, float]]]:
        """Get micro-level breakdown for a specific section"""
        section_keywords = {
            "CUSTOS FIXOS": ["CUSTOS FIXOS", "FIXOS"],
            "CUSTOS VARIÁVEIS": ["CUSTOS VARIÁVEIS", "VARIÁVEIS"],
            "CUSTOS NÃO OPERACIONAIS": ["CUSTOS NÃO OPERACIONAIS", "NÃO OPERACIONAIS"],
            "RECEITA": ["RECEITA", "FATURAMENTO"]
        }
        
        keywords = section_keywords.get(section, [section])
        breakdown = {}
        
        for year in years:
            year_data = self.micro_data.get(year, {})
            if not isinstance(year_data, dict) or 'sections' not in year_data:
                continue
            
            year_breakdown = []
            
            for section_data in year_data['sections']:
                section_name = section_data.get('name', '').upper()
                if any(keyword.upper() in section_name for keyword in keywords):
                    # Get subcategories
                    subcategories = section_data.get('subcategories', [])
                    for subcat in subcategories:
                        subcat_name = subcat.get('name', '')
                        subcat_value = subcat.get('value', 0)
                        if subcat_value > 0:
                            year_breakdown.append((subcat_name, subcat_value))
            
            # Sort by value (descending)
            year_breakdown.sort(key=lambda x: x[1], reverse=True)
            breakdown[year] = year_breakdown
        
        return breakdown
    
    def get_section_summary(self, section: str, years: List[int] = None) -> Dict[str, Any]:
        """Get comprehensive summary for a section including macro and micro insights"""
        if not years:
            years = self._get_common_years()
        
        # Get macro totals
        macro_totals = self._get_macro_totals_by_section(section, years)
        
        # Get micro breakdown
        micro_breakdown = self._get_micro_breakdown_by_section(section, years)
        
        # Calculate insights
        summary = {
            'section': section,
            'years': years,
            'macro_totals': macro_totals,
            'micro_breakdown': micro_breakdown,
            'insights': self._generate_insights(section, macro_totals, micro_breakdown)
        }
        
        return summary
    
    def _generate_insights(self, section: str, macro_totals: Dict[int, float], micro_breakdown: Dict[int, List[Tuple[str, float]]]) -> List[str]:
        """Generate insights from the comparison"""
        insights = []
        
        # Macro trend analysis
        if len(macro_totals) >= 2:
            years = sorted(macro_totals.keys())
            latest_year = years[-1]
            previous_year = years[-2]
            
            latest_value = macro_totals[latest_year]
            previous_value = macro_totals[previous_year]
            
            if previous_value > 0:
                change_pct = ((latest_value - previous_value) / previous_value) * 100
                
                if abs(change_pct) > 10:
                    trend = "aumentou" if change_pct > 0 else "diminuiu"
                    insights.append(
                        f"{section} {trend} {abs(change_pct):.1f}% entre {previous_year} e {latest_year}"
                    )
        
        # Micro concentration analysis
        for year, breakdown in micro_breakdown.items():
            if len(breakdown) >= 3:
                total_value = sum(value for _, value in breakdown)
                top_3_value = sum(value for _, value in breakdown[:3])
                
                if total_value > 0:
                    concentration = (top_3_value / total_value) * 100
                    if concentration > 70:
                        insights.append(
                            f"Em {year}, os 3 principais itens representam {concentration:.0f}% do total de {section}"
                        )
        
        return insights


def render_unified_comparison_section(macro_data: Dict, micro_data: Dict, section: str = "CUSTOS FIXOS"):
    """
    Render a unified comparison section in Streamlit
    
    Args:
        macro_data: Macro-level data
        micro_data: Micro-level data 
        section: Section to analyze
    """
    engine = UnifiedComparisonEngine(macro_data, micro_data)
    
    st.markdown(f"### 🔄 Análise Integrada - {section}")
    
    # Get available years
    years = engine._get_common_years()
    
    if len(years) < 2:
        st.warning("Dados insuficientes para comparação integrada")
        return
    
    # Chart type selection
    col1, col2 = st.columns(2)
    
    with col1:
        chart_type = st.selectbox(
            "Tipo de Visualização",
            ["side_by_side", "stacked", "waterfall"],
            format_func=lambda x: {
                "side_by_side": "📊 Lado a Lado (Macro vs Micro)",
                "stacked": "📚 Estrutura Empilhada", 
                "waterfall": "🌊 Análise de Variação"
            }[x],
            key=f"chart_type_{section}"
        )
    
    with col2:
        selected_years = st.multiselect(
            "Anos para Comparação",
            years,
            default=years[-2:] if len(years) >= 2 else years,
            key=f"years_{section}"
        )
    
    if len(selected_years) >= 2:
        # Create and display chart
        fig = engine.create_unified_comparison_chart(section, selected_years, chart_type)
        
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Show summary insights
        summary = engine.get_section_summary(section, selected_years)
        insights = summary.get('insights', [])
        
        if insights:
            st.markdown("#### 💡 Insights")
            for insight in insights:
                st.markdown(f"• {insight}")
        
        # Show detailed breakdown in expander
        with st.expander("📋 Detalhamento por Subcategoria"):
            _render_detailed_breakdown(summary)
    else:
        st.warning("Selecione pelo menos 2 anos para comparação")


def _render_detailed_breakdown(summary: Dict[str, Any]):
    """Render detailed breakdown table"""
    micro_breakdown = summary.get('micro_breakdown', {})
    
    if not micro_breakdown:
        st.info("Nenhum detalhamento micro disponível")
        return
    
    # Create comparison table
    all_subcats = set()
    for year_data in micro_breakdown.values():
        for subcat_name, _ in year_data:
            all_subcats.add(subcat_name)
    
    # Build comparison dataframe
    comparison_data = []
    for subcat in sorted(all_subcats):
        row = {'Subcategoria': subcat}
        
        for year in sorted(micro_breakdown.keys()):
            year_data = micro_breakdown[year]
            value = 0
            
            for name, val in year_data:
                if name == subcat:
                    value = val
                    break
            
            row[str(year)] = value
        
        comparison_data.append(row)
    
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        
        # Format currency columns
        for col in df.columns:
            if col != 'Subcategoria':
                df[col] = df[col].apply(lambda x: format_currency(x) if x > 0 else '-')
        
        st.dataframe(df, use_container_width=True)