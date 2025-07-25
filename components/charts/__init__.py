"""
Chart components for Marine Seguros dashboard
"""

from .receita_chart import create_receita_chart
from .custos_variaveis_chart import create_custos_variaveis_chart
from .custos_fixos_chart import create_custos_fixos_chart
from .resultado_chart import create_resultado_chart
from .margem_contribuicao_chart import create_margem_contribuicao_chart
from .despesas_operacionais_chart import create_despesas_operacionais_chart
from .indicadores import create_kpi_indicators

__all__ = [
    'create_receita_chart',
    'create_custos_variaveis_chart', 
    'create_custos_fixos_chart',
    'create_resultado_chart',
    'create_margem_contribuicao_chart',
    'create_despesas_operacionais_chart',
    'create_kpi_indicators'
]