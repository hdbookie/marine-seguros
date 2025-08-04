import pandas as pd
from typing import Dict
from .base_hierarchical_extractor import BaseHierarchicalExtractor


class FixedCostExtractor(BaseHierarchicalExtractor):
    def __init__(self):
        super().__init__()
        # Main category patterns
        self.fixed_cost_patterns = {
            'fixed_costs': ['CUSTOS FIXOS', 'CUSTO FIXO'],
            'admin_expenses': ['DESPESAS ADMINISTRATIVAS', 'DESPESA ADMINISTRATIVA', 'ADMIN'],
            'marketing_expenses': ['MARKETING', 'PUBLICIDADE', 'PROPAGANDA', 'MÍDIA'],
            'financial_expenses': ['DESPESAS FINANCEIRAS', 'JUROS', 'TAXAS BANCÁRIAS'],
            'tax_expenses': ['IMPOSTOS', 'TRIBUTOS', 'TAXAS', 'IRPJ', 'CSLL'],
            'other_expenses': ['OUTRAS DESPESAS', 'OUTRA DESPESA', 'DIVERSAS'],
            'other_costs': ['OUTROS CUSTOS', 'OUTRO CUSTO']
        }

    def extract_fixed_costs(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract fixed costs with hierarchical structure"""
        extracted_costs = {
            'annual': 0,
            'monthly': {},
            'line_items': {},
            'categories': {}
        }
        
        # Find the CUSTOS FIXOS row
        fixed_costs_row_idx = -1
        for idx, row in df.iterrows():
            row_label = self._get_row_label(df, idx)
            if row_label and any(pattern in row_label.upper() for pattern in ['CUSTOS FIXOS', 'CUSTO FIXO']):
                fixed_costs_row_idx = idx
                # Extract the total value from this row
                row_data = self._extract_row_data(df, idx)
                extracted_costs['annual'] = row_data['annual']
                extracted_costs['monthly'] = row_data['monthly']
                break
        
        if fixed_costs_row_idx == -1:
            return extracted_costs
        
        # Find the next section header to know where fixed costs end
        end_row_idx = len(df)
        section_headers = ['CUSTOS NÃO OPERACIONAIS', 'CUSTOS NAO OPERACIONAIS', 
                          'RESULTADO', 'MARGEM', 'LUCRO', 'PONTO EQUILIBRIO']
        
        for idx in range(fixed_costs_row_idx + 1, len(df)):
            row_label = self._get_row_label(df, idx)
            if row_label and any(header in row_label.upper() for header in section_headers):
                end_row_idx = idx
                break
        
        # Now extract all items between fixed_costs_row_idx and end_row_idx
        processed_rows = set()
        processed_rows.add(fixed_costs_row_idx)  # Skip the header row
        
        for idx in range(fixed_costs_row_idx + 1, end_row_idx):
            if idx in processed_rows:
                continue
                
            row_label = self._get_row_label(df, idx)
            if not row_label:
                continue
            
            # Skip if this is a sub-item (will be handled by parent)
            if row_label.strip().startswith("-"):
                continue
            
            # Check if this row has sub-items
            sub_items = self._extract_sub_items(df, idx, processed_rows)
            
            if sub_items:
                # This is a parent item with sub-items
                row_data = self._extract_row_data(df, idx)
                item_key = self._normalize_key(row_label)
                
                extracted_costs['line_items'][item_key] = {
                    'label': row_label,
                    'annual': row_data['annual'],
                    'monthly': row_data['monthly'],
                    'sub_items': sub_items
                }
                processed_rows.add(idx)
            else:
                # Regular item without sub-items
                row_data = self._extract_row_data(df, idx)
                if row_data['annual'] > 0 or any(v > 0 for v in row_data['monthly'].values()):
                    item_key = self._normalize_key(row_label)
                    
                    extracted_costs['line_items'][item_key] = {
                        'label': row_label,
                        'annual': row_data['annual'],
                        'monthly': row_data['monthly']
                    }
                    processed_rows.add(idx)
        
        return extracted_costs

    def _classify_line_item(self, label: str) -> str:
        """Classify a line item into a category"""
        label_upper = label.upper()
        for category, patterns in self.fixed_cost_patterns.items():
            for pattern in patterns:
                if pattern in label_upper:
                    return category
        return None

    def extract_administrative_expenses(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract administrative expenses"""
        return self._extract_by_category(df, 'admin_expenses')
    
    def extract_marketing_expenses(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract marketing expenses"""
        return self._extract_by_category(df, 'marketing_expenses')
    
    def extract_financial_expenses(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract financial expenses"""
        return self._extract_by_category(df, 'financial_expenses')
    
    def _extract_by_category(self, df: pd.DataFrame, category: str) -> Dict:
        """Extract expenses for a specific category"""
        extracted = {
            'annual': 0,
            'monthly': {},
            'line_items': {}
        }
        
        # This method is for backward compatibility
        # In the new structure, these are part of fixed costs
        return extracted