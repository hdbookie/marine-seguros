"""
Verify the percentage calculation for semester view
"""

# The user showed:
# 2025-S1: Receita: R$ 1,676,472
# Variação: 10.77%

# This means the previous period (2024-S2) revenue should be:
current_revenue = 1676472
variation_percent = 10.77

# Calculate previous revenue
# If current = previous * (1 + variation/100)
# Then previous = current / (1 + variation/100)
previous_revenue = current_revenue / (1 + variation_percent/100)

print(f"Current Revenue (2025-S1): R$ {current_revenue:,.2f}")
print(f"Variation shown: {variation_percent}%")
print(f"Calculated Previous Revenue (2024-S2): R$ {previous_revenue:,.2f}")

# Verify the calculation
calculated_variation = ((current_revenue - previous_revenue) / previous_revenue) * 100
print(f"\nVerification:")
print(f"Calculated variation: {calculated_variation:.2f}%")
print(f"Expected variation: {variation_percent}%")
print(f"Match: {abs(calculated_variation - variation_percent) < 0.01}")

# Alternative calculation to double-check
print(f"\nAlternative calculation:")
print(f"Increase amount: R$ {current_revenue - previous_revenue:,.2f}")
print(f"Percentage: {(current_revenue - previous_revenue) / previous_revenue * 100:.2f}%")