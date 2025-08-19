#!/usr/bin/env python3
"""
Analyze raw data to understand hierarchy issues
"""

import json
from core.database_manager import DatabaseManager

def analyze_data():
    db = DatabaseManager()
    data = db.load_shared_financial_data()
    
    if not data:
        print("No data found in database")
        return
    
    print("=== RAW DATA ANALYSIS ===\n")
    
    # Check each year
    for year, year_data in data.items():
        print(f"\n📅 YEAR {year}:")
        print("=" * 50)
        
        if not isinstance(year_data, dict) or 'sections' not in year_data:
            print(f"  ⚠️ Invalid data structure for year {year}")
            continue
        
        for section in year_data.get('sections', []):
            section_name = section.get('name', 'Unknown')
            section_value = section.get('value', 0)
            
            # Only check CUSTOS FIXOS for now
            if 'CUSTOS FIXOS' in section_name.upper():
                print(f"\n  📁 SECTION: {section_name} (R$ {section_value:,.2f})")
                
                # Look for all subcategories
                subcats = section.get('subcategories', [])
                print(f"  Total subcategories: {len(subcats)}")
                
                # Look specifically for travel-related items
                travel_found = False
                standalone_items = []
                
                for subcat in subcats:
                    subcat_name = subcat.get('name', 'Unknown')
                    subcat_value = subcat.get('value', 0)
                    items = subcat.get('items', [])
                    
                    # Check if this is Viagens e Deslocamentos
                    if 'viagens' in subcat_name.lower() or 'deslocamentos' in subcat_name.lower():
                        travel_found = True
                        print(f"\n    ✅ Found 'Viagens e Deslocamentos': {subcat_name}")
                        print(f"       Value: R$ {subcat_value:,.2f}")
                        print(f"       Has {len(items)} child items:")
                        for item in items:
                            print(f"         - {item.get('name')}: R$ {item.get('value', 0):,.2f}")
                    
                    # Check for items that should be under Viagens
                    elif any(x in subcat_name.lower() for x in ['combustível', 'alimenta', 'hotel', 'estacionamento', 'aluguel']):
                        standalone_items.append((subcat_name, subcat_value, len(items)))
                
                if standalone_items:
                    print(f"\n    ⚠️ Found items that might belong to 'Viagens e Deslocamentos' as standalone:")
                    for name, value, child_count in standalone_items:
                        status = "WITH CHILDREN" if child_count > 0 else "NO CHILDREN"
                        print(f"       - {name}: R$ {value:,.2f} ({status})")
                
                if not travel_found:
                    print(f"\n    ❌ 'Viagens e Deslocamentos' NOT FOUND as subcategory")
                
                # Show all subcategory names for debugging
                print(f"\n    All subcategories in CUSTOS FIXOS:")
                for subcat in subcats[:20]:  # Show first 20
                    subcat_name = subcat.get('name', 'Unknown')
                    items = subcat.get('items', [])
                    print(f"       - {subcat_name} ({len(items)} items)")

if __name__ == "__main__":
    analyze_data()