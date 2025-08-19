#!/usr/bin/env python3
"""Debug test"""

import pandas as pd

test_data = {
    'Item': ['Infraestrutura', 'Condomínios'],
    'Total': [53500, 18100]
}

df = pd.DataFrame(test_data)

# Simulate what the function does
current_idx = 0
label_col = 'Item'
annual_col = 'Total'

current_label = df.iloc[current_idx]['Item']
current_value = df.iloc[current_idx]['Total']

print(f"Current label: {current_label}")
print(f"Current value: {current_value}")
print(f"Value > 0? {current_value > 0}")

# Test condition
if current_value <= 0:
    print("Would return False here")
else:
    print("Would continue...")