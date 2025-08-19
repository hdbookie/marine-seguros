#!/usr/bin/env python3
"""Debug why Viagens e Deslocamentos isn't detected as parent"""

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
import pandas as pd

file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
extractor = ExcelHierarchyExtractor()
df = pd.read_excel(file_path, sheet_name='2024')

target_item = "Viagens e Deslocamentos"
label_col = extractor._find_label_column(df)
annual_col = extractor._find_annual_column(df)

for idx, row in df.iterrows():
    if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == target_item:
        print(f"Found '{target_item}' at row {idx}")
        
        current_value = extractor._get_numeric_value(df.iloc[idx], annual_col)
        print(f"Current value: R$ {current_value:,.2f}")
        
        # Look for expected children manually first
        expected_children = ['Reembolso viagens', 'Alimentacao', 'Combustível', 'Estacionamento/pedagio', 'Hotel', 'Aluguel veículo/ taxi', 'Passagens']
        
        print(f"\nLooking for expected children manually:")
        found_sum = 0
        
        for i in range(1, min(15, len(df) - idx)):
            child_idx = idx + i
            child_label = extractor._get_cell_value(df.iloc[child_idx], label_col)
            
            if not child_label or not isinstance(child_label, str):
                continue
                
            child_label = child_label.strip()
            
            if child_label in expected_children:
                child_value = extractor._get_numeric_value(df.iloc[child_idx], annual_col)
                found_sum += child_value
                print(f"  ✓ {child_label}: R$ {child_value:,.2f}")
            else:
                child_value = extractor._get_numeric_value(df.iloc[child_idx], annual_col)
                if child_value > 0:
                    print(f"  ➖ {child_label}: R$ {child_value:,.2f} (not expected)")
                # Stop if we hit something big that's clearly not a child
                if child_value > current_value * 0.5:
                    print(f"  🛑 Stopped at large item")
                    break
        
        print(f"\nExpected children sum: R$ {found_sum:,.2f}")
        print(f"Parent value: R$ {current_value:,.2f}")
        diff = abs(current_value - found_sum)
        print(f"Difference: R$ {diff:,.2f}")
        
        # Test the actual function
        is_parent = extractor._is_likely_parent_category(df, idx, label_col, annual_col)
        print(f"Detected as parent: {is_parent}")
        break