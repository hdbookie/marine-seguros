"""
Pattern Analysis for Micro Analysis V2
Advanced statistical analysis and pattern detection for expense data
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from typing import Dict, List, Optional, Any, Tuple
from utils import format_currency
import warnings
warnings.filterwarnings('ignore')


def render_pareto_analysis(financial_data: Dict, selected_years: List[int]):
    """
    Render Pareto (80/20) analysis to identify high-impact expense categories
    """
    st.markdown("### 📊 Análise de Pareto (80/20)")
    st.caption("Identifica as categorias de maior impacto nos custos totais")
    
    # Aggregate data across selected years
    expense_data = _aggregate_expense_data(financial_data, selected_years)
    
    if not expense_data:
        st.warning("Dados insuficientes para análise de Pareto")
        return
    
    # Create DataFrame and sort by value
    df = pd.DataFrame(expense_data)
    df = df.sort_values('value', ascending=False).reset_index(drop=True)
    
    # Calculate cumulative percentages
    df['cumulative_value'] = df['value'].cumsum()
    df['cumulative_percentage'] = (df['cumulative_value'] / df['value'].sum()) * 100
    df['individual_percentage'] = (df['value'] / df['value'].sum()) * 100
    
    # Create Pareto chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add bar chart for individual values
    fig.add_trace(
        go.Bar(
            x=df['category'],
            y=df['value'],
            name='Valor Individual',
            marker_color='lightblue',
            text=[format_currency(v) for v in df['value']],
            textposition='outside',
            yaxis='y'
        ),
        secondary_y=False
    )
    
    # Add line chart for cumulative percentage
    fig.add_trace(
        go.Scatter(
            x=df['category'],
            y=df['cumulative_percentage'],
            mode='lines+markers',
            name='% Acumulado',
            line=dict(color='red', width=3),
            marker=dict(size=8),
            yaxis='y2'
        ),
        secondary_y=True
    )
    
    # Add 80% line
    fig.add_hline(
        y=80,
        line=dict(color='orange', dash='dash', width=2),
        annotation_text="80%",
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        title='Análise de Pareto - Categorias de Despesas',
        xaxis=dict(title='Categorias', tickangle=45),
        height=500
    )
    
    fig.update_yaxes(title_text="Valor (R$)", secondary_y=False, tickformat=',.0f')
    fig.update_yaxes(title_text="Percentual Acumulado (%)", secondary_y=True, range=[0, 100])
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Find 80% cutoff point
    pareto_80_index = df[df['cumulative_percentage'] <= 80].index.max()
    if pd.isna(pareto_80_index):
        pareto_80_index = 0
    
    # Display Pareto insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vital_few = pareto_80_index + 1
        st.metric("📈 Categorias Vitais", f"{vital_few}/{len(df)}")
        st.caption(f"Representam 80% do total")
    
    with col2:
        vital_value = df.iloc[:vital_few]['value'].sum()
        st.metric("💰 Valor das Vitais", format_currency(vital_value))
    
    with col3:
        vital_percentage = (vital_few / len(df)) * 100
        st.metric("📊 % das Categorias", f"{vital_percentage:.1f}%")
    
    # Show vital few categories
    st.markdown("#### 🎯 Categorias Vitais (80% do Impact)")
    vital_categories = df.iloc[:vital_few][['category', 'value', 'individual_percentage']]
    vital_categories.columns = ['Categoria', 'Valor', '% do Total']
    vital_categories['Valor'] = vital_categories['Valor'].apply(format_currency)
    vital_categories['% do Total'] = vital_categories['% do Total'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(vital_categories, use_container_width=True, hide_index=True)


def render_correlation_analysis(financial_data: Dict, selected_years: List[int]):
    """
    Analyze correlations between expense categories
    """
    st.markdown("### 🔗 Análise de Correlação")
    st.caption("Identifica relações entre diferentes categorias de despesas")
    
    # Prepare time series data for correlation analysis
    correlation_data = _prepare_correlation_data(financial_data, selected_years)
    
    if correlation_data.empty or len(correlation_data.columns) < 2:
        st.warning("Dados insuficientes para análise de correlação")
        return
    
    # Calculate correlation matrix
    corr_matrix = correlation_data.corr()
    
    # Create correlation heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu_r',
        zmid=0,
        text=[[f'{val:.2f}' for val in row] for row in corr_matrix.values],
        texttemplate='%{text}',
        textfont={"size": 10},
        hovertemplate='<b>%{x}</b> vs <b>%{y}</b><br>Correlação: %{text}<extra></extra>',
        colorbar=dict(title="Correlação", tickvals=[-1, -0.5, 0, 0.5, 1])
    ))
    
    fig.update_layout(
        title='Matriz de Correlação - Categorias de Despesas',
        xaxis=dict(title='Categoria', tickangle=45),
        yaxis=dict(title='Categoria'),
        height=600,
        width=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Find strongest correlations
    _render_correlation_insights(corr_matrix)


def render_distribution_analysis(financial_data: Dict, selected_years: List[int]):
    """
    Analyze statistical distribution of expenses
    """
    st.markdown("### 📈 Análise de Distribuição Estatística")
    st.caption("Examina padrões estatísticos nas distribuições de despesas")
    
    # Get expense data
    expense_data = _aggregate_expense_data(financial_data, selected_years)
    
    if not expense_data:
        st.warning("Dados insuficientes para análise de distribuição")
        return
    
    values = [item['value'] for item in expense_data]
    categories = [item['category'] for item in expense_data]
    
    # Create distribution plots
    col1, col2 = st.columns(2)
    
    with col1:
        # Histogram with normal curve overlay
        fig = go.Figure()
        
        # Add histogram
        fig.add_trace(go.Histogram(
            x=values,
            nbinsx=20,
            name='Distribuição Real',
            opacity=0.7,
            marker_color='lightblue',
            yaxis='y'
        ))
        
        # Add normal distribution overlay
        mean_val = np.mean(values)
        std_val = np.std(values)
        x_norm = np.linspace(min(values), max(values), 100)
        y_norm = stats.norm.pdf(x_norm, mean_val, std_val)
        
        # Scale to match histogram
        y_norm_scaled = y_norm * len(values) * (max(values) - min(values)) / 20
        
        fig.add_trace(go.Scatter(
            x=x_norm,
            y=y_norm_scaled,
            mode='lines',
            name='Distribuição Normal',
            line=dict(color='red', width=2),
            yaxis='y'
        ))
        
        fig.update_layout(
            title='Distribuição de Valores',
            xaxis=dict(title='Valor (R$)', tickformat=',.0f'),
            yaxis=dict(title='Frequência'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Box plot for outlier detection
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=values,
            name='Distribuição',
            boxpoints='outliers',
            marker_color='lightgreen',
            text=categories
        ))
        
        fig.update_layout(
            title='Box Plot - Detecção de Outliers',
            yaxis=dict(title='Valor (R$)', tickformat=',.0f'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Statistical summary
    _render_distribution_summary(values, categories)


def render_clustering_analysis(financial_data: Dict, selected_years: List[int]):
    """
    Perform clustering analysis to group similar expense patterns
    """
    st.markdown("### 🎯 Análise de Clustering")
    st.caption("Agrupa categorias com padrões de despesas similares")
    
    # Prepare data for clustering
    clustering_data = _prepare_clustering_data(financial_data, selected_years)
    
    if clustering_data.empty:
        st.warning("Dados insuficientes para análise de clustering")
        return
    
    # Standardize the data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(clustering_data.iloc[:, 1:])  # Exclude category names
    
    # Determine optimal number of clusters using elbow method
    n_clusters = st.slider("Número de Clusters", min_value=2, max_value=min(8, len(clustering_data)), value=3)
    
    # Perform K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_data)
    
    # Add cluster labels to dataframe
    clustering_data['Cluster'] = cluster_labels
    
    # Perform PCA for visualization
    pca = PCA(n_components=2)
    pca_data = pca.fit_transform(scaled_data)
    
    # Create scatter plot
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1[:n_clusters]
    
    for i in range(n_clusters):
        cluster_mask = cluster_labels == i
        cluster_categories = clustering_data[cluster_mask]['category'].tolist()
        
        fig.add_trace(go.Scatter(
            x=pca_data[cluster_mask, 0],
            y=pca_data[cluster_mask, 1],
            mode='markers+text',
            name=f'Cluster {i+1}',
            text=cluster_categories,
            textposition='top center',
            marker=dict(
                size=12,
                color=colors[i],
                opacity=0.7
            ),
            hovertemplate='<b>%{text}</b><br>PC1: %{x:.2f}<br>PC2: %{y:.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=f'Clustering de Categorias de Despesas ({n_clusters} clusters)',
        xaxis=dict(title=f'PC1 ({pca.explained_variance_ratio_[0]:.1%} da variância)'),
        yaxis=dict(title=f'PC2 ({pca.explained_variance_ratio_[1]:.1%} da variância)'),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show cluster characteristics
    _render_cluster_analysis(clustering_data, n_clusters)


def render_seasonality_analysis(financial_data: Dict, selected_years: List[int]):
    """
    Analyze seasonal patterns in expenses
    """
    st.markdown("### 🗓️ Análise de Sazonalidade")
    st.caption("Identifica padrões sazonais nas despesas")
    
    # Prepare monthly data
    monthly_data = _prepare_monthly_seasonality_data(financial_data, selected_years)
    
    if monthly_data.empty:
        st.warning("Dados mensais insuficientes para análise de sazonalidade")
        return
    
    # Calculate seasonal indices
    seasonal_analysis = _calculate_seasonal_indices(monthly_data)
    
    # Create seasonal pattern visualization
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    fig = go.Figure()
    
    categories = seasonal_analysis['category'].unique()
    colors = px.colors.qualitative.Set1[:len(categories)]
    
    for i, category in enumerate(categories):
        cat_data = seasonal_analysis[seasonal_analysis['category'] == category]
        
        fig.add_trace(go.Scatter(
            x=months,
            y=cat_data['seasonal_index'],
            mode='lines+markers',
            name=category,
            line=dict(color=colors[i], width=2),
            marker=dict(size=8),
            hovertemplate=f'<b>{category}</b><br>Mês: %{{x}}<br>Índice Sazonal: %{{y:.2f}}<extra></extra>'
        ))
    
    # Add baseline (100%)
    fig.add_hline(
        y=1.0,
        line=dict(color='gray', dash='dash'),
        annotation_text="Média (1.0)"
    )
    
    fig.update_layout(
        title='Índices Sazonais por Categoria',
        xaxis=dict(title='Mês'),
        yaxis=dict(title='Índice Sazonal (1.0 = média)'),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show seasonality insights
    _render_seasonality_insights(seasonal_analysis)


# Helper functions

def _aggregate_expense_data(financial_data: Dict, selected_years: List[int]) -> List[Dict]:
    """Aggregate expense data across selected years"""
    expense_data = []
    
    for year in selected_years:
        if year not in financial_data or 'sections' not in financial_data[year]:
            continue
        
        for section in financial_data[year]['sections']:
            category = section['name']
            value = section.get('value', 0)
            
            if value > 0:
                expense_data.append({
                    'category': category,
                    'value': value,
                    'year': year
                })
    
    # Aggregate by category across years
    aggregated = {}
    for item in expense_data:
        category = item['category']
        if category not in aggregated:
            aggregated[category] = 0
        aggregated[category] += item['value']
    
    return [{'category': k, 'value': v} for k, v in aggregated.items()]


def _prepare_correlation_data(financial_data: Dict, selected_years: List[int]) -> pd.DataFrame:
    """Prepare time series data for correlation analysis"""
    
    data_rows = []
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    for year in selected_years:
        if year not in financial_data or 'sections' not in financial_data[year]:
            continue
        
        for month in months:
            row = {'year': year, 'month': month}
            
            for section in financial_data[year]['sections']:
                category = section['name']
                monthly_data = section.get('monthly', {})
                value = monthly_data.get(month, 0)
                row[category] = value
            
            data_rows.append(row)
    
    df = pd.DataFrame(data_rows)
    
    # Remove year and month columns, keep only category columns
    category_columns = [col for col in df.columns if col not in ['year', 'month']]
    
    return df[category_columns].fillna(0)


def _render_correlation_insights(corr_matrix: pd.DataFrame):
    """Render insights from correlation analysis"""
    
    st.markdown("#### 🔍 Principais Correlações")
    
    # Find strongest positive and negative correlations (excluding diagonal)
    mask = np.triu(np.ones(corr_matrix.shape, dtype=bool), k=1)
    corr_values = corr_matrix.where(mask).stack().sort_values(key=abs, ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Correlações Positivas Mais Fortes:**")
        positive_corrs = corr_values[corr_values > 0.5][:5]
        
        for (cat1, cat2), corr in positive_corrs.items():
            st.success(f"{cat1} ↔ {cat2}: {corr:.2f}")
    
    with col2:
        st.markdown("**Correlações Negativas Mais Fortes:**")
        negative_corrs = corr_values[corr_values < -0.3][:5]
        
        for (cat1, cat2), corr in negative_corrs.items():
            st.error(f"{cat1} ↔ {cat2}: {corr:.2f}")


def _render_distribution_summary(values: List[float], categories: List[str]):
    """Render statistical summary of distribution"""
    
    st.markdown("#### 📊 Resumo Estatístico")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 Média", format_currency(np.mean(values)))
    
    with col2:
        st.metric("📊 Mediana", format_currency(np.median(values)))
    
    with col3:
        st.metric("📏 Desvio Padrão", format_currency(np.std(values)))
    
    with col4:
        # Coefficient of variation
        cv = (np.std(values) / np.mean(values)) * 100
        st.metric("🎯 Coef. Variação", f"{cv:.1f}%")
    
    # Identify outliers
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = [(cat, val) for cat, val in zip(categories, values) 
                if val < lower_bound or val > upper_bound]
    
    if outliers:
        st.markdown("#### ⚠️ Outliers Identificados")
        outlier_df = pd.DataFrame(outliers, columns=['Categoria', 'Valor'])
        outlier_df['Valor'] = outlier_df['Valor'].apply(format_currency)
        st.dataframe(outlier_df, use_container_width=True, hide_index=True)


def _prepare_clustering_data(financial_data: Dict, selected_years: List[int]) -> pd.DataFrame:
    """Prepare data for clustering analysis"""
    
    clustering_rows = []
    
    # Collect all categories
    all_categories = set()
    for year in selected_years:
        if year not in financial_data or 'sections' not in financial_data[year]:
            continue
        for section in financial_data[year]['sections']:
            all_categories.add(section['name'])
    
    for category in all_categories:
        row = {'category': category}
        
        # Add features for clustering
        yearly_values = []
        
        for year in selected_years:
            if year not in financial_data or 'sections' not in financial_data[year]:
                yearly_values.append(0)
                continue
            
            year_value = 0
            for section in financial_data[year]['sections']:
                if section['name'] == category:
                    year_value = section.get('value', 0)
                    break
            
            yearly_values.append(year_value)
        
        # Calculate features
        row['mean_value'] = np.mean(yearly_values)
        row['std_value'] = np.std(yearly_values) if len(yearly_values) > 1 else 0
        row['cv'] = (row['std_value'] / row['mean_value']) * 100 if row['mean_value'] > 0 else 0
        row['trend'] = np.polyfit(range(len(yearly_values)), yearly_values, 1)[0] if len(yearly_values) > 1 else 0
        
        clustering_rows.append(row)
    
    return pd.DataFrame(clustering_rows)


def _render_cluster_analysis(clustering_data: pd.DataFrame, n_clusters: int):
    """Render analysis of clusters"""
    
    st.markdown("#### 🎯 Características dos Clusters")
    
    for i in range(n_clusters):
        cluster_data = clustering_data[clustering_data['Cluster'] == i]
        
        with st.expander(f"Cluster {i+1} ({len(cluster_data)} categorias)"):
            
            # Show categories in cluster
            categories = cluster_data['category'].tolist()
            st.write("**Categorias:**", ", ".join(categories))
            
            # Show cluster statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_value = cluster_data['mean_value'].mean()
                st.metric("Valor Médio", format_currency(avg_value))
            
            with col2:
                avg_cv = cluster_data['cv'].mean()
                st.metric("Variabilidade Média", f"{avg_cv:.1f}%")
            
            with col3:
                avg_trend = cluster_data['trend'].mean()
                trend_direction = "↗️ Crescendo" if avg_trend > 0 else "↘️ Declinando" if avg_trend < 0 else "➡️ Estável"
                st.metric("Tendência", trend_direction)


def _prepare_monthly_seasonality_data(financial_data: Dict, selected_years: List[int]) -> pd.DataFrame:
    """Prepare monthly data for seasonality analysis"""
    
    data_rows = []
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    for year in selected_years:
        if year not in financial_data or 'sections' not in financial_data[year]:
            continue
        
        for section in financial_data[year]['sections']:
            category = section['name']
            monthly_data = section.get('monthly', {})
            
            for month in months:
                value = monthly_data.get(month, 0)
                if value > 0:
                    data_rows.append({
                        'category': category,
                        'year': year,
                        'month': month,
                        'value': value
                    })
    
    return pd.DataFrame(data_rows)


def _calculate_seasonal_indices(monthly_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate seasonal indices for each category"""
    
    seasonal_results = []
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    for category in monthly_data['category'].unique():
        cat_data = monthly_data[monthly_data['category'] == category]
        
        # Calculate average for each month across all years
        monthly_averages = cat_data.groupby('month')['value'].mean()
        
        # Calculate overall average
        overall_average = monthly_averages.mean()
        
        # Calculate seasonal indices
        for month in months:
            if month in monthly_averages.index and overall_average > 0:
                seasonal_index = monthly_averages[month] / overall_average
            else:
                seasonal_index = 0
            
            seasonal_results.append({
                'category': category,
                'month': month,
                'seasonal_index': seasonal_index
            })
    
    return pd.DataFrame(seasonal_results)


def _render_seasonality_insights(seasonal_analysis: pd.DataFrame):
    """Render insights from seasonality analysis"""
    
    st.markdown("#### 🗓️ Padrões Sazonais Identificados")
    
    # Find most seasonal categories
    seasonal_variance = seasonal_analysis.groupby('category')['seasonal_index'].var().sort_values(ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Categorias Mais Sazonais:**")
        for category in seasonal_variance.head(3).index:
            variance = seasonal_variance[category]
            st.info(f"📊 {category}: Variância {variance:.3f}")
    
    with col2:
        st.markdown("**Picos Sazonais:**")
        # Find peak months for each category
        peak_months = seasonal_analysis.loc[seasonal_analysis.groupby('category')['seasonal_index'].idxmax()]
        
        for _, row in peak_months.head(3).iterrows():
            if row['seasonal_index'] > 1.2:  # 20% above average
                st.success(f"📈 {row['category']}: Pico em {row['month']} ({row['seasonal_index']:.2f}x)")