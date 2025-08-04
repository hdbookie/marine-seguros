"""
Graph modules for Micro Analysis
"""

from .pnl_evolution import render_pnl_evolution
from .cost_structure import render_cost_structure
from .group_analysis import render_group_evolution, render_group_comparison, render_margin_impact
from .margin_analysis import render_margin_analysis
from .financial_notes import render_financial_notes
from .interactive_cost_breakdown import render_interactive_cost_breakdown

__all__ = [
    'render_pnl_evolution',
    'render_cost_structure', 
    'render_group_evolution',
    'render_group_comparison',
    'render_margin_impact',
    'render_margin_analysis',
    'render_financial_notes',
    'render_interactive_cost_breakdown'
]