#!/usr/bin/env python3
"""Debug script to check data extraction"""

import json
import os
from core.flexible_extractor import FlexibleFinancialExtractor
from core.process_manager import process_detailed_monthly_data

def main():
    # Check if we have extracted data
    if os.path.exists('data/extracted_data.json'):
        print("Loading extracted data from file...")
        with open('data/extracted_data.json', 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)
    else:
        print("No extracted data file found. Please run the app and upload Excel files first.")
        return
    
    # Show what years we have
    years = list(extracted_data.keys())
    print(f"\nYears in data: {years}")
    
    # Focus on 2024
    if '2024' in extracted_data:
        print("\n=== 2024 Data Analysis ===")
        year_data = extracted_data['2024']
        
        # Show categories
        if 'categories' in year_data:
            print("\nCategories found:")
            for cat, items in year_data['categories'].items():
                total = sum(year_data['line_items'][item]['annual'] for item in items if item in year_data['line_items'])
                print(f"  {cat}: {len(items)} items, R$ {total:,.2f}")
        
        # Show some large items
        print("\n\nTop 10 largest expenses:")
        all_items = []
        for key, item in year_data['line_items'].items():
            all_items.append({
                'label': item['label'],
                'annual': item['annual'],
                'category': item.get('category', 'unknown')
            })
        
        all_items.sort(key=lambda x: x['annual'], reverse=True)
        for i, item in enumerate(all_items[:10]):
            print(f"  {i+1}. {item['label']}: R$ {item['annual']:,.2f} ({item['category']})")
        
        # Total
        total = sum(item['annual'] for item in all_items)
        print(f"\nTotal for all items: R$ {total:,.2f}")
        
        # Now process through the detailed monthly data function
        print("\n\n=== After Processing ===")
        detailed_data = process_detailed_monthly_data(extracted_data)
        
        # Count items for 2024
        items_2024 = [item for item in detailed_data['line_items'] if item['ano'] == '2024']
        total_2024 = sum(item['valor_anual'] for item in items_2024)
        
        print(f"\nItems after processing for 2024: {len(items_2024)}")
        print(f"Total after processing: R$ {total_2024:,.2f}")
        
        # Show what was filtered out
        original_total = sum(item['annual'] for item in all_items)
        if total_2024 < original_total:
            print(f"\nFiltered out: R$ {original_total - total_2024:,.2f}")
            print("\nSome items that might have been filtered:")
            
            # Find items that were filtered
            processed_labels = {item['descricao'] for item in items_2024}
            for item in all_items[:20]:  # Check first 20
                if item['label'] not in processed_labels:
                    print(f"  - {item['label']}: R$ {item['annual']:,.2f}")

if __name__ == "__main__":
    main()