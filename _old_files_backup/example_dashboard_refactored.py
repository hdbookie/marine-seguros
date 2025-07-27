"""
Example of how to use the new chart components in your dashboard
"""
import streamlit as st
import pandas as pd
from components.charts import (
    create_receita_chart,
    create_custos_variaveis_chart,
    create_custos_fixos_chart,
    create_resultado_chart,
    create_margem_contribuicao_chart,
    create_despesas_operacionais_chart,
    create_kpi_indicators
)

# Example: Replace this section in your app.py:
# Instead of having all chart code inline, you can now do:

def render_dashboard_tab(processed_data, selected_years, selected_months, view_type):
    """Render the main dashboard tab using modular components"""
    
    # Filter data based on selections
    display_df = filter_data(processed_data, selected_years, selected_months)
    
    if display_df.empty:
        st.warning("Nenhum dado disponível para os filtros selecionados.")
        return
    
    # Show KPI indicators
    st.subheader("📊 Indicadores Principais")
    create_kpi_indicators(
        current_data=display_df,
        previous_data=None,  # You can add previous period comparison
        period_label=f"{min(selected_years)}-{max(selected_years)}"
    )
    
    st.divider()
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Receita Chart
        st.subheader("📈 Receita")
        fig_receita = create_receita_chart(display_df, view_type)
        if fig_receita:
            st.plotly_chart(fig_receita, use_container_width=True)
        else:
            st.info("Dados de receita não disponíveis")
        
        # Custos Fixos Chart
        st.subheader("🏢 Custos Fixos")
        fig_fixos = create_custos_fixos_chart(display_df, view_type)
        if fig_fixos:
            st.plotly_chart(fig_fixos, use_container_width=True)
        else:
            st.info("Dados de custos fixos não disponíveis")
    
    with col2:
        # Custos Variáveis Chart
        st.subheader("📦 Custos Variáveis")
        fig_variaveis = create_custos_variaveis_chart(display_df, view_type)
        if fig_variaveis:
            st.plotly_chart(fig_variaveis, use_container_width=True)
        else:
            st.info("Dados de custos variáveis não disponíveis")
        
        # Margem de Contribuição Chart
        st.subheader("📊 Margem de Contribuição")
        fig_margem = create_margem_contribuicao_chart(display_df, view_type)
        if fig_margem:
            st.plotly_chart(fig_margem, use_container_width=True)
        else:
            st.info("Dados de margem não disponíveis")
    
    # Full width charts
    st.divider()
    
    # Resultado Chart
    st.subheader("💰 Resultado Financeiro")
    fig_resultado = create_resultado_chart(display_df, view_type)
    if fig_resultado:
        st.plotly_chart(fig_resultado, use_container_width=True)
    else:
        st.info("Dados de resultado não disponíveis")
    
    # Despesas Operacionais Chart
    st.subheader("🏭 Despesas Operacionais")
    fig_despesas = create_despesas_operacionais_chart(display_df, view_type)
    if fig_despesas:
        st.plotly_chart(fig_despesas, use_container_width=True)
    else:
        st.info("Dados de despesas operacionais não disponíveis")


# In your app.py, replace the dashboard section with:
"""
# Import the components
from components.charts import (
    create_receita_chart,
    create_custos_variaveis_chart,
    create_custos_fixos_chart,
    create_resultado_chart,
    create_margem_contribuicao_chart,
    create_despesas_operacionais_chart,
    create_kpi_indicators
)

# Then in your dashboard tab:
if selected_tab == "Dashboard":
    # Show KPIs
    create_kpi_indicators(display_df, previous_period_df, "2024")
    
    # Show charts
    col1, col2 = st.columns(2)
    with col1:
        fig = create_receita_chart(display_df, view_type)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = create_custos_variaveis_chart(display_df, view_type)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # And so on...
"""