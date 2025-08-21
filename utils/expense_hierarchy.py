"""
Expense Hierarchy Mapping System
Handles 4-level categorization of expenses with smart parsing
"""

from typing import Dict, List, Tuple, Optional
import re


class ExpenseHierarchy:
    """
    3-Level Expense Hierarchy with 3 Main Categories:
    Level 1: Main Category (Custos Fixos, Variáveis, Não Operacionais)
    Level 2: Subcategory (Pessoal, Ocupação, etc.)
    Level 3: Detail Category (from "/" separator - e.g., Funcionários, Terceiros)
    Level 4: Individual line items
    """
    
    # Main category definitions - simplified to 3 main types
    HIERARCHY = {
        'custos_fixos': {
            'name': '📊 Custos Fixos',
            'description': 'Despesas fixas mensais que não variam com volume de vendas',
            'subcategories': {
                'pessoal': {
                    'name': '👥 Pessoal',
                    'keywords': ['salário', 'salarios', 'férias', 'ferias', '13º', 'fgts', 'inss', 
                                'vale', 'benefício', 'beneficio', 'plano de saúde', 'plano saude',
                                'alimentação', 'alimentacao', 'transporte', 'rescisão', 'rescisao',
                                'folha', 'funcionário', 'funcionario', 'colaborador'],
                    'detail_categories': ['funcionários', 'terceiros', 'diretoria', 'estagiários']
                },
                'ocupacao': {
                    'name': '🏢 Ocupação e Utilidades',
                    'keywords': ['aluguel', 'condomínio', 'condominio', 'iptu', 'energia', 
                                'água', 'agua', 'luz', 'internet', 'telefone', 'gás', 'gas',
                                'limpeza', 'segurança', 'seguranca', 'manutenção', 'manutencao'],
                    'detail_categories': ['imóvel', 'utilidades', 'manutenção', 'segurança']
                },
                'servicos_profissionais': {
                    'name': '🔧 Serviços Profissionais',
                    'keywords': ['contabilidade', 'contador', 'jurídico', 'juridico', 'advocacia',
                                'consultoria', 'auditoria', 'assessoria', 'profissional',
                                'terceirizado', 'prestador'],
                    'detail_categories': ['contábil', 'jurídico', 'consultoria', 'outros']
                },
                'tecnologia': {
                    'name': '💻 Tecnologia e Sistemas',
                    'keywords': ['software', 'sistema', 'licença', 'licenca', 'ti', 'informática',
                                'informatica', 'computador', 'servidor', 'cloud', 'nuvem',
                                'assinatura', 'plataforma'],
                    'detail_categories': ['software', 'hardware', 'infraestrutura', 'licenças']
                },
                'seguros': {
                    'name': '🛡️ Seguros',
                    'keywords': ['seguro', 'apólice', 'apolice', 'proteção', 'protecao',
                                'cobertura', 'sinistro'],
                    'detail_categories': ['vida', 'saúde', 'patrimonial', 'responsabilidade']
                },
                'administrativas': {
                    'name': '📋 Despesas Administrativas',
                    'keywords': ['administrativo', 'administração', 'administracao', 'escritório',
                                'escritorio', 'material', 'papelaria', 'correio', 'cartório',
                                'cartorio', 'documentação', 'documentacao', 'despesa administrativa'],
                    'detail_categories': ['escritório', 'documentação', 'materiais', 'serviços']
                },
                'financeiras': {
                    'name': '💰 Despesas Financeiras',
                    'keywords': ['financeiro', 'banco', 'tarifa', 'juros', 'multa', 'iof',
                                'taxa', 'cobrança', 'cobranca', 'cartão', 'cartao', 'despesa financeira',
                                'tarifa bancária', 'tarifa bancaria'],
                    'detail_categories': ['tarifas', 'juros', 'impostos', 'taxas']
                },
                'impostos_taxas': {
                    'name': '💸 Impostos e Taxas',
                    'keywords': ['imposto', 'tributo', 'iss', 'icms', 'pis', 'cofins', 'csll', 
                                'irpj', 'iptu', 'taxa', 'contribuição', 'contribuicao'],
                    'detail_categories': ['federais', 'estaduais', 'municipais', 'taxas']
                }
            }
        },
        'custos_variaveis': {
            'name': '📈 Custos Variáveis',
            'description': 'Despesas que variam com o volume de vendas',
            'subcategories': {
                'comissoes': {
                    'name': '💼 Comissões e Repasses',
                    'keywords': ['comissão', 'comissao', 'repasse', 'corretagem', 'agenciamento',
                                'intermediação', 'intermediacao', 'parceiro', 'afiliado'],
                    'detail_categories': ['vendas', 'parceiros', 'corretores', 'agentes']
                },
                'custos_producao': {
                    'name': '🏭 Custos de Produção',
                    'keywords': ['produção', 'producao', 'material', 'insumo', 'matéria prima',
                                'materia prima', 'embalagem', 'frete', 'logística', 'logistica'],
                    'detail_categories': ['materiais', 'logística', 'produção', 'embalagem']
                },
                'marketing_vendas': {
                    'name': '📢 Marketing e Vendas',
                    'keywords': ['marketing', 'publicidade', 'propaganda', 'campanha', 'anúncio',
                                'anuncio', 'mídia', 'midia', 'divulgação', 'divulgacao',
                                'promoção', 'promocao', 'evento'],
                    'detail_categories': ['digital', 'offline', 'eventos', 'materiais']
                },
                'comerciais': {
                    'name': '🤝 Despesas Comerciais',
                    'keywords': ['comercial', 'venda', 'cliente', 'negociação', 'negociacao',
                                'representação', 'representacao', 'viagem', 'hospedagem',
                                'deslocamento', 'viagem de negócios'],
                    'detail_categories': ['viagens', 'representação', 'clientes', 'vendas']
                }
            }
        },
        'custos_nao_operacionais': {
            'name': '🔴 Custos Não Operacionais',
            'description': 'Despesas extraordinárias ou não relacionadas à operação principal',
            'subcategories': {
                'extraordinarias': {
                    'name': '⚡ Extraordinárias',
                    'keywords': ['extraordinário', 'extraordinario', 'eventual', 'imprevisto',
                                'emergência', 'emergencia', 'excepcional', 'único', 'unico'],
                    'detail_categories': ['emergências', 'imprevistos', 'únicos', 'especiais']
                },
                'provisoes': {
                    'name': '📊 Provisões e Reservas',
                    'keywords': ['provisão', 'provisao', 'reserva', 'contingência', 'contingencia',
                                'depreciação', 'depreciacao', 'amortização', 'amortizacao'],
                    'detail_categories': ['depreciação', 'contingências', 'reservas', 'provisões']
                },
                'multas_penalidades': {
                    'name': '⚖️ Multas e Penalidades',
                    'keywords': ['multa', 'penalidade', 'infração', 'infracao', 'autuação',
                                'autuacao', 'processo', 'judicial'],
                    'detail_categories': ['fiscais', 'trabalhistas', 'contratuais', 'judiciais']
                }
            }
        }
    }
    
    @classmethod
    def parse_expense_item(cls, item_label: str) -> Dict[str, str]:
        """
        Parse an expense item label to extract hierarchy levels
        
        Args:
            item_label: The expense label (e.g., "Salários/Funcionários")
            
        Returns:
            Dictionary with parsed hierarchy levels
        """
        result = {
            'original_label': item_label,
            'main_category': None,
            'main_category_name': None,
            'subcategory': None,
            'subcategory_name': None,
            'detail_category': None,
            'item_name': None
        }
        
        # Check for "/" separator to extract detail category
        if '/' in item_label:
            parts = item_label.split('/', 1)
            base_item = parts[0].strip()
            detail_category = parts[1].strip()
            result['detail_category'] = detail_category.lower()
            result['item_name'] = base_item
        else:
            result['item_name'] = item_label
            base_item = item_label
        
        # Classify into main and subcategories
        classification = cls._classify_item(base_item.lower())
        result.update(classification)
        
        return result
    
    @classmethod
    def _classify_item(cls, item_text: str) -> Dict[str, str]:
        """
        Classify an item into main category and subcategory based on keywords
        
        Args:
            item_text: Lowercase text to classify
            
        Returns:
            Dictionary with category classifications
        """
        result = {
            'main_category': 'custos_nao_operacionais',
            'main_category_name': '🔴 Custos Não Operacionais',
            'subcategory': 'extraordinarias',
            'subcategory_name': '⚡ Extraordinárias'
        }
        
        # Check each main category
        for main_cat_key, main_cat_data in cls.HIERARCHY.items():
            # Check each subcategory's keywords
            for subcat_key, subcat_data in main_cat_data['subcategories'].items():
                for keyword in subcat_data['keywords']:
                    if keyword in item_text:
                        result['main_category'] = main_cat_key
                        result['main_category_name'] = main_cat_data['name']
                        result['subcategory'] = subcat_key
                        result['subcategory_name'] = subcat_data['name']
                        return result
        
        # Additional intelligent classification based on patterns
        result = cls._apply_pattern_rules(item_text, result)
        
        return result
    
    @classmethod
    def _apply_pattern_rules(cls, item_text: str, current_result: Dict[str, str]) -> Dict[str, str]:
        """
        Apply pattern-based rules for better classification
        """
        # Tax-related patterns
        tax_patterns = ['imposto', 'tributo', 'iss', 'icms', 'pis', 'cofins', 'csll', 'irpj']
        if any(pattern in item_text for pattern in tax_patterns):
            current_result['main_category'] = 'custos_fixos'
            current_result['main_category_name'] = '📊 Custos Fixos'
            current_result['subcategory'] = 'impostos_taxas'
            current_result['subcategory_name'] = '💸 Impostos e Taxas'
        
        # Personnel patterns not caught by keywords
        personnel_patterns = ['folha', 'rh', 'recursos humanos', 'departamento pessoal']
        if any(pattern in item_text for pattern in personnel_patterns):
            current_result['main_category'] = 'custos_fixos'
            current_result['main_category_name'] = '📊 Custos Fixos'
            current_result['subcategory'] = 'pessoal'
            current_result['subcategory_name'] = '👥 Pessoal'
        
        return current_result
    
    @classmethod
    def _classify_by_source_category(cls, source_category: str, label: str) -> Dict[str, str]:
        """
        Classify expense based on source category when automatic classification fails
        """
        category_mapping = {
            'taxes': {
                'main_category': 'custos_fixos',
                'main_category_name': '📊 Custos Fixos',
                'subcategory': 'impostos_taxas',
                'subcategory_name': '💸 Impostos e Taxas'
            },
            'commissions': {
                'main_category': 'custos_variaveis',
                'main_category_name': '📈 Custos Variáveis',
                'subcategory': 'comissoes',
                'subcategory_name': '💼 Comissões e Repasses'
            },
            'administrative_expenses': {
                'main_category': 'custos_fixos',
                'main_category_name': '📊 Custos Fixos',
                'subcategory': 'administrativas',
                'subcategory_name': '📋 Despesas Administrativas'
            },
            'operational_costs': {
                'main_category': 'custos_fixos',
                'main_category_name': '📊 Custos Fixos',
                'subcategory': 'administrativas',
                'subcategory_name': '📋 Despesas Administrativas'
            },
            'marketing_expenses': {
                'main_category': 'custos_variaveis',
                'main_category_name': '📈 Custos Variáveis',
                'subcategory': 'marketing_vendas',
                'subcategory_name': '📢 Marketing e Vendas'
            },
            'financial_expenses': {
                'main_category': 'custos_fixos',
                'main_category_name': '📊 Custos Fixos',
                'subcategory': 'financeiras',
                'subcategory_name': '💰 Despesas Financeiras'
            },
            'non_operational_costs': {
                'main_category': 'custos_nao_operacionais',
                'main_category_name': '🔴 Custos Não Operacionais',
                'subcategory': 'extraordinarias',
                'subcategory_name': '⚡ Extraordinárias'
            },
            'fixed_costs': {
                'main_category': 'custos_fixos',
                'main_category_name': '📊 Custos Fixos',
                'subcategory': 'administrativas',
                'subcategory_name': '📋 Despesas Administrativas'
            },
            'variable_costs': {
                'main_category': 'custos_variaveis',
                'main_category_name': '📈 Custos Variáveis',
                'subcategory': 'custos_producao',
                'subcategory_name': '🏭 Custos de Produção'
            }
        }
        
        # Default to source category mapping
        if source_category in category_mapping:
            return category_mapping[source_category]
        
        # Fallback
        return {
            'main_category': 'custos_nao_operacionais',
            'main_category_name': '🔴 Custos Não Operacionais',
            'subcategory': 'extraordinarias',
            'subcategory_name': '⚡ Extraordinárias'
        }
    
    @classmethod
    def get_hierarchy_path(cls, item_data: Dict[str, str]) -> List[str]:
        """
        Get the full hierarchy path for an item
        
        Args:
            item_data: Parsed item data from parse_expense_item
            
        Returns:
            List representing the hierarchy path
        """
        path = []
        
        if item_data.get('main_category_name'):
            path.append(item_data['main_category_name'])
        
        if item_data.get('subcategory_name'):
            path.append(item_data['subcategory_name'])
        
        if item_data.get('detail_category'):
            path.append(item_data['detail_category'].title())
        
        if item_data.get('item_name'):
            path.append(item_data['item_name'])
        
        return path
    
    @classmethod
    def aggregate_by_level(cls, expenses: List[Dict], level: int = 1) -> Dict[str, Dict]:
        """
        Aggregate expenses by hierarchy level
        
        Args:
            expenses: List of expense dictionaries with 'label' and 'value' keys
            level: Hierarchy level to aggregate by (1-4)
            
        Returns:
            Dictionary with aggregated data by the specified level
        """
        aggregated = {}
        
        for expense in expenses:
            parsed = cls.parse_expense_item(expense.get('label', ''))
            value = expense.get('value', 0)
            
            # Determine the key based on level
            if level == 1:
                key = parsed['main_category']
                name = parsed['main_category_name']
            elif level == 2:
                key = f"{parsed['main_category']}.{parsed['subcategory']}"
                name = parsed['subcategory_name']
            elif level == 3 and parsed['detail_category']:
                key = f"{parsed['main_category']}.{parsed['subcategory']}.{parsed['detail_category']}"
                name = parsed['detail_category'].title()
            else:
                key = expense.get('label', 'Unknown')
                name = key
            
            if key not in aggregated:
                aggregated[key] = {
                    'name': name,
                    'value': 0,
                    'items': [],
                    'count': 0
                }
            
            aggregated[key]['value'] += value
            aggregated[key]['items'].append(expense)
            aggregated[key]['count'] += 1
        
        return aggregated
    
    @classmethod
    def get_insights(cls, expenses: List[Dict]) -> Dict[str, any]:
        """
        Generate insights from expense data
        
        Args:
            expenses: List of expense dictionaries
            
        Returns:
            Dictionary with various insights
        """
        insights = {
            'total_expenses': sum(e.get('value', 0) for e in expenses),
            'expense_count': len(expenses),
            'top_categories': {},
            'uncategorized_items': [],
            'distribution': {}
        }
        
        # Aggregate by main category
        level1_agg = cls.aggregate_by_level(expenses, level=1)
        
        # Calculate distribution
        total = insights['total_expenses']
        for key, data in level1_agg.items():
            percentage = (data['value'] / total * 100) if total > 0 else 0
            insights['distribution'][data['name']] = {
                'value': data['value'],
                'percentage': percentage,
                'item_count': data['count']
            }
        
        # Find top categories
        sorted_categories = sorted(
            level1_agg.items(),
            key=lambda x: x[1]['value'],
            reverse=True
        )
        insights['top_categories'] = {
            k: v for k, v in sorted_categories[:5]
        }
        
        # Find uncategorized items
        for expense in expenses:
            parsed = cls.parse_expense_item(expense.get('label', ''))
            if parsed['main_category'] == 'despesas_nao_operacionais' and \
               parsed['subcategory'] == 'extraordinarias':
                insights['uncategorized_items'].append(expense)
        
        return insights