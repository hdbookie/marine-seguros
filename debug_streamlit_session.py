#!/usr/bin/env python3
"""Debug what happens to session state data specifically for Streamlit integration"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import DatabaseManager
from core import FinancialProcessor

def test_full_streamlit_flow():
    """Test the complete flow that happens in app.py"""
    print("=== Testing Full Streamlit Flow ===")
    
    # Step 1: Load from database (simulating st.session_state.extracted_data)
    print("\n--- Step 1: Database Load ---")
    db = DatabaseManager()
    extracted_data = db.load_all_financial_data()
    
    print(f"Extracted data years: {sorted(extracted_data.keys())}")
    
    # Step 2: Convert to processed format (from app.py convert_extracted_to_processed)
    print("\n--- Step 2: Converting to processed format ---")
    processed_data = convert_extracted_to_processed(extracted_data)
    
    if processed_data and 'consolidated' in processed_data:
        df = processed_data['consolidated']
        print(f"Consolidated DataFrame shape: {df.shape}")
        print(f"Years in consolidated DataFrame: {sorted(df['year'].tolist())}")
        
        # Step 3: Test the filter logic from app.py (lines 608-612)
        print("\n--- Step 3: Testing Filter Logic ---")
        available_years = sorted(df['year'].unique())
        print(f"Available years: {available_years}")
        
        # This is the problematic line from app.py
        default_selected = available_years[-3:] if len(available_years) >= 3 else available_years
        print(f"Default selected years (last 3): {default_selected}")
        
        # Test year filtering
        for selected_years_test in [available_years, default_selected, [2024, 2025]]:
            print(f"\n  Testing with selected years: {selected_years_test}")
            if selected_years_test:
                filtered_df = df[df['year'].isin(selected_years_test)]
                print(f"  Filtered DataFrame shape: {filtered_df.shape}")
                print(f"  Years in filtered DataFrame: {sorted(filtered_df['year'].tolist())}")
                
                if filtered_df.empty:
                    print("  ❌ PROBLEM: Filtered DataFrame is empty!")
                elif len(filtered_df) < len(selected_years_test):
                    print(f"  ⚠️  WARNING: Expected {len(selected_years_test)} years but got {len(filtered_df)}")
            else:
                print("  ❌ PROBLEM: No years selected!")
        
        return processed_data
    else:
        print("❌ PROBLEM: No processed data generated!")
        return None

def convert_extracted_to_processed(extracted_data):
    """Convert extracted_data format (from database) to processed_data format (for app) - copied from app.py"""
    if not extracted_data:
        return None
    
    try:
        # Create a DataFrame from extracted_data
        consolidated_data = []
        for year, year_data in sorted(extracted_data.items()):
            revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
            costs = year_data.get('costs', {}).get('ANNUAL', 0)
            
            # Calculate other metrics
            if revenue > 0:
                margin = ((revenue - costs) / revenue) * 100
            else:
                margin = 0
            
            consolidated_data.append({
                'year': int(year),
                'revenue': revenue,
                'variable_costs': costs,
                'gross_profit': revenue - costs,
                'gross_margin': margin,
                'fixed_costs': year_data.get('fixed_costs', 0),
                'operational_costs': year_data.get('operational_costs', 0)
            })
        
        if consolidated_data:
            consolidated_df = pd.DataFrame(consolidated_data)
            
            # Calculate growth metrics
            processor = FinancialProcessor()
            consolidated_df = processor.calculate_growth_metrics(consolidated_df)
            
            return {
                'raw_data': extracted_data,
                'consolidated': consolidated_df,
                'summary': processor.get_financial_summary(consolidated_df),
                'anomalies': []
            }
    except Exception as e:
        print(f"Error converting data: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_year_data_types():
    """Test if there are any data type issues with years"""
    print("\n=== Testing Year Data Types ===")
    
    db = DatabaseManager()
    extracted_data = db.load_all_financial_data()
    
    for year_key, year_data in extracted_data.items():
        print(f"Year key: '{year_key}' (type: {type(year_key)})")
        
        # Test conversion to int
        try:
            year_int = int(year_key)
            print(f"  Converts to int: {year_int}")
        except:
            print(f"  ❌ CANNOT convert to int!")
        
        # Check if revenue data exists
        revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
        print(f"  Revenue: R$ {revenue:,.2f}")
        
        if revenue <= 0:
            print(f"  ⚠️  WARNING: Zero or negative revenue for {year_key}")

if __name__ == "__main__":
    print("Testing Streamlit session flow for missing years...\n")
    
    # Test the conversion and filtering
    processed_data = test_full_streamlit_flow()
    
    # Test year data types
    test_year_data_types()
    
    print("\nDebug completed.")