import pandas as pd
import numpy as np
from pathlib import Path

def analyze_financial_data():
    """Analyze Excel files to verify reported anomalies"""
    
    # File paths
    base_path = Path("/Users/hunter/marine-seguros")
    file_2018_2023 = base_path / "Análise de Resultado Financeiro 2018_2023.xlsx"
    file_2024 = base_path / "Resultado Financeiro - 2024.xlsx"
    file_2025 = base_path / "Resultado Financeiro - 2025.xlsx"
    
    print("=== FINANCIAL DATA ANOMALY VERIFICATION ===\n")
    
    # Read the 2018-2023 file which should contain 2020, 2021, 2022 data
    print(f"Reading file: {file_2018_2023}")
    
    try:
        # Try to read all sheets first to understand structure
        xl_file = pd.ExcelFile(file_2018_2023)
        print(f"Available sheets: {xl_file.sheet_names}\n")
        
        # Initialize dictionaries to store values by year
        revenue_by_year = {}
        variable_costs_by_year = {}
        net_profit_by_year = {}
        
        # Read each sheet and extract data
        for sheet_name in xl_file.sheet_names:
            print(f"\nAnalyzing sheet: {sheet_name}")
            df = pd.read_excel(file_2018_2023, sheet_name=sheet_name)
            
            # Display first few rows to understand structure
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("\nFirst 10 rows:")
            print(df.head(10))
            
            # Look for revenue, costs, and profit data
            # Common patterns in Portuguese financial statements
            revenue_keywords = ['receita', 'faturamento', 'vendas', 'revenue']
            cost_keywords = ['custo', 'variável', 'variáveis', 'costs', 'despesa']
            profit_keywords = ['lucro', 'resultado', 'líquido', 'profit', 'margem']
            
            # Try to identify year columns (could be column headers or in rows)
            year_columns = []
            for col in df.columns:
                if str(col).isdigit() and 2018 <= int(str(col)) <= 2023:
                    year_columns.append(col)
            
            if year_columns:
                print(f"Found year columns: {year_columns}")
                
                # Search for financial metrics in rows
                for idx, row in df.iterrows():
                    row_str = str(row.iloc[0]).lower() if pd.notna(row.iloc[0]) else ""
                    
                    # Check for revenue
                    if any(keyword in row_str for keyword in revenue_keywords):
                        print(f"\nFound revenue row: {row.iloc[0]}")
                        for year_col in year_columns:
                            if str(year_col) in ['2020', '2021', '2022']:
                                value = row[year_col]
                                if pd.notna(value) and isinstance(value, (int, float)):
                                    revenue_by_year[str(year_col)] = float(value)
                                    print(f"  {year_col}: {value:,.2f}")
                    
                    # Check for variable costs
                    if any(keyword in row_str for keyword in cost_keywords) and 'variável' in row_str:
                        print(f"\nFound variable costs row: {row.iloc[0]}")
                        for year_col in year_columns:
                            if str(year_col) in ['2020', '2021', '2022']:
                                value = row[year_col]
                                if pd.notna(value) and isinstance(value, (int, float)):
                                    variable_costs_by_year[str(year_col)] = float(value)
                                    print(f"  {year_col}: {value:,.2f}")
                    
                    # Check for net profit
                    if any(keyword in row_str for keyword in profit_keywords) and ('líquido' in row_str or 'net' in row_str):
                        print(f"\nFound net profit row: {row.iloc[0]}")
                        for year_col in year_columns:
                            if str(year_col) in ['2020', '2021', '2022']:
                                value = row[year_col]
                                if pd.notna(value) and isinstance(value, (int, float)):
                                    net_profit_by_year[str(year_col)] = float(value)
                                    print(f"  {year_col}: {value:,.2f}")
            
            # Also check if years are in rows
            else:
                # Look for year indicators in the data
                for col_idx, col in enumerate(df.columns):
                    for idx, row in df.iterrows():
                        cell_value = str(row.iloc[col_idx]) if col_idx < len(row) else ""
                        if cell_value in ['2020', '2021', '2022']:
                            print(f"\nFound year {cell_value} in row {idx}, column {col}")
                            # Try to extract values from this row
                            for i, val in enumerate(row):
                                if pd.notna(val) and isinstance(val, (int, float)) and val != int(cell_value):
                                    print(f"  Column {i}: {val:,.2f}")
        
        print("\n=== EXTRACTED VALUES ===")
        print(f"Revenue by year: {revenue_by_year}")
        print(f"Variable costs by year: {variable_costs_by_year}")
        print(f"Net profit by year: {net_profit_by_year}")
        
        # Calculate growth rates if we have the data
        print("\n=== GROWTH RATE CALCULATIONS ===")
        
        # Revenue growth 2020 to 2021
        if '2020' in revenue_by_year and '2021' in revenue_by_year:
            revenue_2020 = revenue_by_year['2020']
            revenue_2021 = revenue_by_year['2021']
            revenue_growth = ((revenue_2021 - revenue_2020) / abs(revenue_2020)) * 100 if revenue_2020 != 0 else float('inf')
            print(f"\n2021 Revenue Growth:")
            print(f"  2020 Revenue: {revenue_2020:,.2f}")
            print(f"  2021 Revenue: {revenue_2021:,.2f}")
            print(f"  Growth Rate: {revenue_growth:,.2f}%")
            print(f"  Reported Anomaly: 13,970.12%")
            print(f"  Match: {'YES' if abs(revenue_growth - 13970.12) < 1 else 'NO'}")
        
        # Variable costs growth 2021 to 2022
        if '2021' in variable_costs_by_year and '2022' in variable_costs_by_year:
            costs_2021 = variable_costs_by_year['2021']
            costs_2022 = variable_costs_by_year['2022']
            costs_growth = ((costs_2022 - costs_2021) / abs(costs_2021)) * 100 if costs_2021 != 0 else float('inf')
            print(f"\n2022 Variable Costs Growth:")
            print(f"  2021 Variable Costs: {costs_2021:,.2f}")
            print(f"  2022 Variable Costs: {costs_2022:,.2f}")
            print(f"  Growth Rate: {costs_growth:,.2f}%")
            print(f"  Reported Anomaly: 37,683,176.91%")
            print(f"  Match: {'YES' if abs(costs_growth - 37683176.91) < 1 else 'NO'}")
        
        # Net profit growth 2020 to 2021
        if '2020' in net_profit_by_year and '2021' in net_profit_by_year:
            profit_2020 = net_profit_by_year['2020']
            profit_2021 = net_profit_by_year['2021']
            profit_growth = ((profit_2021 - profit_2020) / abs(profit_2020)) * 100 if profit_2020 != 0 else float('inf')
            print(f"\n2021 Net Profit Growth:")
            print(f"  2020 Net Profit: {profit_2020:,.2f}")
            print(f"  2021 Net Profit: {profit_2021:,.2f}")
            print(f"  Growth Rate: {profit_growth:,.2f}%")
            print(f"  Reported Anomaly: -4,701.35%")
            print(f"  Match: {'YES' if abs(profit_growth - (-4701.35)) < 1 else 'NO'}")
        
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_financial_data()