#!/usr/bin/env python3
"""Test the hierarchy extraction with the actual Excel file"""

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor

# Use the actual uploaded file
file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"

extractor = ExcelHierarchyExtractor()
result = extractor.extract_from_excel(file_path)

# Check a specific year
if 2024 in result:
    print("2024 Data Extracted Successfully!")
    print("=" * 60)
    
    data = result[2024]
    
    # Show sections
    for section in data['sections']:
        print(f"\n{section['name']} - R$ {section['value']:,.2f}")
        
        # Show first few subcategories
        for i, subcat in enumerate(section.get('subcategories', [])[:3]):
            print(f"  └─ {subcat['name']} - R$ {subcat['value']:,.2f}")
            
            # Check if children sum matches parent
            children_sum = sum(item['value'] for item in subcat.get('items', []))
            if children_sum > 0:
                diff = abs(subcat['value'] - children_sum)
                match = "✓" if diff < 100 else "✗"
                print(f"     (children sum: R$ {children_sum:,.2f}) {match}")
            
            # Show first few items
            for item in subcat.get('items', [])[:2]:
                print(f"      ├─ {item['name']} - R$ {item['value']:,.2f}")
        
        if len(section.get('subcategories', [])) > 3:
            print(f"  ... and {len(section['subcategories']) - 3} more subcategories")
else:
    print("No 2024 data found!")
    print("Available years:", list(result.keys()))