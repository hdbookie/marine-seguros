import streamlit as st
from core import FinancialProcessor
import pandas as pd

# Test with actual file loading
processor = FinancialProcessor()

# Load the Excel files
files = [
    "Análise de Resultado Financeiro 2018_2023.xlsx",
    "Resultado Financeiro - 2024.xlsx", 
    "Resultado Financeiro - 2025.xlsx"
]

print("Loading Excel files...")
excel_data = processor.load_excel_files(files)

print("\nConsolidating data...")
df = processor.consolidate_all_years(excel_data)

print("\nCalculating growth metrics...")
df_with_growth = processor.calculate_growth_metrics(df)

print("\nData with growth metrics:")
print(df_with_growth[['year', 'revenue_growth', 'variable_costs_growth', 'net_profit_growth']])

print("\nDetecting anomalies...")
anomalies = processor.detect_anomalies(df_with_growth)

print(f"\nNumber of anomalies: {len(anomalies)}")
if anomalies:
    for anomaly in anomalies:
        print(f"  {anomaly['year']}: {anomaly['metric']} = {anomaly['value']:.2f}% ({anomaly['type']})")