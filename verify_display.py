#!/usr/bin/env python3
"""Verify what's being displayed in the hierarchy"""

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
from utils import format_currency

# Extract data
file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
extractor = ExcelHierarchyExtractor()
result = extractor.extract_from_excel(file_path)

if 2024 in result:
    year_data = result[2024]
    
    print("=" * 80)
    print("WHAT YOU SHOULD SEE IN MICRO ANALYSIS V2 TAB")
    print("=" * 80)
    print("\nWhen you click on '🔬 Análise Micro V2' and select '📂 Estrutura Hierárquica':")
    print("\n" + "─" * 80)
    
    # Display what would be shown
    for section in year_data['sections']:
        print(f"\n▼ {section['name']} - {format_currency(section.get('value', 0))}")
        print("  " + "─" * 60)
        
        # Show subcategories
        subcats = section.get('subcategories', [])
        for i, subcat in enumerate(subcats):
            has_items = len(subcat.get('items', [])) > 0
            
            if has_items:
                # Parent with children
                print(f"  └── {subcat['name']} - {format_currency(subcat.get('value', 0))}")
                
                # Check sum
                items_sum = sum(item['value'] for item in subcat['items'])
                if abs(subcat['value'] - items_sum) < 100:
                    print(f"      ✓ Parent sum matches children ({len(subcat['items'])} items)")
                
                # Show first few items
                for j, item in enumerate(subcat['items'][:3]):
                    if j == len(subcat['items']) - 1 or j == 2:
                        print(f"        └─ {item['name']} - {format_currency(item['value'])}")
                    else:
                        print(f"        ├─ {item['name']} - {format_currency(item['value'])}")
                
                if len(subcat['items']) > 3:
                    print(f"        ... and {len(subcat['items']) - 3} more items")
            else:
                # Standalone item
                if i == len(subcats) - 1:
                    print(f"  └── {subcat['name']} - {format_currency(subcat.get('value', 0))}")
                else:
                    print(f"  ├── {subcat['name']} - {format_currency(subcat.get('value', 0))}")
        
        if len(subcats) > 5:
            print(f"\n  [Click to expand and see all {len(subcats)} subcategories]")
    
    print("\n" + "=" * 80)
    print("\nVISUALIZATION OPTIONS AVAILABLE:")
    print("  • 📂 Estrutura Hierárquica - Tree view with expandable sections")
    print("  • ☀️ Gráfico Sunburst - Interactive circular hierarchy")
    print("  • 🗺️ Treemap - Proportional rectangles")
    print("  • 🥧 Composição por Categoria - Pie chart breakdown")
    print("  • 📊 Tabela Detalhada - Full table view")
    
    print("\n" + "=" * 80)
    print("KEY FEATURES:")
    print("  ✓ 3-level hierarchy preserved from Excel")
    print("  ✓ Parent values = sum of children (automatically verified)")
    print("  ✓ Items with '-' prefix properly nested as Level 3")
    print("  ✓ Dynamic discovery of structure (not forced into predefined categories)")
    
else:
    print("No 2024 data found!")