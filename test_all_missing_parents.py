#!/usr/bin/env python3
"""Test all missing parent categories"""

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
import pandas as pd

file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
extractor = ExcelHierarchyExtractor()
df = pd.read_excel(file_path, sheet_name='2024')

label_col = extractor._find_label_column(df)
annual_col = extractor._find_annual_column(df)

print("Testing parent detection for missing categories:")
print("=" * 60)

test_items = [
    "Tecnologia e Comunicação",
    "Distribuição de Lucros", 
    "Comunicação e Marketing",
    "Viagens e Deslocamentos",
    "Manutenção Administrativa"
]

for item in test_items:
    # Find the item in the dataframe
    for idx, row in df.iterrows():
        if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == item:
            is_parent = extractor._is_likely_parent_category(df, idx, label_col, annual_col)
            annual_val = extractor._get_numeric_value(row, annual_col)
            print(f"'{item}' (R$ {annual_val:,.2f}): Parent = {is_parent}")
            break
    else:
        print(f"'{item}': NOT FOUND")

print("\n" + "=" * 60)
print("Now testing the full extraction to see if these are captured:")

# Test the full extraction
result = extractor._extract_hierarchy(df, 2024)

# Find CUSTOS FIXOS section
custos_fixos = None
for section in result['sections']:
    if section['name'] == 'CUSTOS FIXOS':
        custos_fixos = section
        break

if custos_fixos:
    print(f"\nCUSTOS FIXOS subcategories: {len(custos_fixos['subcategories'])}")
    
    # Look for our test items
    found_items = {}
    for subcat in custos_fixos['subcategories']:
        for item in test_items:
            if item in subcat['name']:
                found_items[item] = {
                    'value': subcat['value'],
                    'children': len(subcat.get('items', []))
                }
    
    print("\nFound in extraction:")
    for item, info in found_items.items():
        print(f"  {item}: R$ {info['value']:,.2f} ({info['children']} children)")
    
    # Show items that weren't found as parents
    print("\nStandalone items (should be parents):")
    for subcat in custos_fixos['subcategories']:
        if len(subcat.get('items', [])) == 0:  # No children
            for item in test_items:
                if item in subcat['name']:
                    print(f"  {subcat['name']}: R$ {subcat['value']:,.2f} (should have children)")
else:
    print("CUSTOS FIXOS section not found!")