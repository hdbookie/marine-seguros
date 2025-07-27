import pandas as pd
from typing import Dict, Any, List
import re

class RevenueExtractor:
    def __init__(self):
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        self.revenue_patterns = ['FATURAMENTO', 'RECEITA', 'VENDAS', 'REVENUE']

    def extract_revenue(self, df: pd.DataFrame, year: int) -> Dict:
        revenue_data = {
            'annual': 0,
            'monthly': {},
            'line_items': {}
        }

        # Find revenue row
        revenue_row_idx = -1
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and any(pattern in str(row.iloc[0]).upper() for pattern in self.revenue_patterns):
                revenue_row_idx = idx
                break

        if revenue_row_idx == -1:
            print(f"Warning: No revenue row found for year {year}")
            return revenue_data

        row_label = str(df.iloc[revenue_row_idx, 0]).strip()
        annual_col = self._find_annual_column(df)

        # Extract monthly revenue data
        for i, month in enumerate(self.months):
            # Assuming monthly values are in columns next to each other, starting from col 1
            # This might need adjustment based on actual Excel structure
            col_idx = i * 2 + 1  # Example: Col 1 for JAN, Col 3 for FEV, etc.
            if col_idx < len(df.columns):
                value = self._parse_value(df.iloc[revenue_row_idx, col_idx])
                if value is not None:
                    revenue_data['monthly'][month] = value

        # Extract annual revenue
        if annual_col and annual_col in df.columns:
            annual_value = self._parse_value(df.iloc[revenue_row_idx][annual_col])
            if annual_value is not None:
                revenue_data['annual'] = annual_value
        elif revenue_data['monthly']:
            revenue_data['annual'] = sum(revenue_data['monthly'].values())

        revenue_data['line_items'][self._normalize_key(row_label)] = {
            'label': row_label,
            'category': 'revenue',
            'monthly': revenue_data['monthly'],
            'annual': revenue_data['annual'],
            'is_subtotal': False
        }

        return revenue_data

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
