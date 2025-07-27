#!/usr/bin/env python3
"""Test monthly data display to debug any issues"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.financial_processor import FinancialProcessor
import pandas as pd

def test_monthly_display():
    """Test monthly data extraction and display"""
    
    # Initialize processor
    processor = FinancialProcessor()
    
    # Test files
    excel_files = [
        '/Users/hunter/marine-seguros/data/arquivos_enviados/Análise de Resultado Financeiro 2018_2023.xlsx',
        '/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2024.xlsx',
        '/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2025.xlsx'
    ]
    
    # Load Excel files
    excel_data = {}
    for file in excel_files:
        if os.path.exists(file):
            excel_data[file] = file
    
    if not excel_data:
        print("❌ No Excel files found")
        return
    
    # Get monthly data
    print("\n" + "="*60)
    print("Testing Monthly Data Extraction")
    print("="*60)
    
    monthly_df = processor.get_monthly_data(excel_data)
    
    if monthly_df.empty:
        print("❌ No monthly data extracted")
        return
    
    print(f"\n✅ Monthly data extracted: {len(monthly_df)} records")
    print(f"Columns: {list(monthly_df.columns)}")
    print(f"Years: {sorted(monthly_df['year'].unique())}")
    
    # Show sample data for 2024
    print("\n" + "="*60)
    print("Sample Monthly Data for 2024")
    print("="*60)
    
    df_2024 = monthly_df[monthly_df['year'] == 2024]
    if not df_2024.empty:
        print(f"\nFound {len(df_2024)} months for 2024")
        
        # Display first few months
        for idx, row in df_2024.head(6).iterrows():
            print(f"\n{row['month']} 2024:")
            print(f"  Revenue: R$ {row['revenue']:,.2f}")
            print(f"  Variable Costs: R$ {row['variable_costs']:,.2f}")
            print(f"  Fixed Costs: R$ {row['fixed_costs']:,.2f}")
            print(f"  Contribution Margin: R$ {row['contribution_margin']:,.2f}")
            print(f"  Net Profit: R$ {row['net_profit']:,.2f}")
            print(f"  Profit Margin: {row['profit_margin']:.2f}%")
    
    # Test period column creation (as done in app.py)
    print("\n" + "="*60)
    print("Testing Period Column Creation")
    print("="*60)
    
    # Create period column as in prepare_x_axis
    month_abbr = {
        'JAN': 'Jan', 'FEV': 'Fev', 'MAR': 'Mar', 'ABR': 'Abr',
        'MAI': 'Mai', 'JUN': 'Jun', 'JUL': 'Jul', 'AGO': 'Ago',
        'SET': 'Set', 'OUT': 'Out', 'NOV': 'Nov', 'DEZ': 'Dez'
    }
    
    test_df = df_2024.copy()
    test_df['period'] = test_df.apply(lambda x: f"{month_abbr.get(x['month'], x['month'])}/{str(int(x['year']))[-2:]}", axis=1)
    
    print("\nPeriod column created:")
    print(test_df[['month', 'year', 'period', 'revenue']].head(6).to_string())
    
    # Check for any issues with monthly aggregation
    print("\n" + "="*60)
    print("Checking Monthly Totals vs Annual")
    print("="*60)
    
    for year in sorted(monthly_df['year'].unique())[-3:]:  # Last 3 years
        year_data = monthly_df[monthly_df['year'] == year]
        
        monthly_revenue_sum = year_data['revenue'].sum()
        monthly_costs_sum = year_data['variable_costs'].sum()
        
        print(f"\n{year}:")
        print(f"  Sum of monthly revenues: R$ {monthly_revenue_sum:,.2f}")
        print(f"  Sum of monthly costs: R$ {monthly_costs_sum:,.2f}")
        print(f"  Number of months: {len(year_data)}")
        
        # Show any months with zero or negative values
        zero_months = year_data[year_data['revenue'] <= 0]
        if not zero_months.empty:
            print(f"  ⚠️ Months with zero/negative revenue: {list(zero_months['month'])}")

if __name__ == "__main__":
    test_monthly_display()