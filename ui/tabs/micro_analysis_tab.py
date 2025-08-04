"""Micro Analysis Tab - Bridge to new modular structure"""

# Import the new modular implementation
from .micro_analysis.tab_renderer import render_micro_analysis_tab

# Export for backward compatibility
__all__ = ['render_micro_analysis_tab']