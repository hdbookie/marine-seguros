import pandas as pd
import numpy as np
from typing import Dict, Any

class DirectDataExtractor:
    """Direct data extraction without AI for reliability"""
    
    def extract_from_excel(self, file_path: str) -> Dict[int, Dict]:
        """Extract financial data from Excel files"""
        extracted_data = {}
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            # First pass: collect all potential year sheets
            year_sheets = {}
            
            for sheet_name in excel_file.sheet_names:
                # Skip non-year sheets
                if any(skip in sheet_name.lower() for skip in ['comparativo', 'gráfico', 'projeç', 'dre']):
                    continue
                
                # Check if it's a year sheet
                year = None
                if sheet_name.isdigit() and 2000 <= int(sheet_name) <= 2030:
                    year = int(sheet_name)
                elif 'resultado' in sheet_name.lower() or 'previsão' in sheet_name.lower():
                    import re
                    year_match = re.search(r'20\d{2}', file_path)
                    if year_match:
                        year = int(year_match.group())
                
                if year:
                    if year not in year_sheets:
                        year_sheets[year] = []
                    year_sheets[year].append(sheet_name)
            
            # Second pass: process sheets with priority (Resultado > specific year > Previsão)
            for year, sheets in year_sheets.items():
                # Sort sheets by priority
                def sheet_priority(sheet_name):
                    sheet_lower = sheet_name.lower()
                    if 'resultado' in sheet_lower and 'previsão' not in sheet_lower:
                        return 0  # Highest priority
                    elif sheet_name.isdigit():
                        return 1  # Medium priority
                    elif 'previsão' in sheet_lower:
                        return 2  # Lowest priority
                    else:
                        return 3
                
                sorted_sheets = sorted(sheets, key=sheet_priority)
                
                # Try sheets in priority order
                for sheet_name in sorted_sheets:
                    print(f"Processing sheet: {sheet_name} for year {year}")
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # Extract data directly
                    financial_data = self._extract_sheet_data(df, year)
                    if financial_data and (financial_data.get('revenue') or financial_data.get('costs')):
                        extracted_data[year] = financial_data
                        print(f"✓ Extracted data for {year} from sheet '{sheet_name}'")
                        break  # Use the first successful extraction
                    else:
                        print(f"✗ No data found for {year} in sheet '{sheet_name}'")
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
        
        return extracted_data
    
    def _extract_sheet_data(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract financial data from a sheet"""
        data = {
            'revenue': {},
            'costs': {},
            'profits': {},
            'margins': {},
            'year': year
        }
        
        # Identify month columns
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        month_cols = {}
        
        for col_idx, col in enumerate(df.columns):
            col_str = str(col).upper().strip()
            for month in months:
                # Check if month appears in column name
                if month in col_str or col_str == month:
                    month_cols[month] = col
                    break
        
        print(f"Found month columns: {list(month_cols.keys())}")
        
        # Find annual column
        annual_col = None
        for col in df.columns:
            if 'ANUAL' in str(col).upper():
                annual_col = col
                break
        
        # Extract revenue and costs
        if len(df.columns) > 0:
            first_col = df.iloc[:, 0]
            
            for idx, value in enumerate(first_col):
                if pd.notna(value):
                    value_str = str(value).upper()
                    
                    # Revenue row - prioritize FATURAMENTO over other revenue types
                    if value_str == 'FATURAMENTO' or (value_str.startswith('FATURAMENTO') and len(value_str) < 20):
                        print(f"Found primary revenue row at {idx}: {value_str}")
                        # Extract monthly values
                        for month, col in month_cols.items():
                            if col in df.columns:
                                val = df.iloc[idx][col]
                                if pd.notna(val):
                                    # Handle different number formats
                                    if isinstance(val, (int, float)):
                                        data['revenue'][month] = float(val)
                                    elif isinstance(val, str):
                                        # Try to parse string numbers
                                        val_clean = val.replace('.', '').replace(',', '.').replace('R$', '').strip()
                                        try:
                                            data['revenue'][month] = float(val_clean)
                                        except:
                                            print(f"Could not parse value: {val}")
                        
                        # Extract annual value - store as PRIMARY revenue
                        if annual_col and annual_col in df.columns:
                            val = df.iloc[idx][annual_col]
                            if pd.notna(val):
                                if isinstance(val, (int, float)):
                                    data['revenue']['ANNUAL'] = float(val)
                                    data['revenue']['PRIMARY'] = float(val)  # Mark as primary
                                elif isinstance(val, str):
                                    val_clean = val.replace('.', '').replace(',', '.').replace('R$', '').strip()
                                    try:
                                        data['revenue']['ANNUAL'] = float(val_clean)
                                        data['revenue']['PRIMARY'] = float(val_clean)
                                    except:
                                        print(f"Could not parse annual value: {val}")
                    
                    # Other revenue sources (should not overwrite primary)
                    elif 'RECEITA' in value_str and 'PRIMARY' not in data.get('revenue', {}):
                        print(f"Found secondary revenue row at {idx}: {value_str}")
                        # Only update if we don't have primary revenue yet
                        if annual_col and annual_col in df.columns:
                            val = df.iloc[idx][annual_col]
                            if pd.notna(val) and isinstance(val, (int, float)):
                                if 'ANNUAL' not in data['revenue']:
                                    data['revenue']['ANNUAL'] = float(val)
                    
                    # Costs row - be specific to avoid false matches
                    elif value_str.startswith('CUSTOS VARIÁVEIS') or value_str.startswith('CUSTO VARIÁVEL') or value_str == 'CUSTOS VARIÁVEIS':
                        print(f"Found variable costs row at {idx}: {value_str}")
                        # Extract monthly values
                        for month, col in month_cols.items():
                            if col in df.columns:
                                val = df.iloc[idx][col]
                                if pd.notna(val):
                                    if isinstance(val, (int, float)):
                                        data['costs'][month] = float(val)
                                    elif isinstance(val, str):
                                        val_clean = val.replace('.', '').replace(',', '.').replace('R$', '').strip()
                                        try:
                                            data['costs'][month] = float(val_clean)
                                        except:
                                            print(f"Could not parse value: {val}")
                        
                        # Extract annual value
                        if annual_col and annual_col in df.columns:
                            val = df.iloc[idx][annual_col]
                            if pd.notna(val):
                                if isinstance(val, (int, float)):
                                    data['costs']['ANNUAL'] = float(val)
                                elif isinstance(val, str):
                                    val_clean = val.replace('.', '').replace(',', '.').replace('R$', '').strip()
                                    try:
                                        data['costs']['ANNUAL'] = float(val_clean)
                                    except:
                                        print(f"Could not parse annual value: {val}")
                    
                    # Extract profit margin (Margem de lucro) - BEFORE profit check
                    # Prioritize operational margin over net margin
                    elif 'MARGEM DE LUCRO' in value_str.upper() and 'PONTO' not in value_str.upper():
                        # Skip the net margin version if we already have operational margin
                        if 'LÍQUIDO' in value_str.upper() or 'LIQUIDO' in value_str.upper():
                            if 'ANNUAL' in data.get('margins', {}):
                                print(f"Skipping net margin at {idx} (already have operational): {value_str}")
                                continue
                        
                        print(f"Found profit margin at {idx}: {value_str}")
                        
                        # Extract monthly values first
                        for month, col in month_cols.items():
                            if col in df.columns:
                                val = df.iloc[idx][col]
                                if pd.notna(val):
                                    if isinstance(val, (int, float)):
                                        # Check if value is a decimal fraction (< 1) that needs converting to percentage
                                        # Most margin percentages are between 0 and 100%, so if value < 1, it's likely a fraction
                                        if -1 < float(val) < 1:
                                            # Convert decimal to percentage (0.2975 -> 29.75)
                                            data['margins'][month] = float(val) * 100
                                            print(f"  Stored margin for {month}: {float(val) * 100:.2f}% (converted from {val})")
                                        else:
                                            # Value is already a percentage
                                            data['margins'][month] = float(val)
                                            print(f"  Stored margin for {month}: {val}%")
                        
                        # Extract annual value
                        if annual_col and annual_col in df.columns:
                            val = df.iloc[idx][annual_col]
                            if pd.notna(val):
                                # Extract percentage value
                                if isinstance(val, str):
                                    val_clean = val.replace('%', '').replace(',', '.').strip()
                                    try:
                                        data['margins']['ANNUAL'] = float(val_clean)
                                        print(f"  Stored profit margin: {val_clean}%")
                                    except:
                                        pass
                                elif isinstance(val, (int, float)):
                                    # Check if value is a decimal fraction that needs converting to percentage
                                    if -1 < float(val) < 1:
                                        # Convert decimal to percentage (0.2975 -> 29.75)
                                        data['margins']['ANNUAL'] = float(val) * 100
                                        print(f"  Stored profit margin: {float(val) * 100:.2f}% (converted from {val})")
                                    else:
                                        # Value is already a percentage
                                        data['margins']['ANNUAL'] = float(val)
                                        print(f"  Stored profit margin: {val:.2f}%")
                    
                    # Profit/Result rows - look for specific profit indicators
                    elif any(profit_term in value_str for profit_term in ['RESULTADO', 'LUCRO']):
                        # Skip rows that are calculations or have additional qualifiers
                        skip_terms = ['MARGEM', 'PONTO', 'EQUILIBRIO', 'EXCLUINDO']
                        if not any(skip in value_str.upper() for skip in skip_terms):
                            print(f"Found profit row at {idx}: {value_str}")
                            
                            # Extract monthly values first for RESULTADO
                            if value_str.strip().upper() == 'RESULTADO':
                                for month, col in month_cols.items():
                                    if col in df.columns:
                                        val = df.iloc[idx][col]
                                        if pd.notna(val) and isinstance(val, (int, float)):
                                            data['profits'][month] = float(val)
                                            print(f"  Stored monthly profit for {month}: {val:,.2f}")
                            
                            # Extract annual value
                            if annual_col and annual_col in df.columns:
                                val = df.iloc[idx][annual_col]
                                if pd.notna(val) and isinstance(val, (int, float)):
                                    # Prioritize different types of profit/result
                                    if value_str.strip().upper() == 'LUCRO' or value_str.strip().upper() == 'LUCRO BRUTO':
                                        # Simple "LUCRO" or "LUCRO BRUTO" is gross profit
                                        data['profits']['GROSS'] = float(val)
                                        data['gross_profit'] = float(val)  # Also store as direct field
                                        print(f"  Stored gross profit: {val:,.2f}")
                                    elif 'INVESTIMENTOS' in value_str.upper() or 'RETIRADA' in value_str.upper():
                                        # This is the final net result after all adjustments
                                        # But be careful - if it has a minus sign, it's deducting these items
                                        if '-' in value_str:
                                            # This is after deducting investments/withdrawals
                                            data['profits']['NET_FINAL'] = float(val)
                                            print(f"  Stored final net profit (after deductions): {val:,.2f}")
                                        else:
                                            # This might be adding back investments/withdrawals
                                            data['profits']['NET_ADJUSTED'] = float(val)
                                            print(f"  Stored adjusted net profit: {val:,.2f}")
                                    elif 'C/CUSTOS NÃO OP' in value_str.upper() or 'C/CUSTOS N' in value_str.upper():
                                        # Result with non-operational costs (more complete)
                                        data['profits']['WITH_NON_OP'] = float(val)
                                        print(f"  Stored result with non-op costs: {val:,.2f}")
                                    elif 'S/CUSTOS NÃO OP' in value_str.upper() or 'S/CUSTOS N' in value_str.upper():
                                        # Result without non-operational costs
                                        data['profits']['WITHOUT_NON_OP'] = float(val)
                                        print(f"  Stored result without non-op costs: {val:,.2f}")
                                    elif value_str.strip().upper() == 'RESULTADO':
                                        # Plain "RESULTADO" is usually operational result
                                        data['profits']['OPERATIONAL'] = float(val)
                                        print(f"  Stored operational result: {val:,.2f}")
                                    else:
                                        # Other profit types
                                        data['profits']['OTHER'] = float(val)
                                        print(f"  Stored other profit type: {val:,.2f}")
                    
                    # Extract other important financial metrics
                    elif 'MARGEM DE CONTRIBUIÇÃO' in value_str:
                        print(f"Found contribution margin at {idx}: {value_str}")
                        if annual_col and annual_col in df.columns:
                            val = df.iloc[idx][annual_col]
                            if pd.notna(val) and isinstance(val, (int, float)):
                                data['contribution_margin'] = float(val)
                                print(f"  Stored contribution margin: {val:,.2f}")
                    
                    elif 'MARGEM BRUTA' in value_str and '%' in str(df.iloc[idx][annual_col] if annual_col else ''):
                        print(f"Found gross margin % at {idx}: {value_str}")
                        if annual_col and annual_col in df.columns:
                            val = df.iloc[idx][annual_col]
                            if pd.notna(val):
                                # Extract percentage value
                                if isinstance(val, str):
                                    val_clean = val.replace('%', '').replace(',', '.').strip()
                                    try:
                                        data['gross_margin'] = float(val_clean)
                                        print(f"  Stored gross margin: {val_clean}%")
                                    except:
                                        pass
                                elif isinstance(val, (int, float)):
                                    data['gross_margin'] = float(val)
                                    print(f"  Stored gross margin: {val}%")
                    
                    
                    elif value_str == 'CUSTOS FIXOS' or value_str.startswith('CUSTOS FIXOS'):
                        print(f"Found fixed costs (operational costs) at {idx}: {value_str}")
                        
                        # Initialize fixed_costs dict if not exists
                        if 'fixed_costs' not in data:
                            data['fixed_costs'] = {}
                        if 'operational_costs' not in data:
                            data['operational_costs'] = {}
                        
                        # Extract monthly values first
                        for month, col in month_cols.items():
                            if col in df.columns:
                                val = df.iloc[idx][col]
                                if pd.notna(val):
                                    # Handle different number formats
                                    if isinstance(val, (int, float)):
                                        data['fixed_costs'][month] = float(val)
                                        data['operational_costs'][month] = float(val)
                                    elif isinstance(val, str):
                                        # Try to parse string numbers
                                        val_clean = val.replace('.', '').replace(',', '.').replace('R$', '').strip()
                                        try:
                                            data['fixed_costs'][month] = float(val_clean)
                                            data['operational_costs'][month] = float(val_clean)
                                        except:
                                            print(f"Could not parse fixed cost value: {val}")
                        
                        # Extract annual value
                        if annual_col and annual_col in df.columns:
                            val = df.iloc[idx][annual_col]
                            if pd.notna(val) and isinstance(val, (int, float)):
                                data['fixed_costs']['ANNUAL'] = float(val)
                                data['operational_costs']['ANNUAL'] = float(val)
                                print(f"  Stored annual fixed costs: {val:,.2f}")
                                print(f"  Stored monthly fixed costs: {len([k for k in data['fixed_costs'].keys() if k != 'ANNUAL'])} months")
        
        # Calculate profits and only calculate margins if not already extracted from Excel
        if data['revenue'] and data['costs']:
            for month in data['revenue']:
                if month in data['costs']:
                    revenue = data['revenue'][month]
                    cost = data['costs'][month]
                    if revenue > 0:
                        data['profits'][month] = revenue - cost
                        # Only calculate margin if we don't have it from Excel already
                        if month not in data['margins']:
                            data['margins'][month] = ((revenue - cost) / revenue) * 100
        
        return data

# Test the extractor
if __name__ == "__main__":
    extractor = DirectDataExtractor()
    
    # Test with 2018-2023 file
    print("Testing 2018-2023 file:")
    data_2018_2023 = extractor.extract_from_excel('Análise de Resultado Financeiro 2018_2023.xlsx')
    print(f"Years extracted: {sorted(data_2018_2023.keys())}")
    
    for year, data in sorted(data_2018_2023.items()):
        revenue = data.get('revenue', {}).get('ANNUAL', 0)
        print(f"{year}: Revenue = R$ {revenue:,.2f}")