import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import re


class UnifiedFinancialExtractor:
    """Unified extractor that combines the best of both DirectDataExtractor and FlexibleFinancialExtractor"""
    
    def __init__(self):
        # Core financial patterns for dashboard metrics
        self.core_patterns = {
            'revenue': ['FATURAMENTO', 'RECEITA', 'VENDAS', 'REVENUE'],
            'variable_costs': ['CUSTOS VARIÁVEIS', 'CUSTO VARIÁVEL', 'CMV', 'CUSTO DA MERCADORIA'],
            'fixed_costs': ['CUSTOS FIXOS', 'CUSTO FIXO'],
            'profits': ['RESULTADO', 'LUCRO', 'PREJUÍZO'],
            'margins': ['MARGEM DE LUCRO', 'MARGEM BRUTA']
        }
        
        # Extended category patterns for detailed analysis
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
        
        # Calculation/subtotal patterns to exclude from line items
        self.calculation_patterns = [
            'TOTAL', 'SUBTOTAL', 'SOMA', 'PONTO EQUILIBRIO', 'PONTO EQUILÍBRIO',
            'APLICAÇÕES', 'RETIRADA', 'COMPOSIÇÃO', 'SALDOS',
            'EXCLUINDO', 'DESPESAS - TOTAL', 'CUSTO FIXO + VARIAVEL',
            'CUSTOS FIXOS + VARIÁVEIS', 'CUSTOS VARIÁVEIS + FIXOS',
            'TOTAL CUSTOS', 'CUSTO TOTAL', 'TOTAL GERAL',
            'DESPESA TOTAL', 'TOTAL DE CUSTOS', 'TOTAL DE DESPESAS'
        ]
    
    def extract_from_excel(self, file_path: str, mode: str = 'unified') -> Dict[int, Dict]:
        """
        Extract financial data from Excel file
        
        Args:
            file_path: Path to Excel file
            mode: 'unified' (default), 'dashboard' (core metrics only), or 'detailed' (all line items)
        
        Returns:
            Dictionary with extracted data by year
        """
        extracted_data = {}
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                year = self._identify_year(sheet_name, file_path)
                if not year:
                    continue
                
                print(f"\n{'='*50}")
                print(f"Processing sheet: {sheet_name} (Year: {year})")
                print(f"{'='*50}")
                
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Extract data based on mode
                if mode == 'dashboard':
                    financial_data = self._extract_core_metrics(df, year)
                elif mode == 'detailed':
                    financial_data = self._extract_all_line_items(df, year)
                else:  # unified mode
                    financial_data = self._extract_unified_data(df, year)
                
                if financial_data:
                    extracted_data[year] = financial_data
                    print(f"✓ Extracted data for {year}")
                
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
            return int(year_match.group())
        
        # Skip non-year sheets
        skip_terms = ['comparativo', 'gráfico', 'projeç', 'dre', 'dashboard', 'resumo']
        if any(term in sheet_name.lower() for term in skip_terms):
            return None
        
        # Check file path for single-year files
        if '_' not in file_path or not re.search(r'20\d{2}_20\d{2}', file_path):
            year_match = re.search(r'20\d{2}', file_path)
            if year_match:
                return int(year_match.group())
        
        return None
    
    def _extract_unified_data(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract both core metrics and detailed line items"""
        data = {
            'year': year,
            # Core metrics for dashboard
            'revenue': {},
            'costs': {},  # Variable costs
            'fixed_costs': {},
            'operational_costs': {},  # Same as fixed_costs for compatibility
            'profits': {},
            'margins': {},
            # Additional metrics
            'contribution_margin': None,
            'gross_profit': None,
            'gross_margin': None,
            # Detailed line items for micro analysis
            'line_items': {},
            'categories': {},
            'monthly_data': {},
            'hierarchy': []
        }
        
        # Find columns
        month_cols = self._find_month_columns(df)
        annual_col = self._find_annual_column(df)
        
        print(f"Found {len(month_cols)} month columns and annual column: {annual_col is not None}")
        
        # Process each row
        for idx in range(len(df)):
            row_label = self._get_row_label(df, idx)
            if not row_label:
                continue
            
            # Extract row data
            row_data = self._extract_row_data(df, idx, month_cols, annual_col)
            if not row_data['has_data']:
                continue
            
            # Check if this is a calculation/subtotal
            if self._is_calculation_row(row_label):
                print(f"  Skipping calculation row: {row_label}")
                continue
            
            # Normalize label for matching
            label_upper = row_label.upper().strip()
            
            # Extract core metrics
            if label_upper == 'FATURAMENTO' or (label_upper.startswith('FATURAMENTO') and len(label_upper) < 20):
                print(f"Found primary revenue: {row_label}")
                data['revenue'] = row_data['monthly']
                data['revenue']['ANNUAL'] = row_data['annual']
                data['revenue']['PRIMARY'] = row_data['annual']  # Mark as primary
            
            elif label_upper.startswith('CUSTOS VARIÁVEIS') or label_upper == 'CUSTOS VARIÁVEIS':
                print(f"Found variable costs: {row_label}")
                data['costs'] = row_data['monthly']
                data['costs']['ANNUAL'] = row_data['annual']
            
            elif label_upper == 'CUSTOS FIXOS' or label_upper.startswith('CUSTOS FIXOS'):
                print(f"Found fixed costs: {row_label}")
                data['fixed_costs'] = row_data['monthly']
                data['fixed_costs']['ANNUAL'] = row_data['annual']
                # Mirror to operational_costs for compatibility
                data['operational_costs'] = data['fixed_costs'].copy()
            
            elif label_upper == 'RESULTADO':
                print(f"Found RESULTADO: {row_label} = {row_data['annual']:,.2f}")
                data['profits'] = row_data['monthly']
                data['profits']['ANNUAL'] = row_data['annual']
            
            elif 'MARGEM DE LUCRO' in label_upper and 'PONTO' not in label_upper:
                print(f"Found profit margin: {row_label}")
                # Convert to percentage if needed
                annual_margin = row_data['annual']
                if -1 < annual_margin < 1:
                    annual_margin *= 100
                data['margins']['ANNUAL'] = annual_margin
                # Process monthly margins
                for month, value in row_data['monthly'].items():
                    if -1 < value < 1:
                        data['margins'][month] = value * 100
                    else:
                        data['margins'][month] = value
            
            elif 'MARGEM DE CONTRIBUIÇÃO' in label_upper:
                print(f"Found contribution margin: {row_label}")
                data['contribution_margin'] = row_data['annual']
            
            # Always store as line item for detailed analysis
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
        
        # Calculate derived metrics if not found
        if data['revenue'] and data['costs'] and not data['profits']:
            print("Calculating profits from revenue - costs...")
            data['profits'] = {}
            for month in data['revenue']:
                if month in data['costs']:
                    data['profits'][month] = data['revenue'][month] - data['costs'][month]
        
        # Build hierarchy
        data['hierarchy'] = self._build_hierarchy(df, data['line_items'])
        
        return data
    
    def _extract_core_metrics(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract only core financial metrics for dashboard"""
        # This is a simplified version that only extracts main metrics
        data = self._extract_unified_data(df, year)
        
        # Keep only core metrics
        core_data = {
            'year': year,
            'revenue': data.get('revenue', {}),
            'costs': data.get('costs', {}),
            'fixed_costs': data.get('fixed_costs', {}),
            'operational_costs': data.get('operational_costs', {}),
            'profits': data.get('profits', {}),
            'margins': data.get('margins', {}),
            'contribution_margin': data.get('contribution_margin'),
            'gross_profit': data.get('gross_profit'),
            'gross_margin': data.get('gross_margin')
        }
        
        return core_data
    
    def _extract_all_line_items(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract all line items for detailed analysis"""
        # This uses the full extraction
        return self._extract_unified_data(df, year)
    
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
        """Find column containing annual totals"""
        for idx, col in enumerate(df.columns):
            col_str = str(col).upper()
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
    
    def consolidate_all_years(self, all_data: Dict) -> pd.DataFrame:
        """Consolidate data from all years into a summary DataFrame"""
        consolidated = []
        
        for year in sorted(all_data.keys()):
            year_data = all_data[year]
            row = {
                'year': year,
                'revenue': year_data.get('revenue', {}).get('ANNUAL', 0),
                'variable_costs': year_data.get('costs', {}).get('ANNUAL', 0),
                'fixed_costs': year_data.get('fixed_costs', {}).get('ANNUAL', 0),
                'net_profit': year_data.get('profits', {}).get('ANNUAL', 0),
                'profit_margin': year_data.get('margins', {}).get('ANNUAL', 0)
            }
            
            # Calculate operational costs (fixed + variable)
            row['operational_costs'] = row['variable_costs'] + row['fixed_costs']
            
            consolidated.append(row)
        
        return pd.DataFrame(consolidated)
    
    def get_category_summary(self, all_data: Dict) -> Dict:
        """Get summary by category across all years"""
        summary = {}
        
        for year, year_data in all_data.items():
            summary[year] = {}
            
            # Use line items for detailed categories
            if 'categories' in year_data:
                for category, items in year_data['categories'].items():
                    total = sum(
                        year_data['line_items'][item]['annual'] 
                        for item in items
                    )
                    summary[year][category] = total
            else:
                # Fall back to core metrics
                summary[year] = {
                    'revenue': year_data.get('revenue', {}).get('ANNUAL', 0),
                    'variable_costs': year_data.get('costs', {}).get('ANNUAL', 0),
                    'fixed_costs': year_data.get('fixed_costs', {}).get('ANNUAL', 0)
                }
        
        return summary