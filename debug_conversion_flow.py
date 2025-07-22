#!/usr/bin/env python3
"""Debug the conversion flow between extracted_data and processed_data to find missing 2024/2025 data"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import DatabaseManager
from core.financial_processor import FinancialProcessor

def debug_conversion_flow():
    """Debug the entire conversion flow to find where 2024/2025 data is lost"""
    print("=== Testing Conversion Flow ===")
    
    # Step 1: Load from database (what the app loads)
    print("\n--- Step 1: Loading from Database ---")
    db = DatabaseManager()
    loaded_data = db.load_all_financial_data()
    
    print(f"Years loaded from database: {sorted(loaded_data.keys())}")
    for year in sorted(loaded_data.keys()):
        revenue = loaded_data[year].get('revenue', {}).get('ANNUAL', 0)
        print(f"  {year}: Revenue = R$ {revenue:,.2f}")
    
    # Step 2: Convert to the format expected by financial processor
    print("\n--- Step 2: Converting extracted_data format to processor format ---")
    
    # This is what app.py does in convert_extracted_to_processed
    try:
        all_years_data = []
        
        for year, year_data in sorted(loaded_data.items()):
            print(f"\nProcessing year {year}:")
            
            # Debug: show what data we have for this year
            revenue_data = year_data.get('revenue', {})
            costs_data = year_data.get('costs', {})
            margins_data = year_data.get('margins', {})
            profits_data = year_data.get('profits', {})
            
            print(f"  Revenue keys: {list(revenue_data.keys())}")
            print(f"  Costs keys: {list(costs_data.keys())}")
            print(f"  Margins keys: {list(margins_data.keys())}")
            print(f"  Profits keys: {list(profits_data.keys())}")
            
            # Check if we have the required annual data
            annual_revenue = revenue_data.get('ANNUAL', 0)
            annual_costs = costs_data.get('ANNUAL', 0)
            
            print(f"  Annual revenue: {annual_revenue:,.2f}")
            print(f"  Annual costs: {annual_costs:,.2f}")
            
            if annual_revenue > 0:  # Only process if we have revenue data
                # Use the most appropriate profit value (from financial_processor.py logic)
                net_profit = (profits_data.get('OPERATIONAL') or 
                             profits_data.get('WITH_NON_OP') or
                             profits_data.get('NET_FINAL') or 
                             profits_data.get('OTHER') or
                             profits_data.get('WITHOUT_NON_OP') or
                             profits_data.get('NET_ADJUSTED') or
                             profits_data.get('GROSS') or 0)
                
                row_data = {
                    'year': int(year),
                    'revenue': annual_revenue,
                    'variable_costs': annual_costs,  # Note: using 'variable_costs' column name
                    'net_profit': net_profit,
                    'profit_margin': (net_profit / annual_revenue * 100) if annual_revenue > 0 else 0
                }
                
                all_years_data.append(row_data)
                print(f"  ✅ Added to processed data: R$ {annual_revenue:,.2f} revenue")
            else:
                print(f"  ❌ Skipped due to zero revenue")
        
        # Step 3: Create DataFrame like the processor does
        print(f"\n--- Step 3: Creating DataFrame ---")
        if all_years_data:
            df = pd.DataFrame(all_years_data)
            print(f"DataFrame shape: {df.shape}")
            print(f"Years in DataFrame: {sorted(df['year'].tolist())}")
            print("\nDataFrame contents:")
            for _, row in df.iterrows():
                print(f"  {int(row['year'])}: Revenue = R$ {row['revenue']:,.2f}, Profit = R$ {row['net_profit']:,.2f}")
        else:
            print("❌ No data was processed into DataFrame!")
            return None
        
        return df
        
    except Exception as e:
        print(f"❌ Error in conversion: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_processor_directly():
    """Test the FinancialProcessor directly with loaded files"""
    print("\n=== Testing FinancialProcessor Directly ===")
    
    processor = FinancialProcessor()
    
    # Try to load the files directly like the processor would
    files = [
        'Análise de Resultado Financeiro 2018_2023.xlsx',
        'Resultado Financeiro - 2024.xlsx',
        'Resultado Financeiro - 2025.xlsx'
    ]
    
    # Check which files exist
    existing_files = []
    for file in files:
        if os.path.exists(file):
            existing_files.append(file)
            print(f"✅ Found file: {file}")
        else:
            print(f"❌ Missing file: {file}")
    
    if existing_files:
        try:
            # Load files
            excel_data = processor.load_excel_files(existing_files)
            print(f"Loaded {len(excel_data)} files")
            
            # Consolidate using the processor's method
            df, raw_data = processor.consolidate_all_years_flexible(excel_data)
            
            print(f"\nProcessor results:")
            print(f"DataFrame shape: {df.shape}")
            if not df.empty:
                print(f"Years in DataFrame: {sorted(df['year'].tolist())}")
                print(f"Raw data years: {sorted(raw_data.keys())}")
            else:
                print("❌ Processor returned empty DataFrame")
                
        except Exception as e:
            print(f"❌ Error in processor: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("Debugging conversion flow for missing 2024/2025 data...\n")
    
    # Test the conversion flow that happens in app.py
    df = debug_conversion_flow()
    
    # Also test the processor directly to compare
    test_processor_directly()
    
    print("\nDebug completed.")