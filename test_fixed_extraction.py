from core import FinancialProcessor

print("=== TESTING FIXED EXTRACTION ===\n")

# Load and process data
processor = FinancialProcessor()
files = ["Análise de Resultado Financeiro 2018_2023.xlsx"]
excel_data = processor.load_excel_files(files)
df = processor.consolidate_all_years(excel_data)

print("\n=== EXTRACTED VALUES ===")
print("Year | Revenue | Variable Costs | Net Profit")
print("-" * 70)

for _, row in df.iterrows():
    if row['year'] in [2020, 2021, 2022]:
        print(f"{row['year']} | R$ {row['revenue']:>13,.2f} | R$ {row['variable_costs']:>13,.2f} | R$ {row['net_profit']:>13,.2f}")

print("\n=== EXPECTED VALUES ===")
print("Year | Revenue | Variable Costs | Net Profit")
print("-" * 70)
print("2020 | R$  1,131,510.61 | R$    134,063.82 | R$    386,444.33")
print("2021 | R$  2,036,810.95 | R$    261,932.20 | R$     11,833.43")
print("2022 | R$  2,895,603.23 | R$    486,710.12 | R$    213,986.61")

# Test growth calculations
print("\n\n=== TESTING GROWTH CALCULATIONS ===")
df_with_growth = processor.calculate_growth_metrics(df)

print("\nGrowth Rates:")
for _, row in df_with_growth.iterrows():
    if row['year'] in [2021, 2022]:
        print(f"\n{row['year']}:")
        print(f"  Revenue Growth: {row['revenue_growth']:.2f}%")
        print(f"  Variable Costs Growth: {row['variable_costs_growth']:.2f}%")
        print(f"  Net Profit Growth: {row['net_profit_growth']:.2f}%")

# Test anomaly detection
anomalies = processor.detect_anomalies(df_with_growth)
print(f"\n\nAnomalies detected: {len(anomalies)}")
if anomalies:
    for anomaly in anomalies:
        print(f"  {anomaly['year']}: {anomaly['metric']} = {anomaly['value']:.2f}%")