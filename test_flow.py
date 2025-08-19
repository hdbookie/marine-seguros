#!/usr/bin/env python3
"""Trace the flow of extraction"""

current_subcategory = {'name': 'Infraestrutura', 'value': 53500, 'items': []}
expecting_level3_items = True

# Simulate processing each item
items = [
    ('Condomínios', 18100),
    ('Escritório Contábil', 9300),
    ('Advogados', 11400),
    ('Energia Elétrica', 4300),
    ('Seguros', 10400),
    ('Funcionários', 836700)
]

for label, value in items:
    print(f"\nProcessing '{label}' with value {value:,.0f}")
    
    if expecting_level3_items and current_subcategory:
        current_sum = sum(item['value'] for item in current_subcategory['items'])
        parent_value = current_subcategory['value']
        
        print(f"  Current sum: {current_sum:,.0f}, Parent value: {parent_value:,.0f}")
        
        # Check if we've reached the parent's value
        if abs(current_sum - parent_value) < 100:
            print(f"  -> Reached parent sum, stopping children")
            expecting_level3_items = False
            current_subcategory = None
        else:
            print(f"  -> Adding as child")
            current_subcategory['items'].append({'name': label, 'value': value})
            
            # Check again
            new_sum = sum(item['value'] for item in current_subcategory['items'])
            if abs(new_sum - parent_value) < 100:
                print(f"  -> Now reached parent sum ({new_sum:,.0f}), stopping")
                expecting_level3_items = False
                current_subcategory = None
    else:
        print(f"  -> Would create as new Level 2")

print(f"\n\nFinal Infraestrutura children:")
if current_subcategory:
    for item in current_subcategory['items']:
        print(f"  - {item['name']}: {item['value']:,.0f}")