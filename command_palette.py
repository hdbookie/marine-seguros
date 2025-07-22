import streamlit as st
from typing import Dict, List, Callable, Optional
import re

class CommandPalette:
    """Modern command palette for quick actions"""
    
    def __init__(self):
        if 'command_palette_open' not in st.session_state:
            st.session_state.command_palette_open = False
        if 'command_search' not in st.session_state:
            st.session_state.command_search = ""
        
        # Available commands
        self.commands = {
            'dashboard': {
                'name': 'Go to Dashboard',
                'icon': '📊',
                'description': 'View main dashboard',
                'keywords': ['home', 'overview', 'kpi'],
                'action': lambda: self._navigate_to('dashboard')
            },
            'analysis': {
                'name': 'Open Analysis',
                'icon': '🔍',
                'description': 'Deep dive into data',
                'keywords': ['analyze', 'insights', 'trends'],
                'action': lambda: self._navigate_to('analysis')
            },
            'chat': {
                'name': 'Start AI Chat',
                'icon': '💬',
                'description': 'Ask questions about data',
                'keywords': ['ai', 'assistant', 'help', 'question'],
                'action': lambda: self._navigate_to('chat')
            },
            'export_pdf': {
                'name': 'Export to PDF',
                'icon': '📄',
                'description': 'Generate PDF report',
                'keywords': ['download', 'report', 'pdf'],
                'action': lambda: self._export_report('pdf')
            },
            'export_excel': {
                'name': 'Export to Excel',
                'icon': '📊',
                'description': 'Download Excel file',
                'keywords': ['download', 'xlsx', 'spreadsheet'],
                'action': lambda: self._export_report('excel')
            },
            'refresh': {
                'name': 'Refresh Data',
                'icon': '🔄',
                'description': 'Reload all data',
                'keywords': ['reload', 'update'],
                'action': lambda: st.cache_data.clear()
            },
            'filter_year': {
                'name': 'Filter by Year',
                'icon': '📅',
                'description': 'Quick year filter',
                'keywords': ['date', 'period', 'annual'],
                'action': lambda: self._show_filter_modal('year')
            },
            'filter_month': {
                'name': 'Filter by Month',
                'icon': '🗓️',
                'description': 'Quick month filter',
                'keywords': ['date', 'period', 'monthly'],
                'action': lambda: self._show_filter_modal('month')
            },
            'compare': {
                'name': 'Compare Periods',
                'icon': '⚖️',
                'description': 'Compare two time periods',
                'keywords': ['versus', 'vs', 'comparison'],
                'action': lambda: self._show_comparison_modal()
            },
            'settings': {
                'name': 'Settings',
                'icon': '⚙️',
                'description': 'App settings',
                'keywords': ['config', 'preferences'],
                'action': lambda: self._show_settings()
            },
            'help': {
                'name': 'Help & Documentation',
                'icon': '❓',
                'description': 'View help docs',
                'keywords': ['guide', 'tutorial', 'docs'],
                'action': lambda: self._show_help()
            },
            'shortcuts': {
                'name': 'Keyboard Shortcuts',
                'icon': '⌨️',
                'description': 'View all shortcuts',
                'keywords': ['hotkeys', 'keys'],
                'action': lambda: self._show_shortcuts()
            }
        }
    
    def toggle_palette(self):
        """Toggle command palette visibility"""
        st.session_state.command_palette_open = not st.session_state.command_palette_open
        st.session_state.command_search = ""
    
    def render_palette(self):
        """Render the command palette"""
        if not st.session_state.command_palette_open:
            # Render trigger button
            if st.button("🔍 Quick Actions (Ctrl+K)", key="cmd_trigger"):
                self.toggle_palette()
                st.rerun()
            return
        
        # Create modal overlay
        st.markdown("""
            <style>
            .cmd-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
                z-index: 9999;
                animation: fadeIn 0.2s ease;
            }
            
            .cmd-palette {
                position: fixed;
                top: 20%;
                left: 50%;
                transform: translateX(-50%);
                width: 600px;
                max-width: 90%;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
                z-index: 10000;
                animation: slideDown 0.3s ease;
            }
            
            @keyframes slideDown {
                from {
                    opacity: 0;
                    transform: translateX(-50%) translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(-50%) translateY(0);
                }
            }
            
            .cmd-search {
                padding: 1.5rem;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .cmd-results {
                max-height: 400px;
                overflow-y: auto;
                padding: 0.5rem;
            }
            
            .cmd-item {
                padding: 0.75rem 1rem;
                margin: 0.25rem;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            
            .cmd-item:hover {
                background: #f8fafc;
                transform: translateX(4px);
            }
            
            .cmd-item-icon {
                font-size: 1.25rem;
            }
            
            .cmd-item-content {
                flex: 1;
            }
            
            .cmd-item-name {
                font-weight: 600;
                color: #1e293b;
            }
            
            .cmd-item-desc {
                font-size: 0.875rem;
                color: #64748b;
            }
            
            .cmd-shortcut {
                font-size: 0.75rem;
                padding: 0.25rem 0.5rem;
                background: #f1f5f9;
                border-radius: 4px;
                color: #64748b;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Modal container
        modal = st.container()
        
        with modal:
            # Search input
            search_query = st.text_input(
                "Search commands...",
                value=st.session_state.command_search,
                key="cmd_search_input",
                placeholder="Type to search commands...",
                label_visibility="collapsed"
            )
            
            # Filter commands based on search
            filtered_commands = self._filter_commands(search_query)
            
            # Display results
            if filtered_commands:
                for cmd_id, cmd in filtered_commands.items():
                    col1, col2 = st.columns([10, 2])
                    
                    with col1:
                        if st.button(
                            f"{cmd['icon']} **{cmd['name']}** - {cmd['description']}",
                            key=f"cmd_{cmd_id}",
                            use_container_width=True
                        ):
                            # Execute command
                            cmd['action']()
                            self.toggle_palette()
                            st.rerun()
                    
                    with col2:
                        # Show shortcut if available
                        shortcut = self._get_shortcut(cmd_id)
                        if shortcut:
                            st.markdown(f"<span class='cmd-shortcut'>{shortcut}</span>", 
                                      unsafe_allow_html=True)
            else:
                st.info("No commands found. Try a different search term.")
            
            # Close button
            if st.button("Close (Esc)", key="cmd_close"):
                self.toggle_palette()
                st.rerun()
    
    def _filter_commands(self, query: str) -> Dict:
        """Filter commands based on search query"""
        if not query:
            return self.commands
        
        query_lower = query.lower()
        filtered = {}
        
        for cmd_id, cmd in self.commands.items():
            # Check name
            if query_lower in cmd['name'].lower():
                filtered[cmd_id] = cmd
                continue
            
            # Check description
            if query_lower in cmd['description'].lower():
                filtered[cmd_id] = cmd
                continue
            
            # Check keywords
            if any(query_lower in keyword for keyword in cmd.get('keywords', [])):
                filtered[cmd_id] = cmd
        
        return filtered
    
    def _get_shortcut(self, cmd_id: str) -> Optional[str]:
        """Get keyboard shortcut for command"""
        shortcuts = {
            'dashboard': 'Ctrl+D',
            'analysis': 'Ctrl+A',
            'chat': 'Ctrl+/',
            'refresh': 'Ctrl+R',
            'export_pdf': 'Ctrl+E'
        }
        return shortcuts.get(cmd_id)
    
    def _navigate_to(self, view: str):
        """Navigate to a specific view"""
        st.session_state.current_view = view
    
    def _export_report(self, format: str):
        """Export report in specified format"""
        st.success(f"Exporting report as {format.upper()}...")
    
    def _show_filter_modal(self, filter_type: str):
        """Show filter modal"""
        st.info(f"Opening {filter_type} filter...")
    
    def _show_comparison_modal(self):
        """Show comparison modal"""
        st.info("Opening comparison tool...")
    
    def _show_settings(self):
        """Show settings modal"""
        st.info("Opening settings...")
    
    def _show_help(self):
        """Show help documentation"""
        st.info("Opening help documentation...")
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts"""
        st.info("Showing keyboard shortcuts...")


class SmartSearch:
    """Intelligent search across all data and features"""
    
    def __init__(self):
        self.search_index = {}
    
    def build_index(self, data: Dict):
        """Build search index from data"""
        self.search_index = {
            'data': [],
            'features': [],
            'help': []
        }
        
        # Index data points
        for year, year_data in data.items():
            self.search_index['data'].append({
                'type': 'year',
                'value': str(year),
                'label': f"Year {year} data",
                'context': year_data
            })
            
            # Index months
            for month in year_data.get('revenue', {}).keys():
                if month != 'ANNUAL':
                    self.search_index['data'].append({
                        'type': 'month',
                        'value': f"{year}-{month}",
                        'label': f"{month} {year}",
                        'context': {'year': year, 'month': month}
                    })
        
        # Index features
        features = [
            ('Dashboard', 'dashboard', 'View KPIs and overview'),
            ('Analysis', 'analysis', 'Deep dive into trends'),
            ('AI Chat', 'chat', 'Ask questions in natural language'),
            ('Filters', 'filters', 'Filter data by time period'),
            ('Export', 'export', 'Export reports and data')
        ]
        
        for name, key, desc in features:
            self.search_index['features'].append({
                'type': 'feature',
                'value': key,
                'label': name,
                'description': desc
            })
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search across all indexed content"""
        if not query:
            return []
        
        query_lower = query.lower()
        results = []
        
        # Search data
        for item in self.search_index.get('data', []):
            if query_lower in str(item['value']).lower() or \
               query_lower in item['label'].lower():
                results.append({
                    'category': 'Data',
                    'item': item,
                    'relevance': self._calculate_relevance(query_lower, item)
                })
        
        # Search features
        for item in self.search_index.get('features', []):
            if query_lower in item['label'].lower() or \
               query_lower in item.get('description', '').lower():
                results.append({
                    'category': 'Features',
                    'item': item,
                    'relevance': self._calculate_relevance(query_lower, item)
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        
        return results[:limit]
    
    def _calculate_relevance(self, query: str, item: Dict) -> float:
        """Calculate relevance score for search result"""
        score = 0.0
        
        # Exact match
        if query == str(item['value']).lower():
            score += 10.0
        
        # Partial match in value
        if query in str(item['value']).lower():
            score += 5.0
        
        # Match in label
        if query in item['label'].lower():
            score += 3.0
        
        # Match in description
        if 'description' in item and query in item['description'].lower():
            score += 2.0
        
        return score