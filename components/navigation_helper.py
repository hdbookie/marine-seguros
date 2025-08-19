"""
Navigation Helper Component
Provides seamless navigation between macro and micro views with context preservation
"""

import streamlit as st
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class NavigationContext:
    """Context information for navigation between views"""
    current_view: str
    section: str = "Todos"
    selected_years: list = None
    chart_type: str = "side_by_side"
    comparison_mode: bool = True
    drill_down_path: list = None


class NavigationManager:
    """Manages navigation state and context between different analysis views"""
    
    def __init__(self):
        self.session_key = "navigation_context"
        self._initialize_context()
    
    def _initialize_context(self):
        """Initialize navigation context if not exists"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = NavigationContext(
                current_view="📊 Visão Macro (Resumo Executivo)",
                selected_years=[],
                drill_down_path=[]
            )
    
    def get_context(self) -> NavigationContext:
        """Get current navigation context"""
        self._initialize_context()  # Ensure context exists
        return st.session_state[self.session_key]
    
    def update_context(self, **kwargs):
        """Update navigation context with new values"""
        context = self.get_context()
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
        st.session_state[self.session_key] = context
    
    def navigate_to_view(self, view: str, **context_updates):
        """Navigate to a specific view with context preservation"""
        self.update_context(current_view=view, **context_updates)
        
        # Update the enhanced dashboard view mode
        view_mapping = {
            "macro": "📊 Visão Macro (Resumo Executivo)",
            "micro": "🔬 Visão Micro (Análise Detalhada)",
            "integrated": "🔄 Visão Integrada (Macro + Micro)"
        }
        
        if view in view_mapping:
            st.session_state["enhanced_view_mode"] = view_mapping[view]
        
        # Update other session state keys if needed
        for key, value in context_updates.items():
            if key == "section":
                st.session_state["drill_down_section"] = value
    
    def add_breadcrumb(self, level: str, section: str = None):
        """Add a breadcrumb to the navigation path"""
        context = self.get_context()
        if context.drill_down_path is None:
            context.drill_down_path = []
        
        breadcrumb = {"level": level}
        if section:
            breadcrumb["section"] = section
        
        context.drill_down_path.append(breadcrumb)
        st.session_state[self.session_key] = context
    
    def clear_breadcrumbs(self):
        """Clear all breadcrumbs"""
        context = self.get_context()
        context.drill_down_path = []
        st.session_state[self.session_key] = context
    
    def render_navigation_bar(self):
        """Render navigation bar with quick access buttons"""
        st.markdown("### 🧭 Navegação Rápida")
        
        context = self.get_context()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🏠 Dashboard Macro", key="nav_macro_btn"):
                self.navigate_to_view("macro")
                st.rerun()
        
        with col2:
            if st.button("🔬 Análise Micro", key="nav_micro_btn"):
                self.navigate_to_view("micro")
                st.rerun()
        
        with col3:
            if st.button("🔄 Visão Integrada", key="nav_integrated_btn"):
                self.navigate_to_view("integrated")
                st.rerun()
        
        with col4:
            if context.current_view != "📊 Visão Macro (Resumo Executivo)":
                if st.button("⬅️ Voltar", key="nav_back_btn"):
                    self.navigate_to_view("macro")
                    st.rerun()
    
    def render_section_navigator(self):
        """Render section-specific navigation"""
        context = self.get_context()
        
        if context.current_view == "🔄 Visão Integrada (Macro + Micro)":
            st.markdown("#### 🎯 Navegação por Seção")
            
            sections = [
                "CUSTOS FIXOS", 
                "CUSTOS VARIÁVEIS", 
                "CUSTOS NÃO OPERACIONAIS",
                "RECEITA"
            ]
            
            cols = st.columns(len(sections))
            
            for i, section in enumerate(sections):
                with cols[i]:
                    button_type = "primary" if context.section == section else "secondary"
                    if st.button(
                        f"📊 {section}", 
                        key=f"nav_section_{section.replace(' ', '_')}",
                        type=button_type
                    ):
                        self.navigate_to_view("integrated", section=section)
                        st.rerun()
    
    def render_breadcrumb_trail(self):
        """Render breadcrumb trail"""
        context = self.get_context()
        
        if context.drill_down_path:
            breadcrumbs = ["🏠 Dashboard"]
            
            for breadcrumb in context.drill_down_path:
                level = breadcrumb.get("level", "")
                section = breadcrumb.get("section", "")
                if section:
                    breadcrumbs.append(f"{level} → {section}")
                else:
                    breadcrumbs.append(level)
            
            st.markdown(f"**📍 Localização:** {' → '.join(breadcrumbs)}")
    
    def create_drill_down_button(
        self, 
        section: str, 
        label: str = None, 
        target_view: str = "integrated",
        key_suffix: str = "",
        **kwargs
    ):
        """Create a drill-down button that preserves context"""
        if label is None:
            label = f"🔍 Analisar {section}"
        
        button_key = f"drill_down_{section.replace(' ', '_').lower()}{key_suffix}"
        
        if st.button(label, key=button_key, **kwargs):
            self.navigate_to_view(target_view, section=section)
            self.add_breadcrumb("Drill-down", section)
            st.rerun()
            return True
        return False
    
    def create_comparison_controls(self):
        """Create comparison controls with context preservation"""
        context = self.get_context()
        
        col1, col2 = st.columns(2)
        
        with col1:
            comparison_mode = st.checkbox(
                "📈 Modo Comparação",
                value=context.comparison_mode,
                key="nav_comparison_mode"
            )
            
            if comparison_mode != context.comparison_mode:
                self.update_context(comparison_mode=comparison_mode)
        
        with col2:
            chart_types = {
                "side_by_side": "📊 Lado a Lado",
                "stacked": "📚 Empilhado",
                "waterfall": "🌊 Waterfall"
            }
            
            chart_type = st.selectbox(
                "Tipo de Gráfico",
                list(chart_types.keys()),
                format_func=lambda x: chart_types[x],
                index=list(chart_types.keys()).index(context.chart_type),
                key="nav_chart_type"
            )
            
            if chart_type != context.chart_type:
                self.update_context(chart_type=chart_type)
        
        return comparison_mode, chart_type
    
    def create_contextual_help(self):
        """Create contextual help based on current view"""
        context = self.get_context()
        
        help_content = {
            "📊 Visão Macro (Resumo Executivo)": {
                "title": "💡 Ajuda - Visão Macro",
                "content": """
                **Visão Macro** oferece uma perspectiva de alto nível dos seus dados financeiros:
                
                • **📊 Gráficos Resumo**: Visualize tendências anuais e comparações
                • **🔍 Drill-down**: Clique nos botões de análise para detalhamento
                • **📈 KPIs**: Métricas principais em destaque
                • **⚡ Navegação**: Use os botões para alternar entre visões
                """
            },
            "🔬 Visão Micro (Análise Detalhada)": {
                "title": "💡 Ajuda - Visão Micro",
                "content": """
                **Visão Micro** permite análise granular dos seus dados:
                
                • **🌳 Seletor em Árvore**: Navegue pela hierarquia de despesas
                • **📊 Comparação Multi-ano**: Compare itens específicos entre anos
                • **📅 Análise Mensal**: Veja variações mês a mês
                • **🔍 Filtros Avançados**: Personalize sua análise
                """
            },
            "🔄 Visão Integrada (Macro + Micro)": {
                "title": "💡 Ajuda - Visão Integrada",
                "content": """
                **Visão Integrada** combina o melhor dos dois mundos:
                
                • **📊 Comparação Unificada**: Macro e micro lado a lado
                • **🎯 Foco por Seção**: Analise seções específicas
                • **📈 Insights Automáticos**: Insights gerados automaticamente
                • **🔄 Navegação Fluida**: Alterne facilmente entre níveis
                """
            }
        }
        
        current_help = help_content.get(context.current_view)
        
        if current_help:
            with st.expander(current_help["title"], expanded=False):
                st.markdown(current_help["content"])


# Global navigation manager instance
nav_manager = NavigationManager()


def get_navigation_manager() -> NavigationManager:
    """Get the global navigation manager instance"""
    return nav_manager


def render_enhanced_navigation():
    """Render enhanced navigation components"""
    nav = get_navigation_manager()
    
    # Render breadcrumb trail
    nav.render_breadcrumb_trail()
    
    # Render navigation bar
    nav.render_navigation_bar()
    
    # Render section navigator if in integrated view
    nav.render_section_navigator()
    
    # Render contextual help
    nav.create_contextual_help()