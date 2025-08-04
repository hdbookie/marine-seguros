"""
Universal Line Extractor
Captures ALL rows with monetary values from Excel sheets while preserving hierarchy
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import re


class UniversalLineExtractor:
    """Extracts every line item with values, maintaining parent-child relationships"""
    
    def __init__(self):
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        # Category patterns for smart categorization
        self.category_patterns = {
            'revenue': ['RECEITA', 'FATURAMENTO', 'VENDAS', 'ENTRADA'],
            'salaries': ['SALÁRIO', 'SALARIO', 'FOLHA', 'FUNCIONÁRIO', 'FUNCIONARIO', 'PRO LABORE', 'PRO-LABORE'],
            'rent_utilities': ['ALUGUEL', 'CONDOMÍNIO', 'CONDOMINIO', 'ÁGUA', 'AGUA', 'LUZ', 'ENERGIA', 'INTERNET', 'TELEFONE'],
            'taxes': ['IMPOSTO', 'TAXA', 'TRIBUTO', 'SIMPLES NACIONAL', 'IRPJ', 'CSLL', 'ISS', 'ICMS'],
            'commissions': ['COMISSÃO', 'COMISSAO', 'REPASSE'],
            'professional_services': ['CONTABILIDADE', 'JURÍDICO', 'JURIDICO', 'ADVOGADO', 'CONTADOR', 'CONSULTORIA'],
            'marketing': ['MARKETING', 'PUBLICIDADE', 'PROPAGANDA', 'MÍDIA', 'MIDIA'],
            'administrative': ['ADMINISTRATIV', 'ESCRITÓRIO', 'ESCRITORIO', 'MATERIAL'],
            'financial': ['JUROS', 'TARIFA', 'BANCO', 'BANCÁRIA', 'BANCARIA', 'FINANCEIRA'],
            'insurance': ['SEGURO'],
            'maintenance': ['MANUTENÇÃO', 'MANUTENCAO', 'REPARO', 'CONSERTO'],
            'software': ['SOFTWARE', 'SISTEMA', 'LICENÇA', 'LICENCA', 'ASSINATURA'],
            'travel': ['VIAGEM', 'TRANSPORTE', 'COMBUSTÍVEL', 'COMBUSTIVEL'],
            'meals': ['ALIMENTAÇÃO', 'ALIMENTACAO', 'REFEIÇÃO', 'REFEICAO'],
            'depreciation': ['DEPRECIAÇÃO', 'DEPRECIACAO', 'AMORTIZAÇÃO', 'AMORTIZACAO']
        }
        
        # Section headers to identify major categories
        self.section_headers = [
            'CUSTOS VARIÁVEIS', 'CUSTOS VARIAVEIS', 'CUSTOS FIXOS', 'CUSTO FIXO',
            'DESPESAS ADMINISTRATIVAS', 'DESPESAS OPERACIONAIS', 'DESPESAS FINANCEIRAS',
            'DESPESAS NÃO OPERACIONAIS', 'DESPESAS NAO OPERACIONAIS', 'RECEITAS', 'RECEITA'
        ]
        
        # Revenue section patterns to skip
        self.revenue_sections = ['RECEITAS', 'RECEITA', 'FATURAMENTO', 'VENDAS']
        
        # Skip patterns - labels that should be ignored to avoid double counting
        self.skip_patterns = [
            'TOTAL', 'SUBTOTAL', 'SUB-TOTAL', 'SOMA', 'CONSOLIDADO',
            'CUSTOS FIXOS', 'CUSTOS VARIÁVEIS', 'CUSTOS VARIAVEIS', 
            'CUSTO FIXO', 'CUSTO VARIÁVEL', 'CUSTO VARIAVEL',
            'DESPESAS ADMINISTRATIVAS', 'DESPESAS OPERACIONAIS', 'DESPESAS FINANCEIRAS',
            'CUSTOS NÃO OPERACIONAIS', 'CUSTOS NAO OPERACIONAIS',
            'RESULTADO', 'LUCRO', 'PREJUÍZO', 'EBITDA', 'MARGEM',
            'PONTO EQUILÍBRIO', 'PONTO EQUILIBRIO', 'EQUILIBRIO',
            'COMPOSIÇÃO', 'COMPOSICAO', 'SALDOS', 'SALDO',
            'CAIXA', 'APLICAÇÃO', 'APLICACAO', 'RETIRADA', 'EXCEDENTE',
            'BALANCE', 'BALANÇO', 'BALANCO', 'POSIÇÃO', 'POSICAO',
            'ATIVO', 'PASSIVO', 'PATRIMÔNIO', 'PATRIMONIO',
            'CAPITAL', 'RESERVA', 'PROVISÃO', 'PROVISAO'
        ]
    
    def extract_all_lines(self, df: pd.DataFrame, year: int) -> Dict:
        """
        Extract ALL line items from DataFrame, preserving hierarchy
        
        Returns:
            Dictionary with categorized line items and uncategorized items
        """
        result = {
            'year': year,
            'categorized_items': {},
            'uncategorized_items': {},
            'hierarchy': [],
            'totals_by_category': {},
            'all_line_items': []
        }
        
        # Find column indices
        annual_col = self._find_annual_column(df)
        month_cols = self._find_month_columns(df)
        
        # Track current section
        current_section = None
        current_parent = None
        processed_rows = set()
        
        for idx, row in df.iterrows():
            if idx in processed_rows:
                continue
                
            row_label = self._get_row_label(df, idx)
            if not row_label:
                continue
            
            # Clean the label
            row_label = row_label.strip()
            
            # Skip if this matches a skip pattern (totals, subtotals, etc.)
            if self._should_skip_label(row_label):
                processed_rows.add(idx)
                continue
            
            # Check if this is a section header
            if self._is_section_header(row_label):
                current_section = row_label
                
                # Skip revenue sections entirely
                if any(rev in row_label.upper() for rev in self.revenue_sections):
                    current_section = 'REVENUE_SECTION'  # Mark as revenue section
                    processed_rows.add(idx)
                    continue
                
                row_data = self._extract_row_data(df, idx, annual_col, month_cols)
                
                # Add section totals if they have values (but not revenue)
                if row_data['annual'] > 0:
                    section_key = self._normalize_key(row_label)
                    result['totals_by_category'][section_key] = {
                        'label': row_label,
                        'annual': row_data['annual'],
                        'monthly': row_data['monthly']
                    }
                processed_rows.add(idx)
                continue
            
            # Check if this is a sub-item (starts with dash)
            is_sub_item = row_label.startswith('-') or row_label.startswith('- ')
            
            if is_sub_item:
                # This is a sub-item of the current parent
                if current_parent is not None:
                    sub_label = row_label.lstrip('- ').strip()
                    row_data = self._extract_row_data(df, idx, annual_col, month_cols)
                    
                    # Only add if it has values
                    if row_data['annual'] > 0 or any(v > 0 for v in row_data['monthly'].values()):
                        sub_key = self._normalize_key(sub_label)
                        current_parent['sub_items'][sub_key] = {
                            'label': sub_label,
                            'annual': row_data['annual'],
                            'monthly': row_data['monthly']
                        }
                        
                        # Also add to flat list
                        result['all_line_items'].append({
                            'label': sub_label,
                            'parent': current_parent['label'],
                            'section': current_section,
                            'annual': row_data['annual'],
                            'monthly': row_data['monthly'],
                            'is_sub_item': True
                        })
                processed_rows.add(idx)
            else:
                # Skip if we're in a revenue section
                if current_section == 'REVENUE_SECTION':
                    processed_rows.add(idx)
                    continue
                    
                # This is a parent item or standalone item
                row_data = self._extract_row_data(df, idx, annual_col, month_cols)
                
                # Only process if it has values
                if row_data['annual'] > 0 or any(v > 0 for v in row_data['monthly'].values()):
                    # Look ahead for sub-items
                    has_sub_items = self._has_sub_items(df, idx)
                    
                    item_key = self._normalize_key(row_label)
                    item_data = {
                        'label': row_label,
                        'annual': row_data['annual'],
                        'monthly': row_data['monthly'],
                        'section': current_section,
                        'sub_items': {}
                    }
                    
                    # Categorize the item
                    category = self._categorize_item(row_label, current_section)
                    
                    if category != 'uncategorized':
                        if category not in result['categorized_items']:
                            result['categorized_items'][category] = {}
                        result['categorized_items'][category][item_key] = item_data
                    else:
                        result['uncategorized_items'][item_key] = item_data
                    
                    # Add to flat list
                    result['all_line_items'].append({
                        'label': row_label,
                        'parent': None,
                        'section': current_section,
                        'category': category,
                        'annual': row_data['annual'],
                        'monthly': row_data['monthly'],
                        'is_sub_item': False
                    })
                    
                    # Set as current parent if it might have sub-items
                    if has_sub_items:
                        current_parent = item_data
                    else:
                        current_parent = None
                    
                processed_rows.add(idx)
        
        # Build hierarchy
        result['hierarchy'] = self._build_hierarchy(result)
        
        return result
    
    def _get_row_label(self, df: pd.DataFrame, row_idx: int) -> str:
        """Get the label from the first non-empty column"""
        for col_idx in range(min(3, len(df.columns))):
            value = df.iloc[row_idx, col_idx]
            if pd.notna(value) and isinstance(value, str) and len(value.strip()) > 0:
                return value.strip()
        return ""
    
    def _find_annual_column(self, df: pd.DataFrame) -> Optional[Any]:
        """Find the column containing annual totals"""
        for col in df.columns:
            if isinstance(col, str) and any(term in col.upper() for term in ['ANUAL', 'TOTAL', 'ANO']):
                return col
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
        return month_cols
    
    def _extract_row_data(self, df: pd.DataFrame, row_idx: int, annual_col: Any, month_cols: Dict) -> Dict:
        """Extract annual and monthly values from a row"""
        data = {
            'annual': 0,
            'monthly': {}
        }
        
        # Extract annual value
        if annual_col and annual_col in df.columns:
            data['annual'] = self._parse_value(df.iloc[row_idx][annual_col])
        
        # Extract monthly values
        for month, col in month_cols.items():
            if col in df.columns:
                value = self._parse_value(df.iloc[row_idx][col])
                if value > 0:
                    data['monthly'][month] = value
        
        # If no annual value but has monthly values, calculate annual
        if data['annual'] == 0 and data['monthly']:
            data['annual'] = sum(data['monthly'].values())
        
        return data
    
    def _parse_value(self, val: Any) -> float:
        """Parse a cell value to float"""
        if pd.isna(val):
            return 0.0
        
        if isinstance(val, (int, float)):
            return float(val)
        
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
    
    def _normalize_key(self, text: str) -> str:
        """Normalize text to create a consistent key"""
        # Remove special characters and normalize spaces
        key = re.sub(r'[^\w\s]', '', text)
        return '_'.join(key.lower().split())
    
    def _is_section_header(self, label: str) -> bool:
        """Check if a label is a major section header"""
        label_upper = label.upper()
        return any(header in label_upper for header in self.section_headers)
    
    def _should_skip_label(self, label: str) -> bool:
        """Check if a label should be skipped to avoid double counting"""
        label_upper = label.upper()
        
        # Skip obvious totals and aggregation labels
        for pattern in self.skip_patterns:
            if pattern in label_upper:
                return True
        
        # Skip labels that are just numbers or currency values without description
        if len(label.strip()) < 3:
            return True
        
        # Skip labels that start with just currency symbols
        if label.strip().startswith(('R$', '$', '€', '£')):
            return True
        
        return False
    
    def _has_sub_items(self, df: pd.DataFrame, row_idx: int) -> bool:
        """Check if the next few rows are sub-items"""
        for i in range(1, min(5, len(df) - row_idx)):
            next_label = self._get_row_label(df, row_idx + i)
            if next_label and (next_label.startswith('-') or next_label.startswith('- ')):
                return True
            elif next_label and not next_label.startswith(' '):
                # Hit another parent item
                break
        return False
    
    def _categorize_item(self, label: str, current_section: Optional[str]) -> str:
        """Categorize an item based on its label and section"""
        label_upper = label.upper()
        
        # Skip revenue items entirely - we only want costs/expenses
        if current_section and 'RECEITA' in current_section.upper():
            return 'revenue'  # Will be filtered out
        
        # First check category patterns
        for category, patterns in self.category_patterns.items():
            if any(pattern in label_upper for pattern in patterns):
                # Skip revenue patterns
                if category == 'revenue':
                    return 'revenue'  # Will be filtered out
                return category
        
        # Then check section context
        if current_section:
            section_upper = current_section.upper()
            if 'CUSTOS VARIÁVEIS' in section_upper or 'CUSTOS VARIAVEIS' in section_upper:
                return 'variable_costs'
            elif 'CUSTOS FIXOS' in section_upper:
                return 'fixed_costs'
            elif 'ADMINISTRATIV' in section_upper:
                return 'administrative'
            elif 'OPERACIONAL' in section_upper:
                return 'operational'
            elif 'FINANCEIRA' in section_upper:
                return 'financial'
            elif 'NÃO OPERACIONAL' in section_upper or 'NAO OPERACIONAL' in section_upper:
                return 'non_operational'
        
        return 'uncategorized'
    
    def _build_hierarchy(self, result: Dict) -> List[Dict]:
        """Build a hierarchical structure from the extracted data"""
        hierarchy = []
        
        # Add categorized items
        for category, items in result['categorized_items'].items():
            category_node = {
                'label': category.replace('_', ' ').title(),
                'type': 'category',
                'children': []
            }
            
            for item_key, item_data in items.items():
                item_node = {
                    'label': item_data['label'],
                    'type': 'item',
                    'annual': item_data['annual'],
                    'children': []
                }
                
                # Add sub-items
                for sub_key, sub_data in item_data.get('sub_items', {}).items():
                    item_node['children'].append({
                        'label': sub_data['label'],
                        'type': 'sub_item',
                        'annual': sub_data['annual']
                    })
                
                category_node['children'].append(item_node)
            
            hierarchy.append(category_node)
        
        # Add uncategorized items
        if result['uncategorized_items']:
            uncategorized_node = {
                'label': 'Other/Uncategorized',
                'type': 'category',
                'children': []
            }
            
            for item_key, item_data in result['uncategorized_items'].items():
                item_node = {
                    'label': item_data['label'],
                    'type': 'item',
                    'annual': item_data['annual'],
                    'children': []
                }
                
                # Add sub-items
                for sub_key, sub_data in item_data.get('sub_items', {}).items():
                    item_node['children'].append({
                        'label': sub_data['label'],
                        'type': 'sub_item',
                        'annual': sub_data['annual']
                    })
                
                uncategorized_node['children'].append(item_node)
            
            hierarchy.append(uncategorized_node)
        
        return hierarchy