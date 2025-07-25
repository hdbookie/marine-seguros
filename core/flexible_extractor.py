import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import re

class FlexibleFinancialExtractor:
    """Flexible extractor that automatically captures all financial line items"""
    
    def __init__(self):
        # Category patterns for automatic classification
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
        
        # Result line patterns (these are calculated, not raw data)
        self.result_patterns = ['RESULTADO', 'LUCRO', 'PREJUÍZO', 'MARGEM', 'TOTAL', 'SUBTOTAL']
        
    def extract_from_excel(self, file_path: str) -> Dict[int, Dict]:
        """Extract all financial data from Excel file"""
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
                print(f"Sheet shape: {df.shape}")
                financial_data = self._extract_all_financial_data(df, year)
                
                if financial_data['line_items']:
                    extracted_data[year] = financial_data
                    print(f"✓ Extracted {len(financial_data['line_items'])} line items for {year}")
                else:
                    print(f"✗ No line items found in sheet {sheet_name} for year {year}")
                    print(f"  Categories found: {list(financial_data['categories'].keys())}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()
            
        return extracted_data
    
    def _identify_year(self, sheet_name: str, file_path: str) -> int:
        """Identify the year from sheet name or file path"""
        # Check if sheet name is a year
        if sheet_name.isdigit() and 2000 <= int(sheet_name) <= 2030:
            return int(sheet_name)
            
        # Check for year in sheet name
        year_match = re.search(r'20\d{2}', sheet_name)
        if year_match:
            return int(year_match.group())
            
        # For multi-year files, the sheet should have the year
        # Don't try to extract year from file path for multi-year files
        if '_' in file_path and re.search(r'20\d{2}_20\d{2}', file_path):
            print(f"Multi-year file detected. Sheet '{sheet_name}' must contain year.")
            return None
            
        # Check for year in file path (for single year files)
        year_match = re.search(r'20\d{2}', file_path)
        if year_match:
            return int(year_match.group())
            
        return None
    
    def _extract_all_financial_data(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract all financial line items from a sheet"""
        data = {
            'year': year,
            'line_items': {},  # All financial line items
            'categories': {},  # Grouped by category
            'monthly_data': {},  # Monthly breakdown
            'hierarchy': []  # Preserve row order and indentation
        }
        
        # Find month columns
        month_cols = self._find_month_columns(df)
        annual_col = self._find_annual_column(df)
        
        print(f"Found {len(month_cols)} month columns and annual column: {annual_col is not None}")
        
        # Process each row
        rows_checked = 0
        rows_with_labels = 0
        rows_with_data = 0
        
        for idx in range(len(df)):
            rows_checked += 1
            row_label = self._get_row_label(df, idx)
            if not row_label:
                continue
            rows_with_labels += 1
                
            # Check if this row has numerical data
            row_data = self._extract_row_data(df, idx, month_cols, annual_col)
            if not row_data['has_data']:
                continue
            rows_with_data += 1
                
            # Classify the line item
            category = self._classify_line_item(row_label)
            item_key = self._normalize_key(row_label)
            
            # Store the data
            data['line_items'][item_key] = {
                'label': row_label,
                'category': category,
                'monthly': row_data['monthly'],
                'annual': row_data['annual'],
                'row_index': idx,
                'is_subtotal': self._is_subtotal(row_label)
            }
            
            # Group by category
            if category not in data['categories']:
                data['categories'][category] = []
            data['categories'][category].append(item_key)
            
            print(f"  [{category}] {row_label}: R$ {row_data['annual']:,.2f}")
            
        # Debug: Print category summary
        print(f"\nCategory summary for year {year}:")
        for cat, items in data['categories'].items():
            total = sum(data['line_items'][item]['annual'] for item in items)
            print(f"  {cat}: {len(items)} items, R$ {total:,.2f}")
            if cat in ['other_expenses', 'other_costs', 'other']:
                print(f"    Items: {[data['line_items'][item]['label'] for item in items[:3]]}...")  # Show first 3
            
        # Build hierarchy (preserves indentation/structure)
        data['hierarchy'] = self._build_hierarchy(df, data['line_items'])
        
        print(f"Row processing stats: {rows_checked} checked, {rows_with_labels} with labels, {rows_with_data} with data")
        
        return data
    
    def _find_month_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Find columns containing month data"""
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                  'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        month_cols = {}
        
        print(f"Looking for month columns in {len(df.columns)} columns")
        print(f"First 10 columns: {list(df.columns[:10])}")
        
        for col_idx, col in enumerate(df.columns):
            col_str = str(col).upper().strip()
            for month in months:
                if month in col_str:
                    month_cols[month] = col
                    print(f"  Found {month} in column '{col}'")
                    break
                    
        return month_cols
    
    def _find_annual_column(self, df: pd.DataFrame) -> Any:
        """Find column containing annual totals"""
        for col in df.columns:
            col_str = str(col).upper()
            if any(term in col_str for term in ['ANUAL', 'ANNUAL', 'TOTAL', 'ANO']):
                return col
        return None
    
    def _get_row_label(self, df: pd.DataFrame, row_idx: int) -> str:
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
                         month_cols: Dict, annual_col: Any) -> Dict:
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
        if annual_col and annual_col in df.columns:
            val = self._parse_value(df.iloc[row_idx][annual_col])
            if val is not None:
                row_data['annual'] = val
                row_data['has_data'] = True
        elif row_data['monthly']:
            # Calculate annual from monthly if not provided
            row_data['annual'] = sum(row_data['monthly'].values())
            
        return row_data
    
    def _parse_value(self, val: Any) -> float:
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
    
    def _classify_line_item(self, label: str) -> str:
        """Classify a line item into a category"""
        label_upper = label.upper()
        
        # Check each category pattern
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if pattern in label_upper:
                    return category
                    
        # Check if it's a calculated result
        for pattern in self.result_patterns:
            if pattern in label_upper:
                return 'calculated_results'
                
        # Default category for unclassified items
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
    
    def _is_subtotal(self, label: str) -> bool:
        """Check if a line item is a subtotal or total"""
        label_upper = label.upper()
        return any(term in label_upper for term in ['TOTAL', 'SUBTOTAL', 'SOMA'])
    
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
        
        # Get all unique line items across all years
        all_items = set()
        for year_data in all_data.values():
            all_items.update(year_data['line_items'].keys())
        
        # Create a row for each year
        for year in sorted(all_data.keys()):
            year_data = all_data[year]
            row = {'year': year}
            
            # Add each line item's annual value
            for item_key in all_items:
                if item_key in year_data['line_items']:
                    row[item_key] = year_data['line_items'][item_key]['annual']
                else:
                    row[item_key] = 0  # Item doesn't exist in this year
                    
            consolidated.append(row)
            
        return pd.DataFrame(consolidated)
    
    def get_category_summary(self, all_data: Dict) -> Dict:
        """Get summary by category across all years"""
        summary = {}
        
        for year, year_data in all_data.items():
            summary[year] = {}
            
            for category, items in year_data['categories'].items():
                total = sum(
                    year_data['line_items'][item]['annual'] 
                    for item in items
                )
                summary[year][category] = total
                
        return summary