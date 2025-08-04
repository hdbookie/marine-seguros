#!/usr/bin/env python3
"""Check 2018 Excel structure"""

import pandas as pd

xl = pd.ExcelFile('Análise de Resultado Financeiro 2018_2023.xlsx')
df = pd.read_excel(xl, sheet_name='2018')

print('Looking for all expense categories in 2018:')
print('='*60)

# Get annual column index
annual_col = 31  # Found from previous check

revenue = 369928.42
running_total = 0

for i in range(len(df)):
    if pd.notna(df.iloc[i, 0]):
        label = str(df.iloc[i, 0]).strip()
        if i < len(df) and annual_col < len(df.columns):
            annual_val = df.iloc[i, annual_col]
            if pd.notna(annual_val) and isinstance(annual_val, (int, float)) and annual_val != 0:
                pct = annual_val / revenue * 100
                
                # Show major categories
                if any(term in label.upper() for term in ['FATURAMENTO', 'CUSTOS', 'RESULTADO', 'LUCRO', 'IMPOSTOS', 'COMISS', 'DESPESA', 'TAXAS']):
                    print(f'{label}: R$ {annual_val:,.2f} ({pct:.2f}%)')
                    
                    if label == 'FATURAMENTO':
                        print('  ^ This is 100% (Revenue)')
                    elif 'VARIÁVEIS' in label.upper():
                        running_total = annual_val
                        print(f'  Running total: {running_total/revenue*100:.2f}%')
                    elif 'CUSTOS FIXOS' == label.upper():
                        running_total += annual_val
                        print(f'  Running total: {running_total/revenue*100:.2f}%')
                    elif 'NÃO OPERACIONAIS' in label.upper():
                        running_total += annual_val
                        print(f'  Running total: {running_total/revenue*100:.2f}%')

# Also show structure around key areas
print('\n\nStructure around CUSTOS:')
for i in range(len(df)):
    if pd.notna(df.iloc[i, 0]):
        label = str(df.iloc[i, 0]).strip()
        if 'CUSTOS' in label.upper() or 'LUCRO' in label.upper() or 'RESULTADO' in label.upper():
            annual_val = df.iloc[i, annual_col] if annual_col < len(df.columns) else None
            if pd.notna(annual_val):
                print(f'Row {i}: {label} = {annual_val}')