"""
Legacy helper functions extracted from app.py
Preserves all original functionality while organizing code
"""

import streamlit as st
import pandas as pd
from core.financial_processor import FinancialProcessor
from gerenciador_arquivos import GerenciadorArquivos


# Helper functions for data conversion (must be defined before use)
def convert_extracted_to_processed(extracted_data):
    """Convert extracted_data format (from database) to processed_data format (for app)"""
    if not extracted_data:
        return None
    
    print(f"DEBUG convert_extracted_to_processed: Processing {len(extracted_data)} years")
    
    try:
        # Create a DataFrame from extracted_data
        consolidated_data = []
        for year, year_data in sorted(extracted_data.items()):
            print(f"DEBUG: Processing year {year}")
            if year == list(extracted_data.keys())[0]:  # First year only
                print(f"  Keys in year_data: {list(year_data.keys())}")
            
            # Handle different data formats
            revenue_data = year_data.get('revenue', {})
            if isinstance(revenue_data, dict):
                # Try lowercase 'annual' first (unified extractor format)
                revenue = revenue_data.get('annual', revenue_data.get('ANNUAL', 0))
                if year == list(extracted_data.keys())[0]:  # First year only
                    print(f"  Revenue data type: {type(revenue_data)}")
                    print(f"  Revenue keys: {list(revenue_data.keys()) if isinstance(revenue_data, dict) else 'Not a dict'}")
                    print(f"  Revenue annual value: {revenue}")
            else:
                revenue = revenue_data if revenue_data else 0
                
            costs_data = year_data.get('costs', year_data.get('variable_costs', {}))
            if isinstance(costs_data, dict):
                costs = costs_data.get('annual', costs_data.get('ANNUAL', 0))
            else:
                costs = costs_data if costs_data else 0
            
            # Get expenses - handle both formats
            def get_expense_value(expense_key):
                expense_data = year_data.get(expense_key, {})
                if isinstance(expense_data, dict):
                    return expense_data.get('annual', expense_data.get('ANNUAL', 0))
                return expense_data if expense_data else 0
            
            admin_expenses = get_expense_value('admin_expenses') or get_expense_value('administrative_expenses')
            operational_expenses = get_expense_value('operational_expenses')
            marketing_expenses = get_expense_value('marketing_expenses')
            financial_expenses = get_expense_value('financial_expenses')
            
            # Get fixed costs directly from Excel (CUSTOS FIXOS line)
            fixed_costs_data = year_data.get('fixed_costs', {})
            if isinstance(fixed_costs_data, dict):
                fixed_costs = fixed_costs_data.get('annual', fixed_costs_data.get('ANNUAL', 0))
            else:
                fixed_costs = fixed_costs_data if fixed_costs_data else 0
            
            # If no direct fixed costs data, calculate as sum of expenses (fallback)
            if fixed_costs == 0:
                fixed_costs = admin_expenses + operational_expenses + marketing_expenses + financial_expenses
            
            # Calculate operational costs
            operational_costs_data = year_data.get('operational_costs', {})
            if isinstance(operational_costs_data, dict):
                operational_costs = operational_costs_data.get('annual', operational_costs_data.get('ANNUAL', 0))
            else:
                operational_costs = operational_costs_data if operational_costs_data else 0
                
            if operational_costs == 0:
                operational_costs = admin_expenses + operational_expenses
            
            # Calculate all required fields
            total_costs = costs + fixed_costs
            net_profit = revenue - total_costs
            profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0
            gross_profit = revenue - costs
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
            contribution_margin = revenue - costs
            
            consolidated_data.append({
                'year': int(year),
                'revenue': revenue,
                'variable_costs': costs,
                'fixed_costs': fixed_costs,
                'admin_expenses': admin_expenses,
                'operational_expenses': operational_expenses,
                'marketing_expenses': marketing_expenses,
                'financial_expenses': financial_expenses,
                'operational_costs': operational_costs,
                'total_costs': total_costs,
                'net_profit': net_profit,
                'profit': net_profit,
                'profit_margin': profit_margin,
                'gross_profit': gross_profit,
                'gross_margin': gross_margin,
                'contribution_margin': contribution_margin
            })
        
        if consolidated_data:
            consolidated_df = pd.DataFrame(consolidated_data)
            
            # Calculate growth metrics
            processor = FinancialProcessor()
            consolidated_df = processor.calculate_growth_metrics(consolidated_df)
            
            return {
                'raw_data': extracted_data,
                'consolidated': consolidated_df,
                'summary': processor.get_financial_summary(consolidated_df),
                'anomalies': []
            }
    except Exception as e:
        print(f"Error converting data: {e}")
        return None


