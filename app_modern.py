import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ai_data_extractor import AIDataExtractor
from comparative_analyzer import ComparativeAnalyzer
from direct_extractor import DirectDataExtractor
from filter_system import FilterSystem, FilterState
from ai_chat_assistant import AIChatAssistant
from interactive_charts import InteractiveCharts
from month_analytics import MonthAnalytics
from datetime import datetime
import os
from dotenv import load_dotenv
import json
from typing import Dict, List
import numpy as np

# Load environment variables
load_dotenv()

# Import modern UI components
from modern_navigation import ModernNavigation, InteractiveGuide, SmartNotifications
from guided_tour import GuidedTour, InteractiveTooltips, KeyboardShortcuts, AccessibilityFeatures
from command_palette import CommandPalette, SmartSearch

# Page configuration with modern theme
st.set_page_config(
    page_title="Marine Seguros | Analytics Intelligence",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern CSS with glassmorphism and animations
st.markdown("""
    <style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Modern container with glassmorphism */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    /* Animated gradient background */
    .stApp {
        background: linear-gradient(-45deg, #e3f2fd, #f3e5f5, #e8f5e9, #fff3e0);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Modern KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.8);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    
    .kpi-label {
        font-size: 0.875rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .kpi-change {
        font-size: 0.875rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        margin-top: 0.5rem;
    }
    
    .kpi-change.positive {
        background: rgba(34, 197, 94, 0.1);
        color: #22c55e;
    }
    
    .kpi-change.negative {
        background: rgba(239, 68, 68, 0.1);
        color: #ef4444;
    }
    
    /* Modern tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: transparent;
        border-bottom: 2px solid #f1f5f9;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        padding: 0 1.5rem;
        background: transparent;
        border: none;
        color: #64748b;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #334155;
        background: rgba(148, 163, 184, 0.1);
        border-radius: 8px;
    }
    
    .stTabs [aria-selected="true"] {
        background: transparent;
        color: #667eea;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"]::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    /* Modern buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 14px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }
    
    /* Chat interface improvements */
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
        margin: 1rem 0;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.75rem 0;
        border-radius: 16px;
        animation: fadeIn 0.4s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        margin-left: 20%;
    }
    
    .ai-message {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        margin-right: 20%;
    }
    
    /* Filter pills */
    .filter-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(102, 126, 234, 0.1);
        color: #667eea;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem;
        transition: all 0.2s ease;
    }
    
    .filter-pill:hover {
        background: rgba(102, 126, 234, 0.2);
        transform: scale(1.05);
    }
    
    /* Charts container */
    .chart-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .chart-container:hover {
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #cbd5e1;
        border-radius: 16px;
        padding: 3rem;
        text-align: center;
        background: rgba(248, 250, 252, 0.5);
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.05);
    }
    
    /* Loading animation */
    .loading-wave {
        display: inline-flex;
        gap: 0.25rem;
    }
    
    .loading-wave span {
        display: inline-block;
        width: 4px;
        height: 20px;
        background: #667eea;
        border-radius: 4px;
        animation: wave 1.2s ease-in-out infinite;
    }
    
    .loading-wave span:nth-child(2) { animation-delay: -1.1s; }
    .loading-wave span:nth-child(3) { animation-delay: -1s; }
    .loading-wave span:nth-child(4) { animation-delay: -0.9s; }
    .loading-wave span:nth-child(5) { animation-delay: -0.8s; }
    
    @keyframes wave {
        0%, 40%, 100% { transform: scaleY(0.4); }
        20% { transform: scaleY(1); }
    }
    
    /* Sidebar modern style */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 12px;
        padding: 1rem;
        border: none;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = {}
if 'comparative_analysis' not in st.session_state:
    st.session_state.comparative_analysis = None
if 'ai_insights' not in st.session_state:
    st.session_state.ai_insights = {}
if 'filter_system' not in st.session_state:
    st.session_state.filter_system = FilterSystem()
if 'chat_assistant' not in st.session_state:
    st.session_state.chat_assistant = None
if 'charts' not in st.session_state:
    st.session_state.charts = InteractiveCharts()
if 'month_analytics' not in st.session_state:
    st.session_state.month_analytics = MonthAnalytics()
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'dashboard'

# Initialize modern UI components
navigation = ModernNavigation()
guide = InteractiveGuide()
notifications = SmartNotifications()
tour = GuidedTour()
shortcuts = KeyboardShortcuts()
command_palette = CommandPalette()
search = SmartSearch()

# Setup accessibility
AccessibilityFeatures.setup_accessibility()
shortcuts.setup_shortcuts()

# Sidebar with modern design
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 1.5rem; font-weight: 700; color: #1e293b;'>
                🌊 Marine Seguros
            </h1>
            <p style='color: #64748b; font-size: 0.875rem; margin-top: 0.5rem;'>
                Analytics Intelligence Platform
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # API Key configuration
    with st.expander("🔑 Configuration", expanded=True):
        gemini_api_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            help="Required for AI features"
        )
        
        if gemini_api_key and not st.session_state.chat_assistant:
            st.session_state.chat_assistant = AIChatAssistant(gemini_api_key)
    
    # View mode selector
    st.markdown("### 📊 View Mode")
    view_options = {
        'dashboard': '📈 Dashboard',
        'analysis': '🔍 Analysis',
        'chat': '💬 AI Assistant',
        'reports': '📄 Reports'
    }
    
    for key, label in view_options.items():
        if st.button(label, key=f"view_{key}", use_container_width=True):
            st.session_state.view_mode = key
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
    
    if st.button("📥 Export Report", use_container_width=True):
        st.info("Report export coming soon!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #94a3b8; font-size: 0.75rem;'>
            <p>Version 3.0</p>
            <p>Powered by AI 🤖</p>
        </div>
    """, unsafe_allow_html=True)

# Show guided tour for first-time users
tour.render_tour_overlay()

# Command palette (always available)
command_palette.render_palette()

# Main content area with modern header
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                Marine Seguros Analytics
            </h1>
            <p style='color: #64748b; font-size: 1.125rem; margin-top: 0.5rem;'>
                Intelligent Financial Insights powered by AI
            </p>
        </div>
    """, unsafe_allow_html=True)

# Interactive guide for new users
guide.render_guide()

# Modern navigation bar
navigation.render_top_navigation()

# Show smart notifications
if st.session_state.extracted_data:
    notifications.check_data_insights(st.session_state.extracted_data)
notifications.render_notifications()

# Show filters if data is loaded
if st.session_state.extracted_data:
    with st.container():
        filter_state = st.session_state.filter_system.render_filter_bar(
            st.session_state.extracted_data
        )

# Dynamic content based on view mode
current_view = navigation.get_current_view()

# Show view header
navigation.render_view_header()

# Show contextual help
guide.show_contextual_help(current_view)

if current_view == 'dashboard':
    # Dashboard view
    if st.session_state.extracted_data:
        # Apply filters
        filtered_data = st.session_state.filter_system.apply_filters(
            st.session_state.extracted_data
        )
        
        if filtered_data:
            # Modern KPI Cards
            st.markdown("### 📊 Key Performance Indicators")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate KPIs
            total_revenue = 0
            avg_margin = 0
            years_count = len(filtered_data)
            growth_rate = 0
            
            for year_data in filtered_data.values():
                revenue = sum(v for k, v in year_data.get('revenue', {}).items() 
                            if k != 'ANNUAL' and isinstance(v, (int, float)))
                total_revenue += revenue
                
                margins = [v for k, v in year_data.get('margins', {}).items() 
                          if k != 'ANNUAL' and isinstance(v, (int, float))]
                if margins:
                    avg_margin += sum(margins) / len(margins)
            
            if years_count > 0:
                avg_margin = avg_margin / years_count
            
            # Get growth rate from comparative analysis
            if st.session_state.comparative_analysis:
                growth_rate = st.session_state.comparative_analysis.get(
                    'growth_patterns', {}
                ).get('average_growth', 0)
            
            with col1:
                st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Total Revenue</div>
                        <div class="kpi-value">R$ {total_revenue/1e6:.1f}M</div>
                        <div class="kpi-change positive">
                            <span>↑ {growth_rate:.1f}% YoY</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Average Margin</div>
                        <div class="kpi-value">{avg_margin:.1f}%</div>
                        <div class="kpi-change {'positive' if avg_margin > 15 else 'negative'}">
                            <span>{'↑' if avg_margin > 15 else '↓'} Target: 15%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                months_analyzed = sum(
                    len([v for k, v in year_data.get('revenue', {}).items() 
                         if k != 'ANNUAL' and isinstance(v, (int, float))])
                    for year_data in filtered_data.values()
                )
                st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Data Points</div>
                        <div class="kpi-value">{months_analyzed}</div>
                        <div class="kpi-change positive">
                            <span>{years_count} years</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                best_month = "DEC"
                if st.session_state.comparative_analysis:
                    seasonal = st.session_state.comparative_analysis.get('seasonal_trends', {})
                    strong_months = seasonal.get('strong_months', [])
                    if strong_months:
                        best_month = strong_months[0][:3]
                
                st.markdown(f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Best Month</div>
                        <div class="kpi-value">{best_month}</div>
                        <div class="kpi-change positive">
                            <span>Peak Season</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Interactive Charts Section
            st.markdown("### 📈 Interactive Visualizations")
            
            # Chart tabs
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Revenue Trends", "Monthly Patterns", "Comparative Analysis"])
            
            with chart_tab1:
                dashboard_fig = st.session_state.charts.create_revenue_dashboard(
                    filtered_data,
                    filter_state if st.session_state.filter_system else None
                )
                st.plotly_chart(dashboard_fig, use_container_width=True)
            
            with chart_tab2:
                col1, col2 = st.columns(2)
                with col1:
                    heatmap_fig = st.session_state.charts.create_monthly_heatmap(filtered_data)
                    st.plotly_chart(heatmap_fig, use_container_width=True)
                
                with col2:
                    margin_fig = st.session_state.charts.create_margin_analysis(filtered_data)
                    st.plotly_chart(margin_fig, use_container_width=True)
            
            with chart_tab3:
                if len(filtered_data) >= 2:
                    years = sorted(filtered_data.keys())
                    comparison_fig = st.session_state.charts.create_comparison_chart(
                        filtered_data, years[-2], years[-1]
                    )
                    st.plotly_chart(comparison_fig, use_container_width=True)
                else:
                    st.info("Need at least 2 years of data for comparison")
        else:
            st.warning("No data available with current filters")
    else:
        # Data upload section with modern design
        st.markdown("""
            <div class="upload-area">
                <h3>📁 Upload Your Data</h3>
                <p>Drag and drop Excel files or click to browse</p>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            label_visibility="hidden"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            use_existing = st.checkbox("Use Marine Seguros sample data (2018-2025)", value=True)
        
        with col2:
            if st.button("🚀 Process Data", type="primary", disabled=not gemini_api_key):
                if not gemini_api_key:
                    st.error("Please configure your Gemini API key")
                else:
                    with st.spinner("Processing financial data..."):
                        # Process data logic here
                        direct_extractor = DirectDataExtractor()
                        ai_extractor = AIDataExtractor(gemini_api_key)
                        
                        files_to_process = []
                        if use_existing:
                            files_to_process = [
                                'Análise de Resultado Financeiro 2018_2023.xlsx',
                                'Resultado Financeiro - 2024.xlsx',
                                'Resultado Financeiro - 2025.xlsx'
                            ]
                        else:
                            for uploaded_file in uploaded_files:
                                with open(uploaded_file.name, 'wb') as f:
                                    f.write(uploaded_file.getbuffer())
                                files_to_process.append(uploaded_file.name)
                        
                        extracted_data = {}
                        for file in files_to_process:
                            try:
                                file_data = direct_extractor.extract_from_excel(file)
                                extracted_data.update(file_data)
                            except Exception as e:
                                st.error(f"Error processing {file}: {str(e)}")
                        
                        st.session_state.extracted_data = extracted_data
                        
                        if len(extracted_data) >= 2:
                            analyzer = ComparativeAnalyzer(gemini_api_key)
                            st.session_state.comparative_analysis = analyzer.analyze_all_years(extracted_data)
                        
                        st.success("✅ Data processed successfully!")
                        st.balloons()
                        st.rerun()

elif current_view == 'chat':
    # AI Chat Interface
    st.markdown("### 💬 AI Assistant")
    
    if st.session_state.chat_assistant and st.session_state.extracted_data:
        filter_context = st.session_state.filter_system.get_filter_context()
        filtered_data = st.session_state.filter_system.apply_filters(
            st.session_state.extracted_data
        )
        
        st.session_state.chat_assistant.render_chat_interface(
            filtered_data,
            filter_context
        )
    else:
        st.info("Please load data and configure API key to use the AI Assistant")

elif current_view == 'analysis':
    # Deep Analysis View
    st.markdown("### 🔍 Deep Analysis")
    
    if st.session_state.extracted_data:
        analysis_tabs = st.tabs(["Trends", "Seasonality", "Correlations", "Predictions"])
        
        with analysis_tabs[0]:
            # Trends analysis content
            if st.session_state.comparative_analysis:
                growth_data = st.session_state.comparative_analysis.get('growth_patterns', {})
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    # Create trend chart
                    years = sorted(st.session_state.extracted_data.keys())
                    revenues = []
                    for year in years:
                        revenue = sum(v for k, v in st.session_state.extracted_data[year].get('revenue', {}).items() 
                                    if k != 'ANNUAL' and isinstance(v, (int, float)))
                        revenues.append(revenue)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=years,
                        y=revenues,
                        mode='lines+markers',
                        line=dict(width=3, color='#667eea'),
                        marker=dict(size=8),
                        fill='tonexty',
                        fillcolor='rgba(102, 126, 234, 0.1)'
                    ))
                    
                    fig.update_layout(
                        title="Revenue Trend Analysis",
                        xaxis_title="Year",
                        yaxis_title="Revenue (R$)",
                        hovermode='x unified',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("#### Growth Metrics")
                    st.metric("CAGR", f"{growth_data.get('average_growth', 0):.1f}%")
                    st.metric("Volatility", f"{growth_data.get('growth_volatility', 0):.1f}%")
                    trend = growth_data.get('trend', 'stable')
                    st.metric("Trend", trend.replace('_', ' ').title())
        
        with analysis_tabs[1]:
            # Seasonality analysis
            st.info("Seasonality analysis visualization coming soon")
        
        with analysis_tabs[2]:
            # Correlations
            st.info("Correlation analysis visualization coming soon")
        
        with analysis_tabs[3]:
            # Predictions
            st.info("AI-powered predictions coming soon")
    else:
        st.info("Please load data first to see analysis")

elif current_view == 'filters':
    # Advanced Filters View
    st.markdown("### 🎯 Smart Filters")
    
    if st.session_state.extracted_data:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### Quick Filters")
            
            # Year selector
            years = sorted(st.session_state.extracted_data.keys())
            selected_years = st.multiselect(
                "Select Years",
                years,
                default=years[-2:] if len(years) >= 2 else years
            )
            
            # Month selector
            months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                     'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            selected_months = st.multiselect(
                "Select Months",
                months,
                default=months
            )
            
            # Metric filter
            st.markdown("#### Metric Filters")
            
            revenue_range = st.slider(
                "Revenue Range (R$ thousands)",
                0, 5000, (0, 5000)
            )
            
            margin_range = st.slider(
                "Margin Range (%)",
                0, 100, (0, 100)
            )
            
            # Apply filters button
            if st.button("Apply Filters", type="primary", use_container_width=True):
                st.success("Filters applied!")
                navigation.navigate_to('dashboard')
                st.rerun()
        
        with col2:
            st.markdown("#### Filter Preview")
            
            # Show what data will be included
            st.info(f"""
                **Selected Data:**
                - Years: {', '.join(map(str, selected_years))}
                - Months: {', '.join(selected_months[:3])}{'...' if len(selected_months) > 3 else ''}
                - Revenue: R$ {revenue_range[0]}k - R$ {revenue_range[1]}k
                - Margin: {margin_range[0]}% - {margin_range[1]}%
            """)
            
            # Quick stats
            total_data_points = len(selected_years) * len(selected_months)
            st.metric("Data Points", total_data_points)
    else:
        st.info("Please load data first to use filters")

elif current_view == 'reports':
    # Reports View
    st.markdown("### 📄 Reports")
    st.info("Report generation feature coming soon!")

# Footer with modern design
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <p style='color: #94a3b8; font-size: 0.875rem;'>
            Marine Seguros Analytics Platform v3.0 | Built with ❤️ using Streamlit & AI
        </p>
    </div>
""", unsafe_allow_html=True)