import pandas as pd
import numpy as np
from pathlib import Path

def analyze_financial_data():
    """Analyze Excel files to verify reported anomalies"""
    
    # File paths
    base_path = Path("/Users/hunter/marine-seguros")
    file_2018_2023 = base_path / "Análise de Resultado Financeiro 2018_2023.xlsx"
    
    print("=== FINANCIAL DATA ANOMALY VERIFICATION ===\n")
    
    # Read specific sheets for years 2020, 2021, 2022
    years_to_analyze = ['2020', '2021', '2022']
    financial_data = {}
    
    for year in years_to_analyze:
        print(f"\n=== Analyzing Year {year} ===")
        try:
            df = pd.read_excel(file_2018_2023, sheet_name=year)
            
            # Look for annual totals column
            annual_col = None
            for col in df.columns:
                if 'anual' in str(col).lower():
                    annual_col = col
                    break
            
            if annual_col:
                print(f"Found annual column: {annual_col}")
                
                # Extract financial metrics
                for idx, row in df.iterrows():
                    if pd.notna(row.iloc[0]):
                        row_name = str(row.iloc[0]).strip().upper()
                        
                        # Revenue (FATURAMENTO)
                        if row_name == 'FATURAMENTO':
                            value = row[annual_col]
                            if pd.notna(value) and isinstance(value, (int, float)):
                                if year not in financial_data:
                                    financial_data[year] = {}
                                financial_data[year]['revenue'] = float(value)
                                print(f"  Revenue: {value:,.2f}")
                        
                        # Variable Costs (CUSTOS VARIÁVEIS)
                        elif row_name == 'CUSTOS VARIÁVEIS':
                            value = row[annual_col]
                            if pd.notna(value) and isinstance(value, (int, float)):
                                if year not in financial_data:
                                    financial_data[year] = {}
                                financial_data[year]['variable_costs'] = float(value)
                                print(f"  Variable Costs: {value:,.2f}")
                        
                        # Net Result/Profit (RESULTADO LIQUIDO or similar)
                        elif 'RESULTADO' in row_name and 'LIQUIDO' in row_name:
                            value = row[annual_col]
                            if pd.notna(value) and isinstance(value, (int, float)):
                                if year not in financial_data:
                                    financial_data[year] = {}
                                financial_data[year]['net_profit'] = float(value)
                                print(f"  Net Profit: {value:,.2f}")
                        
                        # Also check for "LUCRO LÍQUIDO"
                        elif 'LUCRO' in row_name and 'LÍQUIDO' in row_name:
                            value = row[annual_col]
                            if pd.notna(value) and isinstance(value, (int, float)):
                                if year not in financial_data:
                                    financial_data[year] = {}
                                financial_data[year]['net_profit'] = float(value)
                                print(f"  Net Profit (Lucro Líquido): {value:,.2f}")
                
        except Exception as e:
            print(f"Error reading sheet {year}: {e}")
    
    # Also check the Comparativo anual sheet for consolidated data
    print("\n=== Checking Comparativo anual sheet ===")
    try:
        df = pd.read_excel(file_2018_2023, sheet_name='Comparativo anual')
        
        # Look for years in rows and extract values
        for idx, row in df.iterrows():
            for col_idx, value in enumerate(row):
                if str(value) in ['2020', '2021', '2022']:
                    year = str(value)
                    print(f"\nFound year {year} in row {idx}")
                    
                    # Look for revenue in same row
                    if col_idx + 1 < len(row) and pd.notna(row.iloc[col_idx + 1]):
                        revenue = row.iloc[col_idx + 1]
                        if isinstance(revenue, (int, float)):
                            if year not in financial_data:
                                financial_data[year] = {}
                            financial_data[year]['revenue_comp'] = float(revenue)
                            print(f"  Revenue (from comparativo): {revenue:,.2f}")
                
                # Look for specific labels
                if pd.notna(value):
                    label = str(value).strip().upper()
                    if label == 'RECEITA':
                        # Check columns for year values
                        for col_idx2 in range(col_idx + 1, len(row)):
                            col_header = df.columns[col_idx2] if col_idx2 < len(df.columns) else None
                            if pd.notna(row.iloc[col_idx2]) and isinstance(row.iloc[col_idx2], (int, float)):
                                # Try to identify which year this column represents
                                print(f"  Found revenue value in column {col_idx2}: {row.iloc[col_idx2]:,.2f}")
                    
                    elif label == 'CUSTOS VARIÁVEIS':
                        # Check columns for year values
                        for col_idx2 in range(col_idx + 1, len(row)):
                            if pd.notna(row.iloc[col_idx2]) and isinstance(row.iloc[col_idx2], (int, float)):
                                print(f"  Found variable costs value in column {col_idx2}: {row.iloc[col_idx2]:,.2f}")
        
    except Exception as e:
        print(f"Error reading Comparativo anual: {e}")
    
    # Check Graficos anuais sheet which showed clear year data
    print("\n=== Checking Graficos anuais sheet ===")
    try:
        df = pd.read_excel(file_2018_2023, sheet_name='Graficos anuais')
        
        for idx, row in df.iterrows():
            if str(row.iloc[0]) in ['2020', '2021', '2022']:
                year = str(row.iloc[0])
                print(f"\nYear {year}:")
                
                # Revenue is typically in column 1
                if pd.notna(row.iloc[1]) and isinstance(row.iloc[1], (int, float)):
                    if year not in financial_data:
                        financial_data[year] = {}
                    financial_data[year]['revenue_graf'] = float(row.iloc[1])
                    print(f"  Revenue: {row.iloc[1]:,.2f}")
                
                # Look for other financial metrics in subsequent columns
                if len(row) > 5 and pd.notna(row.iloc[5]) and isinstance(row.iloc[5], (int, float)):
                    financial_data[year]['expenses_graf'] = float(row.iloc[5])
                    print(f"  Expenses: {row.iloc[5]:,.2f}")
                
                # Net profit might be column 4
                if len(row) > 4 and pd.notna(row.iloc[4]) and isinstance(row.iloc[4], (int, float)):
                    financial_data[year]['result_graf'] = float(row.iloc[4])
                    print(f"  Result: {row.iloc[4]:,.2f}")
    
    except Exception as e:
        print(f"Error reading Graficos anuais: {e}")
    
    print("\n=== CONSOLIDATED FINANCIAL DATA ===")
    print(financial_data)
    
    # Calculate growth rates
    print("\n=== GROWTH RATE VERIFICATION ===")
    
    # Use the most reliable source (from Graficos anuais which had clear data)
    revenue_2020 = financial_data.get('2020', {}).get('revenue_graf', financial_data.get('2020', {}).get('revenue'))
    revenue_2021 = financial_data.get('2021', {}).get('revenue_graf', financial_data.get('2021', {}).get('revenue'))
    
    costs_2021 = financial_data.get('2021', {}).get('variable_costs')
    costs_2022 = financial_data.get('2022', {}).get('variable_costs')
    
    profit_2020 = financial_data.get('2020', {}).get('result_graf', financial_data.get('2020', {}).get('net_profit'))
    profit_2021 = financial_data.get('2021', {}).get('result_graf', financial_data.get('2021', {}).get('net_profit'))
    
    # Revenue growth 2020 to 2021
    if revenue_2020 and revenue_2021:
        growth = ((revenue_2021 - revenue_2020) / abs(revenue_2020)) * 100
        print(f"\n1. Revenue Growth 2020→2021:")
        print(f"   2020 Revenue: R$ {revenue_2020:,.2f}")
        print(f"   2021 Revenue: R$ {revenue_2021:,.2f}")
        print(f"   Calculated Growth: {growth:,.2f}%")
        print(f"   Reported Anomaly: 13,970.12%")
        print(f"   Anomaly Verified: {'NO - Data shows normal growth' if abs(growth) < 1000 else 'POSSIBLY'}")
    
    # Variable costs growth 2021 to 2022
    if costs_2021 and costs_2022:
        growth = ((costs_2022 - costs_2021) / abs(costs_2021)) * 100
        print(f"\n2. Variable Costs Growth 2021→2022:")
        print(f"   2021 Variable Costs: R$ {costs_2021:,.2f}")
        print(f"   2022 Variable Costs: R$ {costs_2022:,.2f}")
        print(f"   Calculated Growth: {growth:,.2f}%")
        print(f"   Reported Anomaly: 37,683,176.91%")
        print(f"   Anomaly Verified: {'YES - Extreme growth detected!' if growth > 1000000 else 'NO'}")
    
    # Net profit growth 2020 to 2021
    if profit_2020 and profit_2021:
        growth = ((profit_2021 - profit_2020) / abs(profit_2020)) * 100
        print(f"\n3. Net Profit Growth 2020→2021:")
        print(f"   2020 Net Profit: R$ {profit_2020:,.2f}")
        print(f"   2021 Net Profit: R$ {profit_2021:,.2f}")
        print(f"   Calculated Growth: {growth:,.2f}%")
        print(f"   Reported Anomaly: -4,701.35%")
        print(f"   Anomaly Verified: {'YES - Extreme negative growth!' if growth < -1000 else 'NO'}")

if __name__ == "__main__":
    analyze_financial_data()