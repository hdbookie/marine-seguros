#!/usr/bin/env python3
"""Test script for Fixed Cost Extractor"""

import pandas as pd
import glob
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.extractors.fixed_cost_extractor import FixedCostExtractor

# Find Excel files
excel_files = glob.glob("*.xlsx")
print(f"Found {len(excel_files)} Excel files")
print("="*60)

# Test with 2024 file
file_2024 = next((f for f in excel_files if '2024' in f and not f.startswith('~')), None)
if not file_2024:
    print("No 2024 file found!")
    exit(1)

print(f"\nTesting Fixed Cost Extractor with: {file_2024}")
print("="*60)

# Read the Excel file
excel_file = pd.ExcelFile(file_2024)
test_sheet = 'Resultado'

print(f"\nTesting with sheet: {test_sheet}")
print("="*60)

# Read the sheet
df = pd.read_excel(file_2024, sheet_name=test_sheet)
print(f"Sheet shape: {df.shape}")

# Show rows around CUSTOS FIXOS
print(f"\nSearching for CUSTOS FIXOS and related rows:")
for i in range(len(df)):
    if pd.notna(df.iloc[i, 0]):
        label = str(df.iloc[i, 0]).strip()
        if i >= 18 and i <= 70:  # Range where fixed costs typically are
            # Get annual value
            annual_val = None
            for col_idx, col in enumerate(df.columns):
                if 'ANUAL' in str(col).upper():
                    annual_val = df.iloc[i, col_idx]
                    break
            if annual_val and (isinstance(annual_val, (int, float)) or '$' not in str(annual_val)):
                print(f"  Row {i}: {label} = {annual_val}")

# Initialize and test the extractor
print("\n" + "="*60)
print("Testing Fixed Cost Extractor")
print("="*60)

extractor = FixedCostExtractor()
year = 2024

try:
    result = extractor.extract_fixed_costs(df, year)
    
    print(f"\nExtraction Results:")
    print(f"Annual total: R$ {result.get('annual', 0):,.2f}")
    
    if 'monthly' in result:
        print(f"\nMonthly breakdown:")
        total_monthly = 0
        for month, value in result['monthly'].items():
            print(f"  {month}: R$ {value:,.2f}")
            total_monthly += value
        print(f"  Monthly sum: R$ {total_monthly:,.2f}")
    
    if 'line_items' in result:
        print(f"\nLine items found: {len(result['line_items'])}")
        for key, item in result['line_items'].items():
            print(f"  - {item['label']}: R$ {item['annual']:,.2f}")
    
    # Test specific known values for 2024
    print("\n" + "="*60)
    print("Validation Check for 2024")
    print("="*60)
    
    # For 2024, we expect CUSTOS FIXOS: R$ 1,415,084.32
    expected_annual = 1415084.32
    actual_annual = result.get('annual', 0)
    diff = abs(actual_annual - expected_annual)
    
    print(f"Expected annual (CUSTOS FIXOS): R$ {expected_annual:,.2f}")
    print(f"Actual annual extracted: R$ {actual_annual:,.2f}")
    print(f"Difference: R$ {diff:,.2f}")
    
    if diff < 1:  # Allow for small rounding differences
        print("✅ PASS: Annual total matches expected value!")
    else:
        print("❌ FAIL: Annual total does not match expected value")
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test Complete")
print("="*60)