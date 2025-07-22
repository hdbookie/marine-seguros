#!/usr/bin/env python3
"""Debug script to check what happens with 2024 and 2025 data"""

import os
import sys
from pathlib import Path
import json
import sqlite3

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.direct_extractor import DirectDataExtractor
from database_manager import DatabaseManager

def test_individual_files():
    """Test each file individually"""
    print("=== Testing Individual Files ===")
    
    extractor = DirectDataExtractor()
    files_to_test = [
        'Análise de Resultado Financeiro 2018_2023.xlsx',
        'Resultado Financeiro - 2024.xlsx',
        'Resultado Financeiro - 2025.xlsx'
    ]
    
    all_data = {}
    
    for file in files_to_test:
        print(f"\n--- Testing {file} ---")
        
        if not os.path.exists(file):
            print(f"❌ File not found: {file}")
            continue
        
        try:
            data = extractor.extract_from_excel(file)
            if data:
                print(f"✅ Extracted {len(data)} years from {file}")
                for year, year_data in sorted(data.items()):
                    print(f"  {year}: Revenue={year_data.get('revenue', {}).get('ANNUAL', 0):,.2f}")
                    all_data[year] = year_data
            else:
                print(f"❌ No data extracted from {file}")
                
        except Exception as e:
            print(f"❌ Error processing {file}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n=== Summary ===")
    print(f"Total years extracted: {len(all_data)}")
    for year in sorted(all_data.keys()):
        print(f"  {year}: {all_data[year].get('revenue', {}).get('ANNUAL', 0):,.2f}")
    
    return all_data

def test_database_save_all(data):
    """Test saving all data to database"""
    print(f"\n=== Testing Database Save for All Years ===")
    
    db = DatabaseManager()
    
    # Clear existing data
    print("Clearing existing data...")
    db.clear_all_data()
    
    saved_years = []
    failed_years = []
    
    for year, year_data in data.items():
        year_str = str(year)
        print(f"\nAttempting to save year {year}...")
        
        # Debug: show what we're trying to save
        revenue = year_data.get('revenue', {})
        costs = year_data.get('costs', {})
        print(f"  Revenue keys: {list(revenue.keys())}")
        print(f"  Costs keys: {list(costs.keys())}")
        print(f"  Annual revenue: {revenue.get('ANNUAL', 0):,.2f}")
        
        if db.save_financial_data(year_str, year_data):
            saved_years.append(year)
            print(f"✅ Successfully saved {year}")
        else:
            failed_years.append(year)
            print(f"❌ Failed to save {year}")
    
    print(f"\nSave Summary:")
    print(f"  Saved: {saved_years}")
    print(f"  Failed: {failed_years}")
    
    # Verify what's in the database
    stats = db.get_data_stats()
    db_count = stats.get('financial_data', {}).get('count', 0)
    print(f"  Database reports {db_count} years saved")
    
    return saved_years, failed_years

def check_database_contents():
    """Check what's actually in the database"""
    print(f"\n=== Database Contents ===")
    
    db = DatabaseManager()
    loaded_data = db.load_all_financial_data()
    
    print(f"Years in database: {sorted(loaded_data.keys())}")
    for year in sorted(loaded_data.keys()):
        year_data = loaded_data[year]
        revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
        print(f"  {year}: R$ {revenue:,.2f}")

if __name__ == "__main__":
    print("Debugging missing 2024/2025 data...\n")
    
    # Test individual file extraction
    all_data = test_individual_files()
    
    if all_data:
        # Test saving to database
        saved, failed = test_database_save_all(all_data)
        
        # Check what's in database
        check_database_contents()
    
    print("\nDebug completed.")