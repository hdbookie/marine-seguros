#!/usr/bin/env python3
"""
Debug why Viagens detection is failing
"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

excel_file = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
df = pd.read_excel(excel_file, sheet_name="2024")

# Find Viagens row
viagens_idx = None
for idx, row in df.iterrows():
    first_col = row.iloc[0] if not pd.isna(row.iloc[0]) else None
    if first_col and isinstance(first_col, str):
        if 'viagens' in first_col.lower() and 'deslocamento' in first_col.lower():
            viagens_idx = idx
            print(f"Found Viagens at row {idx}: {first_col}")
            break

if viagens_idx is not None:
    extractor = ExcelHierarchyExtractor()
    
    # Get the label
    label = df.iloc[viagens_idx].iloc[0]
    print(f"\nLabel: {label}")
    print(f"Label type: {type(label)}")
    print(f"Label lower: {label.lower() if isinstance(label, str) else 'N/A'}")
    
    # Check if it passes the special case test
    if isinstance(label, str):
        label_lower = label.lower()
        print(f"\nChecking special case:")
        print(f"  'viagens' in label_lower: {'viagens' in label_lower}")
        print(f"  'deslocamento' in label_lower: {'deslocamento' in label_lower}")
        
        if 'viagens' in label_lower and 'deslocamento' in label_lower:
            print("  ✓ Passes first check")
            
            # Check for travel children
            travel_keywords = ['alimenta', 'combust', 'hotel', 'estacion', 'pedágio', 'pedagio', 
                             'aluguel', 'taxi', 'passagen', 'reembolso']
            
            print(f"\n  Looking for travel children:")
            for i in range(1, min(10, len(df) - viagens_idx)):
                next_idx = viagens_idx + i
                next_label = df.iloc[next_idx].iloc[0]
                if next_label and isinstance(next_label, str):
                    next_label_lower = next_label.lower()
                    matches = [kw for kw in travel_keywords if kw in next_label_lower]
                    if matches:
                        print(f"    Row {i}: {next_label} - MATCHES: {matches}")
                        break
                    else:
                        print(f"    Row {i}: {next_label} - no match")
    
    # Now actually call the method
    print("\n\nCalling _is_likely_parent_category:")
    label_col = 0
    annual_col = None
    for col_idx, col_name in enumerate(df.columns):
        if 'total' in str(col_name).lower() or 'anual' in str(col_name).lower():
            annual_col = col_idx
            print(f"  Using annual_col: {col_idx} ({col_name})")
            break
    
    if annual_col is not None:
        result = extractor._is_likely_parent_category(df, viagens_idx, label_col, annual_col)
        print(f"  Result: {result}")