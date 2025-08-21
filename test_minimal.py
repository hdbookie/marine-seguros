#!/usr/bin/env python3
"""Minimal test case"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

test_data = {
    'Item': [
        'CUSTOS FIXOS',
        'Infraestrutura',
        'Condomínios',
        'Escritório Contábil', 
        'Energia Elétrica',
        'Seguros',
        'Funcionários',  # This should be Level 2, not child of Infraestrutura
        '- Salário'
    ],
    'Total': [
        65580.49,
        1653.13,  # Sum of next 4
        431.49,
        581.92,
        260.18,
        379.54,
        35649.02,  # New Level 2 parent
        20608.69
    ]
}

df = pd.DataFrame(test_data)
extractor = ExcelHierarchyExtractor()

# Add some debug output
import sys
original_extract = extractor._extract_hierarchy

def debug_extract(df, year):
    result = original_extract(df, year)
    return result

result = extractor._extract_hierarchy(df, 2024)

print("RESULT:")
for section in result['sections']:
    print(f"{section['name']}")
    for subcat in section['subcategories']:
        print(f"  {subcat['name']} ({subcat['value']})")
        for item in subcat['items']:
            print(f"    - {item['name']} ({item['value']})")