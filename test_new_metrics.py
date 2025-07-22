from core import FinancialProcessor
import pandas as pd

print("=== TESTING NEW METRICS EXTRACTION ===\n")

# Load and process data
processor = FinancialProcessor()
files = [
    "Análise de Resultado Financeiro 2018_2023.xlsx",
    "Resultado Financeiro - 2024.xlsx",
    "Resultado Financeiro - 2025.xlsx"
]
excel_data = processor.load_excel_files(files)
df = processor.consolidate_all_years(excel_data)

print("EXTRACTED METRICS:")
print("-" * 120)
print("Year | Revenue | Variable Costs | Fixed Costs | Contrib. Margin | Op. Costs | Net Profit")
print("-" * 120)

for _, row in df.iterrows():
    print(f"{row['year']} | "
          f"R$ {row['revenue']:>12,.2f} | "
          f"R$ {row.get('variable_costs', 0):>12,.2f} | "
          f"R$ {row.get('fixed_costs', 0):>12,.2f} | "
          f"R$ {row.get('contribution_margin', 0):>12,.2f} | "
          f"R$ {row.get('operational_costs', 0):>12,.2f} | "
          f"R$ {row['net_profit']:>12,.2f}")

print("\n\nCOLUMNS IN DATAFRAME:")
print(df.columns.tolist())

# Check what's in the raw data for 2018
print("\n\nRAW DATA CHECK FOR 2018:")
print("-" * 60)
xl = pd.ExcelFile("Análise de Resultado Financeiro 2018_2023.xlsx")
df_2018 = pd.read_excel(xl, sheet_name='2018')

# Look for key metrics
for idx, row in df_2018.iterrows():
    if pd.notna(row.iloc[0]):
        row_name = str(row.iloc[0]).strip().upper()
        if any(term in row_name for term in ['MARGEM DE CONTRIBUIÇÃO', 'CUSTOS FIXOS', 'OPERACIONAIS']):
            # Find ANUAL column value
            annual_val = None
            for col_idx, col in enumerate(df_2018.columns):
                if pd.notna(col) and 'ANUAL' in str(col).upper():
                    if pd.notna(row.iloc[col_idx]):
                        annual_val = row.iloc[col_idx]
                    break
            
            if annual_val is not None:
                print(f"Row {idx}: {row.iloc[0]:<40} = R$ {float(annual_val):>12,.2f}")