"""
Process Manager Module
Handles data processing and transformation for the Marine Seguros dashboard
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
from utils.expense_categorizer import classify_expense_subcategory


def process_detailed_monthly_data(flexible_data: Dict) -> Optional[Dict]:
    """
    Process flexible data to extract detailed monthly line items for analysis.
    Focuses only on costs and expenses, excluding revenue and calculated items.
    
    Args:
        flexible_data: Dictionary with year keys containing financial data
        
    Returns:
        Dictionary with processed line items and summaries
    """
    if not flexible_data:
        return None
    
    detailed_data = {
        'line_items': [],
        'por_mes': {},
        'por_categoria': {},
        'por_subcategoria': {},
        'por_ano': {},
        'summary': {
            'total_items': 0,
            'total_categories': set(),
            'total_subcategories': set(),
            'years': set()
        }
    }
    
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
              'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    # Process each year
    for year, year_data in flexible_data.items():
        detailed_data['por_ano'][year] = []
        detailed_data['summary']['years'].add(year)
        
        # Process each line item
        for item_key, item_data in year_data['line_items'].items():
            label = item_data['label']
            category = item_data['category']
            annual_value = item_data['annual']
            monthly_values = item_data.get('monthly', {})
            
            # Skip calculated items, margins, revenue, results, and headers
            # Focus only on costs and expenses for analysis
            if category in ['calculated_results', 'margins', 'revenue', 'results', 'resultados', 'faturamento'] or item_data.get('is_subtotal', False):
                continue
            
            # Only include actual cost and expense categories
            cost_expense_categories = [
                'variable_costs', 'fixed_costs', 'admin_expenses', 
                'operational_expenses', 'marketing_expenses', 'financial_expenses',
                'tax_expenses', 'other_expenses', 'other_costs', 'other'
            ]
            if category not in cost_expense_categories:
                continue
            
            # Only include items that are explicitly marked as line items
            if not item_data.get('is_line_item', True):
                continue
            
            # Additional check: Skip if label is a known header or calculation
            label_upper = label.upper().strip()
            skip_patterns = [
                'MARGEM DE CONTRIBUIÇÃO', 'MARGEM DE LUCRO',
                'RESULTADO', 'PONTO EQUILIBRIO', 'PONTO EQUILÍBRIO',
                'LUCRO LÍQUIDO', 'COMPOSIÇÃO DE SALDOS', 'APLICAÇÕES', 
                'RETIRADA EXCEDENTE', 'DESPESAS - TOTAL', 
                'CUSTO FIXO + VARIAVEL', 'CUSTOS FIXOS + VARIÁVEIS', 
                'CUSTOS VARIÁVEIS + FIXOS', 'CUSTOS FIXOS + VARIÁVEIS + NÃO OPERACIONAIS',
                'TOTAL CUSTOS', 'CUSTO TOTAL', 'TOTAL GERAL',
                'DESPESA TOTAL', 'TOTAL DE CUSTOS', 'TOTAL DE DESPESAS',
                'SUBTOTAL', 'SUB TOTAL', 'SUB-TOTAL', 'RECEITA'
            ]
            # Only skip if it's an exact match to avoid filtering items that contain these words
            if label_upper in skip_patterns:
                continue
            
            # Skip if label contains mathematical operators (likely a calculation)
            # But don't skip items that start with " - " as those are sub-items
            if not label.strip().startswith('-'):
                if any(op in label for op in ['+', '=', '(', ')']):
                    continue
            
            # Skip if it's ALL CAPS (likely a header) but not a known abbreviation
            # Also check if it has a value - if it does, it's probably a legitimate expense
            exceptions = ['IRRF', 'INSS', 'FGTS', 'IPTU', 'IPVA', 'ISS', 'PIS', 'COFINS']
            if label_upper == label.strip() and len(label.strip()) > 3 and label_upper not in exceptions:
                # But keep it if it has a substantial annual value (likely a real expense category)
                if annual_value < 1000:  # Only skip if it's a header with no/minimal value
                    continue
            
            # Don't skip items based on value - many legitimate expenses exceed 500k
            # Examples: Funcionários (796k), Pro Labore (119k), etc.
            
            detailed_data['summary']['total_categories'].add(category)
            detailed_data['summary']['total_items'] += 1
            
            # Classify subcategory
            classification = classify_expense_subcategory(label)
            
            # Create detailed item entry
            item_entry = {
                'descricao': label,
                'categoria': category,
                'subcategoria_principal': classification['main_category'],
                'subcategoria': classification['subcategory'],
                'subcategoria_nome': classification['subcategory_name'],
                'ano': year,
                'valor_anual': annual_value,
                'valores_mensais': monthly_values,
                'item_key': item_key
            }
            
            detailed_data['line_items'].append(item_entry)
            detailed_data['por_ano'][year].append(item_entry)
            
            # Group by month
            for month, value in monthly_values.items():
                if value > 0:
                    if month not in detailed_data['por_mes']:
                        detailed_data['por_mes'][month] = []
                    detailed_data['por_mes'][month].append({
                        **item_entry,
                        'valor_mes': value
                    })
            
            # Group by category
            if category not in detailed_data['por_categoria']:
                detailed_data['por_categoria'][category] = []
            detailed_data['por_categoria'][category].append(item_entry)
            
            # Group by subcategory
            subcat_key = f"{classification['main_category']}_{classification['subcategory']}"
            if subcat_key not in detailed_data['por_subcategoria']:
                detailed_data['por_subcategoria'][subcat_key] = []
            detailed_data['por_subcategoria'][subcat_key].append(item_entry)
            
            detailed_data['summary']['total_subcategories'].add(subcat_key)
    
    # Convert sets to lists for JSON serialization
    detailed_data['summary']['total_categories'] = list(detailed_data['summary']['total_categories'])
    detailed_data['summary']['total_subcategories'] = list(detailed_data['summary']['total_subcategories'])
    detailed_data['summary']['years'] = sorted(list(detailed_data['summary']['years']))
    
    return detailed_data


def convert_extracted_to_processed(extracted_data: Dict) -> Dict:
    """
    Convert extracted data to processed format for backward compatibility
    
    Args:
        extracted_data: Raw extracted data from Excel
        
    Returns:
        Processed data in legacy format
    """
    processed_data = {}
    
    for year, year_data in extracted_data.items():
        # Initialize year data
        processed_data[year] = {
            'Faturamento': 0,
            'Custos Variáveis': {},
            'Custos Fixos': {},
            'Despesas Administrativas': {},
            'Despesas Operacionais': {},
            'Despesas de Marketing': {},
            'Despesas Financeiras': {},
            'Impostos': {},
            'Resultado Operacional': 0,
            'Outros': {}
        }
        
        # Category mapping
        category_map = {
            'revenue': 'Faturamento',
            'variable_costs': 'Custos Variáveis',
            'fixed_costs': 'Custos Fixos',
            'admin_expenses': 'Despesas Administrativas',
            'operational_expenses': 'Despesas Operacionais',
            'marketing_expenses': 'Despesas de Marketing',
            'financial_expenses': 'Despesas Financeiras',
            'tax_expenses': 'Impostos',
            'other_expenses': 'Outros',
            'other_costs': 'Outros',
            'other': 'Outros'
        }
        
        # Process line items
        for item_key, item_data in year_data.get('line_items', {}).items():
            category = item_data.get('category', 'other')
            mapped_category = category_map.get(category, 'Outros')
            
            if mapped_category == 'Faturamento':
                processed_data[year]['Faturamento'] = item_data.get('annual', 0)
            else:
                label = item_data.get('label', item_key)
                annual_value = item_data.get('annual', 0)
                
                if mapped_category in processed_data[year]:
                    processed_data[year][mapped_category][label] = annual_value
        
        # Calculate result
        revenue = processed_data[year]['Faturamento']
        total_costs = sum(
            sum(costs.values()) if isinstance(costs, dict) else costs
            for key, costs in processed_data[year].items()
            if key not in ['Faturamento', 'Resultado Operacional']
        )
        processed_data[year]['Resultado Operacional'] = revenue - total_costs
    
    return processed_data


def sync_processed_to_extracted(processed_data: Dict = None) -> Dict:
    """
    Sync processed data back to extracted format
    
    Args:
        processed_data: Processed financial data
        
    Returns:
        Data in extracted format
    """
    if not processed_data:
        return {}
    
    extracted_data = {}
    
    # Reverse category mapping
    reverse_category_map = {
        'Faturamento': 'revenue',
        'Custos Variáveis': 'variable_costs',
        'Custos Fixos': 'fixed_costs',
        'Despesas Administrativas': 'admin_expenses',
        'Despesas Operacionais': 'operational_expenses',
        'Despesas de Marketing': 'marketing_expenses',
        'Despesas Financeiras': 'financial_expenses',
        'Impostos': 'tax_expenses',
        'Outros': 'other_expenses'
    }
    
    for year, year_data in processed_data.items():
        extracted_data[year] = {
            'year': year,
            'line_items': {},
            'categories': {},
            'monthly_data': {},
            'hierarchy': []
        }
        
        # Process each category
        for category_name, category_data in year_data.items():
            if category_name == 'Resultado Operacional':
                continue
                
            category_key = reverse_category_map.get(category_name, 'other')
            
            if category_name == 'Faturamento':
                # Single revenue item
                item_key = 'revenue_total'
                extracted_data[year]['line_items'][item_key] = {
                    'label': 'Faturamento Total',
                    'category': category_key,
                    'annual': category_data,
                    'monthly': {},
                    'row_index': 0,
                    'is_subtotal': False
                }
            elif isinstance(category_data, dict):
                # Multiple items in category
                extracted_data[year]['categories'][category_key] = []
                
                for label, value in category_data.items():
                    item_key = label.lower().replace(' ', '_')
                    extracted_data[year]['line_items'][item_key] = {
                        'label': label,
                        'category': category_key,
                        'annual': value,
                        'monthly': {},
                        'row_index': len(extracted_data[year]['line_items']),
                        'is_subtotal': False
                    }
                    extracted_data[year]['categories'][category_key].append(item_key)
    
    return extracted_data


def apply_filters(items: List[Dict], filters: Dict) -> List[Dict]:
    """
    Apply filters to a list of items
    
    Args:
        items: List of line items to filter
        filters: Dictionary containing filter criteria
            - years: List of years to include
            - categories: List of categories to include
            - search_term: Search string
            - months: List of months to include
            - value_range: Tuple of (min, max) values
            - subcategories: List of subcategories to include
    
    Returns:
        Filtered list of items
    """
    filtered = []
    
    for item in items:
        # Year filter
        if 'years' in filters and filters['years']:
            if str(item.get('ano')) not in [str(y) for y in filters['years']]:
                continue
        
        # Category filter
        if 'categories' in filters and filters['categories']:
            if item.get('categoria') not in filters['categories']:
                continue
        
        # Subcategory filter
        if 'subcategories' in filters and filters['subcategories']:
            item_subcat = f"{item.get('subcategoria_principal')}_{item.get('subcategoria')}"
            if item_subcat not in filters['subcategories']:
                continue
        
        # Month filter
        if 'months' in filters and filters['months']:
            has_value_in_month = any(
                item.get('valores_mensais', {}).get(month, 0) > 0
                for month in filters['months']
            )
            if not has_value_in_month:
                continue
        
        # Value range filter
        if 'value_range' in filters and filters['value_range']:
            min_val, max_val = filters['value_range']
            if not (min_val <= item.get('valor_anual', 0) <= max_val):
                continue
        
        # Search filter
        if 'search_term' in filters and filters['search_term']:
            search_words = filters['search_term'].lower().split()
            item_desc = item.get('descricao', '').lower()
            if not any(word in item_desc for word in search_words):
                continue
        
        filtered.append(item)
    
    return filtered