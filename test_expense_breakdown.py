#!/usr/bin/env python3
"""Test to see all expense categories and their percentages"""

import pandas as pd
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.financial_processor import FinancialProcessor

# Create processor
processor = FinancialProcessor()

# Get Excel files
excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~')]
print(f"Found {len(excel_files)} Excel files")

# Load data
excel_data = processor.load_excel_files(excel_files)
df, all_data = processor.consolidate_all_years(excel_data)

# Show breakdown for each year
for _, row in df.iterrows():
    year = row['year']
    revenue = row['revenue']
    
    print(f"\n{'='*60}")
    print(f"Year {year} - Revenue: R$ {revenue:,.2f}")
    print(f"{'='*60}")
    
    # Calculate all percentages
    categories = {
        'Custos Variáveis': row.get('variable_costs', 0),
        'Custos Fixos': row.get('fixed_costs', 0),
        'Custos Não Operacionais': row.get('non_operational_costs', 0),
        'Impostos': row.get('taxes', 0),
        'Comissões': row.get('commissions', 0),
        'Despesas Administrativas': row.get('admin_expenses', 0),
        'Marketing': row.get('marketing_expenses', 0),
        'Despesas Financeiras': row.get('financial_expenses', 0),
        'Lucro Líquido': row.get('net_profit', 0)
    }
    
    total_pct = 0
    for name, value in categories.items():
        pct = (value / revenue * 100) if revenue > 0 else 0
        total_pct += pct
        if value != 0:  # Only show non-zero categories
            print(f"{name:.<30} R$ {value:>15,.2f} ({pct:>6.2f}%)")
    
    print(f"{'Total %':.<30} {' ':>15} ({total_pct:>6.2f}%)")
    
    # Check if it adds to 100%
    if abs(total_pct - 100) > 0.1:
        print(f"\n⚠️  WARNING: Total is {total_pct:.2f}%, not 100%!")