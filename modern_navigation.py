import streamlit as st
from typing import Dict, Optional
import json

class ModernNavigation:
    """Modern navigation system with breadcrumbs and quick actions"""
    
    def __init__(self):
        # Initialize navigation state
        if 'nav_history' not in st.session_state:
            st.session_state.nav_history = ['dashboard']
        if 'current_view' not in st.session_state:
            st.session_state.current_view = 'dashboard'
        
        # Navigation structure
        self.nav_items = {
            'dashboard': {
                'icon': '📊',
                'title': 'Dashboard',
                'description': 'Overview and KPIs',
                'color': '#667eea'
            },
            'analysis': {
                'icon': '🔍',
                'title': 'Analysis',
                'description': 'Deep dive insights',
                'color': '#764ba2'
            },
            'chat': {
                'icon': '💬',
                'title': 'AI Assistant',
                'description': 'Ask questions',
                'color': '#f59e0b'
            },
            'filters': {
                'icon': '🎯',
                'title': 'Smart Filters',
                'description': 'Refine your view',
                'color': '#10b981'
            },
            'reports': {
                'icon': '📄',
                'title': 'Reports',
                'description': 'Export & share',
                'color': '#ef4444'
            }
        }
    
    def render_top_navigation(self):
        """Render modern top navigation bar"""
        # Create navigation container
        nav_container = st.container()
        
        with nav_container:
            # Navigation pills
            cols = st.columns(len(self.nav_items))
            
            for idx, (key, item) in enumerate(self.nav_items.items()):
                with cols[idx]:
                    # Check if current
                    is_current = st.session_state.current_view == key
                    
                    # Create button with custom styling
                    if st.button(
                        f"{item['icon']} {item['title']}",
                        key=f"nav_{key}",
                        use_container_width=True,
                        type="primary" if is_current else "secondary"
                    ):
                        self.navigate_to(key)
                        st.rerun()
                    
                    # Show description on hover (using help)
                    if not is_current:
                        st.caption(item['description'])
    
    def render_breadcrumbs(self):
        """Render breadcrumb navigation"""
        if len(st.session_state.nav_history) > 1:
            breadcrumb_items = []
            
            for view in st.session_state.nav_history[-3:]:  # Show last 3 items
                item = self.nav_items.get(view, {})
                breadcrumb_items.append(f"{item.get('icon', '')} {item.get('title', view)}")
            
            st.markdown(
                " > ".join(breadcrumb_items),
                help="Navigation history"
            )
    
    def render_quick_actions(self, data_loaded: bool = False):
        """Render context-aware quick actions"""
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            if data_loaded:
                if st.button("📊 View Insights", use_container_width=True):
                    self.navigate_to('analysis')
                    st.rerun()
            else:
                if st.button("📁 Load Data", use_container_width=True):
                    self.navigate_to('dashboard')
                    st.rerun()
        
        with col3:
            if st.button("💬 Ask AI", use_container_width=True):
                self.navigate_to('chat')
                st.rerun()
    
    def navigate_to(self, view: str):
        """Navigate to a specific view"""
        st.session_state.current_view = view
        
        # Update history
        if view not in st.session_state.nav_history[-1:]:
            st.session_state.nav_history.append(view)
            
            # Keep history limited
            if len(st.session_state.nav_history) > 10:
                st.session_state.nav_history = st.session_state.nav_history[-10:]
    
    def get_current_view(self) -> str:
        """Get current view"""
        return st.session_state.current_view
    
    def render_view_header(self):
        """Render header for current view"""
        current = self.nav_items.get(st.session_state.current_view, {})
        
        st.markdown(f"""
            <div style='padding: 1rem 0;'>
                <h2 style='color: {current.get('color', '#667eea')}; display: flex; align-items: center; gap: 0.5rem;'>
                    <span style='font-size: 2rem;'>{current.get('icon', '📊')}</span>
                    {current.get('title', 'View')}
                </h2>
                <p style='color: #64748b; margin-top: 0.5rem;'>
                    {current.get('description', '')}
                </p>
            </div>
        """, unsafe_allow_html=True)


