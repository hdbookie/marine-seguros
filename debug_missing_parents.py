#!/usr/bin/env python3
"""Debug missing parent categories"""

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
import pandas as pd

# Extract raw data to see the structure
file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
extractor = ExcelHierarchyExtractor()

# Read the Excel file directly to see the raw data
df = pd.read_excel(file_path, sheet_name='2024')

# Look at the CUSTOS FIXOS section
print("Raw Excel data around CUSTOS FIXOS section:")
print("=" * 60)

# Find CUSTOS FIXOS row
custos_fixos_idx = None
for idx, row in df.iterrows():
    if pd.notna(row.iloc[0]) and 'CUSTOS FIXOS' in str(row.iloc[0]):
        custos_fixos_idx = idx
        break

if custos_fixos_idx:
    # Show rows around CUSTOS FIXOS
    start_idx = custos_fixos_idx
    end_idx = min(custos_fixos_idx + 60, len(df))  # Show next 60 rows
    
    for idx in range(start_idx, end_idx):
        if idx >= len(df):
            break
        row = df.iloc[idx]
        label = row.iloc[0] if pd.notna(row.iloc[0]) else ""
        annual_value = row.iloc[13] if len(row) > 13 and pd.notna(row.iloc[13]) else 0  # Column N (2024 total)
        
        print(f"Row {idx}: '{label}' = {annual_value}")
        
        # Stop when we reach the next major section
        if idx > custos_fixos_idx + 5 and str(label).isupper() and 'CUSTOS' in str(label):
            break

print("\n" + "=" * 60)

# Test the _is_likely_parent_category function specifically for some items
print("Testing parent detection for specific items:")
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
            is_parent = extractor._is_likely_parent_category(df, idx, 0, 13)
            annual_val = row.iloc[13] if len(row) > 13 and pd.notna(row.iloc[13]) else 0
            print(f"'{item}' (R$ {annual_val:,.2f}): Parent = {is_parent}")
            break