import streamlit as st
from typing import Dict, List, Optional
import time

class GuidedTour:
    """Interactive guided tour for first-time users"""
    
    def __init__(self):
        if 'tour_completed' not in st.session_state:
            st.session_state.tour_completed = False
        if 'tour_step' not in st.session_state:
            st.session_state.tour_step = 0
        if 'show_tour' not in st.session_state:
            st.session_state.show_tour = not st.session_state.tour_completed
        
        self.tour_steps = [
            {
                'element': 'welcome',
                'title': '👋 Welcome to Marine Seguros Analytics',
                'content': 'Let me show you around this powerful analytics platform!',
                'position': 'center',
                'highlight': None
            },
            {
                'element': 'data_upload',
                'title': '📁 Start with Your Data',
                'content': 'Upload Excel files here or use our sample data to explore.',
                'position': 'top',
                'highlight': 'upload_area'
            },
            {
                'element': 'dashboard',
                'title': '📊 Your Dashboard',
                'content': 'See key metrics and trends at a glance with interactive charts.',
                'position': 'top',
                'highlight': 'kpi_section'
            },
            {
                'element': 'filters',
                'title': '🎯 Smart Filters',
                'content': 'Click here to filter by year, month, or specific metrics.',
                'position': 'bottom',
                'highlight': 'filter_bar'
            },
            {
                'element': 'ai_chat',
                'title': '💬 AI Assistant',
                'content': 'Ask any question about your data in natural language!',
                'position': 'right',
                'highlight': 'chat_button'
            },
            {
                'element': 'insights',
                'title': '💡 Automatic Insights',
                'content': 'Get AI-powered insights and recommendations automatically.',
                'position': 'top',
                'highlight': 'insights_panel'
            }
        ]
    
    def start_tour(self):
        """Start the guided tour"""
        st.session_state.show_tour = True
        st.session_state.tour_step = 0
        st.rerun()
    
    def next_step(self):
        """Move to next step in tour"""
        if st.session_state.tour_step < len(self.tour_steps) - 1:
            st.session_state.tour_step += 1
        else:
            self.complete_tour()
        st.rerun()
    
    def skip_tour(self):
        """Skip the tour"""
        self.complete_tour()
        st.rerun()
    
    def complete_tour(self):
        """Mark tour as completed"""
        st.session_state.tour_completed = True
        st.session_state.show_tour = False
        st.balloons()
    
    def render_tour_overlay(self):
        """Render the tour overlay"""
        if not st.session_state.show_tour:
            return
        
        current_step = self.tour_steps[st.session_state.tour_step]
        
        # Create overlay container
        st.markdown(f"""
            <style>
            .tour-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 9998;
                backdrop-filter: blur(2px);
            }}
            
            .tour-spotlight {{
                position: absolute;
                background: white;
                border-radius: 20px;
                padding: 2rem;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                max-width: 400px;
                z-index: 9999;
                animation: slideIn 0.3s ease-out;
            }}
            
            @keyframes slideIn {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .tour-title {{
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #1e293b;
            }}
            
            .tour-content {{
                color: #64748b;
                margin-bottom: 1.5rem;
                line-height: 1.6;
            }}
            
            .tour-progress {{
                display: flex;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }}
            
            .tour-dot {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #e2e8f0;
                transition: all 0.3s ease;
            }}
            
            .tour-dot.active {{
                background: #667eea;
                transform: scale(1.5);
            }}
            </style>
        """, unsafe_allow_html=True)
        
        # Tour content
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown(f"""
                    <div class="tour-spotlight">
                        <div class="tour-title">{current_step['title']}</div>
                        <div class="tour-content">{current_step['content']}</div>
                        
                        <div class="tour-progress">
                            {"".join([
                                f'<div class="tour-dot {"active" if i == st.session_state.tour_step else ""}"></div>'
                                for i in range(len(self.tour_steps))
                            ])}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.session_state.tour_step > 0:
                        if st.button("← Back", use_container_width=True):
                            st.session_state.tour_step -= 1
                            st.rerun()
                
                with col_b:
                    if st.button("Skip Tour", use_container_width=True):
                        self.skip_tour()
                
                with col_c:
                    if st.session_state.tour_step < len(self.tour_steps) - 1:
                        if st.button("Next →", type="primary", use_container_width=True):
                            self.next_step()
                    else:
                        if st.button("Finish ✓", type="primary", use_container_width=True):
                            self.complete_tour()


class InteractiveTooltips:
    """Smart tooltips that appear on hover"""
    
    @staticmethod
    def render_tooltip(element_id: str, content: str, position: str = "top"):
        """Render a tooltip for an element"""
        st.markdown(f"""
            <style>
            #{element_id} {{
                position: relative;
                cursor: help;
            }}
            
            #{element_id}:hover::after {{
                content: "{content}";
                position: absolute;
                {position}: 120%;
                left: 50%;
                transform: translateX(-50%);
                background: #1e293b;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-size: 0.875rem;
                white-space: nowrap;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                z-index: 1000;
                animation: fadeIn 0.2s ease;
            }}
            
            #{element_id}:hover::before {{
                content: "";
                position: absolute;
                {position}: 110%;
                left: 50%;
                transform: translateX(-50%);
                border: 6px solid transparent;
                border-{position}-color: #1e293b;
                z-index: 1001;
                animation: fadeIn 0.2s ease;
            }}
            </style>
        """, unsafe_allow_html=True)


class KeyboardShortcuts:
    """Keyboard shortcuts for power users"""
    
    def __init__(self):
        self.shortcuts = {
            'ctrl+k': 'Open command palette',
            'ctrl+/': 'Toggle AI chat',
            'ctrl+f': 'Focus on filters',
            'ctrl+d': 'Go to dashboard',
            'ctrl+a': 'Go to analysis',
            'ctrl+r': 'Refresh data',
            'ctrl+e': 'Export report',
            'esc': 'Close dialogs'
        }
    
    def render_shortcuts_help(self):
        """Render keyboard shortcuts help"""
        with st.expander("⌨️ Keyboard Shortcuts"):
            for shortcut, description in self.shortcuts.items():
                st.markdown(f"**{shortcut}** - {description}")
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts listener"""
        st.markdown("""
            <script>
            document.addEventListener('keydown', function(e) {
                // Command palette
                if (e.ctrlKey && e.key === 'k') {
                    e.preventDefault();
                    window.dispatchEvent(new CustomEvent('openCommandPalette'));
                }
                
                // Toggle chat
                if (e.ctrlKey && e.key === '/') {
                    e.preventDefault();
                    window.dispatchEvent(new CustomEvent('toggleChat'));
                }
                
                // Navigation shortcuts
                if (e.ctrlKey && e.key === 'd') {
                    e.preventDefault();
                    window.location.hash = '#dashboard';
                }
                
                if (e.ctrlKey && e.key === 'a') {
                    e.preventDefault();
                    window.location.hash = '#analysis';
                }
            });
            </script>
        """, unsafe_allow_html=True)


class AccessibilityFeatures:
    """Accessibility features for better usability"""
    
    @staticmethod
    def setup_accessibility():
        """Setup accessibility features"""
        st.markdown("""
            <style>
            /* High contrast mode */
            @media (prefers-contrast: high) {
                .stApp {
                    background: white !important;
                    color: black !important;
                }
                
                .kpi-card {
                    border: 2px solid black !important;
                }
            }
            
            /* Reduced motion */
            @media (prefers-reduced-motion: reduce) {
                * {
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                }
            }
            
            /* Focus indicators */
            button:focus,
            input:focus,
            select:focus,
            textarea:focus {
                outline: 3px solid #667eea !important;
                outline-offset: 2px !important;
            }
            
            /* Screen reader only content */
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border-width: 0;
            }
            </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def add_aria_label(element: str, label: str):
        """Add ARIA label to element"""
        return f'<div aria-label="{label}">{element}</div>'