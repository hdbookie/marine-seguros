#!/usr/bin/env python3
"""Diagnose what the UI should be displaying"""

from core.extractors.excel_hierarchy_extractor import ExcelHierarchyExtractor
from core.gerenciador_arquivos import GerenciadorArquivos

# Initialize file manager
file_manager = GerenciadorArquivos()
file_paths = file_manager.obter_caminhos_arquivos()

print("=" * 80)
print("DIAGNOSTIC: What should be in Micro Analysis V2 tab")
print("=" * 80)

if file_paths:
    print(f"\n✓ Files found: {len(file_paths)}")
    for fp in file_paths:
        print(f"  - {fp}")
    
    # Extract using Excel hierarchy extractor
    excel_extractor = ExcelHierarchyExtractor()
    excel_hierarchy_data = {}
    
    for file_path in file_paths:
        extracted = excel_extractor.extract_from_excel(file_path)
        excel_hierarchy_data.update(extracted)
    
    print(f"\n✓ Years extracted: {list(excel_hierarchy_data.keys())}")
    
    if excel_hierarchy_data:
        print("\nWhat you should see in '🔬 Análise Micro V2' → '🏗️ Estrutura Excel Nativa':")
        print("-" * 70)
        
        # Check what the year selector should show
        print(f"1. Year selector should show: {sorted(excel_hierarchy_data.keys())}")
        print(f"   Default selected: {max(excel_hierarchy_data.keys())}")
        
        # Check 2024 data
        if 2024 in excel_hierarchy_data:
            year_data = excel_hierarchy_data[2024]
            
            print(f"\n2. When 2024 is selected:")
            print(f"   - Sections available: {len(year_data.get('sections', []))}")
            print(f"   - Calculations available: {len(year_data.get('calculations', {}))}")
            
            print(f"\n3. In '📂 Estrutura Hierárquica' visualization:")
            
            # Check if sections exist
            if 'sections' in year_data and year_data['sections']:
                print(f"   ✓ {len(year_data['sections'])} main sections should appear as expandable items")
                
                # Show what should be displayed
                for i, section in enumerate(year_data['sections'][:3]):
                    print(f"\n   Section {i+1}: {section['name']}")
                    print(f"   - Value: R$ {section['value']:,.2f}")
                    print(f"   - Has {len(section.get('subcategories', []))} subcategories")
                    
                    # Check first subcategory
                    if section.get('subcategories'):
                        first_sub = section['subcategories'][0]
                        print(f"   - First subcategory: {first_sub['name']} (R$ {first_sub['value']:,.2f})")
                        print(f"     Has {len(first_sub.get('items', []))} items")
            else:
                print("   ✗ ERROR: No sections found in data!")
                print(f"   Keys in year_data: {list(year_data.keys())}")
        else:
            print("\n✗ ERROR: 2024 data not found!")
    else:
        print("\n✗ ERROR: No data extracted from Excel files!")
else:
    print("\n✗ ERROR: No files found in data/arquivos_enviados!")

print("\n" + "=" * 80)
print("TROUBLESHOOTING:")
print("1. Make sure you're in the '🔬 Análise Micro V2' tab")
print("2. Look for the '🏗️ Estrutura Excel Nativa' sub-tab")
print("3. Check the year selector shows 2024")
print("4. Select '📂 Estrutura Hierárquica' from the visualization dropdown")
print("5. Check 'Expandir Tudo' to see all levels")
print("=" * 80)