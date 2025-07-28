#!/usr/bin/env python3
"""Check 2019 cost structure"""

import pandas as pd

# Check 2019 structure
xl = pd.ExcelFile('Análise de Resultado Financeiro 2018_2023.xlsx')
df = pd.read_excel(xl, sheet_name='2019')

# Find annual column
annual_col = None
for i, col in enumerate(df.columns):
    if isinstance(col, str) and 'ANUAL' in col.upper():
        annual_col = i
        break

print('2019 Cost Structure from Excel:')
print('='*60)

key_items = ['FATURAMENTO', 'CUSTOS VARIÁVEIS', 'CUSTOS FIXOS', 'CUSTOS NÃO OPERACIONAIS', 'RESULTADO C/CUSTOS NÃO OP']
values = {}

if annual_col:
    for i in range(len(df)):
        if pd.notna(df.iloc[i, 0]):
            label = str(df.iloc[i, 0]).strip()
            for key in key_items:
                if key in label.upper() and key not in values:
                    val = df.iloc[i, annual_col]
                    if pd.notna(val):
                        values[key] = (label, float(val))
                        break

# Show results
revenue = values.get('FATURAMENTO', ('', 0))[1]
for key in key_items:
    if key in values:
        label, val = values[key]
        if key == 'FATURAMENTO':
            pct = 100
        else:
            pct = val / revenue * 100 if revenue > 0 else 0
        print(f'{label}: R$ {val:,.2f} ({pct:.2f}%)')

# Calculate what the percentages should add to
if all(key in values for key in ['CUSTOS VARIÁVEIS', 'CUSTOS FIXOS', 'CUSTOS NÃO OPERACIONAIS', 'RESULTADO C/CUSTOS NÃO OP']):
    total_pct = sum(values[key][1] / revenue * 100 for key in ['CUSTOS VARIÁVEIS', 'CUSTOS FIXOS', 'CUSTOS NÃO OPERACIONAIS', 'RESULTADO C/CUSTOS NÃO OP'])
    print(f'\nTotal percentage: {total_pct:.2f}%')
    print('(Should be 100% if all components are included)')