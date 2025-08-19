"""
Test multi-year comparison for items that exist in both years
"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

# Initialize extractor
extractor = ExcelHierarchyExtractor()

# Load data from the actual file
file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
data = extractor.extract_from_excel(file_path)

# Find common subcategories between 2023 and 2024
subcats_2023 = {}
subcats_2024 = {}

if 2023 in data:
    for section in data[2023].get('sections', []):
        for subcat in section.get('subcategories', []):
            key = f"{section['name']}:{subcat['name']}"
            subcats_2023[key] = {
                'section': section['name'],
                'subcat': subcat['name'],
                'value': subcat['value'],
                'monthly': subcat.get('monthly', {}),
                'items': subcat.get('items', [])
            }

if 2024 in data:
    for section in data[2024].get('sections', []):
        for subcat in section.get('subcategories', []):
            key = f"{section['name']}:{subcat['name']}"
            subcats_2024[key] = {
                'section': section['name'],
                'subcat': subcat['name'],
                'value': subcat['value'],
                'monthly': subcat.get('monthly', {}),
                'items': subcat.get('items', [])
            }

# Find common subcategories with monthly data in both years
common_subcats = set(subcats_2023.keys()) & set(subcats_2024.keys())

print("=== Common subcategories with monthly data ===")
for key in sorted(common_subcats):
    data_2023 = subcats_2023[key]
    data_2024 = subcats_2024[key]
    
    # Check if both have monthly data
    if data_2023['monthly'] and data_2024['monthly']:
        print(f"\n✓ {key}")
        print(f"  2023: {len(data_2023['monthly'])} months of data")
        print(f"  2024: {len(data_2024['monthly'])} months of data")

# Let's specifically check for "Combustível", "Energia Elétrica", "Comunicação e Marketing"
print("\n\n=== Checking specific subcategories for testing ===")
test_subcats = ["Comunicação e Marketing", "Funcionários", "Infraestrutura", "Tecnologia e Comunicação"]

for subcat_name in test_subcats:
    print(f"\n--- {subcat_name} ---")
    found_2023 = False
    found_2024 = False
    
    for key in subcats_2023:
        if subcat_name in key:
            found_2023 = True
            data = subcats_2023[key]
            print(f"2023: Found in {data['section']}")
            print(f"  Value: {data['value']}")
            print(f"  Monthly data: {bool(data['monthly'])}")
            
    for key in subcats_2024:
        if subcat_name in key:
            found_2024 = True
            data = subcats_2024[key]
            print(f"2024: Found in {data['section']}")
            print(f"  Value: {data['value']}")
            print(f"  Monthly data: {bool(data['monthly'])}")
    
    if found_2023 and found_2024:
        print("  ✓ Available in both years!")
    elif not found_2023:
        print("  ✗ Not found in 2023")
    elif not found_2024:
        print("  ✗ Not found in 2024")