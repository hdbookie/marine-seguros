import pandas as pd

print("=== VERIFYING 2018 PROFIT FIX ===\n")

# Read 2018 sheet directly
xl = pd.ExcelFile("Análise de Resultado Financeiro 2018_2023.xlsx")
df_2018 = pd.read_excel(xl, sheet_name='2018')

print("2018 FINANCIAL RESULTS IN EXCEL:")
print("-" * 60)

# Find all profit/result rows
results = []
for idx, row in df_2018.iterrows():
    if pd.notna(row.iloc[0]):
        row_name = str(row.iloc[0]).strip()
        if any(term in row_name.upper() for term in ['RESULTADO', 'LUCRO']):
            # Find ANUAL column value
            annual_val = None
            for col_idx, col in enumerate(df_2018.columns):
                if pd.notna(col) and 'ANUAL' in str(col).upper():
                    if pd.notna(row.iloc[col_idx]):
                        annual_val = row.iloc[col_idx]
                    break
            
            if annual_val is not None:
                results.append((idx, row_name, float(annual_val)))
                print(f"Row {idx}: {row_name:<45} = R$ {float(annual_val):>12,.2f}")

# Find revenue
revenue_2018 = None
for idx, row in df_2018.iterrows():
    if pd.notna(row.iloc[0]) and 'FATURAMENTO' == str(row.iloc[0]).strip().upper():
        for col_idx, col in enumerate(df_2018.columns):
            if pd.notna(col) and 'ANUAL' in str(col).upper():
                if pd.notna(row.iloc[col_idx]):
                    revenue_2018 = float(row.iloc[col_idx])
                    print(f"\nRevenue 2018: R$ {revenue_2018:,.2f}")
                break

print("\n\nWHICH PROFIT TO USE?")
print("-" * 60)

# Analyze which profit makes sense
for idx, name, value in results:
    if revenue_2018 and revenue_2018 > 0:
        margin = (value / revenue_2018) * 100
        print(f"{name:<45} → {margin:>6.1f}% margin")
        
        # Recommendation
        if 'INVESTIMENTOS' in name.upper() or 'RETIRADA' in name.upper():
            print("  ↳ This seems like the final NET result after all adjustments")
        elif name.strip().upper() == 'RESULTADO':
            print("  ↳ This could be operational result")
        elif name.strip().upper() == 'LUCRO' and value == 0:
            print("  ↳ Zero profit indicates break-even at gross level")
        elif 'NÃO OP' in name.upper() or 'N OP' in name.upper():
            print("  ↳ This includes/excludes non-operational costs")

print("\n\nRECOMMENDATION:")
print("-" * 60)
print("For 2018, we should probably use:")
print("- 'RESULTADO C/Custos Não Op.' = R$ 36,211.06 (9.8% margin)")
print("- This gives a more realistic net profit margin")
print("\nThe system now correctly shows 0% because it found 'LUCRO = 0'")
print("But we might want to prioritize 'RESULTADO' rows over 'LUCRO' rows")