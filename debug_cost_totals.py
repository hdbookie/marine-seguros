#!/usr/bin/env python3
"""
Debug script to check why costs are showing R$ 34.43M instead of R$ 2.53M
"""

import pandas as pd
from core.unified_extractor import UnifiedFinancialExtractor
from utils import format_currency
import json

def debug_cost_totals():
    """Debug cost totals from 2025 file"""
    
    extractor = UnifiedFinancialExtractor()
    file_path = "/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2025.xlsx"
    
    print("=== DEBUGGING COST TOTALS FOR 2025 ===\n")
    
    # Extract data
    year_data = extractor.extract_from_excel(file_path)
    
    if 2025 in year_data:
        data = year_data[2025]
        
        # Check main cost categories
        print("1. MAIN COST CATEGORIES (should sum to ~R$ 2.53M):")
        main_categories = ['variable_costs', 'fixed_costs', 'non_operational_costs']
        main_total = 0
        
        for cat in main_categories:
            if cat in data and isinstance(data[cat], dict):
                value = data[cat].get('annual', 0)
                main_total += value
                print(f"   - {cat}: {format_currency(value)}")
        
        print(f"\n   TOTAL MAIN CATEGORIES: {format_currency(main_total)}")
        print("   Expected: ~R$ 2.53M")
        
        # Check if revenue is being included
        print("\n2. CHECKING FOR REVENUE:")
        if 'revenue' in data:
            if isinstance(data['revenue'], dict):
                revenue_value = data['revenue'].get('annual', 0)
            else:
                revenue_value = data['revenue']
            print(f"   - Revenue found: {format_currency(revenue_value)}")
        
        # Check universal data
        print("\n3. UNIVERSAL DATA ANALYSIS:")
        if 'universal_data' in data and data['universal_data']:
            universal = data['universal_data']
            
            print("\n   Categorized items:")
            categorized_total = 0
            for category, items in universal.get('categorized_items', {}).items():
                cat_total = sum(item['annual'] for item in items.values() if isinstance(item, dict))
                categorized_total += cat_total
                print(f"   - {category}: {format_currency(cat_total)} ({len(items)} items)")
            
            print(f"\n   TOTAL CATEGORIZED: {format_currency(categorized_total)}")
            
            # Check uncategorized
            uncategorized_total = sum(
                item['annual'] for item in universal.get('uncategorized_items', {}).values() 
                if isinstance(item, dict)
            )
            print(f"   TOTAL UNCATEGORIZED: {format_currency(uncategorized_total)}")
            
            print(f"\n   GRAND TOTAL (ALL ITEMS): {format_currency(categorized_total + uncategorized_total)}")
            
            # Check if revenue items are in categorized
            print("\n   Revenue items check:")
            if 'revenue' in universal.get('categorized_items', {}):
                revenue_items = universal['categorized_items']['revenue']
                revenue_total = sum(item['annual'] for item in revenue_items.values() if isinstance(item, dict))
                print(f"   - Revenue items found: {format_currency(revenue_total)}")
                print(f"   - This should NOT be included in cost calculations!")
            
            # Show what categories are actually costs
            print("\n   Cost-only categories (excluding revenue):")
            cost_total = 0
            for category, items in universal.get('categorized_items', {}).items():
                if category != 'revenue':  # Exclude revenue
                    cat_total = sum(item['annual'] for item in items.values() if isinstance(item, dict))
                    cost_total += cat_total
                    print(f"   - {category}: {format_currency(cat_total)}")
            
            print(f"\n   TOTAL COSTS (excluding revenue): {format_currency(cost_total)}")
            
            # Add uncategorized to cost total
            total_with_uncategorized = cost_total + uncategorized_total
            print(f"   TOTAL WITH UNCATEGORIZED: {format_currency(total_with_uncategorized)}")
            
            # Show uncategorized items
            if uncategorized_total > 0:
                print("\n   UNCATEGORIZED ITEMS:")
                for item_key, item_data in universal.get('uncategorized_items', {}).items():
                    if isinstance(item_data, dict):
                        print(f"   - {item_data.get('label', item_key)}: {format_currency(item_data['annual'])}")
                        # Show section if available
                        if 'section' in item_data:
                            print(f"     (Section: {item_data['section']})")
        
        # Show all top-level categories
        print("\n4. ALL TOP-LEVEL CATEGORIES IN DATA:")
        all_categories = sorted(data.keys())
        for cat in all_categories:
            if cat not in ['year', 'all_line_items', 'hierarchy', 'universal_data']:
                if isinstance(data[cat], dict) and 'annual' in data[cat]:
                    print(f"   - {cat}: {format_currency(data[cat]['annual'])}")
                elif isinstance(data[cat], (int, float)):
                    print(f"   - {cat}: {format_currency(data[cat])}")


if __name__ == "__main__":
    debug_cost_totals()