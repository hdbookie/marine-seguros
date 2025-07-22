import pandas as pd

print("=== INVESTIGATING PROFIT CALCULATION ISSUE ===\n")

# Read 2018 data directly
xl = pd.ExcelFile("Análise de Resultado Financeiro 2018_2023.xlsx")
df_2018 = pd.read_excel(xl, sheet_name='2018')

print("Looking for key financial rows in 2018:")
print("-" * 60)

# Find key rows
for idx, row in df_2018.iterrows():
    if pd.notna(row.iloc[0]):
        row_name = str(row.iloc[0]).strip()
        annual_col = None
        
        # Find ANUAL column
        for col_idx, col in enumerate(df_2018.columns):
            if pd.notna(col) and 'ANUAL' in str(col).upper():
                annual_col = col_idx
                break
        
        if annual_col and pd.notna(row.iloc[annual_col]):
            value = row.iloc[annual_col]
            
            # Show key financial items
            if any(keyword in row_name.upper() for keyword in [
                'FATURAMENTO', 'CUSTO', 'DESPESA', 'LUCRO', 'RESULTADO', 
                'MARGEM', 'OPERACIONAL', 'LÍQUIDO'
            ]):
                print(f"Row {idx}: {row_name:<40} = {value:>15,.2f}")

print("\n\nCALCULATION CHECK:")
print("-" * 60)

# Find specific values
revenue = None
variable_costs = None
all_costs = []
all_expenses = []

for idx, row in df_2018.iterrows():
    if pd.notna(row.iloc[0]):
        row_name = str(row.iloc[0]).strip().upper()
        
        # Find ANUAL column value
        annual_val = None
        for col_idx, col in enumerate(df_2018.columns):
            if pd.notna(col) and 'ANUAL' in str(col).upper():
                if pd.notna(row.iloc[col_idx]):
                    annual_val = float(row.iloc[col_idx])
                break
        
        if annual_val:
            if row_name == 'FATURAMENTO':
                revenue = annual_val
            elif 'CUSTOS VARIÁVEIS' in row_name:
                variable_costs = annual_val
            elif 'CUSTO' in row_name or 'CUSTOS' in row_name:
                all_costs.append((row_name, annual_val))
            elif 'DESPESA' in row_name:
                all_expenses.append((row_name, annual_val))

if revenue and variable_costs:
    print(f"\nRevenue: R$ {revenue:,.2f}")
    print(f"Variable Costs: R$ {variable_costs:,.2f}")
    print(f"Revenue - Variable Costs = R$ {revenue - variable_costs:,.2f}")
    print(f"\nThis gives a margin of {((revenue - variable_costs) / revenue * 100):.1f}%")
    print("\nBUT THIS IS GROSS MARGIN, NOT NET PROFIT MARGIN!")
    
    print("\n\nOther costs and expenses found:")
    total_other = 0
    for name, val in all_costs + all_expenses:
        if 'VARIÁVEIS' not in name:  # Skip variable costs
            print(f"  {name}: R$ {val:,.2f}")
            total_other += val
    
    print(f"\nTotal other costs/expenses: R$ {total_other:,.2f}")
    print(f"\nActual Net Profit should be:")
    print(f"Revenue - Variable Costs - Other Costs = R$ {revenue - variable_costs - total_other:,.2f}")
    actual_margin = ((revenue - variable_costs - total_other) / revenue) * 100
    print(f"Actual Net Profit Margin = {actual_margin:.1f}%")