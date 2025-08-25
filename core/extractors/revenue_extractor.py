import pandas as pd
from typing import Dict, Any, List, Optional
import re

class RevenueExtractor:
    def __init__(self):
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        self.revenue_patterns = ['FATURAMENTO', 'RECEITA', 'VENDAS', 'REVENUE']
        self.revenue_subcategory_patterns = {
            'produtos': ['PRODUTO', 'MERCADORIA', 'VENDA DE PRODUTO'],
            'servicos': ['SERVIÇO', 'PRESTAÇÃO', 'CONSULTORIA'],
            'assinaturas': ['ASSINATURA', 'MENSALIDADE', 'RECORRENTE'],
            'outros': ['OUTRO', 'DIVERSO', 'ADICIONAL']
        }

    def extract_revenue(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract revenue with hierarchical structure similar to expenses"""
        revenue_data = {
            'annual': 0,
            'monthly': {},
            'line_items': {},
            'hierarchy': {
                'faturamento': {
                    'name': 'Faturamento',
                    'total': 0,
                    'subcategories': {},
                    'items': []
                }
            }
        }

        # Find all revenue-related rows
        revenue_rows = []
        revenue_section_start = -1
        revenue_section_end = -1
        
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]):
                row_text = str(row.iloc[0]).upper()
                # Check if this is the main revenue header
                if any(pattern in row_text for pattern in self.revenue_patterns):
                    revenue_section_start = idx
                    # Look for revenue items in subsequent rows
                    for next_idx in range(idx + 1, min(idx + 20, len(df))):
                        next_row = df.iloc[next_idx]
                        if pd.notna(next_row.iloc[0]):
                            next_text = str(next_row.iloc[0]).strip()
                            # Stop if we hit another major section
                            if any(term in next_text.upper() for term in ['CUSTO', 'DESPESA', 'TOTAL GERAL', 'IMPOSTOS']):
                                revenue_section_end = next_idx
                                break
                            # Check if it's a revenue line item (has values)
                            if self._has_values(next_row):
                                revenue_rows.append((next_idx, next_text))
                    break

        if revenue_section_start == -1:
            print(f"Warning: No revenue section found for year {year}")
            return revenue_data

        annual_col = self._find_annual_column(df)
        
        # Process each revenue line item
        for row_idx, row_label in revenue_rows:
            row = df.iloc[row_idx]
            
            # Extract values
            item_data = {
                'label': row_label,
                'category': 'revenue',
                'monthly': {},
                'annual': 0,
                'is_subtotal': False
            }
            
            # Extract monthly values
            for i, month in enumerate(self.months):
                col_idx = i * 2 + 1
                if col_idx < len(df.columns):
                    value = self._parse_value(row[col_idx])
                    if value is not None and value > 0:
                        item_data['monthly'][month] = value
            
            # Extract annual value
            if annual_col and annual_col in df.columns:
                annual_value = self._parse_value(row[annual_col])
                if annual_value is not None:
                    item_data['annual'] = annual_value
            elif item_data['monthly']:
                item_data['annual'] = sum(item_data['monthly'].values())
            
            # Add to hierarchy
            subcategory = self._classify_revenue_item(row_label)
            
            if subcategory not in revenue_data['hierarchy']['faturamento']['subcategories']:
                revenue_data['hierarchy']['faturamento']['subcategories'][subcategory] = {
                    'name': subcategory.replace('_', ' ').title(),
                    'total': 0,
                    'items': []
                }
            
            revenue_data['hierarchy']['faturamento']['subcategories'][subcategory]['items'].append(item_data)
            revenue_data['hierarchy']['faturamento']['subcategories'][subcategory]['total'] += item_data['annual']
            revenue_data['hierarchy']['faturamento']['total'] += item_data['annual']
            revenue_data['hierarchy']['faturamento']['items'].append(item_data)
            
            # Add to line items
            revenue_data['line_items'][self._normalize_key(row_label)] = item_data
            
            # Update totals
            revenue_data['annual'] += item_data['annual']
            for month, value in item_data['monthly'].items():
                revenue_data['monthly'][month] = revenue_data['monthly'].get(month, 0) + value

        # If no detailed items found, create a single item from the header row
        if not revenue_rows and revenue_section_start >= 0:
            row = df.iloc[revenue_section_start]
            row_label = str(row.iloc[0]).strip()
            
            item_data = {
                'label': row_label,
                'category': 'revenue',
                'monthly': {},
                'annual': 0,
                'is_subtotal': True
            }
            
            # Extract values from header row
            for i, month in enumerate(self.months):
                col_idx = i * 2 + 1
                if col_idx < len(df.columns):
                    value = self._parse_value(row[col_idx])
                    if value is not None and value > 0:
                        item_data['monthly'][month] = value
                        revenue_data['monthly'][month] = revenue_data['monthly'].get(month, 0) + value
            
            if annual_col and annual_col in df.columns:
                annual_value = self._parse_value(row[annual_col])
                if annual_value is not None:
                    item_data['annual'] = annual_value
                    revenue_data['annual'] = annual_value
            elif item_data['monthly']:
                item_data['annual'] = sum(item_data['monthly'].values())
                revenue_data['annual'] = item_data['annual']
            
            # Add as general revenue
            revenue_data['hierarchy']['faturamento']['subcategories']['geral'] = {
                'name': 'Receita Geral',
                'total': item_data['annual'],
                'items': [item_data]
            }
            revenue_data['hierarchy']['faturamento']['total'] = item_data['annual']
            revenue_data['hierarchy']['faturamento']['items'].append(item_data)
            revenue_data['line_items'][self._normalize_key(row_label)] = item_data

        return revenue_data
    
    def _classify_revenue_item(self, label: str) -> str:
        """Classify revenue item into subcategories"""
        label_upper = label.upper()
        
        for category, patterns in self.revenue_subcategory_patterns.items():
            for pattern in patterns:
                if pattern in label_upper:
                    return category
        
        return 'geral'  # Default category
    
    def _has_values(self, row: pd.Series) -> bool:
        """Check if a row has numeric values"""
        for i in range(1, len(row)):
            val = self._parse_value(row.iloc[i])
            if val is not None and val > 0:
                return True
        return False

    def _find_annual_column(self, df: pd.DataFrame) -> Any:
        for col in df.columns:
            col_str = str(col).upper()
            if any(term in col_str for term in ['ANUAL', 'ANNUAL', 'TOTAL', 'ANO']):
                return col
        return None

    def _parse_value(self, val: Any) -> float:
        if pd.isna(val):
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            val_clean = val.replace('R$', '').replace('$', '').strip()
            val_clean = val_clean.replace('.', '').replace(',', '.')
            val_clean = re.sub(r'[^\d.-]', '', val_clean)
            try:
                return float(val_clean)
            except:
                return None
        return None

    def _normalize_key(self, label: str) -> str:
        key = re.sub(r'[^\w\s]', '', label)
        key = '_'.join(key.lower().split())
        return key
