import pandas as pd
from pathlib import Path

def debug_extraction():
    """Debug why extractor is getting wrong values"""
    
    file = Path("/Users/hunter/marine-seguros/Análise de Resultado Financeiro 2018_2023.xlsx")
    
    # Let's check year 2021 specifically since it has the worst extraction
    df = pd.read_excel(file, sheet_name='2021')
    
    print("=== DEBUGGING 2021 EXTRACTION ===\n")
    
    # Find annual column
    annual_col = None
    for col in df.columns:
        if 'anual' in str(col).lower():
            annual_col = col
            print(f"Annual column found: {annual_col}")
            break
    
    print("\nALL ROWS WITH 'CUSTOS' IN THE NAME:")
    print("-" * 60)
    
    # Find ALL rows with CUSTOS
    custos_rows = []
    for idx, row in df.iterrows():
        if pd.notna(row.iloc[0]):
            row_name = str(row.iloc[0]).upper()
            if 'CUSTOS' in row_name or 'CUSTO' in row_name:
                annual_val = row[annual_col] if annual_col else None
                custos_rows.append((idx, row.iloc[0], annual_val))
                print(f"Row {idx}: {row.iloc[0]}")
                print(f"  Annual value: {annual_val}")
                if pd.notna(annual_val) and isinstance(annual_val, (int, float)):
                    print(f"  Formatted: R$ {annual_val:,.2f}")
                print()
    
    print("\nEXTRACTOR LOGIC ISSUE:")
    print("-" * 60)
    print("The extractor is using 'CUSTOS' in value_str which matches ANY row with 'CUSTOS'")
    print("This includes:")
    print("- CUSTOS VARIÁVEIS (correct)")
    print("- CUSTOS FIXOS (wrong)")
    print("- CUSTOS NÃO OPERACIONAIS (wrong)")
    print("- RESULTADO C/CUSTOS NÃO OP. (wrong)")
    print("- etc.")
    
    print("\nThe extractor might be finding the LAST match instead of the first!")
    
    # Check what happens with profit rows
    print("\n\nALL ROWS WITH 'RESULTADO' IN THE NAME:")
    print("-" * 60)
    
    for idx, row in df.iterrows():
        if pd.notna(row.iloc[0]):
            row_name = str(row.iloc[0]).upper()
            if 'RESULTADO' in row_name:
                annual_val = row[annual_col] if annual_col else None
                print(f"Row {idx}: {row.iloc[0]}")
                print(f"  Annual value: {annual_val}")
                if pd.notna(annual_val) and isinstance(annual_val, (int, float)):
                    print(f"  Formatted: R$ {annual_val:,.2f}")
                print()

if __name__ == "__main__":
    debug_extraction()