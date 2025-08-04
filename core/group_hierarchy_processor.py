"""
Group Hierarchy Processor
Processes financial data to identify and aggregate expense groups
"""

import pandas as pd
from typing import Dict, List, Any
import re


class GroupHierarchyProcessor:
    """Processes financial data to identify hierarchical groups and aggregate sub-items"""
    
    def __init__(self):
        # Define known groups and their patterns
        self.group_patterns = {
            'repasse_comissao': {
                'pattern': r'REPASSE\s*COMISS[ÃA]O',
                'display_name': 'Repasse de Comissão',
                'is_parent': True
            },
            'funcionarios': {
                'pattern': r'FUNCION[ÁA]RIOS?',
                'display_name': 'Funcionários',
                'is_parent': True,
                'sub_patterns': [
                    r'SAL[ÁA]RIO',
                    r'VALE[\s-]?ALIMENTA[ÇC][ÃA]O',
                    r'VALE[\s-]?TRANSPORTE',
                    r'PLANO[\s-]?SA[ÚU]DE',
                    r'BENEF[ÍI]CIO',
                    r'F[ÉE]RIAS',
                    r'13[º°]?\s*SAL[ÁA]RIO',
                    r'FGTS',
                    r'INSS'
                ]
            },
            'telefones': {
                'pattern': r'TELEFONE|CELULAR|TELECOM',
                'display_name': 'Telefones',
                'combine_items': True
            },
            'marketing': {
                'pattern': r'MARKETING|PUBLICIDADE|PROPAGANDA',
                'display_name': 'Marketing',
                'is_parent': True
            },
            'impostos': {
                'pattern': r'IMPOSTO|TRIBUTO|TAXA',
                'display_name': 'Impostos e Taxas',
                'is_parent': True
            }
        }
        
    def process_data(self, data: Dict[int, Dict]) -> Dict[int, Dict]:
        """
        Process financial data to create group hierarchies
        
        Args:
            data: Dictionary with years as keys and financial data as values
            
        Returns:
            Processed data with group hierarchies
        """
        processed_data = {}
        
        for year, year_data in data.items():
            processed_data[year] = self._process_year_data(year, year_data)
            
        return processed_data
    
    def _process_year_data(self, year: int, year_data: Dict) -> Dict:
        """Process data for a single year"""
        processed = year_data.copy()
        processed['groups'] = {}
        
        # Process each expense category
        expense_categories = [
            'variable_costs', 'fixed_costs', 'non_operational_costs',
            'taxes', 'commissions', 'administrative_expenses',
            'marketing_expenses', 'financial_expenses'
        ]
        
        for category in expense_categories:
            if category in year_data and isinstance(year_data[category], dict):
                category_data = year_data[category]
                if 'line_items' in category_data:
                    self._process_line_items(processed, category, category_data['line_items'])
        
        return processed
    
    def _process_line_items(self, processed: Dict, category: str, line_items: Dict):
        """Process line items to identify groups"""
        if not isinstance(line_items, dict):
            return
            
        groups = {}
        processed_items = set()
        
        # First pass: identify parent groups
        for item_key, item_data in line_items.items():
            label = item_data.get('label', '')
            
            for group_key, group_config in self.group_patterns.items():
                if re.search(group_config['pattern'], label, re.IGNORECASE):
                    if group_config.get('is_parent'):
                        # This is a parent group
                        if group_key not in groups:
                            groups[group_key] = {
                                'display_name': group_config['display_name'],
                                'parent_item': item_data,
                                'sub_items': {},
                                'total_annual': item_data.get('annual', 0),
                                'total_monthly': item_data.get('monthly', {})
                            }
                        processed_items.add(item_key)
                        break
        
        # Second pass: identify sub-items
        for item_key, item_data in line_items.items():
            if item_key in processed_items:
                continue
                
            label = item_data.get('label', '')
            
            # Check if this item belongs to a group
            for group_key, group_config in self.group_patterns.items():
                if group_key in groups and 'sub_patterns' in group_config:
                    # Check sub-patterns
                    for sub_pattern in group_config['sub_patterns']:
                        if re.search(sub_pattern, label, re.IGNORECASE):
                            groups[group_key]['sub_items'][item_key] = item_data
                            processed_items.add(item_key)
                            break
        
        # Third pass: combine similar items (like telefones)
        for group_key, group_config in self.group_patterns.items():
            if group_config.get('combine_items'):
                combined_items = {}
                combined_annual = 0
                combined_monthly = {}
                
                for item_key, item_data in line_items.items():
                    if item_key in processed_items:
                        continue
                        
                    label = item_data.get('label', '')
                    if re.search(group_config['pattern'], label, re.IGNORECASE):
                        combined_items[item_key] = item_data
                        combined_annual += item_data.get('annual', 0)
                        
                        # Combine monthly values
                        for month, value in item_data.get('monthly', {}).items():
                            combined_monthly[month] = combined_monthly.get(month, 0) + value
                        
                        processed_items.add(item_key)
                
                if combined_items:
                    groups[group_key] = {
                        'display_name': group_config['display_name'],
                        'combined_items': combined_items,
                        'total_annual': combined_annual,
                        'total_monthly': combined_monthly
                    }
        
        # Store groups in processed data
        if groups:
            if 'groups' not in processed:
                processed['groups'] = {}
            processed['groups'][category] = groups
    
    def get_major_groups(self, processed_data: Dict[int, Dict]) -> Dict[str, Dict]:
        """
        Extract major groups across all years for comparison
        
        Returns:
            Dictionary with group names as keys and yearly data as values
        """
        major_groups = {}
        
        for year, year_data in processed_data.items():
            if 'groups' not in year_data:
                continue
                
            for category, category_groups in year_data['groups'].items():
                for group_key, group_data in category_groups.items():
                    display_name = group_data['display_name']
                    
                    if display_name not in major_groups:
                        major_groups[display_name] = {
                            'years': {},
                            'category': category
                        }
                    
                    major_groups[display_name]['years'][year] = {
                        'annual': group_data['total_annual'],
                        'monthly': group_data['total_monthly'],
                        'item_count': len(group_data.get('sub_items', {})) + len(group_data.get('combined_items', {}))
                    }
        
        return major_groups
    
    def create_group_comparison_df(self, major_groups: Dict[str, Dict]) -> pd.DataFrame:
        """Create a DataFrame for group comparison visualization"""
        rows = []
        
        for group_name, group_data in major_groups.items():
            for year, year_values in group_data['years'].items():
                rows.append({
                    'Grupo': group_name,
                    'Ano': year,
                    'Valor': year_values['annual'],
                    'Categoria': group_data['category'],
                    'Itens': year_values['item_count']
                })
        
        return pd.DataFrame(rows)