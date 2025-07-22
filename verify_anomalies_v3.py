import pandas as pd
import numpy as np
from pathlib import Path

def analyze_financial_data():
    """Deep dive into financial data to find the source of anomalies"""
    
    # File paths
    base_path = Path("/Users/hunter/marine-seguros")
    file_2018_2023 = base_path / "Análise de Resultado Financeiro 2018_2023.xlsx"
    
    print("=== DETAILED FINANCIAL DATA ANALYSIS ===\n")
    
    # Let's examine the 2021 sheet more carefully for the net profit anomaly
    print("=== Examining 2021 Sheet in Detail ===")
    df_2021 = pd.read_excel(file_2018_2023, sheet_name='2021')
    
    # Look for all rows with potential profit/result information
    for idx, row in df_2021.iterrows():
        if pd.notna(row.iloc[0]):
            row_name = str(row.iloc[0]).strip()
            if any(keyword in row_name.upper() for keyword in ['LUCRO', 'RESULTADO', 'LÍQUIDO', 'LIQUIDO', 'MARGEM', 'PROFIT']):
                print(f"\nRow {idx}: {row_name}")
                # Find annual column
                for col_idx, col in enumerate(df_2021.columns):
                    if 'anual' in str(col).lower():
                        value = row.iloc[col_idx]
                        print(f"  Annual value: {value}")
                        if pd.notna(value):
                            print(f"  Type: {type(value)}, Value: {value}")
    
    # Let's also check for the specific anomaly values
    print("\n=== Searching for Anomaly Values ===")
    
    # Check if the 0.01 value we found is actually a percentage
    print("\nIn 2021 sheet, Net Profit shows as 0.01")
    print("This might be 0.01% or a formatting issue")
    
    # Let's calculate what the actual values would need to be for the anomalies
    print("\n=== Reverse Engineering Anomaly Values ===")
    
    # For 13,970.12% revenue growth (2020 to 2021)
    # If 2021 revenue = 2,036,810.95
    # Then 2020 revenue would need to be: 2,036,810.95 / (1 + 139.7012) = 14,497.51
    revenue_2021 = 2036810.95
    implied_revenue_2020 = revenue_2021 / (1 + 139.7012)
    print(f"\n1. For 13,970.12% revenue growth:")
    print(f"   2021 Revenue: R$ {revenue_2021:,.2f}")
    print(f"   Implied 2020 Revenue: R$ {implied_revenue_2020:,.2f}")
    print(f"   Actual 2020 Revenue found: R$ 1,131,510.61")
    print(f"   Actual growth: {((revenue_2021 - 1131510.61) / 1131510.61) * 100:.2f}%")
    
    # For 37,683,176.91% variable costs growth (2021 to 2022)
    # If 2022 costs = 486,710.12
    # Then 2021 costs would need to be: 486,710.12 / (1 + 376831.7691) = 1.29
    costs_2022 = 486710.12
    implied_costs_2021 = costs_2022 / (1 + 376831.7691)
    print(f"\n2. For 37,683,176.91% variable costs growth:")
    print(f"   2022 Variable Costs: R$ {costs_2022:,.2f}")
    print(f"   Implied 2021 Variable Costs: R$ {implied_costs_2021:,.2f}")
    print(f"   Actual 2021 Variable Costs found: R$ 261,932.20")
    print(f"   Actual growth: {((costs_2022 - 261932.20) / 261932.20) * 100:.2f}%")
    
    # For -4,701.35% net profit growth (2020 to 2021)
    # This would mean 2021 profit is -46.01 times the 2020 profit
    # If 2020 profit was positive, 2021 would need to be deeply negative
    
    # Let's check if there might be missing data or formatting issues
    print("\n=== Checking for Data Quality Issues ===")
    
    # Look for very small values that might cause extreme percentages
    for year in ['2020', '2021', '2022']:
        print(f"\n{year} Sheet Analysis:")
        df = pd.read_excel(file_2018_2023, sheet_name=year)
        
        # Find all numeric values less than 1
        small_values = []
        for idx, row in df.iterrows():
            for col_idx, value in enumerate(row):
                if pd.notna(value) and isinstance(value, (int, float)) and 0 < abs(value) < 1:
                    small_values.append((idx, col_idx, value, row.iloc[0] if pd.notna(row.iloc[0]) else 'Unknown'))
        
        if small_values:
            print(f"  Found {len(small_values)} values between 0 and 1:")
            for idx, col_idx, value, row_name in small_values[:5]:  # Show first 5
                print(f"    Row {idx} ({row_name}), Col {col_idx}: {value}")
    
    # Final summary
    print("\n=== ANOMALY VERIFICATION SUMMARY ===")
    print("\n1. Revenue Growth 2020→2021 (Reported: 13,970.12%):")
    print("   VERDICT: FALSE ANOMALY - Actual growth is ~80%")
    print("   Likely cause: Data entry error or calculation mistake")
    
    print("\n2. Variable Costs Growth 2021→2022 (Reported: 37,683,176.91%):")
    print("   VERDICT: FALSE ANOMALY - Actual growth is ~86%")
    print("   Likely cause: Extreme percentage suggests a near-zero base value was used")
    
    print("\n3. Net Profit Growth 2020→2021 (Reported: -4,701.35%):")
    print("   VERDICT: NEEDS INVESTIGATION")
    print("   The 0.01 value found for 2021 net profit seems incorrect")
    print("   This could be a percentage (0.01%) or data quality issue")

if __name__ == "__main__":
    analyze_financial_data()