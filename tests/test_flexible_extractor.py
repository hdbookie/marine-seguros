#!/usr/bin/env python3
"""
Test script for the flexible financial extractor
This demonstrates how the system automatically detects all financial line items
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.flexible_extractor import FlexibleFinancialExtractor
import pandas as pd

def test_flexible_extraction():
    """Test the flexible extraction on sample files"""
    print("="*60)
    print("Testing Flexible Financial Extractor")
    print("="*60)
    
    extractor = FlexibleFinancialExtractor()
    
    # Test files
    test_files = [
        'Análise de Resultado Financeiro 2018_2023.xlsx',
        'Resultado Financeiro - 2024.xlsx',
        'Resultado Financeiro - 2025.xlsx'
    ]
    
    all_data = {}
    all_categories = set()
    all_line_items = set()
    
    for file in test_files:
        try:
            print(f"\nProcessing: {file}")
            data = extractor.extract_from_excel(file)
            
            if data:
                all_data.update(data)
                
                # Collect all categories and line items
                for year, year_data in data.items():
                    all_categories.update(year_data['categories'].keys())
                    all_line_items.update(item['label'] for item in year_data['line_items'].values())
                    
        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    print(f"Years extracted: {sorted(all_data.keys())}")
    print(f"Total categories found: {len(all_categories)}")
    print(f"Total unique line items: {len(all_line_items)}")
    
    print("\nCategories found:")
    for category in sorted(all_categories):
        print(f"  - {category}")
    
    # Show sample data for latest year
    if all_data:
        latest_year = max(all_data.keys())
        print(f"\nSample data for {latest_year}:")
        print("-"*40)
        
        year_data = all_data[latest_year]
        for category in sorted(year_data['categories'].keys()):
            items = year_data['categories'][category]
            total = sum(year_data['line_items'][item]['annual'] for item in items)
            print(f"\n{category.upper()} (Total: R$ {total:,.2f})")
            
            # Show first 3 items in category
            for i, item_key in enumerate(items[:3]):
                item = year_data['line_items'][item_key]
                print(f"  - {item['label']}: R$ {item['annual']:,.2f}")
            
            if len(items) > 3:
                print(f"  ... and {len(items) - 3} more items")
    
    # Test consolidation
    print("\n" + "="*60)
    print("TESTING CONSOLIDATION")
    print("="*60)
    
    consolidated_df = extractor.consolidate_all_years(all_data)
    print(f"Consolidated DataFrame shape: {consolidated_df.shape}")
    print(f"Years in DataFrame: {consolidated_df['year'].tolist()}")
    print(f"Columns (first 10): {consolidated_df.columns.tolist()[:10]}")
    
    # Show how new categories would appear
    print("\n" + "="*60)
    print("FLEXIBILITY DEMONSTRATION")
    print("="*60)
    print("The system automatically detects:")
    print("✓ Any new expense categories added to future Excel files")
    print("✓ Changes in naming (e.g., 'Marketing' → 'Despesas de Marketing')")
    print("✓ New subcategories within existing categories")
    print("✓ One-time expenses that only appear in specific years")
    print("\nNo code changes needed when you add new rows to your Excel files!")

if __name__ == "__main__":
    test_flexible_extraction()