#!/usr/bin/env python3
"""Test the data extraction process to debug the 'Missing required field: revenue' error"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.direct_extractor import DirectDataExtractor
from database_manager import DatabaseManager
import json

def test_extraction():
    """Test extraction and validation process"""
    
    # Initialize extractor
    extractor = DirectDataExtractor()
    db = DatabaseManager()
    
    # Test files
    test_files = [
        '/Users/hunter/marine-seguros/data/arquivos_enviados/Análise de Resultado Financeiro 2018_2023.xlsx',
        '/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2024.xlsx',
        '/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2025.xlsx'
    ]
    
    all_extracted_data = {}
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n{'='*60}")
            print(f"Testing file: {os.path.basename(file_path)}")
            print(f"{'='*60}")
            
            # Extract data
            extracted_data = extractor.extract_from_excel(file_path)
            
            if extracted_data:
                print(f"\n✅ Extracted data for years: {sorted(extracted_data.keys())}")
                
                # Check each year's data
                for year, data in sorted(extracted_data.items()):
                    print(f"\n📅 Year {year}:")
                    
                    # Check revenue
                    revenue_data = data.get('revenue', {})
                    if revenue_data:
                        print(f"  ✅ Revenue data found:")
                        print(f"     - Monthly entries: {len([k for k in revenue_data.keys() if k not in ['ANNUAL', 'PRIMARY']])}")
                        print(f"     - Annual total: R$ {revenue_data.get('ANNUAL', 0):,.2f}")
                        if len(revenue_data) <= 5:  # Show details if not too many
                            for month, value in revenue_data.items():
                                print(f"       {month}: R$ {value:,.2f}")
                    else:
                        print(f"  ❌ NO REVENUE DATA")
                    
                    # Check costs
                    costs_data = data.get('costs', {})
                    if costs_data:
                        print(f"  ✅ Costs data found:")
                        print(f"     - Monthly entries: {len([k for k in costs_data.keys() if k != 'ANNUAL'])}")
                        print(f"     - Annual total: R$ {costs_data.get('ANNUAL', 0):,.2f}")
                    else:
                        print(f"  ❌ NO COSTS DATA")
                    
                    # Test database validation
                    print(f"\n  🔍 Testing database validation for year {year}:")
                    if db._validate_financial_data(data):
                        print(f"  ✅ Data passes validation")
                        all_extracted_data[str(year)] = data
                    else:
                        print(f"  ❌ Data FAILS validation")
            else:
                print(f"\n❌ No data extracted from {os.path.basename(file_path)}")
        else:
            print(f"\n❌ File not found: {file_path}")
    
    # Try to save to database
    print(f"\n{'='*60}")
    print("Testing database save")
    print(f"{'='*60}")
    
    saved_count = 0
    for year, data in all_extracted_data.items():
        if db.save_financial_data(year, data):
            saved_count += 1
            print(f"✅ Saved year {year}")
        else:
            print(f"❌ Failed to save year {year}")
    
    print(f"\nSummary: {saved_count}/{len(all_extracted_data)} years saved successfully")
    
    # Show what's in the database
    print(f"\n{'='*60}")
    print("Database contents")
    print(f"{'='*60}")
    
    loaded_data = db.load_all_financial_data()
    if loaded_data:
        print(f"Years in database: {sorted(loaded_data.keys())}")
        for year in sorted(loaded_data.keys()):
            year_data = loaded_data[year]
            revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
            costs = year_data.get('costs', {}).get('ANNUAL', 0)
            print(f"  {year}: Revenue = R$ {revenue:,.2f}, Costs = R$ {costs:,.2f}")
    else:
        print("No data in database")

if __name__ == "__main__":
    test_extraction()