def sync_processed_to_extracted():
    """Sync processed_data to extracted_data format for database saving"""
    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data and 'raw_data' in st.session_state.processed_data:
        # If we have raw_data, it's already in extracted format with all monthly data
        st.session_state.extracted_data = st.session_state.processed_data['raw_data']
    elif hasattr(st.session_state, 'processed_data') and st.session_state.processed_data and 'consolidated' in st.session_state.processed_data:
        # If we don't have raw_data, but we have monthly_data, use that
        if (hasattr(st.session_state, 'monthly_data') and 
            st.session_state.monthly_data is not None and
            isinstance(st.session_state.monthly_data, pd.DataFrame) and
            not st.session_state.monthly_data.empty and
            'year' in st.session_state.monthly_data.columns):
            extracted = {}
            monthly_df = st.session_state.monthly_data
            
            # Group by year and rebuild the extracted format with monthly data
            for year in monthly_df['year'].unique():
                year_data = monthly_df[monthly_df['year'] == year]
                revenue_dict = {}
                costs_dict = {}
                
                # Add monthly data
                for _, row in year_data.iterrows():
                    month = row['month']
                    revenue_dict[month] = row.get('revenue', 0)
                    # Handle both 'costs' and 'variable_costs' columns
                    if 'variable_costs' in row:
                        costs_dict[month] = row.get('variable_costs', 0)
                    else:
                        costs_dict[month] = row.get('costs', 0)
                
                # Add annual totals
                revenue_dict['ANNUAL'] = sum(v for k, v in revenue_dict.items() if k != 'ANNUAL')
                costs_dict['ANNUAL'] = sum(v for k, v in costs_dict.items() if k != 'ANNUAL')
                
                extracted[str(year)] = {
                    'revenue': revenue_dict,
                    'costs': costs_dict,
                    'year': int(year)
                }
            
            st.session_state.extracted_data = extracted
        else:
            # Fallback: only ANNUAL data available
            extracted = {}
            df = st.session_state.processed_data.get('consolidated', pd.DataFrame())
            
            # Ensure df is a DataFrame before iterating
            if isinstance(df, pd.DataFrame) and not df.empty:
                for _, row in df.iterrows():
                    year = str(int(row['year']))
                    extracted[year] = {
                        'revenue': {'ANNUAL': row.get('revenue', 0)},
                        'costs': {'ANNUAL': row.get('variable_costs', 0)},
                        'fixed_costs': row.get('fixed_costs', 0),
                        'operational_costs': row.get('operational_costs', 0),
                        'year': int(year)
                    }
            
            st.session_state.extracted_data = extracted


