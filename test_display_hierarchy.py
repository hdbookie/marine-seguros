#!/usr/bin/env python3
"""Test what hierarchy is being displayed"""

import json
from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

# Use the actual uploaded file
file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"

extractor = ExcelHierarchyExtractor()
result = extractor.extract_from_excel(file_path)

# Check 2024 data
if 2024 in result:
    data = result[2024]
    
    print("=" * 60)
    print("CHECKING 2024 HIERARCHY STRUCTURE")
    print("=" * 60)
    
    # Check what sections we have
    print(f"\nNumber of sections: {len(data.get('sections', []))}")
    for section in data.get('sections', []):
        print(f"\nSection: {section['name']}")
        print(f"  Value: R$ {section['value']:,.2f}")
        print(f"  Subcategories: {len(section.get('subcategories', []))}")
        
        # Show first few subcategories with their structure
        for i, subcat in enumerate(section.get('subcategories', [])[:5]):
            items_count = len(subcat.get('items', []))
            print(f"    [{i+1}] {subcat['name']}: R$ {subcat['value']:,.2f} ({items_count} items)")
            
            # Check if parent-child sums match
            if items_count > 0:
                items_sum = sum(item['value'] for item in subcat['items'])
                diff = abs(subcat['value'] - items_sum)
                if diff < 100:
                    print(f"        ✓ Sum matches! ({items_sum:.2f})")
                else:
                    print(f"        ✗ Sum mismatch! Parent: {subcat['value']:.2f}, Children: {items_sum:.2f}")
            
            # Show first 2 items
            for j, item in enumerate(subcat.get('items', [])[:2]):
                print(f"          - {item['name']}: R$ {item['value']:,.2f}")
    
    # Check calculations
    print(f"\n\nCalculations found: {len(data.get('calculations', {}))}")
    for calc_name in list(data.get('calculations', {}).keys())[:5]:
        print(f"  - {calc_name}")
    
    # Save to JSON for inspection
    with open('hierarchy_output.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print("\n✅ Full hierarchy saved to hierarchy_output.json")
    
else:
    print("No 2024 data found!")
    print("Available years:", list(result.keys()))