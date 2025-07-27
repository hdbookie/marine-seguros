#!/usr/bin/env python3
"""Test to identify the specific issue with monthly data display"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from database_manager import DatabaseManager

def test_monthly_issue():
    """Test monthly data flow from database to display"""
    
    db = DatabaseManager()
    
    # Load data from database
    print("="*60)
    print("Loading data from database")
    print("="*60)
    
    loaded_data = db.load_all_financial_data()
    if not loaded_data:
        print("❌ No data in database")
        return
    
    print(f"✅ Loaded data for years: {sorted(loaded_data.keys())}")
    
    # Check 2024 data specifically
    if '2024' in loaded_data:
        data_2024 = loaded_data['2024']
        revenue_data = data_2024.get('revenue', {})
        
        print(f"\n2024 Revenue Data:")
        print(f"  Annual: R$ {revenue_data.get('ANNUAL', 0):,.2f}")
        print(f"  Monthly entries: {len([k for k in revenue_data.keys() if k not in ['ANNUAL', 'PRIMARY']])}")
        
        # Show first 3 months
        for month in ['JAN', 'FEV', 'MAR']:
            if month in revenue_data:
                print(f"  {month}: R$ {revenue_data[month]:,.2f}")
    
    # Simulate the monthly data generation as done in app.py
    print("\n" + "="*60)
    print("Simulating monthly data generation (as in app.py)")
    print("="*60)
    
    monthly_data = []
    for year, year_data in loaded_data.items():
        revenue_data = year_data.get('revenue', {})
        costs_data = year_data.get('costs', {})
        fixed_costs_data = year_data.get('fixed_costs', {})
        
        months_processed = 0
        for month in ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']:
            if month in revenue_data:
                revenue = revenue_data[month]
                variable_costs = costs_data.get(month, 0)
                
                # Get fixed costs - check if it's a dict with monthly data
                if isinstance(fixed_costs_data, dict) and month in fixed_costs_data:
                    fixed_costs = fixed_costs_data[month]
                elif isinstance(fixed_costs_data, dict) and 'ANNUAL' in fixed_costs_data:
                    # Fallback to distributed annual
                    fixed_costs = fixed_costs_data['ANNUAL'] / 12
                else:
                    fixed_costs = fixed_costs_data / 12 if fixed_costs_data else 0
                
                contribution_margin = revenue - variable_costs
                net_profit = contribution_margin - fixed_costs
                
                monthly_data.append({
                    'year': int(year),
                    'month': month,
                    'revenue': revenue,
                    'variable_costs': variable_costs,
                    'fixed_costs': fixed_costs,
                    'contribution_margin': contribution_margin,
                    'net_profit': net_profit,
                    'profit_margin': (net_profit / revenue * 100) if revenue > 0 else 0
                })
                months_processed += 1
        
        print(f"Year {year}: Processed {months_processed} months")
    
    if monthly_data:
        monthly_df = pd.DataFrame(monthly_data)
        print(f"\n✅ Generated monthly DataFrame with {len(monthly_df)} records")
        print(f"Columns: {list(monthly_df.columns)}")
        
        # Show sample for 2024
        df_2024 = monthly_df[monthly_df['year'] == 2024]
        if not df_2024.empty:
            print(f"\n2024 Monthly Sample (first 3 months):")
            print(df_2024.head(3)[['month', 'revenue', 'variable_costs', 'fixed_costs', 'net_profit']].to_string())
    
    # Check if the issue is with the session state
    print("\n" + "="*60)
    print("Checking potential session state issues")
    print("="*60)
    
    # Simulate what happens in the app
    print("\nIn the app, monthly_data would be stored in st.session_state.monthly_data")
    print("The app checks: hasattr(st.session_state, 'monthly_data') and st.session_state.monthly_data is not None")
    print("and not st.session_state.monthly_data.empty")
    
    if monthly_df is not None and not monthly_df.empty:
        print("✅ All checks would pass")
        print(f"   - DataFrame exists: True")
        print(f"   - DataFrame not None: True")
        print(f"   - DataFrame not empty: True")
        print(f"   - Has required columns: {all(col in monthly_df.columns for col in ['variable_costs', 'fixed_costs', 'net_profit', 'profit_margin'])}")
    
    return monthly_df

if __name__ == "__main__":
    monthly_df = test_monthly_issue()
    
    # Additional check for display
    if monthly_df is not None and not monthly_df.empty:
        print("\n" + "="*60)
        print("Testing prepare_x_axis logic")
        print("="*60)
        
        # Test with a sample of 2024 data
        test_df = monthly_df[monthly_df['year'] == 2024].copy()
        
        # Apply the period creation logic
        month_abbr = {
            'JAN': 'Jan', 'FEV': 'Fev', 'MAR': 'Mar', 'ABR': 'Abr',
            'MAI': 'Mai', 'JUN': 'Jun', 'JUL': 'Jul', 'AGO': 'Ago',
            'SET': 'Set', 'OUT': 'Out', 'NOV': 'Nov', 'DEZ': 'Dez'
        }
        
        if 'month' in test_df.columns:
            test_df['period'] = test_df.apply(lambda x: f"{month_abbr.get(x['month'], x['month'])}/{str(int(x['year']))[-2:]}", axis=1)
            print("✅ Period column created successfully")
            print(test_df[['month', 'year', 'period', 'revenue']].head(3).to_string())
        else:
            print("❌ Missing 'month' column")