def format_currency(value):
    """Format value as Brazilian currency"""
    if abs(value) >= 1_000_000:
        # For millions, show 1 decimal place and 'M' suffix
        return f"R$ {value/1_000_000:,.1f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    elif abs(value) >= 1_000:
        # For thousands, show as full number with thousands separator
        return f"R$ {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        # For smaller amounts, show 2 decimal places
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def get_expense_subcategories():
    """Define detailed expense subcategories for better organization"""
    return {
        'pessoal': {
            'name': '👥 Pessoal',
            'subcategories': {
                'salarios': {
                    'name': 'Salários e Ordenados',
                    'patterns': ['salario', 'salário', 'ordenado', 'remuneracao', 'remuneração', 'folha de pagamento', 'holerite']
                },
                'beneficios': {
                    'name': 'Benefícios',
                    'patterns': ['vale transporte', 'vale-transporte', 'vt', 'vale refeicao', 'vale refeição', 'vale alimentacao', 'vale alimentação', 'va', 'vr']
                },
                'encargos': {
                    'name': 'Encargos Sociais',
                    'patterns': ['inss', 'fgts', 'encargo', 'previdencia', 'previdência', 'contribuicao social', 'contribuição social']
                },
                'provisoes': {
                    'name': 'Provisões',
                    'patterns': ['ferias', 'férias', '13o', '13º', 'decimo terceiro', 'décimo terceiro', 'provisao', 'provisão']
                }
            }
        },
        'ocupacao': {
            'name': '🏢 Ocupação e Utilidades',
            'subcategories': {
                'aluguel': {
                    'name': 'Aluguel e Condomínio',
                    'patterns': ['aluguel', 'locacao', 'locação', 'condominio', 'condomínio', 'iptu', 'taxa condominial']
                },
                'energia': {
                    'name': 'Energia Elétrica',
                    'patterns': ['energia', 'eletrica', 'elétrica', 'luz', 'cemig', 'light', 'cpfl', 'coelba', 'celesc']
                },
                'agua': {
                    'name': 'Água e Esgoto',
                    'patterns': ['agua', 'água', 'esgoto', 'saneamento', 'sabesp', 'copasa', 'cedae', 'cagece']
                },
                'telecom': {
                    'name': 'Telecomunicações',
                    'patterns': ['telefone', 'internet', 'telefonia', 'celular', 'vivo', 'claro', 'tim', 'oi', 'net']
                }
            }
        },
        'servicos': {
            'name': '💼 Serviços Profissionais',
            'subcategories': {
                'contabilidade': {
                    'name': 'Contabilidade',
                    'patterns': ['contabilidade', 'contador', 'contabil', 'contábil', 'escritorio contabil', 'escritório contábil']
                },
                'juridico': {
                    'name': 'Jurídico',
                    'patterns': ['advocacia', 'advogado', 'juridico', 'jurídico', 'honorario', 'honorário', 'judicial']
                },
                'consultoria': {
                    'name': 'Consultoria',
                    'patterns': ['consultoria', 'consultor', 'assessoria', 'treinamento', 'capacitacao', 'capacitação']
                },
                'ti': {
                    'name': 'TI e Software',
                    'patterns': ['software', 'sistema', 'ti', 'informatica', 'informática', 'licenca', 'licença', 'assinatura', 'cloud', 'nuvem']
                }
            }
        },
        'manutencao': {
            'name': '🔧 Manutenção e Conservação',
            'subcategories': {
                'limpeza': {
                    'name': 'Limpeza',
                    'patterns': ['limpeza', 'higienizacao', 'higienização', 'faxina', 'jardinagem', 'conservacao', 'conservação']
                },
                'predial': {
                    'name': 'Manutenção Predial',
                    'patterns': ['manutencao predial', 'manutenção predial', 'reforma', 'pintura', 'obra', 'reparo', 'conserto']
                },
                'equipamentos': {
                    'name': 'Manutenção de Equipamentos',
                    'patterns': ['manutencao equipamento', 'manutenção equipamento', 'assistencia tecnica', 'assistência técnica', 'reparo equipamento']
                }
            }
        },
        'material': {
            'name': '📦 Material de Consumo',
            'subcategories': {
                'escritorio': {
                    'name': 'Material de Escritório',
                    'patterns': ['material escritorio', 'material escritório', 'papelaria', 'papel', 'caneta', 'toner', 'cartucho']
                },
                'limpeza_material': {
                    'name': 'Material de Limpeza',
                    'patterns': ['material limpeza', 'produto limpeza', 'detergente', 'desinfetante', 'papel higienico', 'papel higiênico']
                },
                'combustivel': {
                    'name': 'Combustíveis',
                    'patterns': ['combustivel', 'combustível', 'gasolina', 'alcool', 'álcool', 'diesel', 'posto', 'abastecimento']
                }
            }
        }
    }


def classify_expense_subcategory(description):
    """Classify an expense into a subcategory based on its description"""
    description_lower = description.lower()
    subcategories = get_expense_subcategories()
    
    for main_cat, main_data in subcategories.items():
        for sub_cat, sub_data in main_data['subcategories'].items():
            for pattern in sub_data['patterns']:
                if pattern in description_lower:
                    return {
                        'main_category': main_cat,
                        'main_category_name': main_data['name'],
                        'subcategory': sub_cat,
                        'subcategory_name': sub_data['name']
                    }
    
    # Default to uncategorized
    return {
        'main_category': 'outros',
        'main_category_name': '📌 Outros',
        'subcategory': 'nao_categorizado',
        'subcategory_name': 'Não Categorizado'
    }


def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100


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
    return names.get(category, category.title())


def prepare_x_axis(df, view_type):
    """Prepare x-axis column and title based on view type"""
    if view_type == "Anual":
        return 'year', 'Ano'
    elif view_type == "Mensal":
        # Check if we actually have monthly data (with 'month' column)
        if 'month' in df.columns:
            if 'period' not in df.columns:
                # Create more readable period format
                month_abbr = {
                    'JAN': 'Jan', 'FEV': 'Fev', 'MAR': 'Mar', 'ABR': 'Abr',
                    'MAI': 'Mai', 'JUN': 'Jun', 'JUL': 'Jul', 'AGO': 'Ago',
                    'SET': 'Set', 'OUT': 'Out', 'NOV': 'Nov', 'DEZ': 'Dez'
                }
                df['period'] = df.apply(lambda x: f"{month_abbr.get(x['month'], x['month'])}/{str(int(x['year']))[-2:]}", axis=1)
            return 'period', 'Período'
        else:
            # Fallback to annual view when monthly data is not available
            return 'year', 'Ano'
    elif view_type in ["Trimestral", "Trimestre Personalizado", "Semestral"]:
        return 'period', 'Período'
    else:
        return 'year', 'Ano'


