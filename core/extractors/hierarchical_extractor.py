"""
Hierarchical Financial Data Extractor
Extracts and organizes financial data with multi-level hierarchy support
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import re
from datetime import datetime
from utils.expense_hierarchy import ExpenseHierarchy


class HierarchicalExtractor:
    """
    Extractor that handles hierarchical expense structure with slash-separated categories
    """
    
    def __init__(self):
        self.hierarchy = ExpenseHierarchy()
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    def extract_from_excel(self, file_path: str) -> Dict[int, Dict]:
        """
        Extract hierarchical financial data from Excel file
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dictionary with years as keys and hierarchical data as values
        """
        result = {}
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                # Try to extract year from sheet name
                year = self._extract_year_from_sheet(sheet_name)
                if not year:
                    continue
                
                # Read the sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Extract hierarchical data
                year_data = self._extract_hierarchical_data(df, year)
                
                if year_data:
                    result[year] = year_data
        
        except Exception as e:
            print(f"Error extracting from {file_path}: {str(e)}")
        
        return result
    
    def _extract_year_from_sheet(self, sheet_name: str) -> Optional[int]:
        """Extract year from sheet name"""
        # Look for 4-digit year
        year_match = re.search(r'20\d{2}', sheet_name)
        if year_match:
            return int(year_match.group())
        
        # Try to parse as year directly
        try:
            year = int(sheet_name)
            if 2000 <= year <= 2100:
                return year
        except ValueError:
            pass
        
        return None
    
    def _extract_hierarchical_data(self, df: pd.DataFrame, year: int) -> Dict[str, Any]:
        """
        Extract hierarchical data from a DataFrame
        """
        data = {
            'year': year,
            'hierarchy': {
                'custos_fixos': {'total': 0, 'subcategories': {}, 'items': []},
                'custos_variaveis': {'total': 0, 'subcategories': {}, 'items': []},
                'despesas_operacionais': {'total': 0, 'subcategories': {}, 'items': []},
                'despesas_nao_operacionais': {'total': 0, 'subcategories': {}, 'items': []}
            },
            'monthly_data': {month: {} for month in self.months},
            'revenue': {'annual': 0, 'monthly': {}},
            'totals': {
                'total_costs': 0,
                'gross_profit': 0,
                'net_profit': 0
            },
            'all_items': []
        }
        
        # Find the column with expense descriptions
        desc_col = self._find_description_column(df)
        if desc_col is None:
            return None
        
        # Process each row
        for idx, row in df.iterrows():
            item_label = str(row[desc_col]).strip()
            
            # Skip empty or invalid rows
            if not item_label or item_label.lower() in ['nan', 'none', '']:
                continue
            
            # Check if this is a revenue item
            if self._is_revenue_item(item_label):
                revenue_data = self._extract_row_values(row, df.columns)
                data['revenue']['annual'] = revenue_data.get('annual', 0)
                data['revenue']['monthly'] = revenue_data.get('monthly', {})
                continue
            
            # Parse the expense item
            parsed = self.hierarchy.parse_expense_item(item_label)
            
            # Extract values
            values = self._extract_row_values(row, df.columns)
            
            # Skip if no values
            if values['annual'] == 0:
                continue
            
            # Create item record
            item = {
                'label': item_label,
                'parsed': parsed,
                'annual': values['annual'],
                'monthly': values['monthly'],
                'hierarchy_path': self.hierarchy.get_hierarchy_path(parsed)
            }
            
            # Add to all items
            data['all_items'].append(item)
            
            # Add to hierarchy structure
            main_cat = parsed['main_category']
            if main_cat in data['hierarchy']:
                # Update main category total
                data['hierarchy'][main_cat]['total'] += values['annual']
                data['hierarchy'][main_cat]['items'].append(item)
                
                # Update subcategory
                subcat = parsed['subcategory']
                if subcat not in data['hierarchy'][main_cat]['subcategories']:
                    data['hierarchy'][main_cat]['subcategories'][subcat] = {
                        'name': parsed['subcategory_name'],
                        'total': 0,
                        'detail_categories': {},
                        'items': []
                    }
                
                data['hierarchy'][main_cat]['subcategories'][subcat]['total'] += values['annual']
                data['hierarchy'][main_cat]['subcategories'][subcat]['items'].append(item)
                
                # Update detail category if present
                if parsed['detail_category']:
                    detail_cat = parsed['detail_category']
                    if detail_cat not in data['hierarchy'][main_cat]['subcategories'][subcat]['detail_categories']:
                        data['hierarchy'][main_cat]['subcategories'][subcat]['detail_categories'][detail_cat] = {
                            'name': detail_cat.title(),
                            'total': 0,
                            'items': []
                        }
                    
                    data['hierarchy'][main_cat]['subcategories'][subcat]['detail_categories'][detail_cat]['total'] += values['annual']
                    data['hierarchy'][main_cat]['subcategories'][subcat]['detail_categories'][detail_cat]['items'].append(item)
            
            # Update monthly data
            for month, value in values['monthly'].items():
                if month not in data['monthly_data']:
                    data['monthly_data'][month] = {}
                
                if main_cat not in data['monthly_data'][month]:
                    data['monthly_data'][month][main_cat] = 0
                
                data['monthly_data'][month][main_cat] += value
        
        # Calculate totals
        data['totals']['total_costs'] = sum(
            cat_data['total'] 
            for cat_data in data['hierarchy'].values()
        )
        
        if data['revenue']['annual'] > 0:
            data['totals']['gross_profit'] = data['revenue']['annual'] - data['hierarchy']['custos_variaveis']['total']
            data['totals']['net_profit'] = data['revenue']['annual'] - data['totals']['total_costs']
        
        # Add category names
        for main_cat_key, main_cat_data in data['hierarchy'].items():
            if main_cat_key in self.hierarchy.HIERARCHY:
                main_cat_data['name'] = self.hierarchy.HIERARCHY[main_cat_key]['name']
        
        return data
    
    def _find_description_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the column containing expense descriptions"""
        # Common patterns for description columns
        patterns = ['descrição', 'descricao', 'description', 'conta', 'account', 
                   'despesa', 'expense', 'item']
        
        for col in df.columns:
            col_lower = str(col).lower()
            # Check if column name matches patterns
            if any(pattern in col_lower for pattern in patterns):
                return col
            
            # Check if first column (often the description)
            if df.columns.get_loc(col) == 0:
                # Check if it contains text
                sample = df[col].dropna().head(10)
                if sample.dtype == object and any(isinstance(v, str) for v in sample):
                    return col
        
        return None
    
    def _is_revenue_item(self, label: str) -> bool:
        """Check if an item is revenue"""
        revenue_keywords = ['receita', 'faturamento', 'vendas', 'revenue', 
                           'income', 'prêmio', 'premio']
        label_lower = label.lower()
        return any(keyword in label_lower for keyword in revenue_keywords)
    
    def _extract_row_values(self, row: pd.Series, columns: pd.Index) -> Dict[str, Any]:
        """Extract monthly and annual values from a row"""
        result = {
            'annual': 0,
            'monthly': {}
        }
        
        # Look for monthly columns
        for month in self.months:
            for col in columns:
                col_str = str(col).upper()
                if month in col_str:
                    value = self._clean_value(row[col])
                    if value != 0:
                        result['monthly'][month] = value
                        break
        
        # Look for annual/total column
        annual_patterns = ['total', 'anual', 'annual', 'soma', 'sum', 'acumulado']
        for col in columns:
            col_lower = str(col).lower()
            if any(pattern in col_lower for pattern in annual_patterns):
                value = self._clean_value(row[col])
                if value != 0:
                    result['annual'] = value
                    break
        
        # If no annual found, sum monthly values
        if result['annual'] == 0 and result['monthly']:
            result['annual'] = sum(result['monthly'].values())
        
        return result
    
    def _clean_value(self, value: Any) -> float:
        """Clean and convert value to float"""
        if pd.isna(value):
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        # Handle string values
        if isinstance(value, str):
            # Remove currency symbols and spaces
            value = value.replace('R$', '').replace('$', '').replace(' ', '')
            value = value.replace('.', '').replace(',', '.')
            
            # Handle parentheses for negative values
            if '(' in value and ')' in value:
                value = value.replace('(', '-').replace(')', '')
            
            try:
                return float(value)
            except ValueError:
                return 0.0
        
        return 0.0
    
    def get_hierarchy_summary(self, data: Dict[int, Dict]) -> pd.DataFrame:
        """
        Create a summary DataFrame of the hierarchy
        
        Args:
            data: Extracted hierarchical data
            
        Returns:
            DataFrame with hierarchy summary
        """
        rows = []
        
        for year, year_data in data.items():
            if 'hierarchy' not in year_data:
                continue
            
            for main_cat_key, main_cat_data in year_data['hierarchy'].items():
                # Main category row
                rows.append({
                    'Ano': year,
                    'Nível': 1,
                    'Categoria Principal': main_cat_data.get('name', main_cat_key),
                    'Subcategoria': '',
                    'Detalhe': '',
                    'Valor': main_cat_data['total'],
                    'Itens': len(main_cat_data['items'])
                })
                
                # Subcategory rows
                for subcat_key, subcat_data in main_cat_data['subcategories'].items():
                    rows.append({
                        'Ano': year,
                        'Nível': 2,
                        'Categoria Principal': main_cat_data.get('name', main_cat_key),
                        'Subcategoria': subcat_data['name'],
                        'Detalhe': '',
                        'Valor': subcat_data['total'],
                        'Itens': len(subcat_data['items'])
                    })
                    
                    # Detail category rows
                    for detail_key, detail_data in subcat_data.get('detail_categories', {}).items():
                        rows.append({
                            'Ano': year,
                            'Nível': 3,
                            'Categoria Principal': main_cat_data.get('name', main_cat_key),
                            'Subcategoria': subcat_data['name'],
                            'Detalhe': detail_data['name'],
                            'Valor': detail_data['total'],
                            'Itens': len(detail_data['items'])
                        })
        
        return pd.DataFrame(rows)