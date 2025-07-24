#!/usr/bin/env python3
"""Test various data structures to see what passes validation"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager

def test_validation_scenarios():
    """Test different data structures against validation"""
    db = DatabaseManager()
    
    print("Testing different data structures for validation:")
    print("="*60)
    
    # Test 1: Complete data (should pass)
    complete_data = {
        'revenue': {
            'JAN': 100000,
            'FEV': 120000,
            'MAR': 110000,
            'ANNUAL': 1200000
        },
        'costs': {
            'JAN': 20000,
            'FEV': 25000,
            'MAR': 22000,
            'ANNUAL': 240000
        }
    }
    print("\n1. Complete data with monthly and annual:")
    print(f"   Revenue keys: {list(complete_data['revenue'].keys())}")
    print(f"   Validation result: {db._validate_financial_data(complete_data)}")
    
    # Test 2: Only ANNUAL data (might fail)
    annual_only_data = {
        'revenue': {'ANNUAL': 1200000},
        'costs': {'ANNUAL': 240000}
    }
    print("\n2. Only ANNUAL data:")
    print(f"   Revenue keys: {list(annual_only_data['revenue'].keys())}")
    print(f"   Validation result: {db._validate_financial_data(annual_only_data)}")
    
    # Test 3: Empty revenue dict (should fail)
    empty_revenue_data = {
        'revenue': {},
        'costs': {'ANNUAL': 240000}
    }
    print("\n3. Empty revenue dict:")
    print(f"   Revenue keys: {list(empty_revenue_data['revenue'].keys())}")
    print(f"   Validation result: {db._validate_financial_data(empty_revenue_data)}")
    
    # Test 4: Missing revenue field entirely (should fail)
    missing_revenue_data = {
        'costs': {'ANNUAL': 240000}
    }
    print("\n4. Missing revenue field:")
    print(f"   Has 'revenue' field: {'revenue' in missing_revenue_data}")
    print(f"   Validation result: {db._validate_financial_data(missing_revenue_data)}")
    
    # Test 5: Only 2 months of data (should fail)
    two_months_data = {
        'revenue': {
            'JAN': 100000,
            'FEV': 120000
        },
        'costs': {
            'JAN': 20000,
            'FEV': 25000
        }
    }
    print("\n5. Only 2 months of data (no ANNUAL):")
    print(f"   Revenue keys: {list(two_months_data['revenue'].keys())}")
    print(f"   Validation result: {db._validate_financial_data(two_months_data)}")
    
    # Test 6: String year in data structure
    with_year_field = {
        'revenue': {'ANNUAL': 1200000},
        'costs': {'ANNUAL': 240000},
        'year': 2024
    }
    print("\n6. Data with year field (like in sync_processed_to_extracted):")
    print(f"   Revenue keys: {list(with_year_field['revenue'].keys())}")
    print(f"   Has year field: {'year' in with_year_field}")
    print(f"   Validation result: {db._validate_financial_data(with_year_field)}")
    
    # Test 7: None values
    none_values_data = {
        'revenue': {'ANNUAL': None},
        'costs': {'ANNUAL': 240000}
    }
    print("\n7. None values in revenue:")
    print(f"   Revenue ANNUAL value: {none_values_data['revenue']['ANNUAL']}")
    print(f"   Validation result: {db._validate_financial_data(none_values_data)}")

if __name__ == "__main__":
    test_validation_scenarios()