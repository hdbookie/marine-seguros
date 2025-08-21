"""
Financial Forecasting Tab
Provides time series forecasting, scenario planning, and predictive analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import warnings
warnings.filterwarnings('ignore')


def render_forecast_tab(db, extracted_data: Optional[Dict] = None):
    """Render the financial forecasting tab"""
    
    st.header("📈 Previsões Financeiras Avançadas")
    
    # Check if we have data
    if not extracted_data and hasattr(st.session_state, 'extracted_data'):
        extracted_data = st.session_state.extracted_data
    
    if not extracted_data:
        st.warning("📊 Carregue dados na aba 'Upload' primeiro para gerar previsões.")
        return
    
    # Debug: Show data structure
    with st.expander("🔍 Debug: Estrutura dos Dados"):
        st.write("**Keys no extracted_data:**", list(extracted_data.keys()) if extracted_data else "Nenhum")
        if extracted_data:
            for year, year_data in extracted_data.items():
                if isinstance(year_data, dict):
                    st.write(f"**Ano {year}:**", list(year_data.keys()) if isinstance(year_data, dict) else str(type(year_data)))
                    
                    # Show monthly_data structure for first year
                    if year == list(extracted_data.keys())[0] and 'monthly_data' in year_data:
                        monthly_data = year_data['monthly_data']
                        st.write(f"  - Monthly data keys: {list(monthly_data.keys())}")
                        if monthly_data:
                            first_month = list(monthly_data.keys())[0]
                            month_data = monthly_data[first_month]
                            st.write(f"  - {first_month} data keys: {list(month_data.keys()) if isinstance(month_data, dict) else type(month_data)}")
                            if isinstance(month_data, dict):
                                st.write(f"  - Sample values: revenue={month_data.get('revenue', 'N/A')}, fixed_costs={month_data.get('fixed_costs', 'N/A')}")
    
    # Prepare historical data
    historical_data = prepare_historical_data(extracted_data)
    
    st.write(f"**Dados históricos preparados:** {len(historical_data)} registros")
    if not historical_data.empty:
        st.dataframe(historical_data.head())
    
    if historical_data.empty:
        st.warning("Dados históricos insuficientes para gerar previsões.")
        return
    
    # Create tabs for different forecast features
    forecast_tabs = st.tabs([
        "📊 Previsão de Receita",
        "💰 Previsão de Custos", 
        "📈 Análise de Tendências",
        "🎯 Cenários",
        "🎲 Monte Carlo",
        "📉 Sazonalidade"
    ])
    
    with forecast_tabs[0]:
        render_revenue_forecast(historical_data)
    
    with forecast_tabs[1]:
        render_cost_forecast(historical_data)
    
    with forecast_tabs[2]:
        render_trend_analysis(historical_data)
    
    with forecast_tabs[3]:
        render_scenario_planning(historical_data)
    
    with forecast_tabs[4]:
        render_monte_carlo_simulation(historical_data)
    
    with forecast_tabs[5]:
        render_seasonality_analysis(historical_data)


def prepare_historical_data(extracted_data: Dict) -> pd.DataFrame:
    """Prepare historical data for forecasting"""
    
    monthly_data = []
    
    # Extract monthly data from each year
    for year, year_data in extracted_data.items():
        if isinstance(year_data, dict):
            # Get month names in Portuguese
            month_names = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                          'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            
            # Check if we have monthly data in the individual categories
            categories = ['revenue', 'fixed_costs', 'variable_costs', 'non_operational_costs', 
                         'taxes', 'commissions', 'administrative_expenses', 'marketing_expenses', 
                         'financial_expenses']
            
            # Check if any category has monthly data
            has_monthly_data = False
            for category in categories:
                if (category in year_data and 
                    isinstance(year_data[category], dict) and 
                    'monthly' in year_data[category] and
                    isinstance(year_data[category]['monthly'], dict) and
                    any(year_data[category]['monthly'].get(month, 0) != 0 for month in month_names)):
                    has_monthly_data = True
                    break
            
            if has_monthly_data:
                # Use actual monthly data from individual categories
                for month_num, month_key in enumerate(month_names, 1):
                    # Create date
                    try:
                        date = pd.Timestamp(year=int(year), month=month_num, day=1)
                    except (ValueError, TypeError):
                        continue
                    
                    # Extract financial data from each category's monthly data
                    row = {
                        'date': date,
                        'year': int(year),
                        'month': month_num,
                        'revenue': 0,
                        'fixed_costs': 0,
                        'variable_costs': 0,
                        'non_operational_costs': 0,
                        'taxes': 0,
                        'commissions': 0,
                        'administrative_expenses': 0,
                        'marketing_expenses': 0,
                        'financial_expenses': 0
                    }
                    
                    # Extract data from each category's monthly structure
                    for category in categories:
                        if (category in year_data and 
                            isinstance(year_data[category], dict) and 
                            'monthly' in year_data[category] and
                            isinstance(year_data[category]['monthly'], dict)):
                            
                            monthly_value = year_data[category]['monthly'].get(month_key, 0)
                            if isinstance(monthly_value, (int, float)):
                                row[category] = float(monthly_value)
                            else:
                                row[category] = 0.0
                    
                    # Calculate totals
                    row['total_costs'] = (row['fixed_costs'] + row['variable_costs'] + 
                                        row['non_operational_costs'] + row['taxes'] + 
                                        row['commissions'] + row['administrative_expenses'] +
                                        row['marketing_expenses'] + row['financial_expenses'])
                    row['profit'] = row['revenue'] - row['total_costs']
                    
                    monthly_data.append(row)
            
            else:
                # Use annual totals and distribute evenly across months
                # Extract numeric values, handle cases where data might be dict or other types
                def extract_numeric_value(value):
                    if isinstance(value, (int, float)):
                        return float(value)
                    elif isinstance(value, dict):
                        # If it's a dict, try to get 'value' or 'total' key
                        return float(value.get('value', value.get('total', 0)))
                    else:
                        return 0.0
                
                annual_revenue = extract_numeric_value(year_data.get('revenue', 0))
                annual_fixed_costs = extract_numeric_value(year_data.get('fixed_costs', 0))
                annual_variable_costs = extract_numeric_value(year_data.get('variable_costs', 0))
                annual_non_operational = extract_numeric_value(year_data.get('non_operational_costs', 0))
                annual_taxes = extract_numeric_value(year_data.get('taxes', 0))
                annual_commissions = extract_numeric_value(year_data.get('commissions', 0))
                annual_admin = extract_numeric_value(year_data.get('administrative_expenses', 0))
                annual_marketing = extract_numeric_value(year_data.get('marketing_expenses', 0))
                annual_financial = extract_numeric_value(year_data.get('financial_expenses', 0))
                
                # Only create monthly estimates if we have some annual data
                if any([annual_revenue, annual_fixed_costs, annual_variable_costs]):
                    for month_num in range(1, 13):
                        try:
                            date = pd.Timestamp(year=int(year), month=month_num, day=1)
                        except (ValueError, TypeError):
                            continue
                        
                        # Distribute annual totals evenly across 12 months
                        row = {
                            'date': date,
                            'year': int(year),
                            'month': month_num,
                            'revenue': annual_revenue / 12,
                            'fixed_costs': annual_fixed_costs / 12,
                            'variable_costs': annual_variable_costs / 12,
                            'non_operational_costs': annual_non_operational / 12,
                            'taxes': annual_taxes / 12,
                            'commissions': annual_commissions / 12,
                            'administrative_expenses': annual_admin / 12,
                            'marketing_expenses': annual_marketing / 12,
                            'financial_expenses': annual_financial / 12
                        }
                        
                        # Calculate totals
                        row['total_costs'] = (row['fixed_costs'] + row['variable_costs'] + 
                                            row['non_operational_costs'] + row['taxes'] + 
                                            row['commissions'] + row['administrative_expenses'] +
                                            row['marketing_expenses'] + row['financial_expenses'])
                        row['profit'] = row['revenue'] - row['total_costs']
                        
                        monthly_data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(monthly_data)
    
    if not df.empty:
        # Sort by date and clean data
        df = df.sort_values('date')
        df = df.fillna(0)
        
        # Remove rows with all zeros (except date columns)
        numeric_cols = [col for col in df.columns if col not in ['date', 'year', 'month']]
        df = df[df[numeric_cols].sum(axis=1) > 0]
        
    return df


def render_revenue_forecast(historical_data: pd.DataFrame):
    """Render revenue forecasting section"""
    
    st.subheader("📊 Previsão de Receita")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forecast_method = st.selectbox(
            "Método de Previsão",
            ["Média Móvel", "Suavização Exponencial", "Regressão Linear", 
             "Regressão Polinomial", "Holt-Winters"]
        )
    
    with col2:
        forecast_periods = st.slider(
            "Meses para Prever",
            min_value=1,
            max_value=24,
            value=12
        )
    
    with col3:
        confidence_level = st.slider(
            "Nível de Confiança (%)",
            min_value=80,
            max_value=99,
            value=95
        )
    
    # Generate forecast based on selected method
    if forecast_method == "Média Móvel":
        forecast, lower_bound, upper_bound = moving_average_forecast(
            historical_data['revenue'].values, 
            forecast_periods,
            confidence_level
        )
    elif forecast_method == "Suavização Exponencial":
        forecast, lower_bound, upper_bound = exponential_smoothing_forecast(
            historical_data['revenue'].values,
            forecast_periods,
            confidence_level
        )
    elif forecast_method == "Regressão Linear":
        forecast, lower_bound, upper_bound = linear_regression_forecast(
            historical_data,
            'revenue',
            forecast_periods,
            confidence_level
        )
    elif forecast_method == "Regressão Polinomial":
        forecast, lower_bound, upper_bound = polynomial_regression_forecast(
            historical_data,
            'revenue',
            forecast_periods,
            confidence_level,
            degree=3
        )
    else:  # Holt-Winters
        forecast, lower_bound, upper_bound = holt_winters_forecast(
            historical_data['revenue'].values,
            forecast_periods,
            confidence_level
        )
    
    # Create forecast dates
    last_date = historical_data['date'].max()
    forecast_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=forecast_periods,
        freq='MS'
    )
    
    # Create visualization
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=historical_data['date'],
        y=historical_data['revenue'],
        mode='lines+markers',
        name='Histórico',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast,
        mode='lines+markers',
        name='Previsão',
        line=dict(color='red', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    # Confidence interval
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=upper_bound,
        mode='lines',
        name=f'Limite Superior ({confidence_level}%)',
        line=dict(color='rgba(255,0,0,0.2)'),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=lower_bound,
        mode='lines',
        name=f'Limite Inferior ({confidence_level}%)',
        line=dict(color='rgba(255,0,0,0.2)'),
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.1)',
        showlegend=True
    ))
    
    fig.update_layout(
        title=f"Previsão de Receita - {forecast_method}",
        xaxis_title="Mês",
        yaxis_title="Receita (R$)",
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_historical = historical_data['revenue'].mean()
        avg_forecast = np.mean(forecast)
        growth = ((avg_forecast - avg_historical) / avg_historical) * 100
        st.metric(
            "Crescimento Previsto",
            f"{growth:.1f}%",
            f"vs. média histórica"
        )
    
    with col2:
        st.metric(
            "Receita Prevista (Próx. Mês)",
            f"R$ {forecast[0]:,.0f}",
            f"± R$ {(upper_bound[0] - forecast[0]):,.0f}"
        )
    
    with col3:
        total_forecast = np.sum(forecast)
        st.metric(
            f"Total Previsto ({forecast_periods} meses)",
            f"R$ {total_forecast:,.0f}"
        )
    
    with col4:
        max_forecast = np.max(forecast)
        max_month = forecast_dates[np.argmax(forecast)].strftime('%b/%Y')
        st.metric(
            "Pico Previsto",
            f"R$ {max_forecast:,.0f}",
            f"em {max_month}"
        )


def render_cost_forecast(historical_data: pd.DataFrame):
    """Render cost forecasting section"""
    
    st.subheader("💰 Previsão de Custos")
    
    # Cost type selector
    cost_type = st.radio(
        "Tipo de Custo",
        ["Total", "Custos Fixos", "Custos Variáveis"],
        horizontal=True
    )
    
    if cost_type == "Total":
        cost_column = 'total_costs'
    elif cost_type == "Custos Fixos":
        cost_column = 'fixed_costs'
    else:
        cost_column = 'variable_costs'
    
    # Forecast parameters
    col1, col2 = st.columns(2)
    
    with col1:
        forecast_periods = st.slider(
            "Meses para Prever (Custos)",
            min_value=1,
            max_value=24,
            value=12,
            key='cost_forecast_periods'
        )
    
    with col2:
        include_inflation = st.checkbox("Incluir Inflação Projetada", value=True)
        if include_inflation:
            inflation_rate = st.slider(
                "Taxa de Inflação Anual (%)",
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=0.5
            )
        else:
            inflation_rate = 0
    
    # Generate forecast
    forecast, lower_bound, upper_bound = linear_regression_forecast(
        historical_data,
        cost_column,
        forecast_periods,
        95
    )
    
    # Apply inflation if selected
    if include_inflation:
        monthly_inflation = (1 + inflation_rate/100) ** (1/12) - 1
        for i in range(len(forecast)):
            inflation_factor = (1 + monthly_inflation) ** (i + 1)
            forecast[i] *= inflation_factor
            lower_bound[i] *= inflation_factor
            upper_bound[i] *= inflation_factor
    
    # Create forecast dates
    last_date = historical_data['date'].max()
    forecast_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=forecast_periods,
        freq='MS'
    )
    
    # Visualization
    fig = go.Figure()
    
    # Historical costs
    fig.add_trace(go.Scatter(
        x=historical_data['date'],
        y=historical_data[cost_column],
        mode='lines+markers',
        name='Histórico',
        line=dict(color='green', width=2)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast,
        mode='lines+markers',
        name='Previsão',
        line=dict(color='orange', width=2, dash='dash')
    ))
    
    # Confidence interval
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=upper_bound,
        mode='lines',
        line=dict(color='rgba(255,165,0,0.2)'),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=lower_bound,
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(255,165,0,0.1)',
        name='Intervalo de Confiança (95%)'
    ))
    
    fig.update_layout(
        title=f"Previsão de {cost_type}",
        xaxis_title="Mês",
        yaxis_title="Custo (R$)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Cost breakdown forecast
    if cost_type == "Total" and 'fixed_costs' in historical_data.columns:
        st.subheader("📊 Composição dos Custos Previstos")
        
        # Forecast both fixed and variable costs
        fixed_forecast, _, _ = linear_regression_forecast(
            historical_data, 'fixed_costs', forecast_periods, 95
        )
        variable_forecast, _, _ = linear_regression_forecast(
            historical_data, 'variable_costs', forecast_periods, 95
        )
        
        # Apply inflation
        if include_inflation:
            for i in range(len(fixed_forecast)):
                inflation_factor = (1 + monthly_inflation) ** (i + 1)
                fixed_forecast[i] *= inflation_factor
                variable_forecast[i] *= inflation_factor
        
        # Create stacked area chart
        fig2 = go.Figure()
        
        fig2.add_trace(go.Scatter(
            x=forecast_dates,
            y=fixed_forecast,
            mode='lines',
            name='Custos Fixos',
            stackgroup='one',
            fillcolor='rgba(100,100,255,0.5)'
        ))
        
        fig2.add_trace(go.Scatter(
            x=forecast_dates,
            y=variable_forecast,
            mode='lines',
            name='Custos Variáveis',
            stackgroup='one',
            fillcolor='rgba(255,100,100,0.5)'
        ))
        
        fig2.update_layout(
            title="Composição dos Custos Previstos",
            xaxis_title="Mês",
            yaxis_title="Custo (R$)",
            hovermode='x unified',
            height=350
        )
        
        st.plotly_chart(fig2, use_container_width=True)


def render_trend_analysis(historical_data: pd.DataFrame):
    """Render trend analysis section"""
    
    st.subheader("📈 Análise de Tendências")
    
    # Metric selector
    metric = st.selectbox(
        "Métrica para Análise",
        ["Receita", "Lucro", "Margem de Lucro (%)", "Custos Totais"]
    )
    
    if metric == "Receita":
        data_column = 'revenue'
    elif metric == "Lucro":
        data_column = 'profit'
    elif metric == "Margem de Lucro (%)":
        historical_data['margin'] = (historical_data['profit'] / historical_data['revenue']) * 100
        data_column = 'margin'
    else:
        data_column = 'total_costs'
    
    # Calculate trend components
    col1, col2 = st.columns(2)
    
    with col1:
        # Linear trend
        X = np.arange(len(historical_data)).reshape(-1, 1)
        y = historical_data[data_column].values
        
        model = LinearRegression()
        model.fit(X, y)
        trend_line = model.predict(X)
        
        # Calculate trend statistics
        slope = model.coef_[0]
        if metric == "Margem de Lucro (%)":
            trend_direction = f"{slope:.2f} p.p./mês"
        else:
            trend_direction = f"R$ {slope:,.0f}/mês"
        
        # Trend strength (R²)
        from sklearn.metrics import r2_score
        r2 = r2_score(y, trend_line)
        
        st.metric(
            "Tendência",
            trend_direction,
            f"R² = {r2:.3f}"
        )
        
        # Growth rate
        if data_column != 'margin':
            initial_value = historical_data[data_column].iloc[0]
            final_value = historical_data[data_column].iloc[-1]
            periods = len(historical_data)
            
            if initial_value > 0:
                cagr = ((final_value / initial_value) ** (12/periods) - 1) * 100
                st.metric(
                    "Taxa de Crescimento Anual",
                    f"{cagr:.1f}%",
                    "CAGR"
                )
    
    with col2:
        # Volatility
        volatility = historical_data[data_column].std()
        mean_value = historical_data[data_column].mean()
        cv = (volatility / mean_value) * 100 if mean_value != 0 else 0
        
        st.metric(
            "Volatilidade",
            f"{cv:.1f}%",
            "Coeficiente de Variação"
        )
        
        # Seasonality detection
        if len(historical_data) >= 12:
            monthly_avg = historical_data.groupby('month')[data_column].mean()
            seasonality_range = monthly_avg.max() - monthly_avg.min()
            seasonality_pct = (seasonality_range / mean_value) * 100 if mean_value != 0 else 0
            
            st.metric(
                "Sazonalidade",
                f"{seasonality_pct:.1f}%",
                "Variação Sazonal"
            )
    
    # Visualization
    fig = go.Figure()
    
    # Actual data
    fig.add_trace(go.Scatter(
        x=historical_data['date'],
        y=historical_data[data_column],
        mode='lines+markers',
        name='Dados Reais',
        line=dict(color='blue', width=2)
    ))
    
    # Trend line
    fig.add_trace(go.Scatter(
        x=historical_data['date'],
        y=trend_line,
        mode='lines',
        name='Tendência Linear',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # Moving average
    window = min(6, len(historical_data) // 3)
    ma = historical_data[data_column].rolling(window=window, center=True).mean()
    
    fig.add_trace(go.Scatter(
        x=historical_data['date'],
        y=ma,
        mode='lines',
        name=f'Média Móvel ({window} meses)',
        line=dict(color='green', width=2)
    ))
    
    fig.update_layout(
        title=f"Análise de Tendência - {metric}",
        xaxis_title="Mês",
        yaxis_title=metric if metric == "Margem de Lucro (%)" else "Valor (R$)",
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Decomposition if enough data
    if len(historical_data) >= 24:
        st.subheader("🔍 Decomposição da Série Temporal")
        
        try:
            decomposition = seasonal_decompose(
                historical_data[data_column].values,
                model='additive',
                period=12
            )
            
            # Create subplots
            fig2 = go.Figure()
            
            fig2.add_trace(go.Scatter(
                x=historical_data['date'],
                y=decomposition.trend,
                mode='lines',
                name='Tendência',
                line=dict(color='blue', width=2)
            ))
            
            fig2.add_trace(go.Scatter(
                x=historical_data['date'],
                y=decomposition.seasonal,
                mode='lines',
                name='Componente Sazonal',
                line=dict(color='green', width=2)
            ))
            
            fig2.add_trace(go.Scatter(
                x=historical_data['date'],
                y=decomposition.resid,
                mode='lines',
                name='Resíduos',
                line=dict(color='red', width=1)
            ))
            
            fig2.update_layout(
                title="Componentes da Série Temporal",
                xaxis_title="Mês",
                yaxis_title="Valor",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
        except Exception as e:
            st.warning("Dados insuficientes para decomposição sazonal completa.")


def render_scenario_planning(historical_data: pd.DataFrame):
    """Render scenario planning section"""
    
    st.subheader("🎯 Planejamento de Cenários")
    
    st.info("Simule diferentes cenários para entender o impacto nas finanças futuras.")
    
    # Scenario parameters
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Cenário de Receita**")
        revenue_scenario = st.select_slider(
            "Crescimento de Receita",
            options=[-30, -20, -10, 0, 10, 20, 30, 50],
            value=10,
            format_func=lambda x: f"{x:+d}%"
        )
        
        market_expansion = st.checkbox("Expansão de Mercado", value=False)
        if market_expansion:
            expansion_revenue = st.number_input(
                "Receita Adicional Mensal (R$)",
                min_value=0,
                value=50000,
                step=10000
            )
        else:
            expansion_revenue = 0
    
    with col2:
        st.markdown("**Cenário de Custos**")
        cost_scenario = st.select_slider(
            "Variação de Custos",
            options=[-20, -10, -5, 0, 5, 10, 20, 30],
            value=5,
            format_func=lambda x: f"{x:+d}%"
        )
        
        new_investments = st.checkbox("Novos Investimentos", value=False)
        if new_investments:
            investment_cost = st.number_input(
                "Custo Adicional Mensal (R$)",
                min_value=0,
                value=20000,
                step=5000
            )
        else:
            investment_cost = 0
    
    # Calculate scenarios
    forecast_periods = 12
    
    # Base case
    base_revenue = historical_data['revenue'].mean()
    base_costs = historical_data['total_costs'].mean()
    base_profit = base_revenue - base_costs
    
    # Scenario calculations
    scenario_revenue = base_revenue * (1 + revenue_scenario/100) + expansion_revenue
    scenario_costs = base_costs * (1 + cost_scenario/100) + investment_cost
    scenario_profit = scenario_revenue - scenario_costs
    
    # Generate monthly projections
    months = pd.date_range(
        start=historical_data['date'].max() + pd.DateOffset(months=1),
        periods=forecast_periods,
        freq='MS'
    )
    
    # Create scenario comparison
    scenarios_df = pd.DataFrame({
        'Mês': months,
        'Base - Receita': [base_revenue] * forecast_periods,
        'Base - Custos': [base_costs] * forecast_periods,
        'Base - Lucro': [base_profit] * forecast_periods,
        'Cenário - Receita': [scenario_revenue] * forecast_periods,
        'Cenário - Custos': [scenario_costs] * forecast_periods,
        'Cenário - Lucro': [scenario_profit] * forecast_periods
    })
    
    # Add some variability
    np.random.seed(42)
    for col in scenarios_df.columns[1:]:
        scenarios_df[col] = scenarios_df[col] * (1 + np.random.normal(0, 0.05, forecast_periods))
    
    # Visualization
    fig = go.Figure()
    
    # Base case
    fig.add_trace(go.Scatter(
        x=months,
        y=scenarios_df['Base - Lucro'],
        mode='lines',
        name='Cenário Base',
        line=dict(color='blue', width=2)
    ))
    
    # Planned scenario
    fig.add_trace(go.Scatter(
        x=months,
        y=scenarios_df['Cenário - Lucro'],
        mode='lines',
        name='Cenário Planejado',
        line=dict(color='green' if scenario_profit > base_profit else 'red', width=2)
    ))
    
    # Fill between
    fig.add_trace(go.Scatter(
        x=months,
        y=scenarios_df[['Base - Lucro', 'Cenário - Lucro']].max(axis=1),
        mode='lines',
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=months,
        y=scenarios_df[['Base - Lucro', 'Cenário - Lucro']].min(axis=1),
        mode='lines',
        line=dict(color='rgba(0,0,0,0)'),
        fill='tonexty',
        fillcolor='rgba(0,255,0,0.1)' if scenario_profit > base_profit else 'rgba(255,0,0,0.1)',
        showlegend=False
    ))
    
    fig.update_layout(
        title="Comparação de Cenários - Lucro Projetado",
        xaxis_title="Mês",
        yaxis_title="Lucro (R$)",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Metrics comparison
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        profit_change = ((scenario_profit - base_profit) / base_profit) * 100
        st.metric(
            "Impacto no Lucro",
            f"{profit_change:+.1f}%",
            f"R$ {(scenario_profit - base_profit):+,.0f}/mês"
        )
    
    with col2:
        margin_base = (base_profit / base_revenue) * 100
        margin_scenario = (scenario_profit / scenario_revenue) * 100
        st.metric(
            "Margem de Lucro",
            f"{margin_scenario:.1f}%",
            f"{(margin_scenario - margin_base):+.1f} p.p."
        )
    
    with col3:
        annual_impact = (scenario_profit - base_profit) * 12
        st.metric(
            "Impacto Anual",
            f"R$ {annual_impact:+,.0f}",
            "Diferença vs. Base"
        )
    
    with col4:
        breakeven = scenario_costs / (scenario_profit / scenario_revenue) if scenario_profit > 0 else 0
        st.metric(
            "Ponto de Equilíbrio",
            f"R$ {breakeven:,.0f}",
            "Receita necessária"
        )
    
    # Scenario details table
    st.subheader("📋 Detalhes do Cenário")
    
    comparison_df = pd.DataFrame({
        'Métrica': ['Receita Mensal', 'Custos Mensais', 'Lucro Mensal', 'Margem de Lucro', 'ROI Anual'],
        'Cenário Base': [
            f"R$ {base_revenue:,.0f}",
            f"R$ {base_costs:,.0f}",
            f"R$ {base_profit:,.0f}",
            f"{(base_profit/base_revenue)*100:.1f}%",
            f"{(base_profit*12/base_costs):.1f}x"
        ],
        'Cenário Planejado': [
            f"R$ {scenario_revenue:,.0f}",
            f"R$ {scenario_costs:,.0f}",
            f"R$ {scenario_profit:,.0f}",
            f"{(scenario_profit/scenario_revenue)*100:.1f}%",
            f"{(scenario_profit*12/scenario_costs):.1f}x"
        ],
        'Variação': [
            f"{((scenario_revenue-base_revenue)/base_revenue)*100:+.1f}%",
            f"{((scenario_costs-base_costs)/base_costs)*100:+.1f}%",
            f"{((scenario_profit-base_profit)/base_profit)*100:+.1f}%",
            f"{(margin_scenario - margin_base):+.1f} p.p.",
            f"{((scenario_profit*12/scenario_costs) - (base_profit*12/base_costs)):+.1f}x"
        ]
    })
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)


def render_monte_carlo_simulation(historical_data: pd.DataFrame):
    """Render Monte Carlo simulation section"""
    
    st.subheader("🎲 Simulação Monte Carlo")
    
    st.info("Simule milhares de cenários possíveis para entender a distribuição de probabilidades dos resultados futuros.")
    
    # Simulation parameters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        n_simulations = st.select_slider(
            "Número de Simulações",
            options=[100, 500, 1000, 5000, 10000],
            value=1000
        )
    
    with col2:
        forecast_months = st.slider(
            "Meses para Simular",
            min_value=3,
            max_value=24,
            value=12
        )
    
    with col3:
        target_metric = st.selectbox(
            "Métrica Alvo",
            ["Lucro", "Receita", "Custos"]
        )
    
    # Calculate historical statistics
    revenue_mean = historical_data['revenue'].mean()
    revenue_std = historical_data['revenue'].std()
    
    costs_mean = historical_data['total_costs'].mean()
    costs_std = historical_data['total_costs'].std()
    
    # Correlation between revenue and costs
    correlation = historical_data[['revenue', 'total_costs']].corr().iloc[0, 1]
    
    # Run Monte Carlo simulation
    np.random.seed(42)
    simulations = []
    
    with st.spinner(f"Executando {n_simulations} simulações..."):
        for _ in range(n_simulations):
            # Generate correlated random variables
            revenue_sim = np.random.normal(revenue_mean, revenue_std, forecast_months)
            costs_sim = np.random.normal(costs_mean, costs_std, forecast_months)
            
            # Apply correlation
            costs_sim = costs_mean + correlation * (revenue_sim - revenue_mean) * (costs_std / revenue_std) + \
                       np.random.normal(0, costs_std * np.sqrt(1 - correlation**2), forecast_months)
            
            # Calculate profit
            profit_sim = revenue_sim - costs_sim
            
            if target_metric == "Lucro":
                simulations.append(profit_sim.sum())
            elif target_metric == "Receita":
                simulations.append(revenue_sim.sum())
            else:
                simulations.append(costs_sim.sum())
    
    simulations = np.array(simulations)
    
    # Calculate statistics
    mean_result = np.mean(simulations)
    std_result = np.std(simulations)
    percentile_5 = np.percentile(simulations, 5)
    percentile_95 = np.percentile(simulations, 95)
    
    # Visualization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Histogram
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=simulations,
            nbinsx=50,
            name='Distribuição',
            marker_color='blue',
            opacity=0.7
        ))
        
        # Add vertical lines for key statistics
        fig.add_vline(x=mean_result, line_dash="dash", line_color="red", 
                     annotation_text=f"Média: R$ {mean_result:,.0f}")
        fig.add_vline(x=percentile_5, line_dash="dot", line_color="orange",
                     annotation_text=f"5%: R$ {percentile_5:,.0f}")
        fig.add_vline(x=percentile_95, line_dash="dot", line_color="green",
                     annotation_text=f"95%: R$ {percentile_95:,.0f}")
        
        fig.update_layout(
            title=f"Distribuição de {target_metric} - {forecast_months} meses",
            xaxis_title=f"{target_metric} Total (R$)",
            yaxis_title="Frequência",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Estatísticas")
        
        st.metric(
            "Valor Esperado",
            f"R$ {mean_result:,.0f}",
            f"± R$ {std_result:,.0f}"
        )
        
        st.metric(
            "Melhor Caso (95%)",
            f"R$ {percentile_95:,.0f}",
            f"{((percentile_95 - mean_result) / mean_result * 100):+.1f}%"
        )
        
        st.metric(
            "Pior Caso (5%)",
            f"R$ {percentile_5:,.0f}",
            f"{((percentile_5 - mean_result) / mean_result * 100):+.1f}%"
        )
        
        # Probability of achieving targets
        st.markdown("### Probabilidades")
        
        if target_metric == "Lucro":
            prob_positive = (simulations > 0).mean() * 100
            st.metric(
                "Prob. Lucro Positivo",
                f"{prob_positive:.1f}%"
            )
            
            target_value = st.number_input(
                f"Meta de {target_metric} (R$)",
                value=int(mean_result * 1.2),
                step=10000
            )
            
            prob_target = (simulations >= target_value).mean() * 100
            st.metric(
                f"Prob. Atingir Meta",
                f"{prob_target:.1f}%",
                f"R$ {target_value:,.0f}"
            )
    
    # Risk analysis
    st.subheader("📊 Análise de Risco")
    
    # Value at Risk (VaR)
    var_95 = np.percentile(simulations, 5)
    cvar_95 = simulations[simulations <= var_95].mean()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Value at Risk (95%)",
            f"R$ {var_95:,.0f}",
            "Perda máxima com 95% de confiança"
        )
    
    with col2:
        st.metric(
            "CVaR (95%)",
            f"R$ {cvar_95:,.0f}",
            "Perda média no pior cenário (5%)"
        )
    
    with col3:
        sharpe_ratio = (mean_result - 0) / std_result if std_result > 0 else 0
        st.metric(
            "Índice Sharpe",
            f"{sharpe_ratio:.2f}",
            "Retorno ajustado ao risco"
        )


def render_seasonality_analysis(historical_data: pd.DataFrame):
    """Render seasonality analysis section"""
    
    st.subheader("📉 Análise de Sazonalidade")
    
    if len(historical_data) < 12:
        st.warning("É necessário pelo menos 12 meses de dados para análise de sazonalidade.")
        return
    
    # Calculate monthly patterns
    historical_data['month_name'] = historical_data['date'].dt.strftime('%b')
    monthly_stats = historical_data.groupby('month').agg({
        'revenue': ['mean', 'std'],
        'total_costs': ['mean', 'std'],
        'profit': ['mean', 'std']
    }).round(0)
    
    # Create month names in order
    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    # Seasonal index calculation
    col1, col2 = st.columns(2)
    
    with col1:
        metric_seasonal = st.selectbox(
            "Métrica para Análise Sazonal",
            ["Receita", "Custos", "Lucro"]
        )
    
    with col2:
        show_index = st.checkbox("Mostrar Índice Sazonal", value=True)
    
    if metric_seasonal == "Receita":
        column = 'revenue'
    elif metric_seasonal == "Custos":
        column = 'total_costs'
    else:
        column = 'profit'
    
    # Calculate seasonal indices
    overall_mean = historical_data[column].mean()
    seasonal_indices = monthly_stats[column]['mean'] / overall_mean * 100
    
    # Visualization
    fig = go.Figure()
    
    # Bar chart of monthly averages
    fig.add_trace(go.Bar(
        x=month_names,
        y=monthly_stats[column]['mean'],
        name=f'{metric_seasonal} Médio',
        marker_color='lightblue',
        error_y=dict(
            type='data',
            array=monthly_stats[column]['std'],
            visible=True
        )
    ))
    
    if show_index:
        # Add seasonal index line
        fig.add_trace(go.Scatter(
            x=month_names,
            y=seasonal_indices,
            mode='lines+markers',
            name='Índice Sazonal (%)',
            yaxis='y2',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        ))
        
        # Add 100% reference line
        fig.add_hline(y=100, line_dash="dash", line_color="gray",
                     yref='y2', opacity=0.5)
    
    fig.update_layout(
        title=f"Padrão Sazonal - {metric_seasonal}",
        xaxis_title="Mês",
        yaxis_title=f"{metric_seasonal} (R$)",
        yaxis2=dict(
            title="Índice Sazonal (%)",
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Best and worst months
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_month = seasonal_indices.idxmax()
        best_index = seasonal_indices.max()
        st.metric(
            "Melhor Mês",
            month_names[best_month - 1],
            f"Índice: {best_index:.0f}%"
        )
    
    with col2:
        worst_month = seasonal_indices.idxmin()
        worst_index = seasonal_indices.min()
        st.metric(
            "Pior Mês",
            month_names[worst_month - 1],
            f"Índice: {worst_index:.0f}%"
        )
    
    with col3:
        seasonality_strength = (seasonal_indices.max() - seasonal_indices.min())
        st.metric(
            "Força da Sazonalidade",
            f"{seasonality_strength:.0f}%",
            "Variação máx-mín"
        )
    
    # Seasonal forecast adjustment
    st.subheader("🎯 Previsão Ajustada por Sazonalidade")
    
    next_month = (historical_data['date'].max().month % 12) + 1
    next_month_name = month_names[next_month - 1]
    seasonal_adjustment = seasonal_indices.loc[next_month] / 100
    
    base_forecast = historical_data[column].mean()
    adjusted_forecast = base_forecast * seasonal_adjustment
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            f"Previsão Base ({metric_seasonal})",
            f"R$ {base_forecast:,.0f}",
            "Média histórica"
        )
    
    with col2:
        st.metric(
            f"Previsão Ajustada ({next_month_name})",
            f"R$ {adjusted_forecast:,.0f}",
            f"Ajuste: {(seasonal_adjustment - 1) * 100:+.1f}%"
        )
    
    # Seasonal patterns table
    st.subheader("📊 Tabela de Padrões Sazonais")
    
    seasonal_table = pd.DataFrame({
        'Mês': month_names,
        'Receita Média': [f"R$ {v:,.0f}" for v in monthly_stats['revenue']['mean'].values],
        'Índice Receita': [f"{v:.0f}%" for v in (monthly_stats['revenue']['mean'] / historical_data['revenue'].mean() * 100).values],
        'Custos Médios': [f"R$ {v:,.0f}" for v in monthly_stats['total_costs']['mean'].values],
        'Índice Custos': [f"{v:.0f}%" for v in (monthly_stats['total_costs']['mean'] / historical_data['total_costs'].mean() * 100).values],
        'Lucro Médio': [f"R$ {v:,.0f}" for v in monthly_stats['profit']['mean'].values]
    })
    
    st.dataframe(seasonal_table, use_container_width=True, hide_index=True)


# Forecasting helper functions
def moving_average_forecast(data, periods, confidence_level):
    """Simple moving average forecast"""
    window = min(6, len(data) // 2)
    ma = np.mean(data[-window:])
    
    forecast = np.array([ma] * periods)
    std = np.std(data)
    z_score = 1.96 if confidence_level == 95 else 2.58
    
    lower_bound = forecast - z_score * std
    upper_bound = forecast + z_score * std
    
    return forecast, lower_bound, upper_bound


def exponential_smoothing_forecast(data, periods, confidence_level):
    """Exponential smoothing forecast"""
    alpha = 0.3
    forecast = []
    
    # Initialize with first value
    s = data[0]
    
    # Apply exponential smoothing
    for value in data[1:]:
        s = alpha * value + (1 - alpha) * s
    
    # Forecast future values
    forecast = np.array([s] * periods)
    
    # Calculate confidence intervals
    std = np.std(data)
    z_score = 1.96 if confidence_level == 95 else 2.58
    
    lower_bound = forecast - z_score * std
    upper_bound = forecast + z_score * std
    
    return forecast, lower_bound, upper_bound


def linear_regression_forecast(df, column, periods, confidence_level):
    """Linear regression forecast"""
    X = np.arange(len(df)).reshape(-1, 1)
    y = df[column].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Forecast
    future_X = np.arange(len(df), len(df) + periods).reshape(-1, 1)
    forecast = model.predict(future_X)
    
    # Calculate confidence intervals
    residuals = y - model.predict(X)
    std_residuals = np.std(residuals)
    z_score = 1.96 if confidence_level == 95 else 2.58
    
    lower_bound = forecast - z_score * std_residuals
    upper_bound = forecast + z_score * std_residuals
    
    return forecast, lower_bound, upper_bound


def polynomial_regression_forecast(df, column, periods, confidence_level, degree=2):
    """Polynomial regression forecast"""
    X = np.arange(len(df)).reshape(-1, 1)
    y = df[column].values
    
    poly = PolynomialFeatures(degree=degree)
    X_poly = poly.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_poly, y)
    
    # Forecast
    future_X = np.arange(len(df), len(df) + periods).reshape(-1, 1)
    future_X_poly = poly.transform(future_X)
    forecast = model.predict(future_X_poly)
    
    # Calculate confidence intervals
    residuals = y - model.predict(X_poly)
    std_residuals = np.std(residuals)
    z_score = 1.96 if confidence_level == 95 else 2.58
    
    lower_bound = forecast - z_score * std_residuals
    upper_bound = forecast + z_score * std_residuals
    
    return forecast, lower_bound, upper_bound


def holt_winters_forecast(data, periods, confidence_level):
    """Holt-Winters forecast"""
    try:
        # Ensure we have enough data
        if len(data) < 12:
            return exponential_smoothing_forecast(data, periods, confidence_level)
        
        model = ExponentialSmoothing(
            data,
            seasonal_periods=12,
            trend='add',
            seasonal='add'
        )
        
        fitted_model = model.fit()
        forecast = fitted_model.forecast(periods)
        
        # Calculate confidence intervals
        std = np.std(data)
        z_score = 1.96 if confidence_level == 95 else 2.58
        
        lower_bound = forecast - z_score * std
        upper_bound = forecast + z_score * std
        
        return forecast, lower_bound, upper_bound
        
    except Exception:
        # Fallback to exponential smoothing if Holt-Winters fails
        return exponential_smoothing_forecast(data, periods, confidence_level)