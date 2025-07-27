import pandas as pd
from typing import Dict, Any, List
import re

class FixedCostExtractor:
    def __init__(self):
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
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
        extracted_costs = {
            'line_items': {},
            'categories': {}
        }
        annual_col = self._find_annual_column(df)
        month_cols = self._find_month_columns(df)

        for idx, row in df.iterrows():
            row_label = self._get_row_label(df, idx)
            if not row_label:
                continue

            category = self._classify_line_item(row_label)
            if category: # Only process fixed cost/expense categories
                item_key = self._normalize_key(row_label)
                annual_value = 0
                monthly_values = {}

                # Extract monthly values
                for i, month in enumerate(self.months):
                    col_idx = i * 2 + 1 # Assuming value column is at this index
                    if col_idx < len(df.columns):
                        value = self._parse_value(df.iloc[idx, col_idx])
                        if value is not None:
                            monthly_values[month] = value
                
                # Extract annual value
                if annual_col and annual_col in df.columns:
                    annual_value = self._parse_value(df.iloc[idx][annual_col])
                elif monthly_values:
                    annual_value = sum(monthly_values.values())

                if annual_value is not None and annual_value != 0:
                    is_subtotal_item = self._is_subtotal(row_label, annual_value) # Simplified check
                    extracted_costs['line_items'][item_key] = {
                        'label': row_label,
                        'category': category,
                        'monthly': monthly_values,
                        'annual': annual_value,
                        'is_subtotal': is_subtotal_item
                    }
                    if category not in extracted_costs['categories']:
                        extracted_costs['categories'][category] = []
                    extracted_costs['categories'][category].append(item_key)
        return extracted_costs

    def _find_annual_column(self, df: pd.DataFrame) -> Any:
        for col in df.columns:
            col_str = str(col).upper()
            if any(term in col_str for term in ['ANUAL', 'ANNUAL', 'TOTAL', 'ANO']):
                return col
        return None

    def _find_month_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        month_cols = {}
        for col_idx, col in enumerate(df.columns):
            col_str = str(col).upper().strip()
            for month in self.months:
                if month in col_str:
                    month_cols[month] = col
                    break
        return month_cols

    def _get_row_label(self, df: pd.DataFrame, row_idx: int) -> str:
        for col_idx in range(min(3, len(df.columns))):
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and isinstance(value, str) and len(value.strip()) > 0:
                return value.strip()
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

    def _classify_line_item(self, label: str) -> str:
        label_upper = label.upper()
        for category, patterns in self.fixed_cost_patterns.items():
            for pattern in patterns:
                if pattern in label_upper:
                    return category
        return None # Not a recognized fixed cost/expense

    def _normalize_key(self, label: str) -> str:
        key = re.sub(r'[^\w\s]', '', label)
        key = '_'.join(key.lower().split())
        return key

    def _is_subtotal(self, label: str, value: float) -> bool:
        label_upper = label.upper().strip()
        calculation_terms = [
            'TOTAL', 'SUBTOTAL', 'SOMA', 'PONTO EQUILIBRIO', 'PONTO EQUILÍBRIO',
            'COMPOSIÇÃO', 'SALDOS', 'DESPESAS - TOTAL', 'CUSTO FIXO + VARIAVEL',
            'CUSTOS FIXOS + VARIÁVEIS', 'CUSTOS VARIÁVEIS + FIXOS',
            'CUSTOS FIXOS + VARIÁVEIS + NÃO OPERACIONAIS',
            'TOTAL CUSTOS', 'CUSTO TOTAL', 'TOTAL GERAL',
            'DESPESA TOTAL', 'TOTAL DE CUSTOS', 'TOTAL DE DESPESAS',
            'DEMONSTRATIVO DE RESULTADO', 'DRE'
        ]
        if any(term in label_upper for term in calculation_terms):
            return True
        
        # Heuristic: if value is exactly 0 and it's not a known fixed cost line, it might be a subtotal
        if value == 0 and not any(pattern in label_upper for pattern in self.fixed_cost_patterns['fixed_costs']):
            return True

        return False
