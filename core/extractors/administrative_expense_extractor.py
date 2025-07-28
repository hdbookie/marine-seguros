import pandas as pd
from typing import Dict, Any
import re

class AdministrativeExpenseExtractor:
    def __init__(self):
        self.patterns = ["DESPESAS ADMINISTRATIVAS", "CONDOMINIOS", "ESCRITÓRIO CONTÁBIL", "ADVOGADOS", "ENERGIA ELÉTRICA"]
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

    def extract(self, df: pd.DataFrame) -> Dict:
        data = {"line_items": {}, "annual": 0, "monthly": {}}
        for idx, row in df.iterrows():
            label = self._get_row_label(df, idx)
            if not label:
                continue

            if any(re.search(pattern, label, re.IGNORECASE) for pattern in self.patterns):
                row_data = self._extract_row_data(df, idx)
                item_key = self._normalize_key(label)
                data["line_items"][item_key] = {
                    "label": label,
                    "annual": row_data["annual"],
                    "monthly": row_data["monthly"]
                }
                data["annual"] += row_data["annual"]
                for month, value in row_data["monthly"].items():
                    data["monthly"][month] = data["monthly"].get(month, 0) + value
        return data

    def _get_row_label(self, df: pd.DataFrame, row_idx: int) -> str:
        for col_idx in range(min(3, len(df.columns))):
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and isinstance(value, str) and len(value.strip()) > 0:
                return value.strip()
        return ""

    def _extract_row_data(self, df: pd.DataFrame, row_idx: int) -> Dict:
        monthly_values = {}
        annual_value = 0
        annual_col = self._find_annual_column(df)

        for i, month in enumerate(self.months):
            col_idx = i * 2 + 1
            if col_idx < len(df.columns):
                value = self._parse_value(df.iloc[row_idx, col_idx])
                if value is not None:
                    monthly_values[month] = value
        
        if annual_col and annual_col in df.columns:
            annual_value = self._parse_value(df.iloc[row_idx][annual_col]) or 0
        elif monthly_values:
            annual_value = sum(monthly_values.values())
            
        return {"annual": annual_value, "monthly": monthly_values}

    def _find_annual_column(self, df: pd.DataFrame) -> Any:
        for col in df.columns:
            if isinstance(col, str) and any(term in col.upper() for term in ['ANUAL', 'TOTAL']):
                return col
        return None

    def _parse_value(self, val: Any) -> float:
        if pd.isna(val) or not isinstance(val, (int, float, str)):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_clean = re.sub(r'[^\d,.-]', '', val.replace('R$', '')).strip()
        val_clean = val_clean.replace('.', '').replace(',', '.')
        try:
            return float(val_clean)
        except (ValueError, TypeError):
            return 0.0

    def _normalize_key(self, label: str) -> str:
        key = re.sub(r'[^\\w\\s]', '', label)
        return '_'.join(key.lower().split())