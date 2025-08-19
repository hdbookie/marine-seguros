"""
Advanced Time Series Analysis for Micro Analysis V2
Provides sophisticated time series analysis with trend detection, forecasting, and anomaly identification
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats
from scipy.signal import find_peaks
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from typing import Dict, List, Optional, Any, Tuple
from utils import format_currency
import warnings
warnings.filterwarnings('ignore')


def render_advanced_time_series_analysis(financial_data: Dict, selected_years: List[int]):
    """
    Render comprehensive time series analysis with multiple perspectives
    """
    st.markdown("### 📈 Análise Temporal Avançada")
    st.caption("Análise sofisticada de séries temporais com detecção de tendências e anomalias")
    
    if len(selected_years) < 2:
        st.warning("Selecione pelo menos 2 anos para análise temporal completa")
        return
    
    # Analysis type selector
    analysis_type = st.selectbox(
        "Tipo de Análise Temporal",
        [
            "📊 Tendências e Sazonalidade",
            "🔍 Detecção de Anomalias",
            "📈 Previsão e Forecasting",
            "🌊 Análise de Volatilidade",
            "🔄 Ciclos e Padrões",
            "📉 Decomposição Temporal"
        ]
    )
    
    if analysis_type == "📊 Tendências e Sazonalidade":
        _render_trends_and_seasonality(financial_data, selected_years)
    elif analysis_type == "🔍 Detecção de Anomalias":
        _render_anomaly_detection(financial_data, selected_years)
    elif analysis_type == "📈 Previsão e Forecasting":
        _render_forecasting_analysis(financial_data, selected_years)
    elif analysis_type == "🌊 Análise de Volatilidade":
        _render_volatility_analysis(financial_data, selected_years)
    elif analysis_type == "🔄 Ciclos e Padrões":
        _render_cyclical_patterns(financial_data, selected_years)
    elif analysis_type == "📉 Decomposição Temporal":
        _render_time_series_decomposition(financial_data, selected_years)


def _render_trends_and_seasonality(financial_data: Dict, selected_years: List[int]):
    """Render trends and seasonality analysis"""
    
    st.markdown("#### 📊 Análise de Tendências e Sazonalidade")
    
    # Prepare monthly time series data
    time_series_data = _prepare_monthly_time_series(financial_data, selected_years)
    
    if time_series_data.empty:
        st.warning("Dados mensais insuficientes para análise temporal")
        return
    
    # Category selector for detailed analysis
    categories = time_series_data['category'].unique()
    selected_category = st.selectbox(
        "Selecione uma categoria para análise detalhada:",
        categories,
        key="trend_category_selector"
    )
    
    # Filter data for selected category
    category_data = time_series_data[time_series_data['category'] == selected_category].copy()
    category_data['date'] = pd.to_datetime(category_data[['year', 'month_num']].assign(day=1))
    category_data = category_data.sort_values('date')
    
    # Create trend analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Time series plot with trend line
        fig = go.Figure()
        
        # Add actual values
        fig.add_trace(go.Scatter(
            x=category_data['date'],
            y=category_data['value'],
            mode='lines+markers',
            name='Valores Reais',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        # Calculate and add trend line
        if len(category_data) > 3:
            x_numeric = np.arange(len(category_data))
            trend_coef = np.polyfit(x_numeric, category_data['value'], 1)
            trend_line = np.polyval(trend_coef, x_numeric)
            
            fig.add_trace(go.Scatter(
                x=category_data['date'],
                y=trend_line,
                mode='lines',
                name=f'Tendência ({trend_coef[0]:+.0f}/mês)',
                line=dict(color='red', dash='dash', width=2)
            ))
        
        # Add moving average
        if len(category_data) >= 6:
            moving_avg = category_data['value'].rolling(window=6, center=True).mean()
            fig.add_trace(go.Scatter(
                x=category_data['date'],
                y=moving_avg,
                mode='lines',
                name='Média Móvel (6m)',
                line=dict(color='green', width=2, dash='dot')
            ))
        
        fig.update_layout(
            title=f'Análise Temporal - {selected_category}',
            xaxis=dict(title='Período'),
            yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Seasonal pattern analysis
        _render_seasonal_pattern_analysis(category_data)
    
    # Show trend statistics
    _render_trend_statistics(category_data, selected_category)


def _render_seasonal_pattern_analysis(category_data: pd.DataFrame):
    """Render seasonal pattern analysis for a category"""
    
    # Extract month for seasonal analysis
    category_data['month'] = category_data['date'].dt.month
    monthly_avg = category_data.groupby('month')['value'].agg(['mean', 'std']).reset_index()
    
    months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
              'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    monthly_avg['month_name'] = monthly_avg['month'].map(lambda x: months[x-1])
    
    # Create seasonal pattern chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=monthly_avg['month_name'],
        y=monthly_avg['mean'],
        name='Média Mensal',
        marker_color='lightblue',
        text=[format_currency(v) for v in monthly_avg['mean']],
        textposition='outside',
        error_y=dict(
            type='data',
            array=monthly_avg['std'],
            visible=True
        )
    ))
    
    # Add overall average line
    overall_avg = monthly_avg['mean'].mean()
    fig.add_hline(
        y=overall_avg,
        line=dict(color='red', dash='dash'),
        annotation_text=f"Média Geral: {format_currency(overall_avg)}"
    )
    
    fig.update_layout(
        title='Padrão Sazonal',
        xaxis=dict(title='Mês'),
        yaxis=dict(title='Valor Médio (R$)', tickformat=',.0f'),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_trend_statistics(category_data: pd.DataFrame, category_name: str):
    """Render trend statistics and insights"""
    
    st.markdown("#### 📊 Estatísticas de Tendência")
    
    if len(category_data) < 3:
        st.info("Dados insuficientes para análise estatística")
        return
    
    # Calculate trend statistics
    x_numeric = np.arange(len(category_data))
    trend_coef = np.polyfit(x_numeric, category_data['value'], 1)
    
    # Calculate R-squared
    y_pred = np.polyval(trend_coef, x_numeric)
    ss_res = np.sum((category_data['value'] - y_pred) ** 2)
    ss_tot = np.sum((category_data['value'] - np.mean(category_data['value'])) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Calculate monthly growth rate
    monthly_growth = trend_coef[0]
    annual_growth_rate = (monthly_growth * 12 / category_data['value'].mean()) * 100 if category_data['value'].mean() > 0 else 0
    
    # Calculate volatility (coefficient of variation)
    cv = (category_data['value'].std() / category_data['value'].mean()) * 100 if category_data['value'].mean() > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Taxa de Crescimento Anual",
            f"{annual_growth_rate:+.1f}%",
            delta=f"{annual_growth_rate:+.1f}%" if abs(annual_growth_rate) > 1 else None
        )
    
    with col2:
        st.metric(
            "Crescimento Mensal",
            format_currency(monthly_growth),
            delta=f"{monthly_growth:+.0f}" if abs(monthly_growth) > 1000 else None
        )
    
    with col3:
        trend_strength = "Forte" if r_squared > 0.7 else "Moderada" if r_squared > 0.4 else "Fraca"
        st.metric("Força da Tendência", f"{r_squared:.2f}", help=f"R² - {trend_strength}")
    
    with col4:
        volatility_level = "Alta" if cv > 30 else "Média" if cv > 15 else "Baixa"
        st.metric("Volatilidade", f"{cv:.1f}%", help=f"CV - {volatility_level}")


def _render_anomaly_detection(financial_data: Dict, selected_years: List[int]):
    """Render advanced anomaly detection analysis"""
    
    st.markdown("#### 🔍 Detecção Avançada de Anomalias")
    
    # Prepare data for anomaly detection
    time_series_data = _prepare_monthly_time_series(financial_data, selected_years)
    
    if time_series_data.empty:
        st.warning("Dados mensais insuficientes para detecção de anomalias")
        return
    
    # Anomaly detection method selector
    method = st.selectbox(
        "Método de Detecção",
        [
            "🤖 Isolation Forest (ML)",
            "📊 Desvio Padrão (Estatístico)",
            "📈 Z-Score Móvel",
            "🔍 Detecção por Quartis (IQR)"
        ]
    )
    
    # Category selector
    categories = time_series_data['category'].unique()
    selected_category = st.selectbox(
        "Categoria para análise:",
        categories,
        key="anomaly_category_selector"
    )
    
    category_data = time_series_data[time_series_data['category'] == selected_category].copy()
    category_data['date'] = pd.to_datetime(category_data[['year', 'month_num']].assign(day=1))
    category_data = category_data.sort_values('date').reset_index(drop=True)
    
    if len(category_data) < 6:
        st.warning("Dados insuficientes para detecção de anomalias")
        return
    
    # Detect anomalies based on selected method
    anomalies = _detect_anomalies_by_method(category_data, method)
    
    # Visualize results
    fig = go.Figure()
    
    # Add normal points
    normal_data = category_data[~category_data.index.isin(anomalies)]
    fig.add_trace(go.Scatter(
        x=normal_data['date'],
        y=normal_data['value'],
        mode='lines+markers',
        name='Valores Normais',
        line=dict(color='blue', width=2),
        marker=dict(size=6, color='blue')
    ))
    
    # Add anomaly points
    if len(anomalies) > 0:
        anomaly_data = category_data.iloc[anomalies]
        fig.add_trace(go.Scatter(
            x=anomaly_data['date'],
            y=anomaly_data['value'],
            mode='markers',
            name='Anomalias Detectadas',
            marker=dict(size=12, color='red', symbol='x')
        ))
    
    # Add confidence bands
    if method == "📊 Desvio Padrão (Estatístico)":
        mean_val = category_data['value'].mean()
        std_val = category_data['value'].std()
        
        fig.add_hline(
            y=mean_val + 2*std_val,
            line=dict(color='red', dash='dash', width=1),
            annotation_text="Limite Superior (2σ)"
        )
        fig.add_hline(
            y=mean_val - 2*std_val,
            line=dict(color='red', dash='dash', width=1),
            annotation_text="Limite Inferior (2σ)"
        )
    
    fig.update_layout(
        title=f'Detecção de Anomalias - {selected_category}',
        xaxis=dict(title='Período'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display anomaly details
    _render_anomaly_details(category_data, anomalies)


def _detect_anomalies_by_method(data: pd.DataFrame, method: str) -> List[int]:
    """Detect anomalies using different methods"""
    
    values = data['value'].values.reshape(-1, 1)
    
    if method == "🤖 Isolation Forest (ML)":
        # Use Isolation Forest for anomaly detection
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(values)
        return [i for i, label in enumerate(anomaly_labels) if label == -1]
    
    elif method == "📊 Desvio Padrão (Estatístico)":
        # Statistical method using standard deviation
        mean_val = data['value'].mean()
        std_val = data['value'].std()
        threshold = 2  # 2 standard deviations
        
        anomalies = []
        for i, val in enumerate(data['value']):
            if abs(val - mean_val) > threshold * std_val:
                anomalies.append(i)
        return anomalies
    
    elif method == "📈 Z-Score Móvel":
        # Rolling Z-score method
        window = min(6, len(data) // 2)
        rolling_mean = data['value'].rolling(window=window, center=True).mean()
        rolling_std = data['value'].rolling(window=window, center=True).std()
        
        z_scores = abs((data['value'] - rolling_mean) / rolling_std)
        threshold = 2.5
        
        return [i for i, z in enumerate(z_scores) if not pd.isna(z) and z > threshold]
    
    elif method == "🔍 Detecção por Quartis (IQR)":
        # Interquartile range method
        Q1 = data['value'].quantile(0.25)
        Q3 = data['value'].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        return [i for i, val in enumerate(data['value']) if val < lower_bound or val > upper_bound]
    
    return []


def _render_anomaly_details(data: pd.DataFrame, anomalies: List[int]):
    """Render details about detected anomalies"""
    
    st.markdown("#### 📋 Detalhes das Anomalias")
    
    if len(anomalies) == 0:
        st.success("✅ Nenhuma anomalia detectada no período analisado")
        return
    
    anomaly_data = data.iloc[anomalies].copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Anomalias Detectadas", f"{len(anomalies)}")
        st.metric("% do Total", f"{len(anomalies)/len(data)*100:.1f}%")
    
    with col2:
        if len(anomalies) > 0:
            max_anomaly = anomaly_data.loc[anomaly_data['value'].idxmax()]
            min_anomaly = anomaly_data.loc[anomaly_data['value'].idxmin()]
            
            st.metric("Maior Anomalia", format_currency(max_anomaly['value']))
            st.metric("Menor Anomalia", format_currency(min_anomaly['value']))
    
    # Show anomaly table
    st.markdown("**Lista de Anomalias:**")
    anomaly_details = anomaly_data[['year', 'month', 'value']].copy()
    anomaly_details['value'] = anomaly_details['value'].apply(format_currency)
    anomaly_details.columns = ['Ano', 'Mês', 'Valor']
    
    st.dataframe(anomaly_details, use_container_width=True, hide_index=True)


def _render_forecasting_analysis(financial_data: Dict, selected_years: List[int]):
    """Render forecasting analysis with predictions"""
    
    st.markdown("#### 📈 Análise de Previsão")
    st.info("🚧 Funcionalidade de forecasting em desenvolvimento - será implementada com modelos ARIMA/Prophet")
    
    # For now, show a simple linear trend projection
    time_series_data = _prepare_monthly_time_series(financial_data, selected_years)
    
    if time_series_data.empty:
        st.warning("Dados mensais insuficientes para previsão")
        return
    
    # Category selector
    categories = time_series_data['category'].unique()
    selected_category = st.selectbox(
        "Categoria para previsão:",
        categories,
        key="forecast_category_selector"
    )
    
    category_data = time_series_data[time_series_data['category'] == selected_category].copy()
    category_data['date'] = pd.to_datetime(category_data[['year', 'month_num']].assign(day=1))
    category_data = category_data.sort_values('date')
    
    if len(category_data) < 6:
        st.warning("Dados insuficientes para previsão")
        return
    
    # Simple linear trend projection (placeholder for more advanced forecasting)
    months_ahead = st.slider("Meses para prever", 3, 12, 6)
    
    # Fit linear trend
    x_numeric = np.arange(len(category_data))
    trend_coef = np.polyfit(x_numeric, category_data['value'], 1)
    
    # Create future dates
    last_date = category_data['date'].max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=months_ahead, freq='M')
    
    # Generate predictions
    future_x = np.arange(len(category_data), len(category_data) + months_ahead)
    predictions = np.polyval(trend_coef, future_x)
    
    # Add confidence intervals (simplified)
    residuals = category_data['value'] - np.polyval(trend_coef, x_numeric)
    prediction_std = np.std(residuals)
    
    # Visualization
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=category_data['date'],
        y=category_data['value'],
        mode='lines+markers',
        name='Dados Históricos',
        line=dict(color='blue', width=2)
    ))
    
    # Predictions
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=predictions,
        mode='lines+markers',
        name='Previsão',
        line=dict(color='red', dash='dash', width=2)
    ))
    
    # Confidence interval
    upper_bound = predictions + 1.96 * prediction_std
    lower_bound = predictions - 1.96 * prediction_std
    
    fig.add_trace(go.Scatter(
        x=list(future_dates) + list(future_dates)[::-1],
        y=list(upper_bound) + list(lower_bound)[::-1],
        fill='toself',
        fillcolor='rgba(255,0,0,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Intervalo de Confiança (95%)',
        showlegend=True
    ))
    
    fig.update_layout(
        title=f'Previsão - {selected_category}',
        xaxis=dict(title='Período'),
        yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show prediction summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Tendência Mensal", format_currency(trend_coef[0]))
        st.metric("Previsão Próximo Mês", format_currency(predictions[0]))
    
    with col2:
        total_predicted = np.sum(predictions)
        st.metric(f"Total Previsto ({months_ahead}m)", format_currency(total_predicted))
        
        if len(category_data) >= 12:
            last_year_total = category_data['value'].tail(12).sum()
            growth_projection = ((total_predicted - last_year_total) / last_year_total) * 100
            st.metric("Crescimento Projetado", f"{growth_projection:+.1f}%")


def _render_volatility_analysis(financial_data: Dict, selected_years: List[int]):
    """Render volatility analysis"""
    
    st.markdown("#### 🌊 Análise de Volatilidade")
    st.caption("Análise da variabilidade e risco nas despesas ao longo do tempo")
    
    # Prepare volatility data
    volatility_data = _calculate_volatility_metrics(financial_data, selected_years)
    
    if not volatility_data:
        st.warning("Dados insuficientes para análise de volatilidade")
        return
    
    # Create volatility comparison chart
    categories = list(volatility_data.keys())
    volatilities = [volatility_data[cat]['cv'] for cat in categories]
    mean_values = [volatility_data[cat]['mean'] for cat in categories]
    
    # Create bubble chart (volatility vs mean value)
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=mean_values,
        y=volatilities,
        mode='markers+text',
        text=categories,
        textposition='top center',
        marker=dict(
            size=[v/max(mean_values)*50 + 10 for v in mean_values],  # Bubble size based on mean value
            color=volatilities,
            colorscale='RdYlBu_r',
            showscale=True,
            colorbar=dict(title="Volatilidade (%)")
        ),
        name='Categorias'
    ))
    
    fig.update_layout(
        title='Mapa de Risco - Volatilidade vs Valor Médio',
        xaxis=dict(title='Valor Médio (R$)', tickformat=',.0f'),
        yaxis=dict(title='Volatilidade (CV %)'),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show volatility ranking
    st.markdown("#### 📊 Ranking de Volatilidade")
    
    # Sort by volatility
    sorted_categories = sorted(categories, key=lambda x: volatility_data[x]['cv'], reverse=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔴 Mais Voláteis**")
        for cat in sorted_categories[:5]:
            vol_data = volatility_data[cat]
            st.error(f"**{cat}**: {vol_data['cv']:.1f}% CV")
            st.caption(f"Média: {format_currency(vol_data['mean'])} | DP: {format_currency(vol_data['std'])}")
    
    with col2:
        st.markdown("**🟢 Mais Estáveis**")
        for cat in sorted_categories[-5:]:
            vol_data = volatility_data[cat]
            st.success(f"**{cat}**: {vol_data['cv']:.1f}% CV")
            st.caption(f"Média: {format_currency(vol_data['mean'])} | DP: {format_currency(vol_data['std'])}")


def _render_cyclical_patterns(financial_data: Dict, selected_years: List[int]):
    """Render cyclical pattern analysis"""
    
    st.markdown("#### 🔄 Análise de Ciclos e Padrões")
    st.info("🚧 Análise de ciclos em desenvolvimento - será implementada com análise espectral (FFT)")
    
    # Placeholder for cyclical analysis
    time_series_data = _prepare_monthly_time_series(financial_data, selected_years)
    
    if not time_series_data.empty:
        st.markdown("**Padrões Identificados:**")
        st.write("• Análise de Fourier para detecção de ciclos")
        st.write("• Identificação de padrões sazonais complexos")
        st.write("• Detecção de tendências de longo prazo")
        st.write("• Correlações cruzadas entre categorias")


def _render_time_series_decomposition(financial_data: Dict, selected_years: List[int]):
    """Render time series decomposition analysis"""
    
    st.markdown("#### 📉 Decomposição de Séries Temporais")
    st.info("🚧 Decomposição temporal em desenvolvimento - será implementada com STL decomposition")
    
    # Placeholder for time series decomposition
    st.markdown("**Componentes da Série Temporal:**")
    st.write("• **Tendência**: Direção de longo prazo")
    st.write("• **Sazonalidade**: Padrões regulares (mensal/anual)")
    st.write("• **Ciclo**: Padrões irregulares de longo prazo")
    st.write("• **Ruído**: Variações aleatórias")


# Helper functions

def _prepare_monthly_time_series(financial_data: Dict, selected_years: List[int]) -> pd.DataFrame:
    """Prepare monthly time series data for analysis"""
    
    data_rows = []
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    for year in selected_years:
        if year not in financial_data or 'sections' not in financial_data[year]:
            continue
        
        for section in financial_data[year]['sections']:
            category = section['name']
            monthly_data = section.get('monthly', {})
            
            for month_idx, month in enumerate(months):
                value = monthly_data.get(month, 0)
                if value > 0:
                    data_rows.append({
                        'category': category,
                        'year': year,
                        'month': month,
                        'month_num': month_idx + 1,
                        'value': value
                    })
    
    return pd.DataFrame(data_rows)


def _calculate_volatility_metrics(financial_data: Dict, selected_years: List[int]) -> Dict:
    """Calculate volatility metrics for each category"""
    
    category_values = {}
    
    # Collect monthly values for each category
    for year in selected_years:
        if year not in financial_data or 'sections' not in financial_data[year]:
            continue
        
        for section in financial_data[year]['sections']:
            category = section['name']
            monthly_data = section.get('monthly', {})
            
            if category not in category_values:
                category_values[category] = []
            
            # Add monthly values
            for value in monthly_data.values():
                if value > 0:
                    category_values[category].append(value)
    
    # Calculate volatility metrics
    volatility_data = {}
    
    for category, values in category_values.items():
        if len(values) >= 3:  # Need at least 3 data points
            mean_val = np.mean(values)
            std_val = np.std(values)
            cv = (std_val / mean_val) * 100 if mean_val > 0 else 0
            
            volatility_data[category] = {
                'mean': mean_val,
                'std': std_val,
                'cv': cv,
                'count': len(values)
            }
    
    return volatility_data