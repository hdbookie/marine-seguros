import pandas as pd
from pathlib import Path

def debug_2020_revenue():
    """Debug why 2020 revenue is wrong"""
    
    file = Path("/Users/hunter/marine-seguros/Análise de Resultado Financeiro 2018_2023.xlsx")
    df = pd.read_excel(file, sheet_name='2020')
    
    print("=== DEBUGGING 2020 REVENUE EXTRACTION ===\n")
    
    # Find revenue rows
    print("ALL ROWS WITH 'FATURAMENTO' OR 'RECEITA':")
    print("-" * 60)
    
    for idx, row in df.iterrows():
        if pd.notna(row.iloc[0]):
            row_name = str(row.iloc[0]).upper()
            if 'FATURAMENTO' in row_name or 'RECEITA' in row_name:
                print(f"\nRow {idx}: {row.iloc[0]}")
                
                # Show all values in this row
                print("Values in row:")
                for col_idx, value in enumerate(row):
                    if pd.notna(value) and col_idx < 15:  # First 15 columns
                        col_name = df.columns[col_idx] if col_idx < len(df.columns) else f"Col_{col_idx}"
                        print(f"  {col_name}: {value}")
                
                # Find annual column
                for col_idx, col in enumerate(df.columns):
                    if 'anual' in str(col).lower():
                        annual_val = row.iloc[col_idx]
                        print(f"\nAnnual column ({col}): {annual_val}")
                        if isinstance(annual_val, (int, float)):
                            print(f"  Formatted: R$ {annual_val:,.2f}")
                        break
    
    # Check what the direct extractor might be getting
    print("\n\nDirect check of row 0 (FATURAMENTO):")
    faturamento_row = df.iloc[0]
    print(f"First value: {faturamento_row.iloc[0]}")
    print(f"Second value: {faturamento_row.iloc[1]}")
    print(f"Third value: {faturamento_row.iloc[2]}")
    
    # Find the annual column index
    annual_col_idx = None
    for idx, col in enumerate(df.columns):
        if 'anual' in str(col).lower():
            annual_col_idx = idx
            print(f"\nAnnual column is at index {idx}: {col}")
            print(f"Value at this position: {faturamento_row.iloc[idx]}")
            break

if __name__ == "__main__":
    debug_2020_revenue()