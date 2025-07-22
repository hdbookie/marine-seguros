from core import FinancialProcessor
import pandas as pd

print("=== TESTING FIXED PROFIT MARGIN CALCULATIONS ===\n")

# Load and process data
processor = FinancialProcessor()
files = [
    "Análise de Resultado Financeiro 2018_2023.xlsx",
    "Resultado Financeiro - 2024.xlsx",
    "Resultado Financeiro - 2025.xlsx"
]
excel_data = processor.load_excel_files(files)
df = processor.consolidate_all_years(excel_data)

print("\nFIXED PROFIT MARGINS:")
print("-" * 100)
print("Year | Revenue | Net Profit | Margin % | Analysis")
print("-" * 100)

for _, row in df.iterrows():
    year = row['year']
    revenue = row['revenue']
    net_profit = row['net_profit']
    profit_margin = row['profit_margin']
    
    # Analyze the margin
    if profit_margin > 50:
        analysis = "⚠️ STILL TOO HIGH - Check profit extraction"
    elif profit_margin < -20:
        analysis = "📉 Large loss"
    elif profit_margin < 0:
        analysis = "📉 Loss"
    elif profit_margin < 5:
        analysis = "⚠️ Low margin"
    elif profit_margin < 15:
        analysis = "✓ Normal margin"
    else:
        analysis = "✓ Good margin"
    
    print(f"{year} | R$ {revenue:>13,.2f} | R$ {net_profit:>13,.2f} | {profit_margin:>6.1f}% | {analysis}")

print("\n\nCOMPARISON WITH EXCEL VALUES:")
print("-" * 100)

# Let's check 2018 specifically
xl = pd.ExcelFile("Análise de Resultado Financeiro 2018_2023.xlsx")
df_2018 = pd.read_excel(xl, sheet_name='2018')

print("\n2018 Excel Analysis:")
for idx, row in df_2018.iterrows():
    if pd.notna(row.iloc[0]):
        row_name = str(row.iloc[0]).strip().upper()
        if any(term in row_name for term in ['RESULTADO', 'LUCRO']) and not any(skip in row_name for skip in ['MARGEM', 'PONTO', 'EQUILIBRIO']):
            annual_val = None
            for col_idx, col in enumerate(df_2018.columns):
                if pd.notna(col) and 'ANUAL' in str(col).upper():
                    if pd.notna(row.iloc[col_idx]):
                        annual_val = row.iloc[col_idx]
                    break
            print(f"  Row {idx}: {row.iloc[0]:<40} = {annual_val}")

# Also check what profit value we're actually using
print("\n\nPROFIT VALUES BEING USED:")
all_data = processor.direct_extractor.extract_from_excel('Análise de Resultado Financeiro 2018_2023.xlsx')
for year in [2018, 2019]:
    if year in all_data:
        profits = all_data[year].get('profits', {})
        print(f"\n{year} Profit options:")
        for profit_type, value in profits.items():
            print(f"  {profit_type}: R$ {value:,.2f}")
        
        # Show which one is selected
        net_profit = (profits.get('NET_FINAL') or 
                     profits.get('OPERATIONAL') or 
                     profits.get('OTHER') or
                     profits.get('GROSS') or 0)
        print(f"  → Selected: R$ {net_profit:,.2f}")