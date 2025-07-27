import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import re


class UnifiedFinancialExtractor:
    """
    Unified extractor that combines DirectDataExtractor and FlexibleFinancialExtractor.
    Extracts both core financial metrics and detailed line items in a single pass.
    """
    
    def __init__(self):
        # Core financial line identifiers (for dashboard metrics)
        self.core_metrics = {
            'revenue': 'FATURAMENTO',
            'variable_costs': 'CUSTOS VARIÁVEIS',
            'fixed_costs': 'CUSTOS FIXOS',
            'resultado': 'RESULTADO',
            'profit_margin': 'MARGEM DE LUCRO',
            'contribution_margin': 'MARGEM DE CONTRIBUIÇÃO'
        }
        
        # Category patterns for line item classification
        self.category_patterns = {
            'revenue': ['FATURAMENTO', 'RECEITA', 'VENDAS', 'REVENUE'],
            'variable_costs': ['CUSTOS VARIÁVEIS', 'CUSTO VARIÁVEL', 'CMV', 'CUSTO DA MERCADORIA'],
            'fixed_costs': ['CUSTOS FIXOS', 'CUSTO FIXO'],
            'admin_expenses': ['DESPESAS ADMINISTRATIVAS', 'DESPESA ADMINISTRATIVA', 'ADMIN'],
            'operational_expenses': ['DESPESAS OPERACIONAIS', 'DESPESA OPERACIONAL', 'OPERACIONAL'],
            'marketing_expenses': ['MARKETING', 'PUBLICIDADE', 'PROPAGANDA', 'MÍDIA'],
            'financial_expenses': ['DESPESAS FINANCEIRAS', 'JUROS', 'TAXAS BANCÁRIAS'],
            'tax_expenses': ['IMPOSTOS', 'TRIBUTOS', 'TAXAS', 'IRPJ', 'CSLL'],
            'results': ['RESULTADO', 'LUCRO', 'PREJUÍZO', 'EBITDA', 'EBIT'],
            'margins': ['MARGEM', 'MARGIN', '%']
        }
        
        # Patterns to exclude from line items (calculations/subtotals)
        self.calculation_patterns = [
            'TOTAL', 'SUBTOTAL', 'SOMA', 'PONTO EQUILIBRIO', 'PONTO EQUILÍBRIO',
            'APLICAÇÕES', 'RETIRADA', 'COMPOSIÇÃO', 'SALDOS',
            'EXCLUINDO', 'DESPESAS - TOTAL', 'CUSTO FIXO + VARIAVEL',
            'CUSTOS FIXOS + VARIÁVEIS', 'CUSTOS VARIÁVEIS + FIXOS',
            'TOTAL CUSTOS', 'CUSTO TOTAL', 'TOTAL GERAL',
            'DESPESA TOTAL', 'TOTAL DE CUSTOS', 'TOTAL DE DESPESAS',
            'DEMONSTRATIVO DE RESULTADO', 'DRE'
        ]
    
    def extract_from_excel(self, file_path: str) -> Dict[int, Dict]:
        """
        Extract financial data from Excel file.
        Returns a unified data structure with both core metrics and line items.
        """
        extracted_data = {}
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            # First pass: collect all potential year sheets
            year_sheets = {}
            
            for sheet_name in excel_file.sheet_names:
                year = self._identify_year(sheet_name, file_path)
                if not year:
                    continue
                
                if year not in year_sheets:
                    year_sheets[year] = []
                year_sheets[year].append(sheet_name)
            
            # Second pass: process sheets with priority (Resultado > specific year > Previsão)
            for year, sheets in year_sheets.items():
                # Sort sheets by priority
                def sheet_priority(sheet_name):
                    sheet_lower = sheet_name.lower()
                    if 'resultado' in sheet_lower and 'previsão' not in sheet_lower:
                        return 0  # Highest priority - actual results
                    elif sheet_name.isdigit():
                        return 1  # Medium priority - year sheets
                    elif 'previsão' in sheet_lower:
                        return 2  # Lower priority - forecasts
                    else:
                        return 3  # Lowest priority
                
                sorted_sheets = sorted(sheets, key=sheet_priority)
                
                # Process sheets in priority order, use first successful extraction
                for sheet_name in sorted_sheets:
                    print(f"\n{'='*50}")
                    print(f"Processing sheet: {sheet_name} (Year: {year})")
                    print(f"{'='*50}")
                    
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    print(f"Sheet shape: {df.shape}")
                    
                    # Extract unified data
                    financial_data = self._extract_unified_data(df, year)
                    
                    if financial_data:
                        # Check if we have valid data before adding
                        has_core_data = (
                            ('revenue' in financial_data and financial_data['revenue']) or
                            ('costs' in financial_data and financial_data['costs'])
                        )
                        has_line_items = 'line_items' in financial_data and len(financial_data['line_items']) > 0
                        
                        if has_core_data or has_line_items:
                            extracted_data[year] = financial_data
                            print(f"✓ Extracted data for {year} from sheet '{sheet_name}'")
                            # Summary of what was extracted
                            if 'revenue' in financial_data and financial_data['revenue']:
                                print(f"  Revenue: R$ {financial_data['revenue'].get('ANNUAL', 0):,.2f}")
                            if 'profits' in financial_data and financial_data['profits']:
                                print(f"  Profit: R$ {financial_data['profits'].get('ANNUAL', 0):,.2f}")
                            if 'line_items' in financial_data:
                                print(f"  Line items: {len(financial_data['line_items'])}")
                            # Use first successful extraction only
                            break
                        else:
                            print(f"✗ No valid data found for {year} in sheet '{sheet_name}'")
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()
        
        return extracted_data
    
    def _identify_year(self, sheet_name: str, file_path: str) -> Optional[int]:
        """Identify the year from sheet name or file path"""
        # Check if sheet name is a year
        if sheet_name.isdigit() and 2000 <= int(sheet_name) <= 2030:
            return int(sheet_name)
        
        # Check for year in sheet name
        year_match = re.search(r'20\d{2}', sheet_name)
        if year_match:
            year = int(year_match.group())
            # Skip future years that likely don't have data
            if year > 2024:
                print(f"  Skipping future year sheet: {sheet_name}")
                return None
            return year
        
        # Skip non-financial sheets
        skip_terms = ['comparativo', 'gráfico', 'projeç', 'dre', 'dashboard', 'resumo', 'análise']
        if any(term in sheet_name.lower() for term in skip_terms):
            print(f"  Skipping non-financial sheet: {sheet_name}")
            return None
        
        # For single-year files, check file path
        if '_' not in file_path or not re.search(r'20\d{2}_20\d{2}', file_path):
            year_match = re.search(r'20\d{2}', file_path)
            if year_match:
                return int(year_match.group())
        
        return None
    
    def _extract_unified_data(self, df: pd.DataFrame, year: int) -> Dict:
        """
        Extract both core metrics and detailed line items in a single pass.
        This ensures consistency between dashboard and micro analysis data.
        """
        data = {
            'year': year,
            # Core metrics (DirectDataExtractor style)
            'revenue': {},
            'costs': {},  # Variable costs
            'fixed_costs': {},
            'operational_costs': {},  # Mirror of fixed_costs for compatibility
            'profits': {},
            'margins': {},
            'contribution_margin': None,
            'gross_profit': None,
            'gross_margin': None,
            # Detailed line items (FlexibleFinancialExtractor style)
            'line_items': {},
            'categories': {},
            'monthly_data': {},
            'hierarchy': []
        }
        
        # Find columns
        month_cols = self._find_month_columns(df)
        annual_col = self._find_annual_column(df)
        
        print(f"Found {len(month_cols)} month columns")
        if annual_col is not None:
            print(f"Found annual column at index {annual_col}: {df.columns[annual_col]}")
        
        # Track what we've extracted for core metrics
        core_extracted = set()
        
        # Process each row
        for idx in range(len(df)):
            row_label = self._get_row_label(df, idx)
            if not row_label:
                continue
            
            label_upper = row_label.upper().strip()
            
            # Extract row data
            row_data = self._extract_row_data(df, idx, month_cols, annual_col)
            if not row_data['has_data']:
                continue
            
            # Check if this is a calculation/subtotal (skip for line items)
            is_calculation = self._is_calculation_row(row_label)
            
            # Debug logging for 2024 specifically
            if year == 2024 and ('RESULTADO' in label_upper or 'LUCRO' in label_upper or 'MARGEM' in label_upper):
                print(f"  [2024 DEBUG] Row {idx}: {row_label} = R$ {row_data['annual']:,.2f} (is_calculation: {is_calculation})")
            
            # === CORE METRICS EXTRACTION (Direct style) ===
            # Extract FATURAMENTO as primary revenue
            if label_upper == 'FATURAMENTO' or (label_upper.startswith('FATURAMENTO') and len(label_upper) < 20):
                print(f"Found primary revenue: {row_label} = R$ {row_data['annual']:,.2f}")
                data['revenue'] = row_data['monthly'].copy()
                data['revenue']['ANNUAL'] = row_data['annual']
                data['revenue']['PRIMARY'] = row_data['annual']  # Mark as primary
                core_extracted.add('revenue')
            
            # Extract CUSTOS VARIÁVEIS
            elif (label_upper.startswith('CUSTOS VARIÁVEIS') or label_upper == 'CUSTOS VARIÁVEIS') and 'costs' not in core_extracted:
                print(f"Found variable costs: {row_label} = R$ {row_data['annual']:,.2f}")
                data['costs'] = row_data['monthly'].copy()
                data['costs']['ANNUAL'] = row_data['annual']
                core_extracted.add('costs')
            
            # Extract CUSTOS FIXOS
            elif (label_upper == 'CUSTOS FIXOS' or label_upper.startswith('CUSTOS FIXOS')) and 'fixed_costs' not in core_extracted:
                print(f"Found fixed costs: {row_label} = R$ {row_data['annual']:,.2f}")
                data['fixed_costs'] = row_data['monthly'].copy()
                data['fixed_costs']['ANNUAL'] = row_data['annual']
                # Mirror to operational_costs for compatibility
                data['operational_costs'] = data['fixed_costs'].copy()
                core_extracted.add('fixed_costs')
            
            # Extract RESULTADO (most important - preserve exact Excel value)
            elif label_upper == 'RESULTADO' and not is_calculation:
                print(f"Found RESULTADO: {row_label} = R$ {row_data['annual']:,.2f}")
                # Only store as profits if we haven't already found one (avoid overwriting)
                if 'profits' not in core_extracted:
                    data['profits'] = row_data['monthly'].copy()
                    data['profits']['ANNUAL'] = row_data['annual']
                    core_extracted.add('profits')
                    print(f"  Stored as primary profit value")
                else:
                    print(f"  Skipping - already have profit data")
            
            # Extract profit margin
            elif 'MARGEM DE LUCRO' in label_upper and 'PONTO' not in label_upper and 'margins' not in core_extracted:
                print(f"Found profit margin: {row_label}")
                # Convert to percentage if needed
                monthly_margins = {}
                for month, value in row_data['monthly'].items():
                    if -1 < value < 1:
                        monthly_margins[month] = value * 100
                    else:
                        monthly_margins[month] = value
                
                annual_margin = row_data['annual']
                if -1 < annual_margin < 1:
                    annual_margin *= 100
                
                data['margins'] = monthly_margins
                data['margins']['ANNUAL'] = annual_margin
                core_extracted.add('margins')
                print(f"  Stored profit margin: {annual_margin:.2f}%")
            
            # Extract contribution margin
            elif 'MARGEM DE CONTRIBUIÇÃO' in label_upper and not is_calculation:
                print(f"Found contribution margin: {row_label} = R$ {row_data['annual']:,.2f}")
                data['contribution_margin'] = row_data['annual']
                # Check if this value is being confused with profit for 2024
                if year == 2024 and abs(row_data['annual'] - 893047.13) < 1:
                    print(f"  WARNING: This contribution margin value matches the wrong profit shown for 2024!")
            
            # === LINE ITEMS EXTRACTION (Flexible style) ===
            # Always store as line item for detailed analysis (unless it's a calculation)
            if not is_calculation:
                category = self._classify_line_item(row_label)
                item_key = self._normalize_key(row_label)
                
                data['line_items'][item_key] = {
                    'label': row_label,
                    'category': category,
                    'monthly': row_data['monthly'],
                    'annual': row_data['annual'],
                    'row_index': idx,
                    'is_line_item': True
                }
                
                # Group by category
                if category not in data['categories']:
                    data['categories'][category] = []
                data['categories'][category].append(item_key)
                
                print(f"  [{category}] {row_label}: R$ {row_data['annual']:,.2f}")
        
        # Calculate derived metrics ONLY if not found in Excel
        if data['revenue'] and data['costs']:
            # Only calculate profits if we didn't find RESULTADO in Excel
            if 'profits' not in core_extracted:
                print("No RESULTADO found, calculating profits from revenue - costs")
                data['profits'] = {}
                for month in data['revenue']:
                    if month in data['costs']:
                        data['profits'][month] = data['revenue'][month] - data['costs'][month]
                
                # Annual profit
                annual_revenue = data['revenue'].get('ANNUAL', 0)
                annual_costs = data['costs'].get('ANNUAL', 0)
                if annual_revenue and annual_costs:
                    data['profits']['ANNUAL'] = annual_revenue - annual_costs
            
            # Only calculate margins if not found
            if 'margins' not in core_extracted and data['revenue'].get('ANNUAL', 0) > 0:
                print("No margin found, calculating from profits")
                data['margins'] = {}
                for month in data['revenue']:
                    if month in data['profits'] and data['revenue'][month] > 0:
                        data['margins'][month] = (data['profits'][month] / data['revenue'][month]) * 100
                
                if data['profits'].get('ANNUAL') and data['revenue'].get('ANNUAL'):
                    data['margins']['ANNUAL'] = (data['profits']['ANNUAL'] / data['revenue']['ANNUAL']) * 100
        
        # Build hierarchy
        data['hierarchy'] = self._build_hierarchy(df, data['line_items'])
        
        return data
    
    def _find_month_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Find columns containing month data"""
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                  'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        month_cols = {}
        
        for col_idx, col in enumerate(df.columns):
            col_str = str(col).upper().strip()
            for month in months:
                if month in col_str or col_str == month:
                    month_cols[month] = col
                    break
        
        return month_cols
    
    def _find_annual_column(self, df: pd.DataFrame) -> Optional[int]:
        """Find column containing annual totals (return index)"""
        for idx, col in enumerate(df.columns):
            col_str = str(col).upper()
            # Case-insensitive search for annual column
            if any(term in col_str for term in ['ANUAL', 'ANNUAL', 'TOTAL', 'ANO']):
                return idx
        return None
    
    def _get_row_label(self, df: pd.DataFrame, row_idx: int) -> Optional[str]:
        """Get the label from the first column of a row"""
        if row_idx >= len(df):
            return None
        
        # Try first few columns to find the label
        for col_idx in range(min(3, len(df.columns))):
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and isinstance(value, str) and len(value.strip()) > 0:
                return value.strip()
        
        return None
    
    def _extract_row_data(self, df: pd.DataFrame, row_idx: int, 
                         month_cols: Dict, annual_col: Optional[int]) -> Dict:
        """Extract numerical data from a row"""
        row_data = {
            'monthly': {},
            'annual': 0,
            'has_data': False
        }
        
        # Extract monthly values
        for month, col in month_cols.items():
            if col in df.columns:
                val = self._parse_value(df.iloc[row_idx][col])
                if val is not None and val != 0:
                    row_data['monthly'][month] = val
                    row_data['has_data'] = True
        
        # Extract annual value
        if annual_col is not None and annual_col < len(df.columns):
            val = self._parse_value(df.iloc[row_idx, annual_col])
            if val is not None:
                row_data['annual'] = val
                row_data['has_data'] = True
        elif row_data['monthly']:
            # Calculate annual from monthly if not provided
            row_data['annual'] = sum(row_data['monthly'].values())
        
        return row_data
    
    def _parse_value(self, val: Any) -> Optional[float]:
        """Parse a value to float, handling various formats"""
        if pd.isna(val):
            return None
        
        if isinstance(val, (int, float)):
            return float(val)
        
        if isinstance(val, str):
            # Remove currency symbols and spaces
            val_clean = val.replace('R$', '').replace('$', '').strip()
            # Handle Brazilian number format (1.234,56)
            val_clean = val_clean.replace('.', '').replace(',', '.')
            # Remove percentage sign if present
            val_clean = val_clean.replace('%', '')
            # Remove any remaining non-numeric characters except . and -
            val_clean = re.sub(r'[^\d.-]', '', val_clean)
            
            try:
                return float(val_clean)
            except:
                return None
        
        return None
    
    def _is_calculation_row(self, label: str) -> bool:
        """Check if a row is a calculation/subtotal"""
        label_upper = label.upper().strip()
        
        # Check against calculation patterns
        return any(pattern in label_upper for pattern in self.calculation_patterns)
    
    def _classify_line_item(self, label: str) -> str:
        """Classify a line item into a category"""
        label_upper = label.upper()
        
        # Check each category pattern
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if pattern in label_upper:
                    return category
        
        # Default categorization
        if any(term in label_upper for term in ['DESPESA', 'GASTO', 'EXPENSE']):
            return 'other_expenses'
        elif any(term in label_upper for term in ['CUSTO', 'COST']):
            return 'other_costs'
        else:
            return 'other'
    
    def _normalize_key(self, label: str) -> str:
        """Create a normalized key from a label"""
        # Remove special characters and normalize spaces
        key = re.sub(r'[^\w\s]', '', label)
        key = '_'.join(key.lower().split())
        return key
    
    def _build_hierarchy(self, df: pd.DataFrame, line_items: Dict) -> List[Dict]:
        """Build a hierarchical structure based on row positions"""
        hierarchy = []
        
        for item_key, item_data in line_items.items():
            hierarchy.append({
                'key': item_key,
                'label': item_data['label'],
                'category': item_data['category'],
                'row_index': item_data['row_index'],
                'level': 0  # Could be enhanced to detect indentation
            })
        
        # Sort by row index to preserve order
        hierarchy.sort(key=lambda x: x['row_index'])
        
        return hierarchy