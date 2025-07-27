"""Category utilities for Marine Seguros dashboard"""

def get_category_icon(category):
    """Get icon for each category"""
    icons = {
        'revenue': '💰',
        'variable_costs': '📦',
        'fixed_costs': '🏢',
        'admin_expenses': '📋',
        'operational_expenses': '⚙️',
        'marketing_expenses': '📢',
        'financial_expenses': '💳',
        'tax_expenses': '📊',
        'other_expenses': '📌',
        'other_costs': '📍',
        'results': '📈',
        'margins': '📊',
        'calculated_results': '🧮',
        'other': '📄'
    }
    return icons.get(category, '📄')

def get_category_name(category):
    """Get friendly name for category"""
    names = {
        'revenue': 'Receitas',
        'variable_costs': 'Custos Variáveis',
        'fixed_costs': 'Custos Fixos',
        'admin_expenses': 'Despesas Administrativas',
        'operational_expenses': 'Despesas Operacionais',
        'marketing_expenses': 'Despesas de Marketing',
        'financial_expenses': 'Despesas Financeiras',
        'tax_expenses': 'Impostos e Taxas',
        'other_expenses': 'Outras Despesas',
        'other_costs': 'Outros Custos',
        'results': 'Resultados',
        'margins': 'Margens',
        'calculated_results': 'Resultados Calculados',
        'other': 'Outros'
    }
    return names.get(category, category.replace('_', ' ').title())