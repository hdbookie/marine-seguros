#!/usr/bin/env python3
"""Debug column structure"""

import pandas as pd

file_path = "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2024 - Atualizada.xlsx"
df = pd.read_excel(file_path, sheet_name='2024')

print("Column structure:")
for i, col in enumerate(df.columns):
    print(f"Column {i}: '{col}'")

print("\nLooking for 'Tecnologia e Comunicação' row:")
for idx, row in df.iterrows():
    if pd.notna(row.iloc[0]) and 'Tecnologia e Comunicação' in str(row.iloc[0]):
        print(f"\nFound at row {idx}:")
        print(f"Label (col 0): '{row.iloc[0]}'")
        
        # Check various columns for the annual total
        potential_cols = [13, 25, 26, 27, 28, 29, 30]  # Common positions for annual totals
        
        for col_idx in potential_cols:
            if col_idx < len(row):
                val = row.iloc[col_idx]
                print(f"Column {col_idx} ({df.columns[col_idx] if col_idx < len(df.columns) else 'Unknown'}): {val}")
        break

# Also check a few rows around it to see the pattern
print("\nContext around Tecnologia e Comunicação:")
for idx, row in df.iterrows():
    if pd.notna(row.iloc[0]) and 'Tecnologia e Comunicação' in str(row.iloc[0]):
        start_idx = max(0, idx - 2)
        end_idx = min(len(df), idx + 8)
        
        for i in range(start_idx, end_idx):
            label = df.iloc[i, 0] if pd.notna(df.iloc[i, 0]) else ""
            # Try to find the right annual column - look for a column with meaningful values
            for col in [25, 26, 27, 28, 29]:
                if col < df.shape[1]:
                    val = df.iloc[i, col]
                    if pd.notna(val) and val != 0:
                        print(f"Row {i}: '{label}' -> Column {col}: {val}")
                        break
        break