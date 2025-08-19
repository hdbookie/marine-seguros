#!/usr/bin/env python3
"""Test with actual extractor call"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

test_data = {
    'Item': ['Infraestrutura', 'Condomínios', 'Escritório Contábil', 'Advogados', 'Energia Elétrica', 'Seguros', 'Funcionários'],
    'Total': [53500, 18100, 9300, 11400, 4300, 10400, 836700]
}

df = pd.DataFrame(test_data)
extractor = ExcelHierarchyExtractor()

# Find columns as the extractor would
label_col = extractor._find_label_column(df)
annual_col = extractor._find_annual_column(df)

print(f"Label column: {label_col}")
print(f"Annual column: {annual_col}")
print()

# Now test parent detection
if label_col and annual_col:
    result = extractor._is_likely_parent_category(df, 0, label_col, annual_col)
    print(f"Is 'Infraestrutura' a parent? {result}")
    
    # Also test the values we're getting
    val = extractor._get_numeric_value(df.iloc[0], annual_col)
    print(f"Value extracted: {val}")