class InteractiveGuide:
    """Interactive onboarding and help system"""
    
    def __init__(self):
        if 'show_guide' not in st.session_state:
            st.session_state.show_guide = True
        if 'guide_step' not in st.session_state:
            st.session_state.guide_step = 0
        
        self.steps = [
            {
                'title': 'Welcome to Marine Seguros Analytics! 🌊',
                'content': 'This platform provides AI-powered insights for your financial data.',
                'action': 'Let\'s start'
            },
            {
                'title': 'Upload Your Data 📁',
                'content': 'Click the upload area or use our sample data to begin.',
                'action': 'Got it'
            },
            {
                'title': 'Explore Insights 📊',
                'content': 'Use the navigation to switch between Dashboard, Analysis, and AI Chat.',
                'action': 'Explore'
            },
            {
                'title': 'Ask Questions 💬',
                'content': 'Our AI assistant can answer any questions about your data.',
                'action': 'Try it'
            }
        ]
    
    def render_guide(self):
        """Render interactive guide"""
        if st.session_state.show_guide and st.session_state.guide_step < len(self.steps):
            step = self.steps[st.session_state.guide_step]
            
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col2:
                    st.info(f"""
                        **{step['title']}**
                        
                        {step['content']}
                    """)
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if st.button(step['action'], type="primary", use_container_width=True):
                            st.session_state.guide_step += 1
                            if st.session_state.guide_step >= len(self.steps):
                                st.session_state.show_guide = False
                            st.rerun()
                    
                    with col_b:
                        if st.button("Skip tour", use_container_width=True):
                            st.session_state.show_guide = False
                            st.rerun()
                    
                    # Progress indicator
                    progress = (st.session_state.guide_step + 1) / len(self.steps)
                    st.progress(progress)
    
    def show_contextual_help(self, context: str):
        """Show help based on current context"""
        help_content = {
            'dashboard': "💡 **Tip**: Click on any chart to see details. Use filters to focus on specific periods.",
            'analysis': "💡 **Tip**: Compare multiple years and look for patterns in the data.",
            'chat': "💡 **Tip**: Ask questions like 'What was our best month?' or 'Compare 2023 to 2024'.",
            'filters': "💡 **Tip**: Combine multiple filters to drill down into specific insights.",
            'reports': "💡 **Tip**: Export reports in multiple formats for easy sharing."
        }
        
        if context in help_content:
            with st.expander("💡 Quick Help", expanded=False):
                st.markdown(help_content[context])


class SmartNotifications:
    """Smart notification system for insights and alerts"""
    
    def __init__(self):
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        if 'dismissed_notifications' not in st.session_state:
            st.session_state.dismissed_notifications = set()
    
    def add_notification(self, notification_id: str, title: str, message: str, 
                        type: str = 'info', icon: str = '📌'):
        """Add a new notification"""
        if notification_id not in st.session_state.dismissed_notifications:
            st.session_state.notifications.append({
                'id': notification_id,
                'title': title,
                'message': message,
                'type': type,
                'icon': icon
            })
    
    def render_notifications(self):
        """Render notifications panel"""
        active_notifications = [
            n for n in st.session_state.notifications 
            if n['id'] not in st.session_state.dismissed_notifications
        ]
        
        if active_notifications:
            with st.container():
                for notification in active_notifications:
                    col1, col2 = st.columns([10, 1])
                    
                    with col1:
                        if notification['type'] == 'success':
                            st.success(f"{notification['icon']} **{notification['title']}** - {notification['message']}")
                        elif notification['type'] == 'warning':
                            st.warning(f"{notification['icon']} **{notification['title']}** - {notification['message']}")
                        elif notification['type'] == 'error':
                            st.error(f"{notification['icon']} **{notification['title']}** - {notification['message']}")
                        else:
                            st.info(f"{notification['icon']} **{notification['title']}** - {notification['message']}")
                    
                    with col2:
                        if st.button("✕", key=f"dismiss_{notification['id']}"):
                            st.session_state.dismissed_notifications.add(notification['id'])
                            st.rerun()
    
    def check_data_insights(self, data: Dict):
        """Check data and generate smart notifications"""
        if data:
            # Check for significant changes
            years = sorted(data.keys())
            if len(years) >= 2:
                latest_year = years[-1]
                previous_year = years[-2]
                
                latest_revenue = sum(v for k, v in data[latest_year].get('revenue', {}).items() 
                                   if k != 'ANNUAL' and isinstance(v, (int, float)))
                previous_revenue = sum(v for k, v in data[previous_year].get('revenue', {}).items() 
                                     if k != 'ANNUAL' and isinstance(v, (int, float)))
                
                if latest_revenue > previous_revenue * 1.1:
                    self.add_notification(
                        f"growth_{latest_year}",
                        "Strong Growth Detected!",
                        f"Revenue increased by {((latest_revenue/previous_revenue - 1) * 100):.1f}% in {latest_year}",
                        type='success',
                        icon='🚀'
                    )
                elif latest_revenue < previous_revenue * 0.9:
                    self.add_notification(
                        f"decline_{latest_year}",
                        "Revenue Decline Alert",
                        f"Revenue decreased by {((1 - latest_revenue/previous_revenue) * 100):.1f}% in {latest_year}",
                        type='warning',
                        icon='⚠️'
                    )