"""
Configuration for Micro Analysis Graphs
Central place to manage all graph settings
"""

# Color schemes - Professional and high contrast
COLORS = {
    'revenue': '#22C55E',  # Bright green for revenue
    'costs': '#EF4444',    # Red for costs
    'profit': '#3B82F6',   # Blue for profit
    'variable_costs': '#F59E0B',  # Amber/Orange for variable costs
    'fixed_costs': '#8B5CF6',     # Purple for fixed costs
    'taxes': '#EC4899',           # Pink for taxes
    'commissions': '#F97316',     # Orange for commissions
    'administrative': '#14B8A6',  # Teal for administrative
    'marketing': '#A855F7',       # Purple for marketing
    'financial': '#6366F1',       # Indigo for financial
    'non_operational': '#F59E0B',  # Amber for non-operational
    'primary': '#3B82F6',         # Primary blue
    'secondary': '#8B5CF6',       # Secondary purple
    'accent': '#22C55E'           # Accent green
}

# Group colors
GROUP_COLORS = {
    'Repasse de Comissão': '#FF6B6B',
    'Funcionários': '#4ECDC4',
    'Telefones': '#45B7D1',
    'Marketing': '#FFA07A',
    'Impostos e Taxas': '#98D8C8',
    'Administrativo': '#F7DC6F',
    'Financeiro': '#BB8FCE'
}

# Graph configurations
GRAPH_CONFIGS = {
    'kpi_cards': {
        'show_tooltips': True,
        'compact_format': True,
        'comparison_format': 'vs {period}'
    },
    
    'pnl_evolution': {
        'title': 'Evolução do Demonstrativo de Resultados',
        'height': 500,
        'show_grid': True,
        'line_width': 3,
        'marker_size': 8,
        'colors': {
            'revenue': COLORS['revenue'],
            'costs': COLORS['costs'],
            'profit': COLORS['profit']
        }
    },
    
    'cost_structure': {
        'title': 'Estrutura de Custos Detalhada',
        'height': 600,
        'show_values': True,
        'stack_mode': 'relative',
        'colors': {
            'variable_costs': COLORS['variable_costs'],
            'fixed_costs': COLORS['fixed_costs'],
            'taxes': COLORS['taxes'],
            'commissions': COLORS['commissions'],
            'administrative': COLORS['administrative'],
            'marketing': COLORS['marketing'],
            'financial': COLORS['financial'],
            'non_operational': COLORS['non_operational']
        }
    },
    
    'group_evolution': {
        'title': 'Evolução dos Grupos de Despesas',
        'height': 500,
        'show_markers': True,
        'line_width': 3,
        'colors': GROUP_COLORS
    },
    
    'group_comparison': {
        'title': 'Grupos de Despesas como % da Receita',
        'height': 500,
        'bar_mode': 'stack',
        'show_text': True,
        'text_position': 'inside',
        'colors': GROUP_COLORS
    },
    
    'margin_impact': {
        'title': 'Impacto dos Grupos na Margem de Lucro',
        'height': 500,
        'waterfall_connector_color': 'rgb(63, 63, 63)',
        'positive_color': '#00CC88',
        'negative_color': '#FF4444',
        'total_color': '#3366CC'
    },
    
    'pareto_analysis': {
        'title': 'Análise de Pareto (80/20) dos Custos',
        'height': 500,
        'bar_color': '#4ECDC4',
        'line_color': '#FF6B6B',
        'threshold_line': 80
    },
    
    'treemap': {
        'title': 'Composição dos Grupos de Despesas',
        'height': 600,
        'textinfo': 'label+value+percent parent',
        'colors': GROUP_COLORS
    },
    
    'financial_notes': {
        'title': 'Análise Financeira Anual',
        'expanded_by_default': True,
        'show_year_navigation': True
    }
}

# Tab configurations
TAB_CONFIGS = {
    'overview': {
        'name': 'Visão Geral',
        'icon': '📊',
        'graphs': ['kpi_cards', 'pnl_evolution', 'group_evolution']
    },
    'groups': {
        'name': 'Análise de Grupos',
        'icon': '📁',
        'graphs': ['group_comparison', 'group_treemap', 'margin_impact']
    },
    'detailed': {
        'name': 'Análise Detalhada',
        'icon': '🔍',
        'graphs': ['cost_structure', 'pareto_analysis', 'subcategory_drill']
    },
    'insights': {
        'name': 'Insights',
        'icon': '💡',
        'graphs': ['financial_notes', 'trend_analysis', 'key_metrics']
    }
}

# Time period configurations
TIME_PERIOD_CONFIGS = {
    'Anual': {
        'x_column': 'year',
        'x_title': 'Ano',
        'aggregation': None
    },
    'Mensal': {
        'x_column': 'period',
        'x_title': 'Mês',
        'aggregation': None,
        'tick_angle': -45
    },
    'Trimestral': {
        'x_column': 'period',
        'x_title': 'Trimestre',
        'aggregation': 'quarter',
        'period_format': '{year}-Q{quarter}'
    },
    'Semestral': {
        'x_column': 'period',
        'x_title': 'Semestre',
        'aggregation': 'semester',
        'period_format': '{year}-S{semester}'
    }
}

# Export configurations
EXPORT_CONFIGS = {
    'image_format': 'png',
    'image_scale': 2,
    'include_timestamp': True,
    'filename_pattern': 'marine_seguros_{graph_name}_{timestamp}'
}

# Chart color palettes for better visibility
CHART_PALETTES = {
    'main': ['#3B82F6', '#EF4444', '#22C55E', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6'],
    'costs': ['#F97316', '#EC4899', '#8B5CF6', '#14B8A6', '#6366F1', '#F59E0B', '#EF4444'],
    'sequential': ['#C7D2FE', '#A5B4FC', '#818CF8', '#6366F1', '#4F46E5', '#4338CA', '#3730A3'],
    'extended': ['#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#F97316', '#14B8A6']
}