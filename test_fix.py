#!/usr/bin/env python3
"""Test if the fix resolves the 'Missing required field: revenue' error"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.financial_processor import FinancialProcessor
from database_manager import DatabaseManager

def test_fix():
    """Test the fixed extraction and storage process"""
    
    processor = FinancialProcessor()
    db = DatabaseManager()
    
    # Test files
    file_paths = [
        '/Users/hunter/marine-seguros/data/arquivos_enviados/Análise de Resultado Financeiro 2018_2023.xlsx',
        '/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2024.xlsx',
        '/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2025.xlsx'
    ]
    
    print("Testing the fixed extraction process...")
    print("="*60)
    
    # Load Excel files
    excel_data = processor.load_excel_files(file_paths)
    print(f"Loaded {len(excel_data)} Excel files")
    
    # Test the new consolidate_all_years that returns both DataFrame and extracted data
    consolidated_df, extracted_financial_data = processor.consolidate_all_years(excel_data)
    
    print(f"\nExtraction results:")
    print(f"- Consolidated DataFrame shape: {consolidated_df.shape}")
    print(f"- Extracted data years: {sorted(extracted_financial_data.keys())}")
    
    # Test that extracted data has the correct structure
    print("\nValidating extracted data structure:")
    for year, data in sorted(extracted_financial_data.items()):
        has_revenue = 'revenue' in data
        has_costs = 'costs' in data
        revenue_keys = list(data.get('revenue', {}).keys()) if has_revenue else []
        
        print(f"\nYear {year}:")
        print(f"  - Has 'revenue' field: {has_revenue}")
        print(f"  - Has 'costs' field: {has_costs}")
        print(f"  - Revenue keys: {revenue_keys[:5]}{'...' if len(revenue_keys) > 5 else ''}")
        
        # Test database validation
        if db._validate_financial_data(data):
            print(f"  ✅ Passes database validation")
        else:
            print(f"  ❌ FAILS database validation")
    
    # Simulate what happens in the app when saving
    print("\n" + "="*60)
    print("Simulating app save process:")
    
    # This is what would be in st.session_state.processed_data['raw_data']
    raw_data = extracted_financial_data  # Now using the correct extracted data
    
    # Test saving each year
    saved_count = 0
    for year, data in raw_data.items():
        year_str = str(year)
        if db.save_financial_data(year_str, data):
            saved_count += 1
            print(f"✅ Successfully saved year {year_str}")
        else:
            print(f"❌ Failed to save year {year_str}")
    
    print(f"\nSummary: {saved_count}/{len(raw_data)} years saved successfully")
    
    if saved_count == len(raw_data):
        print("\n🎉 SUCCESS! The fix resolves the 'Missing required field: revenue' error!")
    else:
        print("\n⚠️  Some years still failed to save. Check the logs above.")

if __name__ == "__main__":
    test_fix()