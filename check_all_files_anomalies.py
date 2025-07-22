from core import FinancialProcessor

print("=== CHECKING ANOMALIES WITH ALL FILES ===\n")

# Load ALL files like the app does
processor = FinancialProcessor()
files = [
    "Análise de Resultado Financeiro 2018_2023.xlsx",
    "Resultado Financeiro - 2024.xlsx",
    "Resultado Financeiro - 2025.xlsx"
]

excel_data = processor.load_excel_files(files)
df = processor.consolidate_all_years(excel_data)
df_with_growth = processor.calculate_growth_metrics(df)

print("\nALL YEARS DATA:")
print("-" * 90)
print("Year | Revenue | Variable Costs | Growth Rev% | Growth Costs%")
print("-" * 90)

for _, row in df_with_growth.iterrows():
    print(f"{row['year']} | R$ {row['revenue']:>13,.2f} | R$ {row['variable_costs']:>13,.2f} | "
          f"{row.get('revenue_growth', 0):>10.2f}% | {row.get('variable_costs_growth', 0):>12.2f}%")

# Detect anomalies
anomalies = processor.detect_anomalies(df_with_growth)

print(f"\n\nANOMALIES DETECTED: {len(anomalies)}")
print("-" * 90)
for anomaly in anomalies:
    print(f"{anomaly['year']}: {anomaly['metric']} = {anomaly['value']:.2f}% ({anomaly['type']})")

# Show statistical analysis
print("\n\nSTATISTICAL ANALYSIS:")
print("-" * 90)
growth_cols = ['revenue_growth', 'variable_costs_growth', 'net_profit_growth']
for col in growth_cols:
    if col in df_with_growth.columns:
        values = df_with_growth[col]
        mean = values.mean()
        std = values.std()
        print(f"\n{col}:")
        print(f"  Mean: {mean:.2f}%")
        print(f"  Std Dev: {std:.2f}%")
        print(f"  Anomaly threshold: >{mean + 2*std:.2f}% or <{mean - 2*std:.2f}%")
        
        # Check which values are anomalies
        for _, row in df_with_growth.iterrows():
            value = row[col]
            if abs(value - mean) > 2 * std:
                print(f"  → {row['year']}: {value:.2f}% is an anomaly!")