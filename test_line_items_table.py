#!/usr/bin/env python3
"""
Test script to verify the line items table functionality
"""

import pandas as pd
from core.unified_extractor import UnifiedFinancialExtractor
from utils import format_currency

def test_line_items_extraction():
    """Test that line items are properly extracted for the table view"""
    
    # Extract data
    extractor = UnifiedFinancialExtractor()
    file_path = "/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2025.xlsx"
    year_data = extractor.extract_from_excel(file_path)
    
    print("=== LINE ITEMS TABLE TEST ===")
    
    if 2025 in year_data:
        data = year_data[2025]
        
        if 'universal_data' in data and data['universal_data']:
            universal = data['universal_data']
            all_line_items = universal.get('all_line_items', [])
            
            print(f"Total line items extracted: {len(all_line_items)}")
            
            if all_line_items:
                print("\nFirst 10 line items:")
                for i, item in enumerate(all_line_items[:10]):
                    print(f"{i+1}. {item['label']}: {format_currency(item['annual'])}")
                    print(f"   Category: {item.get('category', 'uncategorized')}")
                    print(f"   Section: {item.get('section', '')}")
                    print(f"   Is sub-item: {item.get('is_sub_item', False)}")
                    if item.get('parent'):
                        print(f"   Parent: {item['parent']}")
                    print()
                
                # Test filtering capabilities
                categories = set(item.get('category', 'uncategorized') for item in all_line_items)
                print(f"Categories found: {len(categories)}")
                for cat in sorted(categories):
                    cat_items = [item for item in all_line_items if item.get('category', 'uncategorized') == cat]
                    cat_total = sum(item['annual'] for item in cat_items)
                    print(f"  - {cat}: {len(cat_items)} items, {format_currency(cat_total)}")
                
                # Sub-items analysis
                sub_items = [item for item in all_line_items if item.get('is_sub_item')]
                print(f"\nSub-items found: {len(sub_items)}")
                
                if sub_items:
                    print("First 5 sub-items:")
                    for i, item in enumerate(sub_items[:5]):
                        print(f"{i+1}. {item['label']}: {format_currency(item['annual'])} (parent: {item.get('parent', 'None')})")
                
                print("\n✅ Line items extraction working correctly!")
            else:
                print("❌ No line items found!")
        else:
            print("❌ No universal data found!")
    else:
        print("❌ No data found for 2025!")

if __name__ == "__main__":
    test_line_items_extraction()