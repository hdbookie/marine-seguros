#!/usr/bin/env python3
"""Debug why Distribuição de Lucros isn't detected as parent"""

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
import pandas as pd

file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
extractor = ExcelHierarchyExtractor()
df = pd.read_excel(file_path, sheet_name='2024')

target_item = "Distribuição de Lucros"
target_idx = None

for idx, row in df.iterrows():
    if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == target_item:
        target_idx = idx
        break

if target_idx:
    print(f"Found '{target_item}' at row {target_idx}")
    
    label_col = extractor._find_label_column(df)
    annual_col = extractor._find_annual_column(df)
    
    current_value = extractor._get_numeric_value(df.iloc[target_idx], annual_col)
    print(f"Current value: R$ {current_value:,.2f}")
    
    print(f"\nLooking at next 10 rows:")
    potential_children = []
    children_sum = 0
    
    for i in range(1, min(11, len(df) - target_idx)):
        next_idx = target_idx + i
        next_label = extractor._get_cell_value(df.iloc[next_idx], label_col)
        
        if not next_label or not isinstance(next_label, str):
            print(f"  Row {next_idx}: Empty or not string")
            continue
        
        next_label = next_label.strip()
        
        # Check stopping conditions
        if extractor._is_level1(next_label):
            print(f"  Row {next_idx}: '{next_label}' - STOPPED (Level 1)")
            break
        
        if extractor._is_calculation_row(next_label):
            print(f"  Row {next_idx}: '{next_label}' - STOPPED (Calculation)")
            break
        
        if next_label.startswith('-'):
            print(f"  Row {next_idx}: '{next_label}' - SKIPPED (has dash)")
            continue
        
        next_value = extractor._get_numeric_value(df.iloc[next_idx], annual_col)
        
        # Check early break conditions (len >= 2)
        if len(potential_children) >= 2:
            # Check sum match
            if children_sum > 0 and abs(current_value - children_sum) < max(100, current_value * 0.05):
                print(f"  Row {next_idx}: '{next_label}' - STOPPED (sum already matches: {children_sum:.2f} ≈ {current_value:.2f})")
                break
            
            # Check if too large compared to accumulated
            if next_value > children_sum * 0.5:
                print(f"  Row {next_idx}: '{next_label}' ({next_value:.2f}) - STOPPED (too large vs accumulated {children_sum:.2f})")
                break
            
            # Check if too large compared to parent  
            if next_value > current_value * 0.8:
                print(f"  Row {next_idx}: '{next_label}' ({next_value:.2f}) - STOPPED (too large vs parent {current_value:.2f})")
                break
        
        if next_value > 0:
            potential_children.append((next_label, next_value))
            children_sum += next_value
            print(f"  Row {next_idx}: '{next_label}' (R$ {next_value:,.2f}) - ADDED as child (sum: {children_sum:.2f})")
        else:
            print(f"  Row {next_idx}: '{next_label}' (R$ {next_value:,.2f}) - SKIPPED (zero value)")
    
    print(f"\nFinal result:")
    print(f"Potential children found: {len(potential_children)}")
    print(f"Children sum: R$ {children_sum:,.2f}")
    print(f"Parent value: R$ {current_value:,.2f}")
    
    if potential_children and children_sum > 0:
        diff = abs(current_value - children_sum)
        print(f"Difference: R$ {diff:,.2f}")
        print(f"Percentage diff: {diff / current_value * 100:.2f}%")
        
        is_parent = diff < 100 or (diff / current_value < 0.02)
        print(f"Is parent: {is_parent}")
    else:
        print("No valid children found")
else:
    print(f"'{target_item}' not found")