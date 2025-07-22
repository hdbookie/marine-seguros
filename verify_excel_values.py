import pandas as pd
from pathlib import Path

def check_actual_excel_values():
    """Directly read Excel sheets to verify actual values"""
    
    file = Path("/Users/hunter/marine-seguros/Análise de Resultado Financeiro 2018_2023.xlsx")
    
    print("=== DIRECT EXCEL VERIFICATION ===\n")
    
    # Check 2020, 2021, 2022 sheets
    for year in ['2020', '2021', '2022']:
        print(f"\n{'='*60}")
        print(f"YEAR {year}")
        print(f"{'='*60}")
        
        df = pd.read_excel(file, sheet_name=year)
        
        # Find the annual column
        annual_col = None
        for col in df.columns:
            if 'anual' in str(col).lower():
                annual_col = col
                break
        
        if annual_col:
            print(f"\nFound Annual column: {annual_col}")
            
            # Look for key rows
            for idx, row in df.iterrows():
                if pd.notna(row.iloc[0]):
                    row_name = str(row.iloc[0]).strip()
                    
                    # Check if this is a key metric
                    if any(keyword in row_name.upper() for keyword in ['FATURAMENTO', 'CUSTOS VARIÁVEIS', 'RESULTADO', 'LUCRO']):
                        annual_value = row[annual_col]
                        
                        # Print the row details
                        print(f"\nRow {idx}: {row_name}")
                        print(f"  Annual value: {annual_value}")
                        print(f"  Type: {type(annual_value)}")
                        
                        # If it's a number, show it formatted
                        if pd.notna(annual_value) and isinstance(annual_value, (int, float)):
                            print(f"  Formatted: R$ {annual_value:,.2f}")
                        
                        # Show some context (neighboring cells)
                        print(f"  First 5 cells: {[row.iloc[i] for i in range(min(5, len(row)))]}")
    
    # Also check the "Graficos anuais" sheet which our manual analysis used
    print(f"\n\n{'='*60}")
    print("GRAFICOS ANUAIS SHEET")
    print(f"{'='*60}")
    
    df_graf = pd.read_excel(file, sheet_name='Graficos anuais')
    print(f"\nShape: {df_graf.shape}")
    print("\nLooking for years 2020-2022:")
    
    for idx, row in df_graf.iterrows():
        if str(row.iloc[0]) in ['2020', '2021', '2022']:
            print(f"\nRow {idx} - Year {row.iloc[0]}:")
            print(f"  Full row: {row.tolist()}")
            
            # Specifically check columns where we found values before
            if len(row) > 1 and pd.notna(row.iloc[1]):
                print(f"  Column 1 (Revenue?): R$ {row.iloc[1]:,.2f}")
            if len(row) > 4 and pd.notna(row.iloc[4]):
                print(f"  Column 4 (Result?): R$ {row.iloc[4]:,.2f}")
            if len(row) > 5 and pd.notna(row.iloc[5]):
                print(f"  Column 5 (Expenses?): R$ {row.iloc[5]:,.2f}")

if __name__ == "__main__":
    check_actual_excel_values()