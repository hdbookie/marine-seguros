"""
Excel Hierarchy Extractor
Preserves the natural 3-level hierarchy from Excel files based on capitalization patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import re


class ExcelHierarchyExtractor:
    """
    Extracts data preserving Excel's natural 3-level hierarchy:
    - Level 1: ALL CAPS (main sections like CUSTOS FIXOS)
    - Level 2: Normal capitalization (subcategories like Infraestrutura)
    - Level 3: Items with "-" prefix (detail items like - Salário)
    """
    
    def __init__(self):
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        # Special rows that are calculations/summaries, not hierarchy items
        self.calculation_rows = [
            'RESULTADO',
            'MARGEM DE CONTRIBUIÇÃO',
            'MARGEM DE LUCRO',
            'PONTO EQUILÍBRIO',
            'PONTO EQUILIBRIO',
            'TOTAL DESPESAS',
            'DESPESAS TOTAL',
            'DESPESAS - TOTAL',
            'APLICAÇÕES',
            'APLICACOES',
            'RETIRADA EXCEDENTE',
            'MARGEM DE LUCRO - LÍQUIDO',
            'MARGEM DE LUCRO - LIQUIDO',
            'PONTO EQUILÍBRIO - LÍQUIDO',
            'PONTO EQUILIBRIO - LIQUIDO',
            'TOTAL GERAL',
            'SALDO',
            'LUCRO LÍQUIDO',
            'LUCRO LIQUIDO'
        ]
        
        # Main section headers (Level 1)
        self.main_sections = [
            'FATURAMENTO',
            'RECEITAS',
            'CUSTOS FIXOS',
            'CUSTOS VARIÁVEIS',
            'CUSTOS VARIAVEIS',
            'CUSTOS NÃO OPERACIONAIS',
            'CUSTOS NAO OPERACIONAIS',
            'DESPESAS ADMINISTRATIVAS',
            'DESPESAS OPERACIONAIS',
            'DESPESAS FINANCEIRAS'
        ]
    
    def extract_from_excel(self, file_path: str) -> Dict[int, Dict]:
        """
        Extract data from Excel preserving the natural hierarchy
        
        Returns:
            Dictionary with year as key and hierarchical structure as value
        """
        extracted_data = {}
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                year = self._identify_year(sheet_name, file_path)
                if not year:
                    continue
                
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                hierarchy_data = self._extract_hierarchy(df, year)
                
                if hierarchy_data and (hierarchy_data['sections'] or hierarchy_data['calculations']):
                    extracted_data[year] = hierarchy_data
        
        except Exception as e:
            print(f"Error extracting from {file_path}: {e}")
        
        return extracted_data
    
    def _extract_hierarchy(self, df: pd.DataFrame, year: int) -> Dict:
        """
        Extract the 3-level hierarchy from DataFrame
        """
        result = {
            'year': year,
            'sections': [],  # Main hierarchy
            'calculations': {},  # Calculated/summary rows
            'monthly_data': {}  # Monthly breakdown
        }
        
        # Find columns
        label_col = self._find_label_column(df)
        annual_col = self._find_annual_column(df)
        month_cols = self._find_month_columns(df)
        
        if label_col is None:
            return result
        
        current_section = None  # Level 1
        current_subcategory = None  # Level 2
        expecting_level3_items = False  # Flag to track if next items should be Level 3
        
        for idx, row in df.iterrows():
            # Get label from the label column
            label = self._get_cell_value(row, label_col)
            if not label or not isinstance(label, str):
                continue
            
            label = label.strip()
            if not label:
                continue
            
            # Get values
            annual_value = self._get_numeric_value(row, annual_col) if annual_col else 0
            monthly_values = self._get_monthly_values(row, month_cols)
            
            # Check if it's a calculation/summary row
            if self._is_calculation_row(label):
                result['calculations'][label] = {
                    'value': annual_value,
                    'monthly': monthly_values,
                    'type': 'calculated'
                }
                expecting_level3_items = False
                continue
            
            # Level 1: ALL CAPS main sections
            if self._is_level1(label):
                current_section = {
                    'level': 1,
                    'name': label,
                    'value': annual_value,
                    'monthly': monthly_values,
                    'subcategories': []
                }
                result['sections'].append(current_section)
                current_subcategory = None
                expecting_level3_items = False
            
            # Check if we should process this as a Level 3 item
            elif self._is_level3(label):
                # Explicit Level 3 with dash prefix
                item_name = label.lstrip('- ').strip()
                
                # If we don't have a current subcategory, check if we just created one
                if current_subcategory is None and current_section and current_section['subcategories']:
                    # Use the last subcategory that was just created
                    last_subcat = current_section['subcategories'][-1]
                    # Only use it if it has no items yet (just created) or we're expecting children
                    if not last_subcat['items'] or expecting_level3_items:
                        current_subcategory = last_subcat
                        expecting_level3_items = True
                
                if current_subcategory is not None:
                    current_subcategory['items'].append({
                        'level': 3,
                        'name': item_name,
                        'value': annual_value,
                        'monthly': monthly_values
                    })
                elif current_section is not None:
                    # Sometimes Level 3 items appear directly under Level 1
                    # Create an implicit subcategory
                    current_subcategory = {
                        'level': 2,
                        'name': 'Outros',  # Generic name for ungrouped items
                        'value': 0,
                        'monthly': {},
                        'items': []
                    }
                    current_section['subcategories'].append(current_subcategory)
                    current_subcategory['items'].append({
                        'level': 3,
                        'name': item_name,
                        'value': annual_value,
                        'monthly': monthly_values
                    })
            
            elif expecting_level3_items and not self._is_level1(label) and current_subcategory:
                # We're expecting Level 3 items and have a parent
                current_children_sum = sum(item['value'] for item in current_subcategory.get('items', []))
                parent_value = current_subcategory.get('value', 0)
                parent_name = current_subcategory.get('name', '').lower()
                
                # Special handling for Viagens e Deslocamentos
                is_viagens_parent = 'viagens' in parent_name and 'deslocamento' in parent_name
                
                if is_viagens_parent:
                    # Check if this item is travel-related
                    travel_keywords = ['alimenta', 'combust', 'hotel', 'estacion', 'pedágio', 'pedagio', 
                                     'aluguel', 'taxi', 'passagen', 'reembolso']
                    is_travel_child = any(kw in label.lower() for kw in travel_keywords)
                    
                    if is_travel_child:
                        # Add as child of Viagens
                        current_subcategory['items'].append({
                            'level': 3,
                            'name': label,
                            'value': annual_value,
                            'monthly': monthly_values
                        })
                        continue
                    else:
                        # Not a travel item, end the Viagens parent
                        expecting_level3_items = False
                        current_subcategory = None
                        # Fall through to Level 2 processing
                
                # Regular parent-child sum checking
                elif parent_value > 0 and abs(current_children_sum - parent_value) < 100:
                    # Parent is complete, treat as new Level 2
                    expecting_level3_items = False
                    current_subcategory = None
                    # Don't continue - let it fall through to Level 2 processing
                    
                elif annual_value > parent_value * 0.8 and not is_viagens_parent:
                    # Too large, treat as new Level 2
                    expecting_level3_items = False
                    current_subcategory = None
                    # Don't continue - let it fall through to Level 2 processing
                    
                else:
                    # Add as Level 3 child
                    current_subcategory['items'].append({
                        'level': 3,
                        'name': label,
                        'value': annual_value,
                        'monthly': monthly_values
                    })
                    # Check if this completes the parent
                    new_sum = current_children_sum + annual_value
                    if parent_value > 0 and abs(new_sum - parent_value) < 100:
                        expecting_level3_items = False
                        current_subcategory = None
                    continue
            
            # Level 2: Normal capitalization, no dash
            elif current_section is not None:
                # At this point, we've already handled Level 3 items above
                # So this is definitely a Level 2 item
                # Check if this item is a parent category
                is_likely_parent = self._is_likely_parent_category(df, idx, label_col, annual_col)
                
                if is_likely_parent:
                    # This is Level 2 with children
                    current_subcategory = {
                        'level': 2,
                        'name': label,
                        'value': annual_value,
                        'monthly': monthly_values,
                        'items': []
                    }
                    current_section['subcategories'].append(current_subcategory)
                    expecting_level3_items = True
                else:
                    # Standalone Level 2 item with no children
                    standalone_subcat = {
                        'level': 2,
                        'name': label,
                        'value': annual_value,
                        'monthly': monthly_values,
                        'items': []
                    }
                    current_section['subcategories'].append(standalone_subcat)
                    # Don't expect children since this isn't a parent
                    expecting_level3_items = False
                    current_subcategory = None
        
        # Calculate section totals from subcategories if not set
        for section in result['sections']:
            if section['value'] == 0 and section['subcategories']:
                section['value'] = sum(sub.get('value', 0) for sub in section['subcategories'])
        
        # Build monthly aggregates
        result['monthly_data'] = self._aggregate_monthly_data(result['sections'])
        
        return result
    
    def _is_level1(self, label: str) -> bool:
        """Check if label is a Level 1 section (ALL CAPS)"""
        # Check if it's a known main section
        label_upper = label.upper()
        if any(section in label_upper for section in self.main_sections):
            return True
        
        # Check if it's all caps (but not a calculation row)
        if label.isupper() and len(label) > 3 and not self._is_calculation_row(label):
            # Additional check: should contain meaningful words
            if any(word in label for word in ['CUSTOS', 'DESPESAS', 'RECEITA', 'FATURAMENTO']):
                return True
        
        return False
    
    def _is_likely_parent_category(self, df: pd.DataFrame, current_idx: int, label_col: Any, annual_col: Any) -> bool:
        """
        Check if a row is likely a parent category by looking at:
        1. If its value equals the sum of following items  
        2. If following items are indented or have dashes
        3. If it has a round number that looks like a total
        4. Special cases like "Viagens e Deslocamentos"
        """
        current_label = self._get_cell_value(df.iloc[current_idx], label_col)
        current_value = self._get_numeric_value(df.iloc[current_idx], annual_col) if annual_col else 0
        
        # Special case: "Viagens e Deslocamentos" should always be treated as parent
        if current_label and isinstance(current_label, str):
            label_lower = current_label.lower()
            if 'viagens' in label_lower and 'deslocamento' in label_lower:
                # Check if next items are travel-related
                travel_keywords = ['alimenta', 'combust', 'hotel', 'estacion', 'pedágio', 'pedagio', 
                                 'aluguel', 'taxi', 'passagen', 'reembolso']
                
                # Look at next few rows
                has_travel_children = False
                for i in range(1, min(10, len(df) - current_idx)):
                    next_idx = current_idx + i
                    next_label = self._get_cell_value(df.iloc[next_idx], label_col)
                    if next_label and isinstance(next_label, str):
                        next_label_lower = next_label.lower()
                        # Stop if we hit another section
                        if self._is_level1(next_label):
                            break
                        # Check if it's a travel-related item
                        if any(keyword in next_label_lower for keyword in travel_keywords):
                            has_travel_children = True
                            break
                
                if has_travel_children:
                    return True  # Force "Viagens e Deslocamentos" to be a parent
        
        if current_value <= 0:
            return False
        
        # Look ahead at next few rows to find potential children
        potential_children = []
        children_sum = 0
        
        # Look at the next items
        for i in range(1, min(20, len(df) - current_idx)):
            next_idx = current_idx + i
            next_label = self._get_cell_value(df.iloc[next_idx], label_col)
            
            if not next_label or not isinstance(next_label, str):
                continue
            
            next_label = next_label.strip()
            
            # Stop if we hit a main section or calculation
            if self._is_level1(next_label) or self._is_calculation_row(next_label):
                break
            
            # Items with dashes are explicitly Level 3, include them as children
            is_dash_item = next_label.startswith('-')
            if is_dash_item:
                next_label = next_label.lstrip('- ').strip()
            
            # Get the value of this potential child
            next_value = self._get_numeric_value(df.iloc[next_idx], annual_col) if annual_col else 0
            
            # Check if we should stop looking for more children
            # Stop if we already have a perfect sum match (within 5% or R$100)
            if children_sum > 0 and abs(current_value - children_sum) < max(100, current_value * 0.05):
                break
            
            # Stop if we already have some children and this new item is suspiciously large
            if len(potential_children) >= 2:
                # If this item is larger than the current parent value, it can't be a child  
                if next_value > current_value * 0.9:
                    break
                    
                # If adding this item would make the sum much larger than parent, it's probably not a child
                if (children_sum + next_value) > current_value * 1.1:
                    break
            
            # Add as potential child
            if next_value > 0:
                potential_children.append((next_label, next_value))
                children_sum += next_value
        
        # Check if the current value equals the sum of children
        if potential_children and children_sum > 0:
            diff = abs(current_value - children_sum)
            
            # Allow for small rounding differences (within R$100 or 2%)
            if diff < 100 or (diff / current_value < 0.02):
                return True
            
            # Also check if we have at least 2 children and they sum to approximately the parent
            # This handles cases like "Viagens e Deslocamentos" where children don't have dashes
            if len(potential_children) >= 2:
                # More lenient check for groups of items (within 10% or R$500)
                if diff < 500 or (diff / current_value < 0.10):
                    return True
        
        return False
    
    def _could_be_another_parent(self, df: pd.DataFrame, idx: int, label_col: Any, annual_col: Any, prev_sum: float) -> bool:
        """
        Quick check if an item could be another parent category
        """
        item_value = self._get_numeric_value(df.iloc[idx], annual_col) if annual_col else 0
        
        # If this item's value is much larger than the sum we've seen so far,
        # it's probably a new parent category
        if item_value > prev_sum * 1.5:
            return True
        
        # Look ahead a bit to see if there are items that could be its children
        temp_sum = 0
        for i in range(1, min(5, len(df) - idx)):
            next_idx = idx + i
            next_label = self._get_cell_value(df.iloc[next_idx], label_col)
            if not next_label or not isinstance(next_label, str):
                continue
            if self._is_level1(next_label.strip()) or self._is_calculation_row(next_label.strip()):
                break
            next_value = self._get_numeric_value(df.iloc[next_idx], annual_col) if annual_col else 0
            if next_value > 0:
                temp_sum += next_value
        
        # If the sum of following items is close to this item's value, it's likely a parent
        if temp_sum > 0 and abs(item_value - temp_sum) / item_value < 0.1:
            return True
        
        return False
    
    def _is_level3(self, label: str) -> bool:
        """Check if label is a Level 3 item (starts with dash)"""
        return label.startswith('-') or label.startswith('- ')
    
    def _is_calculation_row(self, label: str) -> bool:
        """Check if this is a calculation/summary row"""
        label_upper = label.upper()
        return any(calc.upper() in label_upper for calc in self.calculation_rows)
    
    def _find_label_column(self, df: pd.DataFrame) -> Optional[Any]:
        """Find the column containing labels (usually first text column)"""
        for col in df.columns:
            # Check first few rows for text content
            for i in range(min(10, len(df))):
                val = df.iloc[i][col]
                if pd.notna(val) and isinstance(val, str) and len(val.strip()) > 0:
                    return col
        return None
    
    def _find_annual_column(self, df: pd.DataFrame) -> Optional[Any]:
        """Find the column containing annual totals"""
        for col in df.columns:
            if isinstance(col, str):
                col_upper = col.upper()
                if any(term in col_upper for term in ['ANUAL', 'TOTAL', 'ANO', 'YEAR']):
                    return col
        
        # If not found by name, look for a numeric column after month columns
        month_cols = self._find_month_columns(df)
        if month_cols:
            last_month_idx = max(df.columns.get_loc(c) for c in month_cols.values())
            if last_month_idx < len(df.columns) - 1:
                next_col = df.columns[last_month_idx + 1]
                # Check if it has numeric values
                if df[next_col].dtype in [np.float64, np.int64]:
                    return next_col
        
        return None
    
    def _find_month_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Find columns for each month"""
        month_cols = {}
        
        for col in df.columns:
            col_str = str(col).upper()
            for month in self.months:
                if month in col_str:
                    month_cols[month] = col
                    break
            
            # Also check for month numbers
            month_numbers = {
                '01': 'JAN', '1': 'JAN',
                '02': 'FEV', '2': 'FEV',
                '03': 'MAR', '3': 'MAR',
                '04': 'ABR', '4': 'ABR',
                '05': 'MAI', '5': 'MAI',
                '06': 'JUN', '6': 'JUN',
                '07': 'JUL', '7': 'JUL',
                '08': 'AGO', '8': 'AGO',
                '09': 'SET', '9': 'SET',
                '10': 'OUT',
                '11': 'NOV',
                '12': 'DEZ'
            }
            
            for num, month in month_numbers.items():
                if col_str.endswith(num) or f'/{num}' in col_str or f'-{num}' in col_str:
                    if month not in month_cols:
                        month_cols[month] = col
        
        return month_cols
    
    def _get_cell_value(self, row: pd.Series, col: Any) -> Any:
        """Get value from a cell, handling missing columns"""
        if col is not None and col in row.index:
            return row[col]
        return None
    
    def _get_numeric_value(self, row: pd.Series, col: Any) -> float:
        """Get numeric value from a cell"""
        val = self._get_cell_value(row, col)
        return self._parse_value(val)
    
    def _get_monthly_values(self, row: pd.Series, month_cols: Dict[str, Any]) -> Dict[str, float]:
        """Extract monthly values from row"""
        monthly = {}
        for month, col in month_cols.items():
            if col in row.index:
                value = self._parse_value(row[col])
                if value != 0:
                    monthly[month] = value
        return monthly
    
    def _parse_value(self, val: Any) -> float:
        """Parse a cell value to float"""
        if pd.isna(val):
            return 0.0
        
        # Check for numeric types (including numpy types)
        if isinstance(val, (int, float, np.integer, np.floating)):
            return float(val)
        
        # Try to convert directly to float (handles numpy types)
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
        
        if isinstance(val, str):
            # Remove currency symbols and clean
            val_clean = re.sub(r'[^\d,.-]', '', val.replace('R$', ''))
            val_clean = val_clean.strip()
            
            # Handle Brazilian number format (1.234,56)
            val_clean = val_clean.replace('.', '').replace(',', '.')
            
            try:
                return float(val_clean)
            except (ValueError, TypeError):
                return 0.0
        
        return 0.0
    
    def _identify_year(self, sheet_name: str, file_path: str) -> Optional[int]:
        """Identify the year from sheet name or file path"""
        # Try to find year in sheet name
        year_match = re.search(r'20\d{2}', sheet_name)
        if year_match:
            year = int(year_match.group())
            if 2018 <= year <= 2030:
                return year
        
        # Try sheet name as year
        if sheet_name.isdigit() and 2018 <= int(sheet_name) <= 2030:
            return int(sheet_name)
        
        # Try to find year in file path
        year_match = re.search(r'20\d{2}', file_path)
        if year_match:
            year = int(year_match.group())
            if 2018 <= year <= 2030:
                return year
        
        return None
    
    def _aggregate_monthly_data(self, sections: List[Dict]) -> Dict[str, Dict]:
        """Aggregate monthly data across all sections"""
        monthly_totals = {}
        
        for month in self.months:
            monthly_totals[month] = {
                'total': 0,
                'by_section': {}
            }
            
            for section in sections:
                section_total = section.get('monthly', {}).get(month, 0)
                
                # Add subcategory values
                for subcat in section.get('subcategories', []):
                    subcat_value = subcat.get('monthly', {}).get(month, 0)
                    section_total += subcat_value
                    
                    # Add item values
                    for item in subcat.get('items', []):
                        item_value = item.get('monthly', {}).get(month, 0)
                        section_total += item_value
                
                if section_total > 0:
                    monthly_totals[month]['by_section'][section['name']] = section_total
                    monthly_totals[month]['total'] += section_total
        
        return monthly_totals