#!/usr/bin/env python3
"""Verify expected parent-child relationships from Excel"""

import pandas as pd

file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
df = pd.read_excel(file_path, sheet_name='2024')

# Check the expected parent-child relationships
test_cases = [
    {
        'parent': 'Distribuição de Lucros',
        'expected_children': ['Lucro']
    },
    {
        'parent': 'Manutenção Administrativa', 
        'expected_children': ['Material de consumo', 'Material de limpeza', 'Limpeza', 'Material de expediente']
    },
    {
        'parent': 'Viagens e Deslocamentos',
        'expected_children': ['Reembolso viagens', 'Alimentacao', 'Combustível', 'Estacionamento/pedagio', 'Hotel', 'Aluguel veículo/ taxi', 'Passagens']
    }
]

print("Verifying expected parent-child relationships:")
print("=" * 60)

for case in test_cases:
    parent_name = case['parent']
    expected_children = case['expected_children']
    
    # Find parent row
    parent_idx = None
    parent_value = 0
    
    for idx, row in df.iterrows():
        if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == parent_name:
            parent_idx = idx
            parent_value = row.iloc[27] if pd.notna(row.iloc[27]) else 0  # Column 27 is Anual
            break
    
    if parent_idx is None:
        print(f"\n❌ {parent_name}: NOT FOUND")
        continue
    
    print(f"\n📊 {parent_name}: R$ {parent_value:,.2f}")
    
    # Look for children in the next rows
    found_children = []
    children_sum = 0
    
    for i in range(1, min(15, len(df) - parent_idx)):
        child_idx = parent_idx + i
        child_label = df.iloc[child_idx, 0]
        
        if pd.isna(child_label):
            continue
            
        child_label = str(child_label).strip()
        
        # Stop if we hit another major section
        if child_label.isupper() and any(word in child_label for word in ['CUSTOS', 'RECEITA', 'RESULTADO']):
            break
            
        # Stop if this looks like another parent category (has a large value)
        child_value = df.iloc[child_idx, 27] if pd.notna(df.iloc[child_idx, 27]) else 0
        
        # Check if this is one of our expected children
        if child_label in expected_children:
            found_children.append((child_label, child_value))
            children_sum += child_value
            print(f"  ✓ {child_label}: R$ {child_value:,.2f}")
        elif child_value > parent_value * 0.5:  # If child is >50% of parent, stop looking
            print(f"  🛑 Stopped at '{child_label}' (R$ {child_value:,.2f}) - too large to be child")
            break
        else:
            print(f"  ➖ {child_label}: R$ {child_value:,.2f} (not expected child)")
    
    # Check if sum matches
    diff = abs(parent_value - children_sum) if children_sum > 0 else parent_value
    percent_diff = (diff / parent_value * 100) if parent_value > 0 else 0
    
    print(f"  📈 Children sum: R$ {children_sum:,.2f}")
    print(f"  📊 Difference: R$ {diff:,.2f} ({percent_diff:.1f}%)")
    
    if diff < 100 or percent_diff < 5:
        print(f"  ✅ MATCH! Should be parent")
    else:
        print(f"  ❌ No match - might not be parent")