"""
Base Hierarchical Extractor
Provides common functionality for extracting parent-child relationships from Excel data
"""

import pandas as pd
from typing import Dict, List, Tuple, Any
import re


class BaseHierarchicalExtractor:
    """Base class for extractors that need to handle hierarchical data (parent with sub-items)"""
    
    def __init__(self):
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    def extract_hierarchical_items(self, df: pd.DataFrame, patterns: List[str] = None) -> Dict:
        """
        Extract hierarchical items from DataFrame
        
        Args:
            df: DataFrame to extract from
            patterns: Optional list of patterns to match parent items (if None, extracts all hierarchical items)
            
        Returns:
            Dictionary with line_items containing hierarchical structure
        """
        data = {"line_items": {}, "annual": 0, "monthly": {}}
        
        # Track which rows we've processed
        processed_rows = set()
        
        for idx, row in df.iterrows():
            if idx in processed_rows:
                continue
                
            label = self._get_row_label(df, idx)
            if not label:
                continue
            
            # Skip if this is a sub-item (starts with dash)
            if label.strip().startswith("-"):
                continue
            
            # Check if this matches our patterns (if provided)
            if patterns and not any(re.search(pattern, label, re.IGNORECASE) for pattern in patterns):
                continue
            
            # Look ahead to see if this has sub-items
            sub_items = self._extract_sub_items(df, idx, processed_rows)
            
            if sub_items:
                # This is a parent item with sub-items
                row_data = self._extract_row_data(df, idx)
                item_key = self._normalize_key(label)
                
                data["line_items"][item_key] = {
                    "label": label,
                    "annual": row_data["annual"],
                    "monthly": row_data["monthly"],
                    "sub_items": sub_items
                }
                
                # Add to totals
                data["annual"] += row_data["annual"]
                for month, value in row_data["monthly"].items():
                    data["monthly"][month] = data["monthly"].get(month, 0) + value
                
                # Mark this row as processed
                processed_rows.add(idx)
            
            elif not patterns:
                # No sub-items and no specific patterns - include as regular item
                row_data = self._extract_row_data(df, idx)
                if row_data["annual"] > 0:  # Only include items with values
                    item_key = self._normalize_key(label)
                    
                    data["line_items"][item_key] = {
                        "label": label,
                        "annual": row_data["annual"],
                        "monthly": row_data["monthly"]
                    }
                    
                    # Add to totals
                    data["annual"] += row_data["annual"]
                    for month, value in row_data["monthly"].items():
                        data["monthly"][month] = data["monthly"].get(month, 0) + value
                    
                    processed_rows.add(idx)
        
        return data
    
    def _extract_sub_items(self, df: pd.DataFrame, parent_idx: int, processed_rows: set) -> Dict:
        """Extract sub-items that belong to a parent item"""
        sub_items = {}
        
        # Look at rows after the parent
        for sub_idx in range(parent_idx + 1, len(df)):
            sub_label = self._get_row_label(df, sub_idx)
            
            if not sub_label:
                continue
            
            # Check if this is a sub-item (starts with dash)
            if sub_label.strip().startswith("-"):
                # Extract the sub-item name (remove leading dashes and spaces)
                sub_name = sub_label.strip()
                # Remove various dash formats: "- ", "- - ", etc.
                sub_name = re.sub(r'^[-\s]+', '', sub_name).strip()
                
                if sub_name:  # Only process if we have a name after removing dashes
                    row_data = self._extract_row_data(df, sub_idx)
                    
                    # Only add if it has a value
                    if row_data["annual"] > 0 or any(v > 0 for v in row_data["monthly"].values()):
                        sub_key = self._normalize_key(sub_name)
                        sub_items[sub_key] = {
                            "label": sub_name,
                            "annual": row_data["annual"],
                            "monthly": row_data["monthly"]
                        }
                        
                        # Mark as processed
                        processed_rows.add(sub_idx)
            else:
                # Hit a non-sub-item row, stop looking
                break
        
        return sub_items
    
    def _get_row_label(self, df: pd.DataFrame, row_idx: int) -> str:
        """Get the label from the first non-empty column"""
        for col_idx in range(min(3, len(df.columns))):
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and isinstance(value, str) and len(value.strip()) > 0:
                return value.strip()
        return ""
    
    def _extract_row_data(self, df: pd.DataFrame, row_idx: int) -> Dict:
        """Extract monthly and annual values from a row"""
        monthly_values = {}
        annual_value = 0
        annual_col = self._find_annual_column(df)
        
        # Extract monthly values
        for i, month in enumerate(self.months):
            col_idx = i * 2 + 1  # Assuming months are in odd columns
            if col_idx < len(df.columns):
                value = self._parse_value(df.iloc[row_idx, col_idx])
                if value is not None:
                    monthly_values[month] = value
        
        # Extract annual value
        if annual_col and annual_col in df.columns:
            annual_value = self._parse_value(df.iloc[row_idx][annual_col]) or 0
        elif monthly_values:
            # If no annual column, sum the monthly values
            annual_value = sum(monthly_values.values())
        
        return {"annual": annual_value, "monthly": monthly_values}
    
    def _find_annual_column(self, df: pd.DataFrame) -> Any:
        """Find the column containing annual/total values"""
        for col in df.columns:
            if isinstance(col, str) and any(term in col.upper() for term in ['ANUAL', 'TOTAL', 'ANO']):
                return col
        return None
    
    def _normalize_key(self, text: str) -> str:
        """Normalize text to create a consistent key"""
        # Remove special characters and normalize
        key = re.sub(r'[^\w\s]', '', text)
        # Replace spaces with underscores and convert to lowercase
        return '_'.join(key.lower().split())
    
    def _parse_value(self, val: Any) -> float:
        """Parse a value from various formats to float"""
        if pd.isna(val) or val is None:
            return 0.0
        
        if isinstance(val, (int, float)):
            return float(val)
        
        if isinstance(val, str):
            # Remove currency symbols, spaces, etc.
            val_clean = re.sub(r'[^\d,.-]', '', val.replace('R$', '')).strip()
            # Handle Brazilian number format (1.234,56)
            val_clean = val_clean.replace('.', '').replace(',', '.')
            try:
                return float(val_clean) if val_clean else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        return 0.0