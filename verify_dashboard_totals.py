#!/usr/bin/env python3
"""Verify dashboard totals calculation"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.financial_processor import FinancialProcessor
import pandas as pd

def verify_totals():
    """Verify the dashboard totals calculation"""
    
    processor = FinancialProcessor()
    
    # Process all files
    excel_files = [
        "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2023.xlsx",
        "data/arquivos_enviados/Resultado Financeiro - 2024.xlsx", 
        "data/arquivos_enviados/Resultado Financeiro - 2025.xlsx"
    ]
    
    excel_data = {}
    for file_path in excel_files:
        if os.path.exists(file_path):
            excel_data[file_path] = None
    
    # Get consolidated data
    print("1. Processing Annual Data...")
    consolidated_df, all_data = processor.consolidate_all_years(excel_data)
    
    if not consolidated_df.empty:
        # Calculate totals
        total_revenue = consolidated_df['revenue'].sum()
        total_profit = consolidated_df['net_profit'].sum()
        avg_margin = consolidated_df['profit_margin'].mean()
        
        print(f"\nAnnual Summary (All Years):")
        print(f"Total Revenue: R$ {total_revenue:,.2f}")
        print(f"Total Profit: R$ {total_profit:,.2f}")
        print(f"Average Margin: {avg_margin:.2f}%")
        
        # Show year by year
        print(f"\nYear-by-Year Breakdown:")
        for _, row in consolidated_df.iterrows():
            print(f"{int(row['year'])}: Revenue={row['revenue']:,.0f}, "
                  f"Profit={row['net_profit']:,.0f}, "
                  f"Margin={row['profit_margin']:.1f}%")
    
    # Get monthly data
    print(f"\n2. Processing Monthly Data...")
    monthly_df = processor.get_monthly_data(excel_data)
    
    if not monthly_df.empty:
        # Calculate monthly totals
        total_monthly_revenue = monthly_df['revenue'].sum()
        total_monthly_profit = monthly_df['net_profit'].sum()
        avg_monthly_margin = monthly_df['profit_margin'].mean()
        
        print(f"\nMonthly Summary (All Months):")
        print(f"Total Revenue: R$ {total_monthly_revenue:,.2f}")
        print(f"Total Profit: R$ {total_monthly_profit:,.2f}")
        print(f"Average Margin: {avg_monthly_margin:.2f}%")
        
        # Verify consistency
        print(f"\nConsistency Check:")
        print(f"Annual vs Monthly Revenue Match: {abs(total_revenue - total_monthly_revenue) < 1}")
        print(f"Annual vs Monthly Profit Difference: R$ {abs(total_profit - total_monthly_profit):,.2f}")

if __name__ == "__main__":
    verify_totals()