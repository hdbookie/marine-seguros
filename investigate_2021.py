import pandas as pd
from core import DirectDataExtractor

print("=== INVESTIGATING 2021 PROFIT EXTRACTION ===\n")

# Read 2021 sheet directly
xl = pd.ExcelFile("Análise de Resultado Financeiro 2018_2023.xlsx")
df_2021 = pd.read_excel(xl, sheet_name='2021')

print("2021 FINANCIAL RESULTS IN EXCEL:")
print("-" * 80)

# Find all profit/result rows
results = []
revenue_2021 = None

for idx, row in df_2021.iterrows():
    if pd.notna(row.iloc[0]):
        row_name = str(row.iloc[0]).strip()
        
        # Find ANUAL column
        annual_val = None
        for col_idx, col in enumerate(df_2021.columns):
            if pd.notna(col) and 'ANUAL' in str(col).upper():
                if pd.notna(row.iloc[col_idx]):
                    annual_val = row.iloc[col_idx]
                break
        
        # Check for revenue
        if 'FATURAMENTO' == row_name.upper() and annual_val:
            revenue_2021 = float(annual_val)
            print(f"REVENUE: {row_name:<50} = R$ {float(annual_val):>15,.2f}")
            
        # Check for profits
        if any(term in row_name.upper() for term in ['RESULTADO', 'LUCRO']) and annual_val is not None:
            val = float(annual_val)
            results.append((idx, row_name, val))
            print(f"Row {idx}: {row_name:<50} = R$ {val:>15,.2f}")

print("\n\nMARGIN ANALYSIS:")
print("-" * 80)

# Calculate margins for each result
if revenue_2021:
    print(f"Revenue 2021: R$ {revenue_2021:,.2f}")
    print("\nMargins for each profit type:")
    for idx, name, value in results:
        margin = (value / revenue_2021) * 100
        print(f"  {name:<50} → {margin:>6.1f}% margin")
        if abs(margin - 35.2) < 1:  # Check if close to 35.2%
            print(f"    ✓ THIS MATCHES THE EXPECTED 35.2% MARGIN!")

print("\n\nWHAT THE EXTRACTOR SEES:")
print("-" * 80)

# Use the extractor to see what it's doing
extractor = DirectDataExtractor()
data_2021 = extractor.extract_year_data(df_2021, 2021)

if 'profits' in data_2021:
    print("Extracted profit values:")
    for profit_type, value in data_2021['profits'].items():
        print(f"  {profit_type:<20} = R$ {value:>15,.2f}")
    
    # Show which one is selected
    profits = data_2021['profits']
    selected = (profits.get('NET_FINAL') or 
                profits.get('WITH_NON_OP') or
                profits.get('OPERATIONAL') or 
                profits.get('OTHER') or
                profits.get('WITHOUT_NON_OP') or
                profits.get('GROSS') or 0)
    print(f"\n  → Selected value: R$ {selected:,.2f}")
    if revenue_2021:
        print(f"  → This gives margin: {(selected / revenue_2021) * 100:.1f}%")
        print(f"  → Expected margin: 35.2%")
        print(f"  → Expected profit: R$ {revenue_2021 * 0.352:,.2f}")