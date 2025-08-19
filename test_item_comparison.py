"""
Test script to debug multi-year item comparison issue
"""

import pandas as pd
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
import json

# Initialize extractor
extractor = ExcelHierarchyExtractor()

# Load data from the actual file
file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
data = extractor.extract_from_excel(file_path)

print(f"Years available: {list(data.keys())}")

# Find "Reembolso viagens" in both years
for year in data.keys():
    print(f"\n=== Year {year} ===")
    year_data = data[year]
    
    # Search for the item
    found = False
    for section in year_data.get('sections', []):
        for subcat in section.get('subcategories', []):
            for item in subcat.get('items', []):
                if 'reembolso' in item['name'].lower() or 'viagens' in item['name'].lower():
                    print(f"Found: {item['name']} in {section['name']} > {subcat['name']}")
                    print(f"  Annual value: {item['value']}")
                    print(f"  Monthly data: {item.get('monthly', {})}")
                    found = True
    
    if not found:
        print(f"'Reembolso viagens' NOT FOUND in {year}")

print("\n\n=== Checking exact matches ===")
# Check for exact matches across years
items_2023 = set()
items_2024 = set()

if 2023 in data:
    for section in data[2023].get('sections', []):
        for subcat in section.get('subcategories', []):
            for item in subcat.get('items', []):
                items_2023.add(item['name'])

if 2024 in data:
    for section in data[2024].get('sections', []):
        for subcat in section.get('subcategories', []):
            for item in subcat.get('items', []):
                items_2024.add(item['name'])

print(f"\nItems in 2023: {len(items_2023)}")
print(f"Items in 2024: {len(items_2024)}")
print(f"\nItems only in 2023: {items_2023 - items_2024}")
print(f"\nItems only in 2024: {items_2024 - items_2023}")
print(f"\nCommon items: {len(items_2023 & items_2024)}")

# Check for similar names that might not be exact matches
print("\n\n=== Checking for similar names ===")
for item_2023 in items_2023:
    if 'reembolso' in item_2023.lower() or 'viagem' in item_2023.lower() or 'viagens' in item_2023.lower():
        print(f"2023: '{item_2023}'")
        
for item_2024 in items_2024:
    if 'reembolso' in item_2024.lower() or 'viagem' in item_2024.lower() or 'viagens' in item_2024.lower():
        print(f"2024: '{item_2024}'")

# Let's look for travel-related items in subcategories
print("\n\n=== Looking for travel expenses in subcategories ===")
for year in [2023, 2024]:
    if year in data:
        print(f"\n--- Year {year} ---")
        for section in data[year].get('sections', []):
            for subcat in section.get('subcategories', []):
                # Check if subcategory name contains travel-related words
                if 'viagem' in subcat['name'].lower() or 'viagens' in subcat['name'].lower() or 'reembolso' in subcat['name'].lower():
                    print(f"Found subcategory: '{subcat['name']}' in section '{section['name']}'")
                    print(f"  Value: {subcat['value']}")
                    print(f"  Monthly: {subcat.get('monthly', {})}")
                    print(f"  Items inside:")
                    for item in subcat.get('items', []):
                        print(f"    - {item['name']}: {item['value']}")

# Let's also list all subcategories
print("\n\n=== All subcategories ===")
subcats_2023 = set()
subcats_2024 = set()

if 2023 in data:
    for section in data[2023].get('sections', []):
        for subcat in section.get('subcategories', []):
            subcats_2023.add(subcat['name'])

if 2024 in data:
    for section in data[2024].get('sections', []):
        for subcat in section.get('subcategories', []):
            subcats_2024.add(subcat['name'])

print(f"\nSubcategories in 2023: {sorted(subcats_2023)}")
print(f"\nSubcategories in 2024: {sorted(subcats_2024)}")