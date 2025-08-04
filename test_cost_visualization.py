#!/usr/bin/env python3
"""
Test script to verify cost visualization shows correct totals
"""

import pandas as pd
from core.unified_extractor import UnifiedFinancialExtractor
from ui.tabs.micro_analysis.graphs.interactive_cost_breakdown import _categorize_expenses
from utils import format_currency

def test_cost_visualization():
    """Test that cost visualization shows correct totals"""
    
    # Extract data
    extractor = UnifiedFinancialExtractor()
    file_path = "/Users/hunter/marine-seguros/data/arquivos_enviados/Resultado Financeiro - 2025.xlsx"
    year_data = extractor.extract_from_excel(file_path)
    
    # Create a simple financial dataframe
    financial_df = pd.DataFrame([{'year': 2025}])
    
    # Test categorize expenses function
    categorized_data = _categorize_expenses(financial_df, year_data)
    
    if 2025 in categorized_data:
        year_categories = categorized_data[2025]['categories']
        
        print("=== COST VISUALIZATION TOTALS ===")
        total_viz = 0
        
        for cat_key, cat_data in year_categories.items():
            cat_total = cat_data['total']
            total_viz += cat_total
            print(f"- {cat_data['name']}: {format_currency(cat_total)}")
        
        print(f"\nTOTAL IN VISUALIZATION: {format_currency(total_viz)}")
        print("Expected: ~R$ 2.53M")
        
        if abs(total_viz - 2530000) < 100000:
            print("✅ SUCCESS: Total is close to expected R$ 2.53M")
        else:
            print("❌ ERROR: Total is still too high!")
    
    else:
        print("No data found for 2025")

if __name__ == "__main__":
    test_cost_visualization()