def get_monthly_layout_config():
    """Get layout configuration for monthly interactive graphs"""
    return dict(
        rangeslider=dict(visible=True, thickness=0.1),
        rangeselector=dict(
            buttons=list([
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=12, label="12M", step="month", stepmode="backward"),
                dict(count=24, label="24M", step="month", stepmode="backward"),
                dict(step="all", label="Tudo")
            ]),
            x=0, y=1.15
        ),
        # Set default range to show last 12 months for better readability
        range=None  # Will be set dynamically in each graph
    )


def process_detailed_monthly_data(flexible_data):
    """Process flexible data to extract detailed monthly line items for analysis"""
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
                'FATURAMENTO', 'CUSTOS VARIÁVEIS', 'CUSTOS FIXOS', 
                'CUSTOS NÃO OPERACIONAIS', 'MARGEM DE CONTRIBUIÇÃO',
                'RESULTADO', 'PONTO EQUILIBRIO', 'PONTO EQUILÍBRIO',
                'LUCRO', 'LUCRO LÍQUIDO', 'MARGEM DE LUCRO', 'TOTAL DESPESAS',
                'COMPOSIÇÃO DE SALDOS', 'APLICAÇÕES', 'RETIRADA',
                'DESPESAS - TOTAL', 'CUSTO FIXO + VARIAVEL',
                'CUSTOS FIXOS + VARIÁVEIS', 'CUSTOS VARIÁVEIS + FIXOS',
                'CUSTOS FIXOS + VARIÁVEIS + NÃO OPERACIONAIS',
                'TOTAL CUSTOS', 'CUSTO TOTAL', 'TOTAL GERAL',
                'DESPESA TOTAL', 'TOTAL DE CUSTOS', 'TOTAL DE DESPESAS',
                'SUBTOTAL', 'SUB TOTAL', 'SUB-TOTAL'
            ]
            if any(pattern in label_upper for pattern in skip_patterns):
                continue
            
            # Skip if label contains mathematical operators (likely a calculation)
            if any(op in label for op in ['+', '=', ' - ', '(', ')']):
                continue
            
            # Skip if it's ALL CAPS (likely a header) but not a known abbreviation
            exceptions = ['IRRF', 'INSS', 'FGTS', 'IPTU', 'IPVA', 'ISS', 'PIS', 'COFINS']
            if label_upper == label.strip() and len(label.strip()) > 3 and label_upper not in exceptions:
                continue
            
            # Skip if annual value is suspiciously high (likely a total/sum)
            # Most individual expense line items should be under 500k annually
            if annual_value > 500000:
                # Only allow high-value items if they're clearly individual expenses
                allowed_high_value = ['salário', 'folha', 'aluguel', 'energia', 'comissão']
                if not any(term in label.lower() for term in allowed_high_value):
                    continue
            
            detailed_data['summary']['total_categories'].add(category)
            detailed_data['summary']['total_items'] += 1
            
            # Classify into subcategory
            subcategory_info = classify_expense_subcategory(label)
            
            # Create detailed record
            record = {
                'ano': year,
                'categoria': category,
                'subcategoria_principal': subcategory_info['main_category'],
                'subcategoria_principal_nome': subcategory_info['main_category_name'],
                'subcategoria': subcategory_info['subcategory'],
                'subcategoria_nome': subcategory_info['subcategory_name'],
                'descricao': label,
                'valor_anual': annual_value,
                'valores_mensais': monthly_values,
                'key': item_key
            }
            
            detailed_data['line_items'].append(record)
            detailed_data['por_ano'][year].append(record)
            
            # Group by category
            if category not in detailed_data['por_categoria']:
                detailed_data['por_categoria'][category] = []
            detailed_data['por_categoria'][category].append(record)
            
            # Group by subcategory
            subcat_key = f"{subcategory_info['main_category']}_{subcategory_info['subcategory']}"
            if subcat_key not in detailed_data['por_subcategoria']:
                detailed_data['por_subcategoria'][subcat_key] = {
                    'nome': f"{subcategory_info['main_category_name']} - {subcategory_info['subcategory_name']}",
                    'items': []
                }
            detailed_data['por_subcategoria'][subcat_key]['items'].append(record)
            detailed_data['summary']['total_subcategories'].add(subcat_key)
            
            # Group by month
            for month, value in monthly_values.items():
                if month not in detailed_data['por_mes']:
                    detailed_data['por_mes'][month] = []
                
                detailed_data['por_mes'][month].append({
                    'ano': year,
                    'categoria': category,
                    'descricao': label,
                    'valor': value
                })
    
    return detailed_data


