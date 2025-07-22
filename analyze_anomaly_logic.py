import pandas as pd
import numpy as np

# Recreate the actual data
data = pd.DataFrame([
    {'year': 2020, 'revenue_growth': 0, 'variable_costs_growth': 0, 'net_profit_growth': 0},
    {'year': 2021, 'revenue_growth': 80.01, 'variable_costs_growth': 95.38, 'net_profit_growth': -96.94},
    {'year': 2022, 'revenue_growth': 42.16, 'variable_costs_growth': 85.82, 'net_profit_growth': 1000.00},
])

print("=== ANOMALY DETECTION ANALYSIS ===\n")

for col in ['revenue_growth', 'variable_costs_growth', 'net_profit_growth']:
    print(f"\n{col}:")
    values = data[col]
    mean = values.mean()
    std = values.std()
    
    print(f"  Values: {values.tolist()}")
    print(f"  Mean: {mean:.2f}")
    print(f"  Std Dev: {std:.2f}")
    print(f"  Threshold (2 * std): {2 * std:.2f}")
    
    print("\n  Year-by-year analysis:")
    for idx, row in data.iterrows():
        value = row[col]
        deviation = abs(value - mean)
        is_anomaly = deviation > 2 * std
        print(f"    {row['year']}: Value={value:.2f}, Deviation={deviation:.2f}, Anomaly={is_anomaly}")

print("\n\nEXPLANATION:")
print("-" * 50)
print("1. The 1000% cap for net_profit_growth in 2022 is flagged because:")
print("   - 2022 profit jumped from R$11,833 to R$953,986 (8,060% actual growth)")
print("   - We capped it at 1000% to avoid showing 8,060%")
print("   - But 1000% is still statistically extreme compared to other years")
print("\n2. The variable_costs_growth is NOT actually 1000%, that was a mistake in the warning.")
print("   - 2022 variable costs growth is actually 85.82%")
print("\n3. These are WARNINGS, not errors. They indicate:")
print("   - 2021: Business had a profit crisis (legitimate anomaly)")
print("   - 2022: Business recovered strongly (also legitimate)")