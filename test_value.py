#!/usr/bin/env python3
"""Test value extraction"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

test_data = {
    'Item': ['Infraestrutura'],
    'Total': [53500]
}

df = pd.DataFrame(test_data)
extractor = ExcelHierarchyExtractor()

# Test getting cell value
val = extractor._get_cell_value(df.iloc[0], 'Total')
print(f"Cell value: {val} (type: {type(val)})")

# Test parsing
parsed = extractor._parse_value(val)
print(f"Parsed value: {parsed}")

# Test with direct access
direct = df.iloc[0]['Total']
print(f"Direct access: {direct} (type: {type(direct)})")

# Test the full chain
numeric = extractor._get_numeric_value(df.iloc[0], 'Total')
print(f"Numeric value: {numeric}")