import pandas as pd
import json

# Load the Excel files
files = [
    'Análise de Resultado Financeiro 2018_2023.xlsx',
    'Resultado Financeiro - 2024.xlsx',
    'Resultado Financeiro - 2025.xlsx'
]

for file in files:
    print(f"\n{'='*50}")
    print(f"File: {file}")
    print('='*50)
    
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file)
        print(f"Sheets: {excel_file.sheet_names}")
        
        # Examine each sheet
        for sheet_name in excel_file.sheet_names:
            print(f"\nSheet: '{sheet_name}'")
            df = pd.read_excel(file, sheet_name=sheet_name)
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("\nFirst 5 rows:")
            print(df.head())
            print("\nData types:")
            print(df.dtypes)
            
    except Exception as e:
        print(f"Error reading {file}: {e}")