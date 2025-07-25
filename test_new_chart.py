import streamlit as st
import pandas as pd
from components.charts import create_custos_variaveis_chart

# Test the new chart component
st.set_page_config(page_title="Test New Chart", layout="wide")

st.title("Test: Custos Variáveis vs Receita e Custos Fixos")

# Create sample data
data = {
    'year': [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    'revenue': [469000, 900000, 1200000, 2100000, 2900000, 2850000, 3000000, 3400000],
    'variable_costs': [46900, 90000, 110000, 200000, 460000, 570000, 550000, 680000],
    'fixed_costs': [150000, 180000, 200000, 250000, 300000, 320000, 350000, 380000],
    'commission': [23450, 45000, 55000, 100000, 230000, 285000, 275000, 340000],
    'tax': [14070, 27000, 33000, 60000, 138000, 171000, 165000, 204000],
    'card_tax': [9380, 18000, 22000, 40000, 92000, 114000, 110000, 136000]
}

df = pd.DataFrame(data)

# Create chart
fig = create_custos_variaveis_chart(df, view_type="Anual")

if fig:
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Could not create chart")