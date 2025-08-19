#!/usr/bin/env python3
"""Debug the parent detection algorithm step by step"""

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
import pandas as pd

file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
extractor = ExcelHierarchyExtractor()
df = pd.read_excel(file_path, sheet_name='2024')

target_item = "Manutenção Administrativa"
label_col = extractor._find_label_column(df)
annual_col = extractor._find_annual_column(df)

for idx, row in df.iterrows():
    if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == target_item:
        print(f"Found '{target_item}' at row {idx}")
        
        current_value = extractor._get_numeric_value(df.iloc[idx], annual_col)
        print(f"Current value: R$ {current_value:,.2f}")
        
        # Manually trace through the algorithm
        potential_children = []
        children_sum = 0
        
        print(f"\nTracing through algorithm:")
        
        for i in range(1, min(20, len(df) - idx)):
            next_idx = idx + i
            next_label = extractor._get_cell_value(df.iloc[next_idx], label_col)
            
            if not next_label or not isinstance(next_label, str):
                print(f"  Row {next_idx}: Empty/non-string - SKIP")
                continue
            
            next_label = next_label.strip()
            
            # Stop conditions
            if extractor._is_level1(next_label) or extractor._is_calculation_row(next_label):
                print(f"  Row {next_idx}: '{next_label}' - STOP (level1/calc)")
                break
            
            if next_label.startswith('-'):
                print(f"  Row {next_idx}: '{next_label}' - SKIP (dash)")
                continue
            
            next_value = extractor._get_numeric_value(df.iloc[next_idx], annual_col)
            
            # Early break check
            if children_sum > 0 and abs(current_value - children_sum) < max(100, current_value * 0.05):
                print(f"  Row {next_idx}: '{next_label}' - BREAK (sum match: {children_sum:.2f} ≈ {current_value:.2f})")
                break
            
            # Large item checks
            if len(potential_children) >= 2:
                if next_value > current_value * 0.9:
                    print(f"  Row {next_idx}: '{next_label}' ({next_value:.2f}) - BREAK (too large vs parent {current_value:.2f})")
                    break
                    
                if (children_sum + next_value) > current_value * 1.1:
                    print(f"  Row {next_idx}: '{next_label}' ({next_value:.2f}) - BREAK (sum would exceed parent: {children_sum + next_value:.2f} > {current_value * 1.1:.2f})")
                    break
            
            # Add child
            if next_value > 0:
                potential_children.append((next_label, next_value))
                children_sum += next_value
                print(f"  Row {next_idx}: '{next_label}' (R$ {next_value:,.2f}) - ADDED (sum: {children_sum:.2f})")
            else:
                print(f"  Row {next_idx}: '{next_label}' (R$ {next_value:,.2f}) - SKIP (zero)")
        
        print(f"\nFinal check:")
        print(f"Potential children: {len(potential_children)}")
        print(f"Children sum: R$ {children_sum:,.2f}")
        
        if potential_children and children_sum > 0:
            diff = abs(current_value - children_sum)
            print(f"Difference: R$ {diff:,.2f}")
            print(f"Percentage: {diff / current_value * 100:.4f}%")
            
            is_parent = diff < 100 or (diff / current_value < 0.02)
            print(f"Is parent: {is_parent}")
        else:
            print("No children found - not parent")
        
        break