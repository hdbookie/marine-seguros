"""Expense categorization utilities"""

# Main category definitions
EXPENSE_CATEGORIES = {
    'administrative': 'Despesas Administrativas',
    'commercial': 'Despesas Comerciais',
    'operational': 'Despesas Operacionais',
    'financial': 'Despesas Financeiras',
    'tax': 'Impostos e Taxas',
    'it_telecom': 'TI e Telecomunicações',
    'facilities': 'Instalações e Infraestrutura',
    'fleet': 'Frota e Transporte',
    'marketing': 'Marketing e Publicidade',
    'insurance': 'Seguros e Garantias',
    'utilities': 'Utilidades',
    'consultancy': 'Consultoria e Serviços',
    'training': 'Treinamento e Desenvolvimento',
    'legal': 'Jurídico',
    'investments': 'Investimentos',
    'other': 'Outras Despesas'
}

# Subcategory definitions
EXPENSE_SUBCATEGORIES = {
    'administrative': {
        'office_supplies': 'Material de Escritório',
        'office_services': 'Serviços de Escritório',
        'general_admin': 'Administração Geral'
    },
    'commercial': {
        'sales_commission': 'Comissões de Vendas',
        'sales_expenses': 'Despesas de Vendas',
        'client_relations': 'Relacionamento com Clientes'
    },
    'operational': {
        'production': 'Produção',
        'maintenance': 'Manutenção',
        'operations': 'Operações Gerais'
    },
    'financial': {
        'bank_fees': 'Taxas Bancárias',
        'interest': 'Juros',
        'financial_services': 'Serviços Financeiros'
    },
    'tax': {
        'federal_tax': 'Impostos Federais',
        'state_tax': 'Impostos Estaduais',
        'municipal_tax': 'Impostos Municipais',
        'other_tax': 'Outras Taxas'
    },
    'it_telecom': {
        'software': 'Software e Licenças',
        'hardware': 'Hardware e Equipamentos',
        'telecom': 'Telecomunicações',
        'it_services': 'Serviços de TI'
    },
    'facilities': {
        'rent': 'Aluguel',
        'maintenance': 'Manutenção Predial',
        'security': 'Segurança',
        'cleaning': 'Limpeza e Conservação'
    },
    'fleet': {
        'fuel': 'Combustível',
        'maintenance': 'Manutenção de Veículos',
        'rental': 'Aluguel de Veículos',
        'transport': 'Transporte e Frete'
    },
    'marketing': {
        'advertising': 'Publicidade',
        'events': 'Eventos',
        'digital_marketing': 'Marketing Digital',
        'materials': 'Material de Marketing'
    },
    'insurance': {
        'property': 'Seguro Patrimonial',
        'vehicle': 'Seguro de Veículos',
        'liability': 'Seguro de Responsabilidade',
        'other_insurance': 'Outros Seguros'
    },
    'utilities': {
        'electricity': 'Energia Elétrica',
        'water': 'Água',
        'gas': 'Gás',
        'other_utilities': 'Outras Utilidades'
    },
    'consultancy': {
        'management': 'Consultoria de Gestão',
        'technical': 'Consultoria Técnica',
        'audit': 'Auditoria',
        'other_consulting': 'Outras Consultorias'
    },
    'training': {
        'professional': 'Treinamento Profissional',
        'technical': 'Treinamento Técnico',
        'leadership': 'Desenvolvimento de Liderança',
        'other_training': 'Outros Treinamentos'
    },
    'legal': {
        'legal_fees': 'Honorários Advocatícios',
        'legal_services': 'Serviços Jurídicos',
        'compliance': 'Compliance',
        'other_legal': 'Outras Despesas Jurídicas'
    },
    'investments': {
        'capex': 'Investimentos de Capital',
        'improvements': 'Melhorias',
        'projects': 'Projetos',
        'other_investments': 'Outros Investimentos'
    },
    'other': {
        'general': 'Despesas Gerais',
        'miscellaneous': 'Despesas Diversas',
        'unclassified': 'Não Classificado'
    }
}

