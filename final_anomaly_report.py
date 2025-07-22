import pandas as pd
from pathlib import Path

def create_final_report():
    """Create final report on anomaly verification"""
    
    # File path
    base_path = Path("/Users/hunter/marine-seguros")
    file_2018_2023 = base_path / "Análise de Resultado Financeiro 2018_2023.xlsx"
    
    print("=== FINAL ANOMALY VERIFICATION REPORT ===")
    print("=" * 50)
    
    # Based on our analysis, here are the actual values found:
    financial_data = {
        '2020': {
            'revenue': 1131510.61,
            'variable_costs': 134063.82,
            'net_profit': 386444.56  # From Graficos anuais "Resultado"
        },
        '2021': {
            'revenue': 2036810.95,
            'variable_costs': 261932.20,
            'net_profit': 11833.43  # From "Resultado - Investimentos + Retirada"
        },
        '2022': {
            'revenue': 2895603.23,
            'variable_costs': 486710.12,
            'net_profit': 953986.61  # From Graficos anuais "Resultado"
        }
    }
    
    print("\nACTUAL FINANCIAL VALUES EXTRACTED:")
    print("-" * 50)
    for year in ['2020', '2021', '2022']:
        print(f"\n{year}:")
        print(f"  Revenue: R$ {financial_data[year]['revenue']:,.2f}")
        print(f"  Variable Costs: R$ {financial_data[year]['variable_costs']:,.2f}")
        print(f"  Net Profit: R$ {financial_data[year]['net_profit']:,.2f}")
    
    print("\n\nANOMALY VERIFICATION RESULTS:")
    print("-" * 50)
    
    # 1. Revenue Growth 2020→2021
    revenue_2020 = financial_data['2020']['revenue']
    revenue_2021 = financial_data['2021']['revenue']
    actual_revenue_growth = ((revenue_2021 - revenue_2020) / revenue_2020) * 100
    
    print("\n1. REVENUE GROWTH 2020→2021")
    print(f"   Reported Anomaly: 13,970.12%")
    print(f"   Actual Growth: {actual_revenue_growth:.2f}%")
    print(f"   Calculation: ({revenue_2021:,.2f} - {revenue_2020:,.2f}) / {revenue_2020:,.2f} * 100")
    print(f"   VERDICT: FALSE ANOMALY")
    print(f"   Explanation: The actual growth is 80%, not 13,970%. This appears to be a")
    print(f"                calculation error in the anomaly detection system.")
    
    # 2. Variable Costs Growth 2021→2022
    costs_2021 = financial_data['2021']['variable_costs']
    costs_2022 = financial_data['2022']['variable_costs']
    actual_costs_growth = ((costs_2022 - costs_2021) / costs_2021) * 100
    
    print("\n2. VARIABLE COSTS GROWTH 2021→2022")
    print(f"   Reported Anomaly: 37,683,176.91%")
    print(f"   Actual Growth: {actual_costs_growth:.2f}%")
    print(f"   Calculation: ({costs_2022:,.2f} - {costs_2021:,.2f}) / {costs_2021:,.2f} * 100")
    print(f"   VERDICT: FALSE ANOMALY")
    print(f"   Explanation: The actual growth is 86%, not 37 million percent. This extreme")
    print(f"                percentage suggests the anomaly detection used an incorrect base value.")
    
    # 3. Net Profit Growth 2020→2021
    profit_2020 = financial_data['2020']['net_profit']
    profit_2021 = financial_data['2021']['net_profit']
    actual_profit_growth = ((profit_2021 - profit_2020) / profit_2020) * 100
    
    print("\n3. NET PROFIT GROWTH 2020→2021")
    print(f"   Reported Anomaly: -4,701.35%")
    print(f"   Actual Growth: {actual_profit_growth:.2f}%")
    print(f"   Calculation: ({profit_2021:,.2f} - {profit_2020:,.2f}) / {profit_2020:,.2f} * 100")
    print(f"   VERDICT: PARTIALLY TRUE")
    print(f"   Explanation: Net profit did drop dramatically from R$ 386,444.56 to R$ 11,833.43,")
    print(f"                a decline of 96.94%. While not -4,701%, this is still a significant drop.")
    print(f"                The 2021 data shows 'Resultado - Investimentos + Retirada' suggesting")
    print(f"                heavy investments or withdrawals impacted the final net profit.")
    
    print("\n\nSUMMARY:")
    print("-" * 50)
    print("• Two of the three reported anomalies are FALSE (revenue and variable costs)")
    print("• The net profit anomaly is partially true - there was a dramatic decline")
    print("• The extreme percentages reported suggest calculation errors in the anomaly detection")
    print("• Actual growth rates are within normal business ranges (80-86% for revenue/costs)")
    print("• The 2021 net profit decline appears related to investments/withdrawals")
    
    print("\n\nRECOMMENDATIONS:")
    print("-" * 50)
    print("1. Review the anomaly detection calculation logic")
    print("2. Ensure proper handling of edge cases and small base values")
    print("3. Investigate the 2021 investments/withdrawals that impacted net profit")
    print("4. Consider using more robust statistical methods for anomaly detection")

if __name__ == "__main__":
    create_final_report()