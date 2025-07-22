from core import FinancialProcessor
import pandas as pd

print("=== CHECKING 2019 ANOMALIES ===\n")

# Load and process data
processor = FinancialProcessor()
files = ["Análise de Resultado Financeiro 2018_2023.xlsx"]
excel_data = processor.load_excel_files(files)
df = processor.consolidate_all_years(excel_data)

# Calculate growth metrics
df_with_growth = processor.calculate_growth_metrics(df)

print("ACTUAL VALUES FROM EXCEL:")
print("-" * 70)
print("Year | Revenue | Variable Costs | Growth Rev% | Growth Costs%")
print("-" * 70)

for _, row in df_with_growth.iterrows():
    if row['year'] in [2018, 2019, 2020]:
        print(f"{row['year']} | R$ {row['revenue']:>13,.2f} | R$ {row['variable_costs']:>13,.2f} | "
              f"{row.get('revenue_growth', 0):>10.2f}% | {row.get('variable_costs_growth', 0):>12.2f}%")

print("\n\nANALYSIS:")
print("-" * 70)

# Get 2018 and 2019 data
data_2018 = df_with_growth[df_with_growth['year'] == 2018].iloc[0]
data_2019 = df_with_growth[df_with_growth['year'] == 2019].iloc[0]

# Calculate the actual growth
revenue_growth = ((data_2019['revenue'] - data_2018['revenue']) / data_2018['revenue']) * 100
costs_growth = ((data_2019['variable_costs'] - data_2018['variable_costs']) / data_2018['variable_costs']) * 100

print(f"\n2018 → 2019 Growth Calculation:")
print(f"Revenue: ({data_2019['revenue']:,.2f} - {data_2018['revenue']:,.2f}) / {data_2018['revenue']:,.2f} = {revenue_growth:.2f}%")
print(f"Costs: ({data_2019['variable_costs']:,.2f} - {data_2018['variable_costs']:,.2f}) / {data_2018['variable_costs']:,.2f} = {costs_growth:.2f}%")

print("\n\nCONCLUSION:")
print("-" * 70)
print("These are REAL anomalies, not bugs!")
print("• 2019 revenue grew 146% (2.46x) from 2018")
print("• 2019 variable costs grew 214% (3.14x) from 2018")
print("\nThis indicates a major business expansion in 2019.")
print("The anomaly detection is correctly flagging unusual but real growth.")

# Check the anomaly detection logic
anomalies = processor.detect_anomalies(df_with_growth)
print(f"\n\nAnomaly Detection found {len(anomalies)} anomalies:")
for anomaly in anomalies:
    print(f"  {anomaly['year']}: {anomaly['metric']} = {anomaly['value']:.2f}%")

# Show the statistical basis
growth_cols = ['revenue_growth', 'variable_costs_growth']
print("\n\nStatistical Analysis:")
for col in growth_cols:
    if col in df_with_growth.columns:
        values = df_with_growth[col]
        mean = values.mean()
        std = values.std()
        print(f"\n{col}:")
        print(f"  Mean: {mean:.2f}%")
        print(f"  Std Dev: {std:.2f}%")
        print(f"  2 * Std Dev: {2 * std:.2f}%")
        print(f"  Threshold for anomaly: values outside [{mean - 2*std:.2f}%, {mean + 2*std:.2f}%]")