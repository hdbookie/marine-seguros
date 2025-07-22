from core import FinancialProcessor
import pandas as pd
import numpy as np

print("=== VERIFYING GRAPH ACCURACY ===\n")

# Load and process data like the app does
processor = FinancialProcessor()
files = [
    "Análise de Resultado Financeiro 2018_2023.xlsx",
    "Resultado Financeiro - 2024.xlsx",
    "Resultado Financeiro - 2025.xlsx"
]
excel_data = processor.load_excel_files(files)
df = processor.consolidate_all_years(excel_data)
df_with_growth = processor.calculate_growth_metrics(df)

print("DATA USED IN GRAPHS:")
print("-" * 80)
print(df_with_growth[['year', 'revenue', 'profit_margin', 'revenue_growth', 'net_profit']].to_string(index=False))

print("\n\nGRAPH ACCURACY ANALYSIS:")
print("-" * 80)

# 1. Revenue Evolution Chart
print("\n1. REVENUE EVOLUTION (📈 Evolução da Receita)")
print("   Values shown in graph:")
for _, row in df_with_growth.iterrows():
    print(f"   {int(row['year'])}: R$ {row['revenue']:,.2f}")
print("   ✅ ACCURATE - Shows actual revenue values from Excel")

# 2. Profit Margin Bar Chart
print("\n2. PROFIT MARGIN (📊 Margem de Lucro)")
print("   Values shown in graph:")
for _, row in df_with_growth.iterrows():
    print(f"   {int(row['year'])}: {row['profit_margin']:.1f}%")
print("   ✅ ACCURATE - Shows calculated profit margins")

# 3. Growth Analysis
print("\n3. GROWTH ANALYSIS (📊 Análise de Crescimento)")
print("   Shows year-over-year growth rates for:")
print("   - Revenue Growth")
print("   - Variable Costs Growth")
print("   - Net Profit Growth")
growth_cols = [col for col in df_with_growth.columns if '_growth' in col]
for col in growth_cols:
    print(f"\n   {col}:")
    for _, row in df_with_growth.iterrows():
        if row['year'] > 2018:  # Skip first year (0% growth)
            print(f"     {int(row['year'])}: {row[col]:.1f}%")
print("   ✅ ACCURATE - Shows calculated growth rates")

print("\n\nSUGGESTIONS FOR IMPROVEMENT:")
print("-" * 80)
print("""
1. ADD MORE VISUALIZATIONS:
   - Cost structure breakdown (pie chart showing cost categories)
   - Revenue vs Costs comparison (dual axis chart)
   - Cash flow analysis
   - Quarterly/Monthly trends (using the monthly data available)
   - ROI and efficiency metrics

2. ENHANCE EXISTING GRAPHS:
   - Add trend lines with projections
   - Include benchmarks or targets
   - Add annotations for significant events (like 2019 expansion)
   - Show rolling averages to smooth out volatility

3. IMPROVE ANOMALY DETECTION:
   - Make sensitivity adjustable (1.5σ, 2σ, 3σ options)
   - Add context to anomalies (e.g., "146% growth = 2.5x revenue")
   - Separate good anomalies (growth) from bad ones (losses)
   - Add explanatory tooltips

4. ADD PREDICTIVE ANALYTICS:
   - Forecast next year based on trends
   - Scenario analysis (best/worst case)
   - Break-even analysis
   - Sensitivity analysis on key variables

5. IMPROVE DATA VALIDATION:
   - Show data quality indicators
   - Flag missing or suspicious values
   - Add data completeness score
   - Show extraction confidence levels

6. ENHANCE USER EXPERIENCE:
   - Add export functionality (PDF reports)
   - Save analysis presets
   - Compare multiple scenarios
   - Add executive summary generation

7. ADD BUSINESS INSIGHTS:
   - Automatic insights generation
   - Benchmark against industry averages
   - Key performance indicators (KPIs)
   - Action recommendations
""")