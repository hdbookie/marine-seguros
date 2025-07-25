#!/usr/bin/env python3
"""Test script to verify profit calculation issues"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.direct_extractor import DirectDataExtractor
from core.financial_processor import FinancialProcessor
import pandas as pd

def test_profit_calculations():
    """Test the profit calculation logic"""
    
    print("=== Testing Profit Calculations ===\n")
    
    # Initialize components
    extractor = DirectDataExtractor()
    processor = FinancialProcessor()
    
    # Test file with known issues
    test_file = '/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2025.xlsx'
    
    if os.path.exists(test_file):
        print(f"1. Extracting data from: {os.path.basename(test_file)}")
        extracted_data = extractor.extract_from_excel(test_file)
        
        if extracted_data and 2025 in extracted_data:
            year_data = extracted_data[2025]
            
            print(f"\n2. Annual Data for 2025:")
            print(f"   Revenue: R$ {year_data.get('revenue', {}).get('ANNUAL', 0):,.2f}")
            print(f"   Variable Costs: R$ {year_data.get('costs', {}).get('ANNUAL', 0):,.2f}")
            
            # Check fixed/operational costs
            fixed_costs = year_data.get('fixed_costs', {})
            operational_costs = year_data.get('operational_costs', {})
            
            if isinstance(fixed_costs, dict):
                fixed_annual = fixed_costs.get('ANNUAL', 0)
            else:
                fixed_annual = fixed_costs
                
            if isinstance(operational_costs, dict):
                operational_annual = operational_costs.get('ANNUAL', 0)
            else:
                operational_annual = operational_costs
            
            print(f"   Fixed Costs: R$ {fixed_annual:,.2f}")
            print(f"   Operational Costs: R$ {operational_annual:,.2f}")
            print(f"   Are they the same? {fixed_annual == operational_annual}")
            
            # Check profit values
            profits = year_data.get('profits', {})
            print(f"\n3. Profit Values Extracted:")
            for profit_type, value in profits.items():
                print(f"   {profit_type}: R$ {value:,.2f}")
            
            # Calculate what profit should be
            revenue = year_data.get('revenue', {}).get('ANNUAL', 0)
            variable_costs = year_data.get('costs', {}).get('ANNUAL', 0)
            contribution_margin = revenue - variable_costs
            
            print(f"\n4. Manual Calculations:")
            print(f"   Contribution Margin = Revenue - Variable Costs")
            print(f"   Contribution Margin = {revenue:,.2f} - {variable_costs:,.2f} = {contribution_margin:,.2f}")
            print(f"   Expected from Excel: R$ {year_data.get('contribution_margin', 0):,.2f}")
            
            # Net profit calculation
            net_profit_calc = contribution_margin - fixed_annual
            print(f"\n   Net Profit = Contribution Margin - Fixed Costs")
            print(f"   Net Profit = {contribution_margin:,.2f} - {fixed_annual:,.2f} = {net_profit_calc:,.2f}")
            print(f"   Operational Result from Excel: R$ {profits.get('OPERATIONAL', 0):,.2f}")
            
            # Test monthly calculation
            print(f"\n5. Testing Monthly Calculation Issue:")
            
            # Get a sample month
            monthly_revenue = year_data.get('revenue', {})
            monthly_costs = year_data.get('costs', {})
            monthly_fixed = year_data.get('fixed_costs', {})
            
            if 'JAN' in monthly_revenue and 'JAN' in monthly_costs:
                jan_revenue = monthly_revenue['JAN']
                jan_variable = monthly_costs['JAN']
                jan_fixed = monthly_fixed.get('JAN', fixed_annual / 12)
                
                print(f"\n   January data:")
                print(f"   Revenue: R$ {jan_revenue:,.2f}")
                print(f"   Variable Costs: R$ {jan_variable:,.2f}")
                print(f"   Fixed Costs: R$ {jan_fixed:,.2f}")
                
                # Current (wrong) calculation in get_monthly_data
                jan_contribution = jan_revenue - jan_variable
                wrong_profit = jan_contribution - jan_fixed - jan_fixed  # Double subtraction!
                print(f"\n   WRONG calculation (current bug):")
                print(f"   Net Profit = {jan_contribution:,.2f} - {jan_fixed:,.2f} - {jan_fixed:,.2f} = {wrong_profit:,.2f}")
                
                # Correct calculation
                correct_profit = jan_contribution - jan_fixed
                print(f"\n   CORRECT calculation:")
                print(f"   Net Profit = {jan_contribution:,.2f} - {jan_fixed:,.2f} = {correct_profit:,.2f}")
                
            # Test the processor's monthly data
            print(f"\n6. Testing FinancialProcessor.get_monthly_data():")
            excel_data = {test_file: None}
            monthly_df = processor.get_monthly_data(excel_data)
            
            if not monthly_df.empty:
                # Get 2025 data
                df_2025 = monthly_df[monthly_df['year'] == 2025]
                
                if not df_2025.empty:
                    print(f"\n   Found {len(df_2025)} months of data for 2025")
                    
                    # Check totals
                    total_revenue = df_2025['revenue'].sum()
                    total_profit = df_2025['net_profit'].sum()
                    avg_margin = df_2025['profit_margin'].mean()
                    
                    print(f"\n   Monthly Totals:")
                    print(f"   Total Revenue: R$ {total_revenue:,.2f}")
                    print(f"   Total Profit: R$ {total_profit:,.2f}")
                    print(f"   Average Margin: {avg_margin:.2f}%")
                    
                    # Show first 3 months
                    print(f"\n   First 3 months detail:")
                    for _, row in df_2025.head(3).iterrows():
                        print(f"   {row['month']}: Revenue={row['revenue']:,.0f}, "
                              f"VarCosts={row['variable_costs']:,.0f}, "
                              f"FixedCosts={row['fixed_costs']:,.0f}, "
                              f"OpCosts={row['operational_costs']:,.0f}, "
                              f"Profit={row['net_profit']:,.0f}")

if __name__ == "__main__":
    test_profit_calculations()