#!/usr/bin/env python3
"""Test parent detection logic directly"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

# Create test data
test_data = {
    'Item': ['Infraestrutura', 'Condomínios', 'Escritório Contábil', 'Advogados'],
    'Total': [53500, 18100, 9300, 11400]
}

df = pd.DataFrame(test_data)
extractor = ExcelHierarchyExtractor()

# Test parent detection for Infraestrutura
print("Testing parent detection for 'Infraestrutura'")
print(f"Value: 53,500")
print(f"Expected children sum: 18,100 + 9,300 + 11,400 = 38,800")
print(f"Wait, that doesn't add up to 53,500!")
print()

# Let's test with correct values
test_data2 = {
    'Item': ['Infraestrutura', 'Condomínios', 'Escritório Contábil', 'Advogados', 'Energia Elétrica', 'Seguros'],
    'Total': [53500, 18100, 9300, 11400, 4300, 10400]
}

df2 = pd.DataFrame(test_data2)
print("Testing with all 5 children:")
print(f"Infraestrutura: 53,500")
print(f"Children sum: 18,100 + 9,300 + 11,400 + 4,300 + 10,400 = {18100 + 9300 + 11400 + 4300 + 10400}")

result = extractor._is_likely_parent_category(df2, 0, 'Item', 'Total')
print(f"Is parent? {result}")