def get_plotly_config():
    """Get Plotly configuration for interactive graphs"""
    return {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToAdd': ['pan2d', 'zoom2d', 'resetScale2d'],
        'scrollZoom': True
    }


def get_default_monthly_range(df, x_col, months=12):
    """Calculate default range for monthly graphs to show last N months"""
    if len(df) > months:
        return [df[x_col].iloc[-months], df[x_col].iloc[-1]]
    return None


def initialize_session_state(db, data_loaded):
    """Initialize session state variables"""
    if 'file_manager' not in st.session_state:
        st.session_state.file_manager = GerenciadorArquivos()
        # Sincronizar arquivos existentes
        st.session_state.file_manager.sincronizar_arquivos_existentes()
    if 'ai_chat_assistant' not in st.session_state:
        st.session_state.ai_chat_assistant = None

    # Only initialize empty defaults if nothing was loaded from database
    if not data_loaded:
        if 'processed_data' not in st.session_state:
            st.session_state.processed_data = None
        if 'gemini_insights' not in st.session_state:
            st.session_state.gemini_insights = None
        if 'flexible_data' not in st.session_state:
            st.session_state.flexible_data = None
        if 'monthly_data' not in st.session_state:
            st.session_state.monthly_data = None
        if 'extracted_data' not in st.session_state:
            st.session_state.extracted_data = {}
        if 'financial_data' not in st.session_state:
            st.session_state.financial_data = None
        # Don't initialize selected_years and selected_months here
        # Let auto_load_state handle it to preserve saved filter states


def generate_monthly_data_from_extracted(extracted_data):
    """Generate monthly DataFrame from extracted data"""
    try:
        # Create monthly DataFrame from extracted data with ALL required fields
        monthly_data = []
        for year, year_data in extracted_data.items():
            revenue_data = year_data.get('revenue', {})
            costs_data = year_data.get('costs', {})
            admin_data = year_data.get('admin_expenses', {})
            operational_data = year_data.get('operational_expenses', {})
            marketing_data = year_data.get('marketing_expenses', {})
            financial_data = year_data.get('financial_expenses', {})
            fixed_costs_data = year_data.get('fixed_costs', {})
            
            for month in ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']:
                if month in revenue_data:
                    revenue = revenue_data.get(month, 0)
                    variable_costs = costs_data.get(month, 0)
                    
                    # Get fixed costs directly from Excel data
                    fixed_costs = fixed_costs_data.get(month, 0)
                    
                    # If no direct fixed costs data, calculate as sum of expenses (fallback)
                    if fixed_costs == 0:
                        fixed_costs = (
                            admin_data.get(month, 0) + 
                            operational_data.get(month, 0) + 
                            marketing_data.get(month, 0) + 
                            financial_data.get(month, 0)
                        )
                    
                    # Calculate operational costs (admin + operational)
                    operational_costs = admin_data.get(month, 0) + operational_data.get(month, 0)
                    
                    # Calculate profit and margins
                    total_costs = variable_costs + fixed_costs
                    net_profit = revenue - total_costs
                    profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0
                    contribution_margin = revenue - variable_costs
                    
                    monthly_data.append({
                        'year': int(year),
                        'month': month,
                        'revenue': revenue,
                        'variable_costs': variable_costs,
                        'fixed_costs': fixed_costs,
                        'admin_expenses': admin_data.get(month, 0),
                        'operational_expenses': operational_data.get(month, 0),
                        'marketing_expenses': marketing_data.get(month, 0),
                        'financial_expenses': financial_data.get(month, 0),
                        'total_costs': total_costs,
                        'operational_costs': operational_costs,
                        'net_profit': net_profit,
                        'profit_margin': profit_margin,
                        'contribution_margin': contribution_margin
                    })
        
        if monthly_data:
            return pd.DataFrame(monthly_data)
    except Exception as e:
        print(f"Error generating monthly data: {e}")
        import traceback
        traceback.print_exc()
    
    return None