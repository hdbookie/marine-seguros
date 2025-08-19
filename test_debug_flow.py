#!/usr/bin/env python3
"""Debug the exact flow"""

# Simulate exact scenario
parent_value = 1653.13  # Infraestrutura
items = [
    ('Condomínios', 431.49),
    ('Escritório Contábil', 581.92),
    ('Energia Elétrica', 260.18),
    ('Seguros', 379.54),
    ('Funcionários', 35649.02)  # This should NOT be a child!
]

current_sum = 0
for name, value in items:
    potential_new_sum = current_sum + value
    
    print(f"\n{name}: {value}")
    print(f"  Current sum: {current_sum:.2f}")
    print(f"  If added: {potential_new_sum:.2f}")
    print(f"  Parent value: {parent_value:.2f}")
    print(f"  Difference if added: {abs(potential_new_sum - parent_value):.2f}")
    
    # Check conditions
    if abs(potential_new_sum - parent_value) < 100:
        print(f"  -> LAST CHILD (completes parent)")
        current_sum = potential_new_sum
        break
    elif value > parent_value * 0.8:
        print(f"  -> NEW PARENT (too large: {value:.2f} > {parent_value * 0.8:.2f})")
        break
    else:
        print(f"  -> Regular child")
        current_sum = potential_new_sum

print(f"\nFinal sum: {current_sum:.2f}")
print(f"Should equal parent: {parent_value:.2f}")
print(f"Match: {abs(current_sum - parent_value) < 1}")