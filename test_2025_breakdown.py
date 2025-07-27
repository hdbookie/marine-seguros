#!/usr/bin/env python3
"""Test to see 2025 breakdown specifically"""

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

# Load data
excel_data = processor.load_excel_files(excel_files)
df, all_data = processor.consolidate_all_years(excel_data)

# Get 2025 data
row_2025 = df[df['year'] == 2025].iloc[0]

revenue = row_2025['revenue']
var_costs = row_2025.get('variable_costs', 0)
fixed_costs = row_2025.get('fixed_costs', 0)
non_op_costs = row_2025.get('non_operational_costs', 0)
profit = row_2025.get('net_profit', 0)

# Calculate percentages
var_pct = (var_costs / revenue * 100)
fixed_pct = (fixed_costs / revenue * 100)
non_op_pct = (non_op_costs / revenue * 100)
profit_pct = (profit / revenue * 100)

print(f"2025 Breakdown:")
print(f"Revenue: R$ {revenue:,.2f}")
print(f"\nCategories shown in chart:")
print(f"Custos Variáveis: R$ {var_costs:,.2f} ({var_pct:.2f}%)")
print(f"Custos Fixos: R$ {fixed_costs:,.2f} ({fixed_pct:.2f}%)")
print(f"Custos Não Operacionais: R$ {non_op_costs:,.2f} ({non_op_pct:.2f}%)")
print(f"Margem de Lucro: R$ {profit:,.2f} ({profit_pct:.2f}%)")
print(f"\nTotal of these 4 categories: {var_pct + fixed_pct + non_op_pct + profit_pct:.2f}%")

# Check what other costs exist
taxes = row_2025.get('taxes', 0)
commissions = row_2025.get('commissions', 0)
admin = row_2025.get('admin_expenses', 0)
marketing = row_2025.get('marketing_expenses', 0)
financial = row_2025.get('financial_expenses', 0)

print(f"\nOther costs NOT in fixed costs:")
print(f"Taxes: R$ {taxes:,.2f} ({taxes/revenue*100:.2f}%)")
print(f"Commissions: R$ {commissions:,.2f} ({commissions/revenue*100:.2f}%)")
print(f"Admin: R$ {admin:,.2f} ({admin/revenue*100:.2f}%)")
print(f"Marketing: R$ {marketing:,.2f} ({marketing/revenue*100:.2f}%)")
print(f"Financial: R$ {financial:,.2f} ({financial/revenue*100:.2f}%)")

other_total = taxes + commissions + admin + marketing + financial
print(f"\nTotal other costs: R$ {other_total:,.2f} ({other_total/revenue*100:.2f}%)")

# True breakdown
print(f"\n\nTrue cost structure that adds to 100%:")
true_total_costs = var_costs + fixed_costs + non_op_costs + other_total
print(f"All costs: R$ {true_total_costs:,.2f} ({true_total_costs/revenue*100:.2f}%)")
print(f"Profit: R$ {profit:,.2f} ({profit_pct:.2f}%)")
print(f"Total: {(true_total_costs + profit)/revenue*100:.2f}%")