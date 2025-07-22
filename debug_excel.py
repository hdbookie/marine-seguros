import pandas as pd
import os

# Check the 2018-2023 file structure
file_path = 'Análise de Resultado Financeiro 2018_2023.xlsx'

print(f"Examining file: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")
print(f"File size: {os.path.getsize(file_path)} bytes")
print("-" * 50)

# Read the Excel file to see all sheets
try:
    excel_file = pd.ExcelFile(file_path)
    print(f"Number of sheets: {len(excel_file.sheet_names)}")
    print(f"Sheet names: {excel_file.sheet_names}")
    print("-" * 50)
    
    # Examine each sheet
    for sheet_name in excel_file.sheet_names[:5]:  # First 5 sheets
        print(f"\nSheet: {sheet_name}")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"First few rows:")
        print(df.head())
        print("-" * 30)
        
except Exception as e:
    print(f"Error reading file: {e}")

# Also check the 2024 file for comparison
print("\n" + "="*50)
print("Checking 2024 file for comparison:")
file_2024 = 'Resultado Financeiro - 2024.xlsx'

try:
    excel_2024 = pd.ExcelFile(file_2024)
    print(f"Number of sheets: {len(excel_2024.sheet_names)}")
    print(f"Sheet names: {excel_2024.sheet_names}")
    
    # Check first sheet
    if excel_2024.sheet_names:
        df_2024 = pd.read_excel(file_2024, sheet_name=excel_2024.sheet_names[0])
        print(f"Shape: {df_2024.shape}")
        print(f"Columns: {df_2024.columns.tolist()}")
        print(f"First few rows:")
        print(df_2024.head())
        
except Exception as e:
    print(f"Error reading 2024 file: {e}")