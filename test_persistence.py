#!/usr/bin/env python3
"""Test script to verify data persistence is working correctly"""

import os
import sys
from pathlib import Path
import json
import sqlite3

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.direct_extractor import DirectDataExtractor
from database_manager import DatabaseManager

def test_data_extraction():
    """Test that data extraction works"""
    print("=== Testing Data Extraction ===")
    
    extractor = DirectDataExtractor()
    
    # Test with the 2018-2023 file
    file_path = 'Análise de Resultado Financeiro 2018_2023.xlsx'
    
    if not os.path.exists(file_path):
        print(f"❌ Test file not found: {file_path}")
        return None
    
    try:
        data = extractor.extract_from_excel(file_path)
        print(f"✅ Extracted {len(data)} years from {file_path}")
        
        for year, year_data in sorted(data.items()):
            revenue = year_data.get('revenue', {})
            costs = year_data.get('costs', {})
            print(f"  {year}: {len(revenue)} revenue entries, {len(costs)} cost entries")
            
            # Show sample data
            annual_revenue = revenue.get('ANNUAL', 0)
            if annual_revenue:
                print(f"    Annual Revenue: R$ {annual_revenue:,.2f}")
        
        return data
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_database_save(data):
    """Test saving data to database"""
    print("\n=== Testing Database Save ===")
    
    db = DatabaseManager()
    
    # Clear existing data first
    print("Clearing existing data...")
    db.clear_all_data()
    
    # Save the extracted data
    saved_count = 0
    for year, year_data in data.items():
        year_str = str(year)
        if db.save_financial_data(year_str, year_data):
            saved_count += 1
            print(f"✅ Saved year {year}")
        else:
            print(f"❌ Failed to save year {year}")
    
    print(f"\nTotal saved: {saved_count}/{len(data)} years")
    
    # Verify data was saved
    stats = db.get_data_stats()
    db_count = stats.get('financial_data', {}).get('count', 0)
    print(f"Database reports {db_count} years saved")
    
    return saved_count == len(data)

def test_database_load():
    """Test loading data from database"""
    print("\n=== Testing Database Load ===")
    
    db = DatabaseManager()
    
    # Load all financial data
    loaded_data = db.load_all_financial_data()
    
    if loaded_data:
        print(f"✅ Loaded {len(loaded_data)} years from database")
        
        for year, year_data in sorted(loaded_data.items()):
            revenue = year_data.get('revenue', {})
            costs = year_data.get('costs', {})
            print(f"  {year}: {len(revenue)} revenue entries, {len(costs)} cost entries")
    else:
        print("❌ No data loaded from database")
    
    return loaded_data

def test_persistence_cycle():
    """Test the complete persistence cycle"""
    print("\n=== Testing Complete Persistence Cycle ===")
    
    # 1. Extract data
    extracted_data = test_data_extraction()
    if not extracted_data:
        print("❌ Extraction failed, cannot continue")
        return False
    
    # 2. Save to database
    save_success = test_database_save(extracted_data)
    if not save_success:
        print("❌ Save failed")
        return False
    
    # 3. Load from database
    loaded_data = test_database_load()
    if not loaded_data:
        print("❌ Load failed")
        return False
    
    # 4. Verify data integrity
    print("\n=== Verifying Data Integrity ===")
    
    for year in extracted_data:
        if str(year) not in loaded_data:
            print(f"❌ Year {year} missing from loaded data")
            return False
        
        # Compare revenue data
        orig_revenue = extracted_data[year].get('revenue', {})
        loaded_revenue = loaded_data[str(year)].get('revenue', {})
        
        if len(orig_revenue) != len(loaded_revenue):
            print(f"❌ Revenue data mismatch for {year}: {len(orig_revenue)} vs {len(loaded_revenue)}")
            return False
        
        # Compare annual values
        orig_annual = orig_revenue.get('ANNUAL', 0)
        loaded_annual = loaded_revenue.get('ANNUAL', 0)
        
        if abs(orig_annual - loaded_annual) > 0.01:  # Allow small float differences
            print(f"❌ Annual revenue mismatch for {year}: {orig_annual} vs {loaded_annual}")
            return False
    
    print("✅ Data integrity verified - all data matches!")
    return True

def check_database_contents():
    """Directly check database contents"""
    print("\n=== Direct Database Check ===")
    
    db_path = "data/dashboard.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check financial_data table
            cursor.execute("SELECT year, LENGTH(data) as data_size, updated_at FROM financial_data ORDER BY year")
            rows = cursor.fetchall()
            
            print(f"Found {len(rows)} records in financial_data table:")
            for year, size, updated in rows:
                print(f"  Year {year}: {size} bytes, updated: {updated}")
            
            # Show sample data
            if rows:
                cursor.execute("SELECT year, data FROM financial_data LIMIT 1")
                year, json_data = cursor.fetchone()
                data = json.loads(json_data)
                
                print(f"\nSample data for year {year}:")
                print(f"  Revenue months: {list(data.get('revenue', {}).keys())}")
                print(f"  Annual revenue: R$ {data.get('revenue', {}).get('ANNUAL', 0):,.2f}")
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting data persistence tests...\n")
    
    # Run the complete test
    success = test_persistence_cycle()
    
    # Check database directly
    check_database_contents()
    
    if success:
        print("\n✅ All tests passed! Data persistence is working correctly.")
    else:
        print("\n❌ Tests failed. Check the errors above.")
    
    print("\nTest completed.")