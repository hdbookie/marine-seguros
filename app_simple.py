import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from core.financial_processor import FinancialProcessor
from core.direct_extractor import DirectDataExtractor

# Page configuration
st.set_page_config(
    page_title="Marine Seguros Analytics",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Marine Seguros - Financial Analytics Dashboard")
st.markdown("---")

# Initialize session state
if 'financial_data' not in st.session_state:
    st.session_state.financial_data = None
if 'excel_data' not in st.session_state:
    st.session_state.excel_data = None

# Sidebar for file upload
with st.sidebar:
    st.header("📁 Data Upload")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload Excel files",
        type=['xlsx', 'xls'],
        accept_multiple_files=True
    )
    
    # Use existing files option
    use_existing = st.checkbox("Use existing Marine Seguros files", value=True)
    
    if st.button("Process Data", type="primary"):
        processor = FinancialProcessor()
        
        files_to_process = []
        if use_existing:
            files_to_process = [
                'Análise de Resultado Financeiro 2018_2023.xlsx',
                'Resultado Financeiro - 2024.xlsx',
                'Resultado Financeiro - 2025.xlsx'
            ]
        elif uploaded_files:
            for uploaded_file in uploaded_files:
                with open(uploaded_file.name, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                files_to_process.append(uploaded_file.name)
        
        if files_to_process:
            with st.spinner("Processing financial data..."):
                # Load Excel files
                excel_data = processor.load_excel_files(files_to_process)
                st.session_state.excel_data = excel_data
                
                # Consolidate data
                df_annual = processor.consolidate_all_years(excel_data)
                df_annual = processor.calculate_growth_metrics(df_annual)
                st.session_state.financial_data = df_annual
                
                st.success(f"✅ Processed {len(df_annual)} years of data!")

# Main content
if st.session_state.financial_data is not None and not st.session_state.financial_data.empty:
    df = st.session_state.financial_data
    
    # Create tabs
    tab1, tab2 = st.tabs(["📈 Annual View", "📅 Monthly View"])
    
    with tab1:
        st.header("Annual Financial Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_revenue = df['revenue'].sum() if 'revenue' in df.columns else 0
            st.metric("Total Revenue", f"R$ {total_revenue:,.0f}")
        
        with col2:
            avg_margin = df['profit_margin'].mean() if 'profit_margin' in df.columns else 0
            st.metric("Avg Profit Margin", f"{avg_margin:.1f}%")
        
        with col3:
            latest_year = df['year'].max() if 'year' in df.columns else 0
            st.metric("Latest Year", str(latest_year))
        
        with col4:
            years_analyzed = len(df) if not df.empty else 0
            st.metric("Years Analyzed", years_analyzed)
        
        # Revenue chart
        st.subheader("Revenue Evolution")
        if 'year' in df.columns and 'revenue' in df.columns:
            fig_revenue = px.bar(
                df, 
                x='year', 
                y='revenue',
                title='Annual Revenue',
                labels={'revenue': 'Revenue (R$)', 'year': 'Year'}
            )
            fig_revenue.update_traces(marker_color='#1f77b4')
            st.plotly_chart(fig_revenue, use_container_width=True)
        
        # Profit margin chart
        st.subheader("Profit Margin Trend")
        if 'year' in df.columns and 'profit_margin' in df.columns:
            fig_margin = px.line(
                df,
                x='year',
                y='profit_margin',
                title='Profit Margin Evolution',
                labels={'profit_margin': 'Profit Margin (%)', 'year': 'Year'},
                markers=True
            )
            fig_margin.update_traces(line_color='#2ca02c')
            st.plotly_chart(fig_margin, use_container_width=True)
        
        # Cost vs Revenue comparison
        st.subheader("Costs vs Revenue")
        if all(col in df.columns for col in ['year', 'revenue', 'variable_costs']):
            fig_comparison = go.Figure()
            fig_comparison.add_trace(go.Bar(
                name='Revenue',
                x=df['year'],
                y=df['revenue'],
                marker_color='#1f77b4'
            ))
            fig_comparison.add_trace(go.Bar(
                name='Variable Costs',
                x=df['year'],
                y=df['variable_costs'],
                marker_color='#ff7f0e'
            ))
            fig_comparison.update_layout(
                title='Revenue vs Variable Costs',
                xaxis_title='Year',
                yaxis_title='Amount (R$)',
                barmode='group'
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Data table
        st.subheader("Detailed Financial Data")
        display_columns = [col for col in df.columns if col in [
            'year', 'revenue', 'variable_costs', 'net_profit', 'profit_margin',
            'revenue_growth', 'net_profit_growth'
        ]]
        if display_columns:
            st.dataframe(
                df[display_columns].style.format({
                    'revenue': 'R$ {:,.0f}',
                    'variable_costs': 'R$ {:,.0f}',
                    'net_profit': 'R$ {:,.0f}',
                    'profit_margin': '{:.1f}%',
                    'revenue_growth': '{:.1f}%',
                    'net_profit_growth': '{:.1f}%'
                }),
                use_container_width=True
            )
    
    with tab2:
        st.header("Monthly Financial Analysis")
        
        if st.session_state.excel_data:
            processor = FinancialProcessor()
            df_monthly = processor.get_monthly_data(st.session_state.excel_data)
            
            if not df_monthly.empty:
                # Year selector
                years = sorted(df_monthly['year'].unique())
                selected_year = st.selectbox("Select Year", years, index=len(years)-1)
                
                # Filter data for selected year
                year_data = df_monthly[df_monthly['year'] == selected_year]
                
                # Monthly revenue chart
                st.subheader(f"Monthly Revenue - {selected_year}")
                fig_monthly = px.bar(
                    year_data,
                    x='month',
                    y='revenue',
                    title=f'Monthly Revenue for {selected_year}',
                    labels={'revenue': 'Revenue (R$)', 'month': 'Month'}
                )
                fig_monthly.update_traces(marker_color='#1f77b4')
                st.plotly_chart(fig_monthly, use_container_width=True)
                
                # Monthly profit margin
                st.subheader(f"Monthly Profit Margins - {selected_year}")
                fig_monthly_margin = px.line(
                    year_data,
                    x='month',
                    y='profit_margin',
                    title=f'Monthly Profit Margin for {selected_year}',
                    labels={'profit_margin': 'Profit Margin (%)', 'month': 'Month'},
                    markers=True
                )
                fig_monthly_margin.update_traces(line_color='#2ca02c')
                st.plotly_chart(fig_monthly_margin, use_container_width=True)
                
                # Monthly data table
                st.subheader("Monthly Details")
                display_cols = ['month', 'revenue', 'variable_costs', 'net_profit', 'profit_margin']
                available_cols = [col for col in display_cols if col in year_data.columns]
                
                if available_cols:
                    st.dataframe(
                        year_data[available_cols].style.format({
                            'revenue': 'R$ {:,.0f}',
                            'variable_costs': 'R$ {:,.0f}',
                            'net_profit': 'R$ {:,.0f}',
                            'profit_margin': '{:.1f}%'
                        }),
                        use_container_width=True
                    )
            else:
                st.info("Monthly data not available. Please ensure the Excel files contain monthly breakdown.")
else:
    # Welcome message
    st.info("👈 Please upload Excel files or use existing Marine Seguros data to begin analysis")
    
    # Instructions
    with st.expander("📖 How to use this dashboard"):
        st.markdown("""
        1. **Upload Files**: Use the sidebar to upload Excel files or check "Use existing Marine Seguros files"
        2. **Process Data**: Click the "Process Data" button to analyze the financial information
        3. **View Results**: 
           - **Annual View**: See year-over-year trends and comparisons
           - **Monthly View**: Analyze monthly performance for each year
        4. **Export**: Use the download buttons to export charts or data
        
        **Expected File Format**: Excel files with yearly sheets containing monthly financial data including revenue, costs, and profit information.
        """)