#!/usr/bin/env python3
"""Debug column detection"""

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
import pandas as pd

file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
extractor = ExcelHierarchyExtractor()
df = pd.read_excel(file_path, sheet_name='2024')

print("Testing column detection:")

# Test label column detection
label_col = extractor._find_label_column(df)
print(f"Label column: {label_col} (index: {df.columns.get_loc(label_col) if label_col in df.columns else 'N/A'})")

# Test annual column detection
annual_col = extractor._find_annual_column(df)
print(f"Annual column: {annual_col} (index: {df.columns.get_loc(annual_col) if annual_col in df.columns else 'N/A'})")

# Test month columns detection
month_cols = extractor._find_month_columns(df)
print(f"Month columns: {month_cols}")

# Test getting value from annual column for "Tecnologia e Comunicação"
for idx, row in df.iterrows():
    if pd.notna(row.iloc[0]) and 'Tecnologia e Comunicação' in str(row.iloc[0]):
        value = extractor._get_numeric_value(row, annual_col)
        print(f"Tecnologia e Comunicação annual value: {value}")
        break

# Now test parent detection with correct annual column
print(f"\nTesting parent detection for 'Tecnologia e Comunicação':")
for idx, row in df.iterrows():
    if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == 'Tecnologia e Comunicação':
        is_parent = extractor._is_likely_parent_category(df, idx, label_col, annual_col)
        print(f"Is parent: {is_parent}")
        break