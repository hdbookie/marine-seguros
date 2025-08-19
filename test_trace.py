#!/usr/bin/env python3
"""Trace through the parent detection logic"""

import pandas as pd

test_data = {
    'Item': ['Infraestrutura', 'Condomínios', 'Escritório Contábil', 'Advogados', 'Energia Elétrica', 'Seguros', 'Funcionários'],
    'Total': [53500, 18100, 9300, 11400, 4300, 10400, 836700]
}

df = pd.DataFrame(test_data)

# Simulate the function
current_idx = 0
label_col = 'Item'
annual_col = 'Total'

current_label = df.iloc[current_idx][label_col]
current_value = df.iloc[current_idx][annual_col]

print(f"Checking if '{current_label}' with value {current_value:,.0f} is a parent...")

potential_children = []
children_sum = 0

for i in range(1, min(20, len(df) - current_idx)):
    next_idx = current_idx + i
    next_label = df.iloc[next_idx][label_col]
    next_value = df.iloc[next_idx][annual_col]
    
    print(f"  Looking at '{next_label}' with value {next_value:,.0f}")
    
    # Check if it's another parent
    if len(potential_children) >= 2:
        if next_value > children_sum * 0.8:
            print(f"    -> Stopping: {next_value:,.0f} > {children_sum * 0.8:,.0f} (80% of current sum)")
            break
    
    # Add as child
    potential_children.append((next_label, next_value))
    children_sum += next_value
    print(f"    -> Added as child. Sum now: {children_sum:,.0f}")

print(f"\nFinal check:")
print(f"  Parent value: {current_value:,.0f}")
print(f"  Children sum: {children_sum:,.0f}")
print(f"  Difference: {abs(current_value - children_sum):,.0f}")

if potential_children and children_sum > 0:
    diff = abs(current_value - children_sum)
    if diff < 100 or (diff / current_value < 0.02):
        print(f"  Result: TRUE - Is a parent!")
    else:
        print(f"  Result: FALSE - Not a parent (difference too large)")
else:
    print(f"  Result: FALSE - No children found")