# Pattern matching for automatic categorization
EXPENSE_PATTERNS = {
    'administrative': [
        r'material.*escritorio', r'papelaria', r'expediente', r'correio', 
        r'cartorio', r'despach.*', r'administra.*'
    ],
    'commercial': [
        r'comiss.*', r'vend.*', r'comercial', r'representant.*', 
        r'bonifica.*', r'premia.*'
    ],
    'operational': [
        r'manuten.*', r'reparo.*', r'conserto.*', r'operacion.*', 
        r'produ.*', r'fabrica.*'
    ],
    'financial': [
        r'banc.*', r'tarifa.*', r'juros', r'multa.*', r'financ.*', 
        r'cpmf', r'iof'
    ],
    'tax': [
        r'impost.*', r'tribut.*', r'cofins', r'pis', r'csll', r'irpj', 
        r'iss', r'icms', r'iptu', r'ipva', r'taxa.*', r'contribui.*'
    ],
    'it_telecom': [
        r'software', r'licen[çc]a.*', r'telefon.*', r'internet', 
        r'celular', r'inform.*', r'computador', r'servidor', r'rede'
    ],
    'facilities': [
        r'aluguel', r'condominio', r'agua', r'luz', r'energia', 
        r'limpeza', r'vigilan.*', r'seguran.*', r'portaria'
    ],
    'fleet': [
        r'combustivel', r'gasolina', r'alcool', r'diesel', r'veiculo', 
        r'carro', r'moto', r'caminhao', r'frete', r'transport.*', 
        r'uber', r'taxi', r'estacionamento'
    ],
    'marketing': [
        r'publicidade', r'propaganda', r'marketing', r'anuncio', 
        r'midia', r'evento.*', r'feira.*', r'brinde.*'
    ],
    'insurance': [
        r'seguro', r'sinistro', r'apolice', r'premio.*segur.*', 
        r'cossegur.*', r'ressegur.*'
    ],
    'utilities': [
        r'energia.*eletr.*', r'agua.*esgoto', r'gas', r'telefon.*', 
        r'internet', r'provedor'
    ],
    'consultancy': [
        r'consult.*', r'assessor.*', r'audit.*', r'contador.*', 
        r'advogad.*', r'juridic.*'
    ],
    'training': [
        r'treinam.*', r'curso.*', r'capacita.*', r'palestra', 
        r'workshop', r'semin.*'
    ],
    'legal': [
        r'advoca.*', r'juridic.*', r'process.*', r'honorar.*', 
        r'judicial', r'extra.*judicial'
    ],
    'investments': [
        r'investim.*', r'imobiliz.*', r'obra.*', r'reforma.*', 
        r'amplia.*', r'melhoria.*'
    ]
}


def get_category_name(category_key):
    """Get the display name for a category"""
    return EXPENSE_CATEGORIES.get(category_key, category_key)


def get_subcategory_name(category_key, subcategory_key):
    """Get the display name for a subcategory"""
    if category_key in EXPENSE_SUBCATEGORIES:
        return EXPENSE_SUBCATEGORIES[category_key].get(subcategory_key, subcategory_key)
    return subcategory_key


def categorize_expense(description, amount=None):
    """Categorize an expense based on its description"""
    import re
    
    description_lower = description.lower()
    
    # Check each category's patterns
    for category, patterns in EXPENSE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, description_lower):
                # Find appropriate subcategory
                subcategory = _find_subcategory(category, description_lower)
                return category, subcategory
    
    # Default to 'other' if no match
    return 'other', 'general'


def _find_subcategory(category, description):
    """Find the appropriate subcategory based on description"""
    import re
    
    # Subcategory patterns
    subcategory_patterns = {
        'administrative': {
            'office_supplies': [r'material', r'papel', r'caneta', r'toner'],
            'office_services': [r'correio', r'malote', r'motoboy'],
            'general_admin': [r'administr', r'geral']
        },
        'it_telecom': {
            'software': [r'software', r'licen[çc]a', r'sistema'],
            'hardware': [r'computador', r'notebook', r'impressora'],
            'telecom': [r'telefon', r'celular', r'internet'],
            'it_services': [r'suporte', r'manuten.*ti', r'inform']
        },
        'fleet': {
            'fuel': [r'combustivel', r'gasolina', r'alcool', r'diesel'],
            'maintenance': [r'manuten.*veic', r'oficina', r'pneu'],
            'rental': [r'aluguel.*veic', r'locacao.*veic'],
            'transport': [r'frete', r'transport', r'uber', r'taxi']
        }
    }
    
    if category in subcategory_patterns:
        for subcat, patterns in subcategory_patterns[category].items():
            for pattern in patterns:
                if re.search(pattern, description):
                    return subcat
    
    # Return first available subcategory as default
    if category in EXPENSE_SUBCATEGORIES:
        return list(EXPENSE_SUBCATEGORIES[category].keys())[0]
    
    return 'general'