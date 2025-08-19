#!/usr/bin/env python3
"""
Test extraction of Viagens e Deslocamentos specifically
"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

# Find Excel file
import glob
excel_files = glob.glob("data/arquivos_enviados/*.xlsx") + glob.glob("data/arquivos_enviados/*.xls")

if not excel_files:
    print("No Excel files found in data/")
else:
    file_path = excel_files[0]
    print(f"Testing with: {file_path}")
    
    # Load and examine the Excel file
    excel_file = pd.ExcelFile(file_path)
    
    # Look for 2024 sheet
    sheet_2024 = None
    for sheet in excel_file.sheet_names:
        if '2024' in str(sheet):
            sheet_2024 = sheet
            break
    
    if sheet_2024:
        df = pd.read_excel(file_path, sheet_name=sheet_2024)
        
        print(f"\nAnalyzing sheet: {sheet_2024}")
        print(f"Shape: {df.shape}")
        
        # Look for Viagens row
        for idx, row in df.iterrows():
            first_col = row.iloc[0] if not pd.isna(row.iloc[0]) else None
            if first_col and isinstance(first_col, str):
                if 'viagens' in first_col.lower() or 'deslocamento' in first_col.lower():
                    print(f"\n✅ Found at row {idx}: {first_col}")
                    
                    # Get the value
                    annual_value = None
                    for col_idx in range(1, len(row)):
                        val = row.iloc[col_idx]
                        if pd.notna(val) and isinstance(val, (int, float)) and val > 0:
                            annual_value = val
                            break
                    
                    print(f"   Value: {annual_value}")
                    
                    # Check next 10 rows for potential children
                    print(f"   Next 10 rows:")
                    for i in range(1, min(11, len(df) - idx)):
                        next_row = df.iloc[idx + i]
                        next_label = next_row.iloc[0] if not pd.isna(next_row.iloc[0]) else None
                        if next_label and isinstance(next_label, str):
                            next_label = str(next_label).strip()
                            # Skip if it's another parent category
                            if next_label.isupper() and len(next_label) > 5:
                                print(f"      [{i}] SECTION: {next_label} (stopping)")
                                break
                            
                            # Get value
                            next_val = None
                            for col_idx in range(1, len(next_row)):
                                val = next_row.iloc[col_idx]
                                if pd.notna(val) and isinstance(val, (int, float)) and val > 0:
                                    next_val = val
                                    break
                            
                            # Check if it could be a child
                            is_child_candidate = any(x in next_label.lower() for x in 
                                ['alimenta', 'combust', 'hotel', 'estacion', 'pedágio', 'pedagio', 
                                 'aluguel', 'taxi', 'passagen'])
                            
                            if is_child_candidate:
                                print(f"      [{i}] CHILD?: {next_label} = {next_val} ✓")
                            elif next_val:
                                print(f"      [{i}] {next_label} = {next_val}")
                    
                    # Now test the extractor
                    print("\n   Testing ExcelHierarchyExtractor:")
                    extractor = ExcelHierarchyExtractor()
                    
                    # Test parent detection
                    label_col = 0  # Usually first column
                    annual_col = None
                    for col_idx in range(1, len(df.columns)):
                        if 'total' in str(df.columns[col_idx]).lower() or 'anual' in str(df.columns[col_idx]).lower():
                            annual_col = col_idx
                            break
                    
                    if annual_col is not None:
                        is_parent = extractor._is_likely_parent_category(df, idx, label_col, annual_col)
                        print(f"   Is detected as parent? {is_parent}")
                    
                    break