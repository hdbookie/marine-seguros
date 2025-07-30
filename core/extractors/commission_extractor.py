import pandas as pd
from typing import Dict, Any
import re

class CommissionExtractor:
    def __init__(self):
        self.patterns = ["REPASSE COMISSÃO"]
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

    def extract(self, df: pd.DataFrame) -> Dict:
        data = {"line_items": {}, "annual": 0, "monthly": {}}
        found_commission_row = False
        commission_row_idx = -1
        
        for idx, row in df.iterrows():
            label = self._get_row_label(df, idx)
            if not label:
                continue

            # Check if this is the main commission row
            if any(re.search(pattern, label, re.IGNORECASE) for pattern in self.patterns):
                found_commission_row = True
                commission_row_idx = idx
                row_data = self._extract_row_data(df, idx)
                item_key = self._normalize_key(label)
                
                # Create main commission entry with sub_items
                data["line_items"][item_key] = {
                    "label": label,
                    "annual": row_data["annual"],
                    "monthly": row_data["monthly"],
                    "sub_items": {}  # Will hold individual providers
                }
                data["annual"] += row_data["annual"]
                for month, value in row_data["monthly"].items():
                    data["monthly"][month] = data["monthly"].get(month, 0) + value
            
            # Check if this is a sub-item (starts with "- " or "- - " and follows commission row)
            elif found_commission_row and (label.strip().startswith("- ") or label.strip().startswith("- - ")):
                # This is a provider sub-item
                provider_name = label.replace("- - ", "").replace("- ", "").strip()
                row_data = self._extract_row_data(df, idx)
                
                # Add to the commission sub_items
                commission_key = self._normalize_key(list(self.patterns)[0])
                if commission_key in data["line_items"]:
                    provider_key = self._normalize_key(provider_name)
                    data["line_items"][commission_key]["sub_items"][provider_key] = {
                        "label": provider_name,
                        "annual": row_data["annual"],
                        "monthly": row_data["monthly"]
                    }
            # If we hit a non-sub-item row, stop looking for sub-items
            elif found_commission_row and not (label.strip().startswith("- ") or label.strip().startswith("- - ")):
                found_commission_row = False
                
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
    
    def _normalize_key(self, text: str) -> str:
        """Normalize text to create a consistent key"""
        return text.lower().strip().replace(' ', '_').replace('-', '_')

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