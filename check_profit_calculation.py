from core import FinancialProcessor
import pandas as pd

print("=== CHECKING PROFIT MARGIN CALCULATION ===\n")

# Load and process data
processor = FinancialProcessor()
files = [
    "Análise de Resultado Financeiro 2018_2023.xlsx",
    "Resultado Financeiro - 2024.xlsx",
    "Resultado Financeiro - 2025.xlsx"
]
excel_data = processor.load_excel_files(files)
df = processor.consolidate_all_years(excel_data)

print("PROFIT MARGIN CALCULATION CHECK:")
print("-" * 100)
print("Year | Revenue | Net Profit | Margin Calc | Margin % | Check")
print("-" * 100)

for _, row in df.iterrows():
    year = row['year']
    revenue = row['revenue']
    net_profit = row['net_profit']
    profit_margin = row['profit_margin']
    
    # Recalculate margin
    if revenue > 0:
        calculated_margin = (net_profit / revenue) * 100
    else:
        calculated_margin = 0
    
    # Check if calculation matches
    match = "✓" if abs(calculated_margin - profit_margin) < 0.01 else "✗"
    
    print(f"{year} | R$ {revenue:>13,.2f} | R$ {net_profit:>13,.2f} | "
          f"({net_profit:,.0f}/{revenue:,.0f})*100 | {calculated_margin:>6.1f}% | {match}")

print("\n\nANALYSIS:")
print("-" * 100)

# Check 2018 specifically
data_2018 = df[df['year'] == 2018].iloc[0]
print(f"\n2018 Analysis:")
print(f"Revenue: R$ {data_2018['revenue']:,.2f}")
print(f"Net Profit: R$ {data_2018['net_profit']:,.2f}")
print(f"Profit Margin: {data_2018['profit_margin']:.1f}%")
print(f"\nIs 91.4% margin realistic? That means R$ {data_2018['net_profit']:,.2f} profit on R$ {data_2018['revenue']:,.2f} revenue.")
print(f"This implies costs were only R$ {data_2018['revenue'] - data_2018['net_profit']:,.2f}")

# Let's check what the Excel actually shows
print("\n\nLet's read the 2018 Excel sheet directly...")

# Read the Excel file directly
xl = pd.ExcelFile("Análise de Resultado Financeiro 2018_2023.xlsx")
df_2018 = pd.read_excel(xl, sheet_name='2018')

print("\nSearching for LUCRO (profit) rows in 2018 sheet:")
for idx, row in df_2018.iterrows():
    if pd.notna(row.iloc[0]) and 'LUCRO' in str(row.iloc[0]).upper():
        print(f"Row {idx}: {row.iloc[0]} = {row.iloc[-1] if pd.notna(row.iloc[-1]) else 'N/A'}")