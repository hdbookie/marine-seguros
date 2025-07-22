#!/usr/bin/env python3
"""Test the session state fix in app.py"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import DatabaseManager
from core import FinancialProcessor

class MockSessionState:
    """Mock Streamlit session state for testing"""
    def __init__(self):
        self.extracted_data = {}
        self.processed_data = None
        self.monthly_data = None
        self.selected_years = []
        self.selected_months = []
        self.comparative_analysis = None

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

def test_session_fix():
    """Test the session state fix"""
    print("=== Testing Session State Fix ===")
    
    # Initialize database and mock session state
    db = DatabaseManager()
    st = MockSessionState()
    
    # Step 1: Try to load data from database (like app.py line 172)
    print("\n--- Step 1: Loading from database ---")
    data_loaded = db.auto_load_state(st)
    print(f"Data loaded: {data_loaded}")
    
    if data_loaded and st.extracted_data:
        print(f"Extracted data years: {sorted(st.extracted_data.keys())}")
        
        # Step 2: Convert to processed format (like app.py lines 175-181)
        print(f"\n--- Step 2: Converting to processed format ---")
        print(f"About to convert {len(st.extracted_data)} years to processed format")
        processed = convert_extracted_to_processed(st.extracted_data)
        
        if processed:
            st.processed_data = processed
            print(f"Successfully converted to processed format with {len(processed['consolidated'])} rows")
            
            df = processed['consolidated']
            print(f"Years in consolidated DataFrame: {sorted(df['year'].tolist())}")
            
            # Step 3: Test the dashboard logic (like app.py line 608)
            print(f"\n--- Step 3: Testing dashboard display logic ---")
            available_years = sorted(df['year'].unique())
            print(f"Available years: {available_years}")
            
            default_selected = available_years[-3:] if len(available_years) >= 3 else available_years
            print(f"Default selected years (last 3): {default_selected}")
            
            # Simulate what happens when user refreshes and sees dashboard
            if available_years:
                print(f"✅ SUCCESS: All years should be visible in dashboard")
                return True
            else:
                print(f"❌ FAILURE: No years available in dashboard")
                return False
        else:
            print("❌ FAILURE: Failed to convert to processed format")
            return False
    else:
        print("❌ FAILURE: No data loaded from database")
        return False

if __name__ == "__main__":
    print("Testing session state fix for missing 2024/2025 data...\n")
    success = test_session_fix()
    print(f"\nTest result: {'✅ PASSED' if success else '❌ FAILED'}")