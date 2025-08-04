"""
Dashboard Tab - Legacy version extracted from app.py
Preserves all original functionality while organizing code
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from core.financial_processor import FinancialProcessor
from utils.legacy_helpers import (
    format_currency,
    calculate_percentage_change,
    prepare_x_axis,
    get_monthly_layout_config,
    get_plotly_config,
    get_default_monthly_range
)
from ui.tabs.micro_analysis_tab import render_micro_analysis_tab


def get_monthly_xaxis_config(display_df, x_col):
    """Get x-axis configuration for monthly charts based on data size"""
    # Adjust tick display based on number of months
    if len(display_df) > 36:
        dtick = 3  # Show every 3rd month
    elif len(display_df) > 24:
        dtick = 2  # Show every 2nd month
    else:
        dtick = 1  # Show every month
    
    xaxis_config = dict(
        tickangle=-45,
        tickmode='linear',
        dtick=dtick,
        **get_monthly_layout_config()
    )
    
    # Set default range to show last 12 months
    default_range = get_default_monthly_range(display_df, x_col)
    if default_range:
        xaxis_config['range'] = default_range
    
    return xaxis_config


def render_dashboard_tab(db, use_unified_extractor=True):
    """Render the dashboard tab with financial visualizations"""
    
    st.header("Dashboard Financeiro")
    
    # Show data freshness indicator
    last_upload = db.get_last_upload_info()
    if last_upload:
        from datetime import datetime
        upload_time = datetime.fromisoformat(last_upload['created_at'].replace(' ', 'T'))
        time_diff = datetime.now() - upload_time
        
        if time_diff.total_seconds() < 300:  # Less than 5 minutes
            st.success(f"🟢 Dados atualizados há {int(time_diff.total_seconds() / 60)} minutos por {last_upload['username']}")
        elif time_diff.total_seconds() < 3600:  # Less than 1 hour
            st.info(f"🔵 Dados atualizados há {int(time_diff.total_seconds() / 60)} minutos por {last_upload['username']}")
        else:
            hours = int(time_diff.total_seconds() / 3600)
            st.warning(f"🟡 Dados atualizados há {hours} hora(s) por {last_upload['username']}")

    if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data is not None:
        data = st.session_state.processed_data
        
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            st.error(f"Erro: processed_data não é um dicionário, é um {type(data)}")
            data = {}
        
        df = data.get('consolidated', pd.DataFrame())
        
        # Ensure df is actually a DataFrame
        if not isinstance(df, pd.DataFrame):
            # Try to reconstruct DataFrame if it's a dict with the right structure
            if isinstance(df, dict) and 'data' in df and 'columns' in df:
                try:
                    df = pd.DataFrame(df['data'], columns=df['columns'])
                    st.info("📊 Dados reconstruídos do cache")
                except:
                    st.error(f"Erro: Não foi possível reconstruir DataFrame dos dados em cache")
                    df = pd.DataFrame()
            else:
                st.error(f"Erro: Dados 'consolidados' não são um DataFrame, é um {type(df)}")
                # Clear the corrupted data and force reprocessing
                st.session_state.processed_data = None
                st.info("🔄 Por favor, clique em 'Analisar Dados' novamente para reprocessar")
                df = pd.DataFrame()  # Create empty DataFrame to prevent errors
        elif df.empty or 'year' not in df.columns:
            st.warning("⚠️ Os dados carregados parecem estar incompletos. Por favor, faça a análise dos dados novamente.")
            df = pd.DataFrame()  # Reset to empty to prevent errors
            
        summary = data.get('summary', {})
        
        # Ensure summary is a dictionary
        if not isinstance(summary, dict):
            st.warning(f"Summary data is not in expected format. Type: {type(summary)}")
            summary = {}


        # Ensure monthly data is available and has all required columns
        required_monthly_cols = ['variable_costs', 'fixed_costs', 'net_profit', 'profit_margin']
        monthly_data_invalid = (
            not hasattr(st.session_state, 'monthly_data') or 
            st.session_state.monthly_data is None or 
            not isinstance(st.session_state.monthly_data, pd.DataFrame) or
            st.session_state.monthly_data.empty or
            not all(col in st.session_state.monthly_data.columns for col in required_monthly_cols)
        )

        if monthly_data_invalid:
            # Extract monthly data from the known Excel files
            try:
                processor = FinancialProcessor()
        
                # Use the actual Excel files instead of the broken raw_data paths
                excel_files = [
                    "data/arquivos_enviados/Análise de Resultado Financeiro 2018_2023.xlsx",
                    "data/arquivos_enviados/Resultado Financeiro - 2024.xlsx", 
                    "data/arquivos_enviados/Resultado Financeiro - 2025.xlsx"
                ]
        
                # Create a properly formatted excel_data dict with existing files
                excel_data = {}
                for file_path in excel_files:
                    if os.path.exists(file_path):
                        excel_data[file_path] = None  # The processor will handle the file reading
        
                if excel_data:
                    monthly_data = processor.get_monthly_data(excel_data)
            
                    if monthly_data.empty:
                        st.error("❌ Falha ao extrair dados mensais dos arquivos Excel")
                    else:
                        st.success(f"✅ Dados mensais extraídos: {len(monthly_data)} registros de {len(excel_data)} arquivos")
                        st.info(f"Anos cobertos: {sorted(monthly_data['year'].unique()) if 'year' in monthly_data.columns else 'Desconhecido'}")
            
                    st.session_state.monthly_data = monthly_data
                else:
                    st.error("❌ Nenhum arquivo Excel encontrado para extração de dados mensais")
                    st.session_state.monthly_data = pd.DataFrame()
            
            except Exception as e:
                st.error(f"Error extracting monthly data: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                st.session_state.monthly_data = pd.DataFrame()


        # Time Period Filters
        st.subheader("🗓️ Filtros de Período")

        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)

        with col_filter1:
            view_type = st.selectbox(
                "Visualização",
                ["Anual", "Mensal", "Trimestral", "Trimestre Personalizado", "Semestral", "Personalizado"],
                key="view_type"
            )

        with col_filter2:
            if view_type in ["Mensal", "Trimestral", "Trimestre Personalizado", "Semestral", "Personalizado"]:
                # For monthly-based views, check if monthly data is available
                if view_type != "Anual" and hasattr(st.session_state, 'monthly_data') and st.session_state.monthly_data is not None and not st.session_state.monthly_data.empty:
                    available_years = sorted(st.session_state.monthly_data['year'].unique())
                elif not df.empty and 'year' in df.columns:
                    available_years = sorted(df['year'].unique())
                else:
                    available_years = []
                
                if available_years:
                    # Use saved selected_years if available and valid, otherwise default to last 3 years
                    saved_years = st.session_state.get('selected_years', [])
                    # Filter saved years to only include those that are available
                    valid_saved_years = [y for y in saved_years if y in available_years]
                    
                    default_years = (
                        valid_saved_years 
                        if valid_saved_years 
                        else available_years[-3:] if len(available_years) >= 3 else available_years
                    )
                    selected_years = st.multiselect(
                        "Anos",
                        available_years,
                        default=default_years,
                        key="dashboard_selected_years"
                    )
                else:
                    selected_years = []
            else:
                if not df.empty and 'year' in df.columns:
                    selected_years = sorted(df['year'].unique())
                else:
                    selected_years = []

        with col_filter3:
            if view_type == "Mensal":
                month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                # Use saved selected_months if available, otherwise default to all months
                # Convert from abbreviations back to full names
                abbrev_to_name = {
                    "JAN": "Janeiro", "FEV": "Fevereiro", "MAR": "Março", "ABR": "Abril",
                    "MAI": "Maio", "JUN": "Junho", "JUL": "Julho", "AGO": "Agosto",
                    "SET": "Setembro", "OUT": "Outubro", "NOV": "Novembro", "DEZ": "Dezembro"
                }
                saved_months = st.session_state.get('selected_months', [])
                default_months = (
                    [abbrev_to_name.get(m, m) for m in saved_months]
                    if saved_months
                    else month_names
                )
                selected_months = st.multiselect(
                    "Meses",
                    month_names,
                    default=default_months,
                    key="dashboard_selected_months"
                )
            elif view_type == "Trimestral":
                selected_quarter = st.multiselect(
                    "Trimestres",
                    ["Q1 (Jan-Mar)", "Q2 (Abr-Jun)", "Q3 (Jul-Set)", "Q4 (Out-Dez)"],
                    default=["Q1 (Jan-Mar)", "Q2 (Abr-Jun)", "Q3 (Jul-Set)", "Q4 (Out-Dez)"],
                    key="dashboard_selected_quarters"
                )
            elif view_type == "Trimestre Personalizado":
                month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                start_month = st.selectbox(
                    "Mês Inicial",
                    month_names,
                    key="start_month_custom"
                )
            elif view_type == "Semestral":
                selected_semester = st.multiselect(
                    "Semestres",
                    ["1º Semestre (Jan-Jun)", "2º Semestre (Jul-Dez)"],
                    default=["1º Semestre (Jan-Jun)", "2º Semestre (Jul-Dez)"],
                    key="dashboard_selected_semesters"
                )

        with col_filter4:
            if view_type == "Trimestre Personalizado":
                # Calculate end month options (3 months from start)
                month_map = {
                    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
                    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
                    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                }
                month_names = list(month_map.keys())
                start_idx = month_names.index(start_month)
        
                # End month is exactly 2 months after start (for a 3-month period)
                end_idx = (start_idx + 2) % 12
                end_month_display = month_names[end_idx]
        
                st.info(f"Trimestre: {start_month} a {end_month_display} (3 meses)")
                end_month = end_month_display
            elif view_type == "Personalizado":
                date_range = st.date_input(
                    "Período",
                    value=(pd.Timestamp(selected_years[0], 1, 1), pd.Timestamp(selected_years[-1], 12, 31)),
                    key="date_range"
                )
        
        # Save current filter selections to session state and database
        if view_type in ["Mensal", "Trimestral", "Trimestre Personalizado", "Semestral", "Personalizado"]:
            # Convert month names back to abbreviations for storage
            month_mapping = {
                "Janeiro": "JAN", "Fevereiro": "FEV", "Março": "MAR", "Abril": "ABR",
                "Maio": "MAI", "Junho": "JUN", "Julho": "JUL", "Agosto": "AGO",
                "Setembro": "SET", "Outubro": "OUT", "Novembro": "NOV", "Dezembro": "DEZ"
            }
            
            # Update session state
            st.session_state.selected_years = selected_years
            if view_type == "Mensal" and 'selected_months' in locals():
                st.session_state.selected_months = [month_mapping.get(m, m) for m in selected_months]
            
            # Save to database (non-blocking)
            try:
                db.save_filter_state(
                    st.session_state.get('selected_years', []),
                    st.session_state.get('selected_months', [])
                )
            except:
                pass  # Don't block UI if saving fails

        # Prepare data based on view type
        if view_type == "Anual":
            if not df.empty and 'year' in df.columns:
                if not df.empty and 'year' in df.columns:
                    display_df = df[df['year'].isin(selected_years)]
                else:
                    display_df = pd.DataFrame()
            else:
                display_df = pd.DataFrame()
                st.warning("⚠️ Dados não disponíveis. Por favor, faça a análise dos dados primeiro.")
        elif view_type == "Mensal":
            if not hasattr(st.session_state, 'monthly_data') or st.session_state.monthly_data is None or not isinstance(st.session_state.monthly_data, pd.DataFrame) or st.session_state.monthly_data.empty:
                st.warning("📋 Dados mensais não disponíveis. Mostrando visualização anual.")
                # Debug info
                if st.checkbox("Mostrar informações de debug"):
                    st.info(f"Debug: monthly_data exists: {hasattr(st.session_state, 'monthly_data')}")
                    if hasattr(st.session_state, 'monthly_data'):
                        st.info(f"Debug: monthly_data is None: {st.session_state.monthly_data is None}")
                        if st.session_state.monthly_data is not None:
                            st.info(f"Debug: monthly_data empty: {st.session_state.monthly_data.empty}")
                            st.info(f"Debug: monthly_data shape: {st.session_state.monthly_data.shape}")
                if not df.empty and 'year' in df.columns:
                    display_df = df[df['year'].isin(selected_years)]
                else:
                    display_df = pd.DataFrame()
            else:
                # Use monthly data
                monthly_df = st.session_state.monthly_data
        
                # Ensure month_num column exists
                if 'month_num' not in monthly_df.columns and 'month' in monthly_df.columns:
                    # Create month_num from month names
                    month_to_num = {
                        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
                        'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
                    }
                    monthly_df['month_num'] = monthly_df['month'].map(month_to_num)
        
                # Map month names to numbers
                month_map = {
                    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
                    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
                    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                }
                selected_month_nums = [month_map[m] for m in selected_months]
        
                display_df = monthly_df[
                    (monthly_df['year'].isin(selected_years)) &
                    (monthly_df['month_num'].isin(selected_month_nums))
                ].copy()  # Explicit copy to avoid any view issues
                
                # Sort by date for chronological order
                display_df = display_df.sort_values(['year', 'month_num'])
                
                # Add data refresh button
                col1, col2 = st.columns([6, 1])
                with col2:
                    if st.button("🔄 Atualizar Dados", help="Limpar cache e reprocessar dados", key="refresh_button"):
                        # Clear all cached data
                        keys_to_clear = ['processed_data', 'extracted_data', 'monthly_data', 'financial_data', 'gemini_insights', 'unified_data']
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        # Clear database cache
                        db.clear_session_data()
                        st.success("✅ Cache limpo! Clique em 'Analisar Dados Financeiros' para reprocessar.")
                        st.rerun()
                
        
        elif view_type == "Trimestral":
            if not hasattr(st.session_state, 'monthly_data') or st.session_state.monthly_data is None or not isinstance(st.session_state.monthly_data, pd.DataFrame) or st.session_state.monthly_data.empty:
                st.warning("📋 Dados mensais não disponíveis para visualização trimestral. Mostrando visualização anual.")
                if not df.empty and 'year' in df.columns:
                    display_df = df[df['year'].isin(selected_years)]
                else:
                    display_df = pd.DataFrame()
            else:
                # Aggregate monthly data by quarter
                monthly_df = st.session_state.monthly_data
    
                # Ensure month_num column exists
                if 'month_num' not in monthly_df.columns and 'month' in monthly_df.columns:
                    month_to_num = {
                        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
                        'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
                    }
                    monthly_df['month_num'] = monthly_df['month'].map(month_to_num)
        
                quarter_map = {
                    "Q1 (Jan-Mar)": [1, 2, 3],
                    "Q2 (Abr-Jun)": [4, 5, 6],
                    "Q3 (Jul-Set)": [7, 8, 9],
                    "Q4 (Out-Dez)": [10, 11, 12]
                }
                selected_months_for_quarters = []
                for q in selected_quarter:
                    selected_months_for_quarters.extend(quarter_map[q])
        
                filtered_monthly = monthly_df[
                    (monthly_df['year'].isin(selected_years)) &
                    (monthly_df['month_num'].isin(selected_months_for_quarters))
                ]
        
                # Aggregate by quarter
                filtered_monthly['quarter'] = (filtered_monthly['month_num'] - 1) // 3 + 1
                display_df = filtered_monthly.groupby(['year', 'quarter']).agg({
                    'revenue': 'sum',
                    'variable_costs': 'sum',
                    'fixed_costs': 'sum',
                    'operational_costs': 'sum',
                    'non_operational_costs': 'sum',
                    'taxes': 'sum',
                    'commissions': 'sum',
                    'admin_expenses': 'sum',
                    'marketing_expenses': 'sum',
                    'financial_expenses': 'sum',
                    'contribution_margin': 'sum',
                    'net_profit': 'sum',
                    'profit_margin': 'mean'  # Average the profit margins
                }).reset_index()
                display_df['period'] = display_df.apply(lambda x: f"{int(x['year'])}-Q{int(x['quarter'])}", axis=1)
        elif view_type == "Trimestre Personalizado":
            if not hasattr(st.session_state, 'monthly_data') or st.session_state.monthly_data is None or not isinstance(st.session_state.monthly_data, pd.DataFrame) or st.session_state.monthly_data.empty:
                st.warning("📋 Dados mensais não disponíveis para trimestre personalizado. Mostrando visualização anual.")
                if not df.empty and 'year' in df.columns:
                    display_df = df[df['year'].isin(selected_years)]
                else:
                    display_df = pd.DataFrame()
            else:
                # Custom trimester logic
                monthly_df = st.session_state.monthly_data
    
                # Ensure month_num column exists
                if 'month_num' not in monthly_df.columns and 'month' in monthly_df.columns:
                    month_to_num = {
                        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
                        'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
                    }
                    monthly_df['month_num'] = monthly_df['month'].map(month_to_num)
        
                month_map = {
                    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
                    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
                    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
                }
        
                start_month_num = month_map[start_month]
                end_month_num = month_map[end_month]
        
                # Handle year wrap-around
                if end_month_num < start_month_num:
                    # Trimester crosses year boundary
                    selected_months_nums = list(range(start_month_num, 13)) + list(range(1, end_month_num + 1))
                else:
                    selected_months_nums = list(range(start_month_num, end_month_num + 1))
        
                # Filter data
                filtered_monthly = monthly_df[
                    (monthly_df['year'].isin(selected_years)) &
                    (monthly_df['month_num'].isin(selected_months_nums))
                ].copy()
        
                # Group by year and custom trimester
                def get_custom_trimester(row):
                    if row['month_num'] in selected_months_nums:
                        # If the trimester crosses year boundary
                        if end_month_num < start_month_num and row['month_num'] < start_month_num:
                            return f"{int(row['year']-1)}/{int(row['year'])}"
                        else:
                            return str(int(row['year']))
                    return None
        
                filtered_monthly['custom_period'] = filtered_monthly.apply(get_custom_trimester, axis=1)
        
                # Aggregate by custom period
                display_df = filtered_monthly.groupby('custom_period').agg({
                    'revenue': 'sum',
                    'variable_costs': 'sum',
                    'fixed_costs': 'sum',
                    'operational_costs': 'sum',
                    'non_operational_costs': 'sum',
                    'taxes': 'sum',
                    'commissions': 'sum',
                    'admin_expenses': 'sum',
                    'marketing_expenses': 'sum',
                    'financial_expenses': 'sum',
                    'contribution_margin': 'sum',
                    'net_profit': 'sum',
                    'profit_margin': 'mean'  # Average the profit margins
                }).reset_index()
        
                # Add period label
                display_df['period'] = display_df['custom_period'].apply(
                    lambda x: f"{x} ({start_month[:3]}-{end_month[:3]})"
                )
                display_df['year'] = display_df['custom_period']  # For compatibility
        elif view_type == "Semestral":
            if not hasattr(st.session_state, 'monthly_data') or st.session_state.monthly_data is None or not isinstance(st.session_state.monthly_data, pd.DataFrame) or st.session_state.monthly_data.empty:
                st.warning("📋 Dados mensais não disponíveis para visualização semestral. Mostrando visualização anual.")
                if not df.empty and 'year' in df.columns:
                    display_df = df[df['year'].isin(selected_years)]
                else:
                    display_df = pd.DataFrame()
            else:
                # Aggregate monthly data by semester
                monthly_df = st.session_state.monthly_data
    
                # Ensure month_num column exists
                if 'month_num' not in monthly_df.columns and 'month' in monthly_df.columns:
                    month_to_num = {
                        'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
                        'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
                    }
                    monthly_df['month_num'] = monthly_df['month'].map(month_to_num)
        
                semester_map = {
                    "1º Semestre (Jan-Jun)": [1, 2, 3, 4, 5, 6],
                    "2º Semestre (Jul-Dez)": [7, 8, 9, 10, 11, 12]
                }
                selected_months_for_semesters = []
                for s in selected_semester:
                    selected_months_for_semesters.extend(semester_map[s])
        
                filtered_monthly = monthly_df[
                    (monthly_df['year'].isin(selected_years)) &
                    (monthly_df['month_num'].isin(selected_months_for_semesters))
                ]
        
                # Aggregate by semester
                filtered_monthly['semester'] = (filtered_monthly['month_num'] - 1) // 6 + 1
                display_df = filtered_monthly.groupby(['year', 'semester']).agg({
                    'revenue': 'sum',
                    'variable_costs': 'sum',
                    'fixed_costs': 'sum',
                    'operational_costs': 'sum',
                    'non_operational_costs': 'sum',
                    'taxes': 'sum',
                    'commissions': 'sum',
                    'admin_expenses': 'sum',
                    'marketing_expenses': 'sum',
                    'financial_expenses': 'sum',
                    'contribution_margin': 'sum',
                    'net_profit': 'sum',
                    'profit_margin': 'mean'  # Average the profit margins
                }).reset_index()
                display_df['period'] = display_df.apply(lambda x: f"{int(x['year'])}-S{int(x['semester'])}", axis=1)
        else:
            # Default to annual view if monthly data not available
            if not df.empty and 'year' in df.columns:
                display_df = df[df['year'].isin(selected_years)].copy()
            else:
                display_df = pd.DataFrame()
    
            # Ensure all numeric columns contain only numeric values (not dicts)
            numeric_cols = ['revenue', 'variable_costs', 'fixed_costs', 'operational_costs', 
                          'gross_profit', 'net_profit', 'contribution_margin']
            for col in numeric_cols:
                if col in display_df.columns:
                    # Convert any dict values to numbers
                    display_df[col] = display_df[col].apply(
                        lambda x: x.get('ANNUAL', 0) if isinstance(x, dict) else x
                    )

    
            # Ensure profit_margin column exists for all views
            if not display_df.empty:
                if 'profit_margin' not in display_df.columns and 'revenue' in display_df.columns and 'net_profit' in display_df.columns:
                    display_df['profit_margin'] = display_df.apply(
                        lambda row: (row['net_profit'] / row['revenue'] * 100) if row['revenue'] > 0 else 0,
                        axis=1
                    )
            else:
                st.caption("⚠️ Nenhum dado disponível para o período selecionado")

        # Key metrics - Calculate based on filtered data
        col1, col2, col3, col4 = st.columns(4)


        # Calculate net_profit if missing
        if 'net_profit' not in display_df.columns and not display_df.empty:
            display_df = display_df.copy()
    
            # Ensure all numeric columns are actually numeric (not dicts)
            for col in ['revenue', 'variable_costs', 'fixed_costs', 'operational_costs']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda x: x.get('ANNUAL', 0) if isinstance(x, dict) else x
                    )
    
            # Check if operational_costs exists and has values
            if 'operational_costs' in display_df.columns:
                operational_costs = display_df['operational_costs']
            else:
                operational_costs = 0
                if st.checkbox("⚠️ Aviso: operational_costs não encontrado", key="warn_op_costs"):
                    st.warning("Coluna 'operational_costs' não encontrada. Usando 0 para custos operacionais.")
    
            # Calculate net profit from available columns
            if all(col in display_df.columns for col in ['revenue', 'variable_costs', 'fixed_costs']):
                display_df['net_profit'] = display_df['revenue'] - display_df['variable_costs'] - display_df['fixed_costs'] - operational_costs
            elif 'gross_profit' in display_df.columns and 'fixed_costs' in display_df.columns:
                display_df['net_profit'] = display_df['gross_profit'] - display_df['fixed_costs'] - operational_costs

        # Calculate profit_margin only if missing
        if 'profit_margin' not in display_df.columns and 'net_profit' in display_df.columns and not display_df.empty:
            display_df = display_df.copy()
            display_df['profit_margin'] = (display_df['net_profit'] / display_df['revenue'] * 100).fillna(0)

        # Calculate metrics from filtered display_df
        total_revenue = display_df['revenue'].sum() if 'revenue' in display_df.columns and not display_df.empty else 0

        # Use existing profit data from the DataFrame
        if not display_df.empty:
            # Debug: Check data types and convert dicts to numbers
            numeric_cols = ['revenue', 'variable_costs', 'fixed_costs', 'net_profit', 'profit_margin']
            for col in numeric_cols:
                if col in display_df.columns:
                    # Check if any values are dicts
                    has_dicts = display_df[col].apply(lambda x: isinstance(x, dict)).any()
                    if has_dicts:
                        # Convert dict values to numbers (using ANNUAL key if available)
                        display_df[col] = display_df[col].apply(
                            lambda x: x.get('ANNUAL', 0) if isinstance(x, dict) else x
                        )
    
            # Use the existing net_profit and profit_margin from the data
            total_profit = display_df['net_profit'].sum() if 'net_profit' in display_df.columns else 0
            avg_profit = display_df['net_profit'].mean() if 'net_profit' in display_df.columns else 0
            avg_margin = display_df['profit_margin'].mean() if 'profit_margin' in display_df.columns else 0
    
        else:
            # Fallback to DataFrame values if we can't calculate
            total_profit = display_df['net_profit'].sum() if 'net_profit' in display_df.columns and not display_df.empty else 0
            avg_profit = display_df['net_profit'].mean() if 'net_profit' in display_df.columns and not display_df.empty else 0
            avg_margin = display_df['profit_margin'].mean() if 'profit_margin' in display_df.columns and not display_df.empty else 0

        # For period views, show period count
        if view_type != 'Anual':
            period_label = f"{len(display_df)} {'meses' if view_type == 'Mensal' else 'períodos'}"
        else:
            # Safely get CAGR value
            cagr = 0
            if isinstance(summary, dict) and 'metrics' in summary:
                metrics = summary['metrics']
                if isinstance(metrics, dict) and 'revenue' in metrics:
                    revenue_metrics = metrics['revenue']
                    if isinstance(revenue_metrics, dict):
                        cagr = revenue_metrics.get('cagr', 0)
            period_label = f"{cagr:.1f}% CAGR"

        with col1:
            st.metric(
                "Receita Total",
                format_currency(total_revenue),
                period_label
            )

        with col2:
            # For yearly view, show total profit and clarify it's total across all years
            if view_type == "Anual":
                profit_label = "Lucro Total (Todos os Anos)"
                profit_value = total_profit
                profit_delta = f"Média anual: {format_currency(avg_profit)}"
            else:
                profit_label = "Lucro Total"
                profit_value = total_profit
                profit_delta = f"{(total_profit / total_revenue * 100) if total_revenue > 0 else 0:.1f}% da receita"
    
            st.metric(
                profit_label,
                format_currency(profit_value),
                profit_delta
            )

        with col3:
            margin_range = display_df['profit_margin'].max() - display_df['profit_margin'].min() if 'profit_margin' in display_df.columns and not display_df.empty else 0
            st.metric(
                "Margem de Lucro Média",
                f"{avg_margin:.2f}%",
                f"{margin_range:.2f}pp variação"
            )

        with col4:
            if hasattr(st.session_state, 'unified_data') and st.session_state.unified_data:
                total_items = sum(
                    len(year_data.get('line_items', {})) 
                    for year_data in st.session_state.unified_data.values()
                ) / len(st.session_state.unified_data)
                st.metric(
                    "Linhas de Dados",
                    f"{int(total_items)}",
                    "Média por ano"
                )
            else:
                st.metric(
                    "Anos Analisados",
                    summary.get('total_years', 0),
                    summary.get('years_range', 'N/A')
                )


        # Revenue Evolution Chart
        st.subheader("📈 Evolução da Receita")
        if not display_df.empty and 'revenue' in display_df.columns and display_df['revenue'].sum() > 0:
            x_col, x_title = prepare_x_axis(display_df, view_type)
    
            fig_revenue = px.line(
                display_df, 
                x=x_col, 
                y='revenue',
                title=f'Receita {view_type}',
                markers=True
            )
    
            # Add text annotations with smart positioning for monthly view
            if view_type == "Mensal" and len(display_df) > 20:
                # For crowded monthly view, show values on hover only
                fig_revenue.update_traces(
                    hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>'
                )
            else:
                # For less crowded views, show selected values
                fig_revenue.add_trace(go.Scatter(
                    x=display_df[x_col],
                    y=display_df['revenue'],
                    mode='text',
                    text=[f'R$ {v:,.0f}' if i % 3 == 0 or v == display_df['revenue'].max() or v == display_df['revenue'].min() 
                          else '' for i, v in enumerate(display_df['revenue'])],
                    textposition='top center',
                    textfont=dict(size=10),
                    showlegend=False
                ))
            # For monthly view with many data points, add interactive features
            if view_type == "Mensal":
                xaxis_config = dict(
                    tickangle=-45,
                    tickmode='linear',
                    **get_monthly_layout_config()
                )
                
                # Set default range to show last 12 months
                default_range = get_default_monthly_range(display_df, x_col)
                if default_range:
                    xaxis_config['range'] = default_range
                    
                fig_revenue.update_layout(
                    yaxis_title="Receita (R$)",
                    xaxis_title=x_title,
                    hovermode='x unified',
                    xaxis=xaxis_config,
                    height=600,
                    margin=dict(t=100, b=100),
                    dragmode='pan'  # Enable panning by default
                )
                # Configure modebar for better interaction
                config = {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToAdd': ['pan2d', 'zoom2d', 'resetScale2d'],
                    'scrollZoom': True
                }
                st.plotly_chart(fig_revenue, use_container_width=True, config=config)
            else:
                fig_revenue.update_layout(
                    yaxis_title="Receita (R$)",
                    xaxis_title=x_title,
                    hovermode='x unified',
                    xaxis=dict(
                        tickangle=-45 if view_type == "Mensal" else 0,
                        tickmode='linear',
                        dtick=1 if view_type == "Anual" else None,
                        type='category' if view_type == "Anual" else None,
                        categoryorder='category ascending' if view_type == "Anual" else None
                    ),
                    height=500 if view_type == "Mensal" else 400,
                    margin=dict(t=50, b=100 if view_type == "Mensal" else 100)
                )
                st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            if display_df.empty:
                st.info("📊 Nenhum dado disponível para o período selecionado. Verifique os filtros.")
            else:
                st.info("📊 Dados de receita não disponíveis")

        # Profit Margin Evolution
        if not display_df.empty and 'profit_margin' in display_df.columns:
            st.subheader("📊 Margem de Lucro")
            x_col, x_title = prepare_x_axis(display_df, view_type)
    
            # Don't recalculate profit margin - we already have it from aggregation or extraction
            # The profit margin is either:
            # - Extracted from Excel for Anual/Mensal views
            # - Averaged during aggregation for Trimestral/Semestral views
            # Only calculate if the column is completely missing
            if 'profit_margin' not in display_df.columns:
                display_df['profit_margin'] = (display_df['net_profit'] / display_df['revenue'] * 100).fillna(0)
    
            fig_margin = px.bar(
                display_df,
                x=x_col,
                y='profit_margin',
                title=f'Margem de Lucro {view_type} (%)',
                color='profit_margin',
                color_continuous_scale='RdYlGn'
            )
    
            # Always show values on bars
            fig_margin.update_traces(
                text=display_df['profit_margin'].apply(lambda x: f'{x:.2f}%'),
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Margem de Lucro: %{y:.2f}%<extra></extra>'
            )
    
            # Apply interactive features for monthly view
            if view_type == "Mensal":
                xaxis_config = get_monthly_xaxis_config(display_df, x_col)
                    
                fig_margin.update_layout(
                    yaxis_title="Margem de Lucro (%)",
                    xaxis_title=x_title,
                    coloraxis_colorbar=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        len=0.6,
                        thickness=15
                    ),
                    xaxis=xaxis_config,
                    height=600,
                    margin=dict(t=100, b=100),
                    showlegend=False,
                    dragmode='pan'
                )
                st.plotly_chart(fig_margin, use_container_width=True, config=get_plotly_config())
            else:
                fig_margin.update_layout(
                    yaxis_title="Margem de Lucro (%)",
                    xaxis_title=x_title,
                    coloraxis_colorbar=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        len=0.6,
                        thickness=15
                    ),
                    xaxis=dict(
                        tickangle=-45 if view_type == "Mensal" else 0,
                        tickmode='linear',
                        dtick=1 if view_type == "Anual" else (2 if view_type == "Mensal" and len(display_df) > 24 else None),
                        type='category' if view_type == "Anual" else None,
                        categoryorder='category ascending' if view_type == "Anual" else None
                    ),
                    height=450 if view_type == "Mensal" else 400,
                    margin=dict(t=80, b=100 if view_type == "Mensal" else 100),
                    showlegend=False
                )
                st.plotly_chart(fig_margin, use_container_width=True)

        # New Financial Metrics Graphs
        st.subheader("📊 Análise de Custos e Margens")

        # 1. Variable Costs vs Revenue Comparison - Full width
        if not display_df.empty and 'variable_costs' in display_df.columns and 'revenue' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
    
            # Create figure with revenue and variable costs
            fig_var_costs = go.Figure()
            
            # Add revenue line (lighter/background)
            fig_var_costs.add_trace(go.Scatter(
                x=display_df[x_col],
                y=display_df['revenue'],
                name='Receita',
                mode='lines+markers',
                line=dict(color='#1f77b4', width=3, dash='dot'),
                marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>'
            ))
            
            # Add variable costs line (highlighted)
            fig_var_costs.add_trace(go.Scatter(
                x=display_df[x_col],
                y=display_df['variable_costs'],
                name='Custos Variáveis',
                mode='lines+markers',
                line=dict(color='#ff7f0e', width=4),
                marker=dict(size=10),
                hovertemplate='<b>%{x}</b><br>Custos Variáveis: R$ %{y:,.0f}<extra></extra>'
            ))
            
            # Calculate percentages for both cost types
            display_df['var_cost_pct'] = (display_df['variable_costs'] / display_df['revenue'] * 100).fillna(0)
            if 'fixed_costs' in display_df.columns:
                display_df['fixed_cost_pct'] = (display_df['fixed_costs'] / display_df['revenue'] * 100).fillna(0)
            
            # Update variable costs trace to include percentage
            fig_var_costs.data[1].update(
                customdata=display_df['var_cost_pct'],
                hovertemplate='<b>%{x}</b><br>Custos Variáveis: R$ %{y:,.0f}<br>% da Receita: %{customdata:.1f}%<extra></extra>'
            )
            
            # Add fixed costs line
            if 'fixed_costs' in display_df.columns:
                fig_var_costs.add_trace(go.Scatter(
                    x=display_df[x_col],
                    y=display_df['fixed_costs'],
                    name='Custos Fixos',
                    mode='lines+markers',
                    line=dict(color='#d62728', width=3),
                    marker=dict(size=8, symbol='square'),
                    customdata=display_df['fixed_cost_pct'],
                    hovertemplate='<b>%{x}</b><br>Custos Fixos: R$ %{y:,.0f}<br>% da Receita: %{customdata:.1f}%<extra></extra>'
                ))
            
            # Add text annotations with smart positioning
            if view_type != "Mensal" or len(display_df) <= 20:
                # For annual/quarterly views, show percentage on variable costs line
                fig_var_costs.add_trace(go.Scatter(
                    x=display_df[x_col],
                    y=display_df['variable_costs'],
                    mode='text',
                    text=[f'{pct:.1f}%' for pct in display_df['var_cost_pct']],
                    textposition='top center',
                    textfont=dict(size=10, color='#ff7f0e', weight='bold'),
                    showlegend=False
                ))
                
                # Add percentage annotations for fixed costs if available
                if 'fixed_costs' in display_df.columns and 'fixed_cost_pct' in display_df.columns:
                    fig_var_costs.add_trace(go.Scatter(
                        x=display_df[x_col],
                        y=display_df['fixed_costs'],
                        mode='text',
                        text=[f'{pct:.1f}%' for pct in display_df['fixed_cost_pct']],
                        textposition='bottom center',
                        textfont=dict(size=10, color='#d62728', weight='bold'),
                        showlegend=False
                    ))
    
            # Apply interactive features for monthly view
            if view_type == "Mensal":
                xaxis_config = get_monthly_xaxis_config(display_df, x_col)
                    
                fig_var_costs.update_layout(
                    title='💸 Custos Variáveis e Fixos vs Receita',
                    yaxis_title="Valores (R$)",
                    xaxis_title=x_title,
                    xaxis=xaxis_config,
                    height=600,
                    margin=dict(t=100, b=100),
                    hovermode='closest',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    dragmode='pan'
                )
                
                # Add shaded area between lines to highlight the gap
                fig_var_costs.add_trace(go.Scatter(
                    x=display_df[x_col].tolist() + display_df[x_col].tolist()[::-1],
                    y=display_df['revenue'].tolist() + display_df['variable_costs'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(31, 119, 180, 0.1)',
                    line=dict(color='rgba(255,255,255,0)'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                st.plotly_chart(fig_var_costs, use_container_width=True, config=get_plotly_config())
            else:
                fig_var_costs.update_layout(
                    title='💸 Custos Variáveis e Fixos vs Receita',
                    yaxis_title="Valores (R$)",
                    xaxis_title=x_title,
                    xaxis=dict(
                        tickangle=-45 if view_type == "Mensal" else 0,
                        tickmode='linear',
                        dtick=1 if view_type == "Anual" else (2 if view_type == "Mensal" and len(display_df) > 24 else None),
                        type='category' if view_type == "Anual" else None,
                        categoryorder='category ascending' if view_type == "Anual" else None
                    ),
                    height=500 if view_type == "Mensal" else 450,
                    margin=dict(t=50, b=100 if view_type == "Mensal" else 100),
                    hovermode='closest',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                # Add shaded area between lines to highlight the gap
                fig_var_costs.add_trace(go.Scatter(
                    x=display_df[x_col].tolist() + display_df[x_col].tolist()[::-1],
                    y=display_df['revenue'].tolist() + display_df['variable_costs'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(31, 119, 180, 0.1)',
                    line=dict(color='rgba(255,255,255,0)'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                st.plotly_chart(fig_var_costs, use_container_width=True)

        # 2. Fixed Costs - Full width
        if not display_df.empty and 'fixed_costs' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            # Calculate percentage if not already calculated
            if 'revenue' in display_df.columns:
                display_df['fixed_cost_pct'] = (display_df['fixed_costs'] / display_df['revenue'] * 100).fillna(0)
    
            # Create figure with bars for fixed costs
            fig_fixed = go.Figure()
            
            # Add fixed costs bars with percentage in hover
            fig_fixed.add_trace(go.Bar(
                x=display_df[x_col],
                y=display_df['fixed_costs'],
                name='Custos Fixos',
                marker_color='#2ca02c',
                text=[f'R$ {v:,.0f}' if i % 2 == 0 or view_type == "Anual" else '' for i, v in enumerate(display_df['fixed_costs'])] if view_type != "Mensal" or len(display_df) <= 20 else None,
                textposition='outside',
                customdata=display_df['fixed_cost_pct'] if 'fixed_cost_pct' in display_df.columns else None,
                hovertemplate='<b>%{x}</b><br>Custos Fixos: R$ %{y:,.0f}<br>% da Receita: %{customdata:.1f}%<extra></extra>'
            ))
            
            # Add revenue line for comparison (same axis)
            if 'revenue' in display_df.columns:
                fig_fixed.add_trace(go.Scatter(
                    x=display_df[x_col],
                    y=display_df['revenue'],
                    name='Receita',
                    mode='lines+markers',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>'
                ))
    
            # Apply interactive features for monthly view
            if view_type == "Mensal":
                xaxis_config = get_monthly_xaxis_config(display_df, x_col)
                    
                fig_fixed.update_layout(
                    title='🏢 Custos Fixos vs Receita',
                    yaxis_title="Valores (R$)",
                    xaxis_title=x_title,
                    xaxis=xaxis_config,
                    height=600,
                    margin=dict(t=100, b=100),
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    dragmode='pan'
                )
                st.plotly_chart(fig_fixed, use_container_width=True, config=get_plotly_config())
            else:
                fig_fixed.update_layout(
                    title='🏢 Custos Fixos vs Receita',
                    yaxis_title="Valores (R$)",
                    xaxis_title=x_title,
                    xaxis=dict(
                        tickangle=-45 if view_type == "Mensal" else 0,
                        tickmode='linear',
                        dtick=1 if view_type == "Anual" else (2 if view_type == "Mensal" and len(display_df) > 24 else None),
                        type='category' if view_type == "Anual" else None,
                        categoryorder='category ascending' if view_type == "Anual" else None
                    ),
                    height=450 if view_type == "Mensal" else 400,
                    margin=dict(t=50, b=100 if view_type == "Mensal" else 100),
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                st.plotly_chart(fig_fixed, use_container_width=True)

        # 3. Variable Costs - Full width (similar to Fixed Costs)
        if not display_df.empty and 'variable_costs' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            # Calculate percentage if not already calculated
            if 'revenue' in display_df.columns:
                display_df['var_cost_pct'] = (display_df['variable_costs'] / display_df['revenue'] * 100).fillna(0)
    
            # Create figure with bars for variable costs
            fig_variable = go.Figure()
            
            # Add variable costs bars with percentage in hover
            fig_variable.add_trace(go.Bar(
                x=display_df[x_col],
                y=display_df['variable_costs'],
                name='Custos Variáveis',
                marker_color='#ff7f0e',
                text=[f'R$ {v:,.0f}' if i % 2 == 0 or view_type == "Anual" else '' for i, v in enumerate(display_df['variable_costs'])] if view_type != "Mensal" or len(display_df) <= 20 else None,
                textposition='outside',
                customdata=display_df['var_cost_pct'] if 'var_cost_pct' in display_df.columns else None,
                hovertemplate='<b>%{x}</b><br>Custos Variáveis: R$ %{y:,.0f}<br>% da Receita: %{customdata:.1f}%<extra></extra>'
            ))
            
            # Add revenue line for comparison (same axis)
            if 'revenue' in display_df.columns:
                fig_variable.add_trace(go.Scatter(
                    x=display_df[x_col],
                    y=display_df['revenue'],
                    name='Receita',
                    mode='lines+markers',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>'
                ))
    
            # Apply interactive features for monthly view
            if view_type == "Mensal":
                xaxis_config = get_monthly_xaxis_config(display_df, x_col)
                    
                fig_variable.update_layout(
                    title='📦 Custos Variáveis vs Receita',
                    yaxis_title="Valores (R$)",
                    xaxis_title=x_title,
                    xaxis=xaxis_config,
                    height=600,
                    margin=dict(t=100, b=100),
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    ),
                    dragmode='pan'
                )
                st.plotly_chart(fig_variable, use_container_width=True, config=get_plotly_config())
            else:
                fig_variable.update_layout(
                    title='📦 Custos Variáveis vs Receita',
                    yaxis_title="Valores (R$)",
                    xaxis_title=x_title,
                    xaxis=dict(
                        tickangle=-45 if view_type == "Mensal" else 0,
                        tickmode='linear',
                        dtick=1 if view_type == "Anual" else (2 if view_type == "Mensal" and len(display_df) > 24 else None),
                        type='category' if view_type == "Anual" else None,
                        categoryorder='category ascending' if view_type == "Anual" else None
                    ),
                    height=450 if view_type == "Mensal" else 400,
                    margin=dict(t=80, b=100 if view_type == "Mensal" else 100),
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5
                    )
                )
                st.plotly_chart(fig_variable, use_container_width=True)

        # 4. Contribution Margin - Full width
        if not display_df.empty and 'contribution_margin' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
    
            fig_contrib = px.bar(
                display_df,
                x=x_col,
                y='contribution_margin',
                title='📈 Margem de Contribuição',
                color='contribution_margin',
                color_continuous_scale='Greens'
            )
    
            # Always show values on top of bars
            fig_contrib.update_traces(
                text=[f'R$ {v:,.0f}' for v in display_df['contribution_margin']],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Margem de Contribuição: R$ %{y:,.0f}<extra></extra>'
            )
    
            # Apply interactive features for monthly view
            if view_type == "Mensal":
                xaxis_config = get_monthly_xaxis_config(display_df, x_col)
                    
                fig_contrib.update_layout(
                    yaxis_title="Margem de Contribuição (R$)",
                    xaxis_title=x_title,
                    showlegend=False,
                    coloraxis_colorbar=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        len=0.6,
                        thickness=15
                    ),
                    xaxis=xaxis_config,
                    height=600,
                    margin=dict(t=100, b=100),
                    dragmode='pan'
                )
                st.plotly_chart(fig_contrib, use_container_width=True, config=get_plotly_config())
            else:
                fig_contrib.update_layout(
                    yaxis_title="Margem de Contribuição (R$)",
                    xaxis_title=x_title,
                    showlegend=False,
                    coloraxis_colorbar=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        len=0.6,
                        thickness=15
                    ),
                    xaxis=dict(
                        tickangle=-45 if view_type == "Mensal" else 0,
                        tickmode='linear',
                        dtick=1 if view_type == "Anual" else (2 if view_type == "Mensal" and len(display_df) > 24 else None),
                        type='category' if view_type == "Anual" else None,
                        categoryorder='category ascending' if view_type == "Anual" else None
                    ),
                    height=450 if view_type == "Mensal" else 400,
                    margin=dict(t=80, b=100 if view_type == "Mensal" else 100)
                )
                st.plotly_chart(fig_contrib, use_container_width=True)

        # 4. Operational Costs - Full width  
        st.subheader("⚙️ Custos Operacionais")
        
        if not display_df.empty and ('operational_costs' in display_df.columns or 
                                     ('fixed_costs' in display_df.columns and 'variable_costs' in display_df.columns)):
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            # Creating operational costs chart
            
            # Calculate percentage of operational costs relative to revenue
            if 'revenue' in display_df.columns and 'fixed_costs' in display_df.columns and 'variable_costs' in display_df.columns:
                display_df['op_cost_pct'] = ((display_df['fixed_costs'] + display_df['variable_costs']) / display_df['revenue'] * 100).fillna(0)
            elif 'revenue' in display_df.columns:
                display_df['op_cost_pct'] = (display_df.get('operational_costs', 0) / display_df['revenue'] * 100).fillna(0)
    
            # Calculate total operational costs as fixed + variable
            # First ensure all numeric columns contain only numeric values (not dicts)
            numeric_cols = ['revenue', 'variable_costs', 'fixed_costs', 'operational_costs', 'costs']
            for col in numeric_cols:
                if col in display_df.columns:
                    # Convert any dict values to numbers
                    display_df[col] = display_df[col].apply(
                        lambda x: x.get('ANNUAL', 0) if isinstance(x, dict) else x
                    )
            
            # Check for different possible column names
            var_costs_col = None
            if 'variable_costs' in display_df.columns:
                var_costs_col = 'variable_costs'
            elif 'costs' in display_df.columns:
                var_costs_col = 'costs'
            
            if 'fixed_costs' in display_df.columns and var_costs_col:
                # Ensure both columns have numeric values
                display_df['fixed_costs'] = pd.to_numeric(display_df['fixed_costs'], errors='coerce').fillna(0)
                display_df[var_costs_col] = pd.to_numeric(display_df[var_costs_col], errors='coerce').fillna(0)
                
                display_df['total_operational_costs'] = display_df['fixed_costs'] + display_df[var_costs_col]
                
                # Calculation complete
            else:
                # Fallback to existing operational_costs if columns not available
                if 'operational_costs' in display_df.columns:
                    display_df['operational_costs'] = pd.to_numeric(display_df['operational_costs'], errors='coerce').fillna(0)
                    display_df['total_operational_costs'] = display_df['operational_costs']
                else:
                    display_df['total_operational_costs'] = 0
                pass  # Using fallback operational_costs
            
            fig_op_costs = px.area(
                display_df,
                x=x_col,
                y='total_operational_costs',
                title='⚙️ Custos Operacionais (Fixos + Variáveis)',
                color_discrete_sequence=['#8B4513'],  # Brown color
                text='total_operational_costs'
            )
            
            # Format text labels
            fig_op_costs.update_traces(
                texttemplate='R$ %{text:,.0f}',
                textposition='top center'
            )
            
            # Update hover template to include percentage and ensure we show the total operational costs
            if 'op_cost_pct' in display_df.columns:
                # Create custom data with both the total value and percentage
                customdata = list(zip(display_df['total_operational_costs'], display_df['op_cost_pct']))
                fig_op_costs.update_traces(
                    customdata=customdata,
                    hovertemplate='<b>%{x}</b><br>Custos Operacionais: R$ %{customdata[0]:,.0f}<br>% da Receita: %{customdata[1]:.1f}%<extra></extra>'
                )
    
            # Apply interactive features for monthly view
            if view_type == "Mensal":
                xaxis_config = get_monthly_xaxis_config(display_df, x_col)
                    
                fig_op_costs.update_layout(
                    yaxis_title="Custos Operacionais (R$)",
                    xaxis_title=x_title,
                    xaxis=xaxis_config,
                    height=600,
                    margin=dict(t=100, b=100),
                    hovermode='x unified',
                    dragmode='pan'
                )
                st.plotly_chart(fig_op_costs, use_container_width=True, config=get_plotly_config())
            else:
                fig_op_costs.update_layout(
                    yaxis_title="Custos Operacionais (R$)",
                    xaxis_title=x_title,
                    xaxis=dict(
                        tickangle=-45 if view_type == "Mensal" else 0,
                        tickmode='linear',
                        dtick=1 if view_type == "Anual" else (2 if view_type == "Mensal" and len(display_df) > 24 else None),
                        type='category' if view_type == "Anual" else None,
                        categoryorder='category ascending' if view_type == "Anual" else None
                    ),
                    height=450 if view_type == "Mensal" else 400,
                    margin=dict(t=50, b=100 if view_type == "Mensal" else 100),
                    hovermode='x unified'
                )
                st.plotly_chart(fig_op_costs, use_container_width=True)

        # 4.5. Non-Operational Costs - Full width
        st.subheader("💸 Custos Não Operacionais")
        
        if not display_df.empty and 'non_operational_costs' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
            
            # Ensure non_operational_costs is numeric
            display_df['non_operational_costs'] = pd.to_numeric(display_df['non_operational_costs'], errors='coerce').fillna(0)
            
            # Calculate percentage of non-operational costs relative to revenue
            if 'revenue' in display_df.columns:
                display_df['non_op_cost_pct'] = (display_df['non_operational_costs'] / display_df['revenue'] * 100).fillna(0)
            
            fig_non_op_costs = px.area(
                display_df,
                x=x_col,
                y='non_operational_costs',
                title='💸 Custos Não Operacionais',
                color_discrete_sequence=['#FF6B6B'],  # Red color
                text='non_operational_costs'
            )
            
            # Format text labels
            fig_non_op_costs.update_traces(
                texttemplate='R$ %{text:,.0f}',
                textposition='top center'
            )
            
            # Update hover template to include percentage
            if 'non_op_cost_pct' in display_df.columns:
                customdata = list(zip(display_df['non_operational_costs'], display_df['non_op_cost_pct']))
                fig_non_op_costs.update_traces(
                    customdata=customdata,
                    hovertemplate='<b>%{x}</b><br>Custos Não Operacionais: R$ %{customdata[0]:,.0f}<br>% da Receita: %{customdata[1]:.1f}%<extra></extra>'
                )
            
            # Apply interactive features for monthly view
            if view_type == "Mensal":
                xaxis_config = get_monthly_xaxis_config(display_df, x_col)
                
                fig_non_op_costs.update_layout(
                    yaxis_title="Custos Não Operacionais (R$)",
                    xaxis_title=x_title,
                    xaxis=xaxis_config,
                    height=600,
                    margin=dict(t=100, b=100),
                    hovermode='x unified',
                    dragmode='pan'
                )
                st.plotly_chart(fig_non_op_costs, use_container_width=True, config=get_plotly_config())
            else:
                fig_non_op_costs.update_layout(
                    yaxis_title="Custos Não Operacionais (R$)",
                    xaxis_title=x_title,
                    xaxis=dict(
                        tickangle=-45 if view_type == "Mensal" else 0,
                        tickmode='linear',
                        dtick=1 if view_type == "Anual" else (2 if view_type == "Mensal" and len(display_df) > 24 else None),
                        type='category' if view_type == "Anual" else None,
                        categoryorder='category ascending' if view_type == "Anual" else None
                    ),
                    height=450 if view_type == "Mensal" else 400,
                    margin=dict(t=50, b=100 if view_type == "Mensal" else 100),
                    hovermode='x unified'
                )
                st.plotly_chart(fig_non_op_costs, use_container_width=True)

        # 5. Result (Profit) - Full width
        st.subheader("💰 Resultado (Lucro Líquido)")
        if not display_df.empty and 'net_profit' in display_df.columns:
            x_col, x_title = prepare_x_axis(display_df, view_type)
    
            # Create a color scale based on positive/negative values
            colors = ['red' if x < 0 else 'green' for x in display_df['net_profit']]
    
            fig_result = go.Figure()
            fig_result.add_trace(go.Bar(
                x=display_df[x_col],
                y=display_df['net_profit'],
                text=display_df['net_profit'].apply(lambda x: f'R$ {x:,.0f}'),
                textposition='outside',
                marker_color=colors,
                name='Resultado'
            ))
    
            # Add a zero line
            fig_result.add_hline(y=0, line_dash="dash", line_color="gray")
    
            # Apply interactive features for monthly view
            if view_type == "Mensal":
                xaxis_config = get_monthly_xaxis_config(display_df, x_col)
                    
                fig_result.update_layout(
                    title=f'Resultado {view_type} (Lucro/Prejuízo)',
                    yaxis_title="Resultado (R$)",
                    xaxis_title=x_title,
                    xaxis=xaxis_config,
                    height=600,
                    margin=dict(t=100, b=100),
                    showlegend=False,
                    dragmode='pan'
                )
                st.plotly_chart(fig_result, use_container_width=True, config=get_plotly_config())
            else:
                fig_result.update_layout(
                    title=f'Resultado {view_type} (Lucro/Prejuízo)',
                    yaxis_title="Resultado (R$)",
                    xaxis_title=x_title,
                    height=500,
                    showlegend=False
                )
                st.plotly_chart(fig_result, use_container_width=True)

        # Cost Structure Comparison
        st.subheader("📊 Estrutura de Custos")
        if not display_df.empty and all(col in display_df.columns for col in ['variable_costs', 'fixed_costs', 'revenue']):
            x_col, x_title = prepare_x_axis(display_df, view_type)
    
            # Use actual net_profit from data
            if 'net_profit' in display_df.columns:
                display_df['profit'] = display_df['net_profit']
            else:
                # Simple calculation: Revenue - Variable Costs - Fixed Costs - Non-Op Costs = Profit
                basic_costs = display_df['variable_costs'] + display_df['fixed_costs']
                if 'non_operational_costs' in display_df.columns:
                    basic_costs += display_df['non_operational_costs']
                display_df['profit'] = display_df['revenue'] - basic_costs
            
            # Create stacked bar chart with improved styling
            fig_cost_structure = go.Figure()
    
            # Calculate percentages of revenue for the categories
            display_df['var_cost_pct'] = (display_df['variable_costs'] / display_df['revenue'] * 100).fillna(0)
            display_df['fixed_cost_pct'] = (display_df['fixed_costs'] / display_df['revenue'] * 100).fillna(0)
            
            # Initialize non-operational costs if not present
            if 'non_operational_costs' not in display_df.columns:
                # Debug: This shouldn't happen if monthly data is correct
                print(f"WARNING: non_operational_costs missing from display_df. Columns: {list(display_df.columns)}")
                display_df['non_operational_costs'] = 0
            display_df['non_op_cost_pct'] = (display_df['non_operational_costs'] / display_df['revenue'] * 100).fillna(0)
            
            display_df['profit_pct'] = (display_df['profit'] / display_df['revenue'] * 100).fillna(0)
    
            # Add variable costs bar (as percentage)
            fig_cost_structure.add_trace(go.Bar(
                name='Custos Variáveis',
                x=display_df[x_col],
                y=display_df['var_cost_pct'],
                text=display_df['var_cost_pct'].apply(lambda x: f"{x:.2f}%"),
                textposition='inside',
                textfont=dict(color='white', size=11, weight='bold'),
                marker=dict(
                    color='#6366F1',  # Modern purple/indigo for variable costs
                    line=dict(color='#4F46E5', width=1)
                ),
                hovertemplate='<b>Custos Variáveis</b><br>' +
                             'Percentual: %{y:.1f}%<br>' +
                             'Valor: R$ %{customdata[0]:,.0f}<br>' +
                             '<b>Receita Total: R$ %{customdata[1]:,.0f}</b><br>' +
                             '<extra></extra>',
                customdata=list(zip(display_df['variable_costs'], display_df['revenue']))
            ))
    
            # Add fixed costs bar (as percentage)
            fig_cost_structure.add_trace(go.Bar(
                name='Custos Fixos',
                x=display_df[x_col],
                y=display_df['fixed_cost_pct'],
                text=display_df['fixed_cost_pct'].apply(lambda x: f"{x:.2f}%"),
                textposition='inside',
                textfont=dict(color='white', size=11, weight='bold'),
                marker=dict(
                    color='#F59E0B',  # Professional amber for fixed costs
                    line=dict(color='#D97706', width=1)
                ),
                hovertemplate='<b>Custos Fixos</b><br>' +
                             'Percentual: %{y:.1f}%<br>' +
                             'Valor: R$ %{customdata[0]:,.0f}<br>' +
                             '<b>Receita Total: R$ %{customdata[1]:,.0f}</b><br>' +
                             '<extra></extra>',
                customdata=list(zip(display_df['fixed_costs'], display_df['revenue']))
            ))
    
            # Add non-operational costs bar (always show, even if zero)
            fig_cost_structure.add_trace(go.Bar(
                name='Custos Não Operacionais',
                x=display_df[x_col],
                y=display_df['non_op_cost_pct'],
                text=display_df['non_op_cost_pct'].apply(lambda x: f"{x:.2f}%"),
                textposition='inside',
                textfont=dict(color='white', size=11, weight='bold'),
                marker=dict(
                    color='#EF4444',  # Red for non-operational costs
                    line=dict(color='#DC2626', width=1)
                ),
                hovertemplate='<b>Custos Não Operacionais</b><br>' +
                             'Percentual: %{y:.1f}%<br>' +
                             'Valor: R$ %{customdata[0]:,.0f}<br>' +
                             '<b>Receita Total: R$ %{customdata[1]:,.0f}</b><br>' +
                             '<extra></extra>',
                customdata=list(zip(display_df['non_operational_costs'], display_df['revenue']))
            ))
    
            # Add profit margin bar
            fig_cost_structure.add_trace(go.Bar(
                name='Margem de Lucro',
                x=display_df[x_col],
                y=display_df['profit_pct'],
                text=display_df['profit_pct'].apply(lambda x: f"{x:.2f}%"),
                textposition='inside',
                textfont=dict(color='white', size=11, weight='bold'),
                marker=dict(
                    color='#10B981',  # Green for profit
                    line=dict(color='#047857', width=1)
                ),
                hovertemplate='<b>Margem de Lucro</b><br>' +
                             'Percentual: %{y:.1f}%<br>' +
                             'Valor: R$ %{customdata[0]:,.0f}<br>' +
                             '<b>Receita Total: R$ %{customdata[1]:,.0f}</b><br>' +
                             '<extra></extra>',
                customdata=list(zip(display_df['profit'], display_df['revenue']))
            ))
    
            # Add 100% reference line
            fig_cost_structure.add_hline(
                y=100, 
                line_dash="dot", 
                line_color="#6B7280",
                annotation_text="100% da Receita",
                annotation_position="top right",
                annotation_font=dict(size=12, color="#6B7280")
            )
    
            # Clean x-axis labels with just periods (revenue moved to hover)
    
    
            # Apply interactive features for monthly view
            if view_type == "Mensal":
                xaxis_config = dict(
                    title=dict(
                        text=x_title,
                        font=dict(size=16, color='#1F2937', weight='bold')
                    ),
                    tickfont=dict(size=12, color='#374151'),
                    showgrid=False,
                    tickangle=-90,  # Vertical labels to prevent overlap
                    tickmode='linear',
                    **get_monthly_layout_config()
                )
                
                # Set default range to show last 12 months
                default_range = get_default_monthly_range(display_df, x_col)
                if default_range:
                    xaxis_config['range'] = default_range
                fig_cost_structure.update_layout(
                    title={
                        'text': '💰 Estrutura de Custos vs Receita (% da Receita)',
                        'font': {'size': 24, 'color': '#1F2937'}
                    },
                    barmode='stack',
                    yaxis=dict(
                        title=dict(
                            text="Percentual da Receita (%)",
                            font=dict(size=16, color='#1F2937', weight='bold')
                        ),
                        tickformat='.1f',
                        ticksuffix='%',
                        tickfont=dict(size=12, color='#374151'),
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.1)',
                        range=[0, 100]
                    ),
                    xaxis=xaxis_config,
                    height=700,  # Increased height for monthly view
                    hovermode='x unified',
                    plot_bgcolor='rgba(248,249,250,0.8)',
                    paper_bgcolor='white',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        bgcolor="rgba(255,255,255,0.9)",
                        bordercolor="rgba(0,0,0,0.1)",
                        borderwidth=1,
                        font=dict(size=14, color='#374151', weight='bold')
                    ),
                    margin=dict(t=120, b=100),
                    dragmode='pan'
                )
                
                # Add shapes for visual appeal
                fig_cost_structure.update_xaxes(showline=True, linewidth=2, linecolor='#E5E7EB')
                fig_cost_structure.update_yaxes(showline=True, linewidth=2, linecolor='#E5E7EB')
                
                st.plotly_chart(fig_cost_structure, use_container_width=True, config=get_plotly_config())
            else:
                fig_cost_structure.update_layout(
                    title={
                        'text': '💰 Estrutura de Custos vs Receita (% da Receita)',
                        'font': {'size': 24, 'color': '#1F2937'}
                    },
                    barmode='stack',
                    yaxis=dict(
                        title=dict(
                            text="Percentual da Receita (%)",
                            font=dict(size=16, color='#1F2937', weight='bold')
                        ),
                        tickformat='.1f',
                        ticksuffix='%',
                        tickfont=dict(size=12, color='#374151'),
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.1)',
                        range=[0, 100]
                    ),
                    xaxis=dict(
                        title=dict(
                            text=x_title,
                            font=dict(size=16, color='#1F2937', weight='bold')
                        ),
                        tickfont=dict(size=12, color='#374151'),
                        showgrid=False,
                        tickangle=-90,  # Vertical labels to prevent overlap
                        tickmode='linear',
                        dtick=1 if view_type == "Anual" else None,
                        type='category' if view_type == "Anual" else None,
                        categoryorder='category ascending' if view_type == "Anual" else None
                    ),
                    height=600,  # Standard height for all views
                    hovermode='x unified',
                    plot_bgcolor='rgba(248,249,250,0.8)',
                    paper_bgcolor='white',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        bgcolor="rgba(255,255,255,0.9)",
                        bordercolor="rgba(0,0,0,0.1)",
                        borderwidth=1,
                        font=dict(size=14, color='#374151', weight='bold')
                    ),
                    margin=dict(t=120, b=100)
                )
                
                # Add shapes for visual appeal
                fig_cost_structure.update_xaxes(showline=True, linewidth=2, linecolor='#E5E7EB')
                fig_cost_structure.update_yaxes(showline=True, linewidth=2, linecolor='#E5E7EB')
                
                st.plotly_chart(fig_cost_structure, use_container_width=True)


        # Anomalies
        if hasattr(st.session_state, 'show_anomalies') and st.session_state.show_anomalies and data.get('anomalies'):
            st.subheader("⚠️ Anomalias Detectadas")
            anomalies = data['anomalies']
            
            # Check if anomalies is a list of dicts
            if isinstance(anomalies, list) and len(anomalies) > 0:
                # Validate each anomaly entry
                valid_anomalies = []
                for a in anomalies:
                    if isinstance(a, dict) and all(k in a for k in ['year', 'metric', 'value', 'type']):
                        valid_anomalies.append(a)
                
                if valid_anomalies:
                    for anomaly in valid_anomalies:
                        try:
                            st.warning(
                                f"**{anomaly['year']}**: {anomaly['metric']} - "
                                f"Valor: {anomaly['value']:.2f}% ({anomaly['type']})"
                            )
                        except (KeyError, TypeError, ValueError) as e:
                            st.error(f"Error displaying anomaly: {str(e)}")
                else:
                    st.info("Nenhuma anomalia válida encontrada.")
            elif not isinstance(anomalies, list):
                # Debug: show what we got instead
                st.error(f"Anomalies data is not a list. Type: {type(anomalies)}")
                if isinstance(anomalies, str):
                    st.error(f"String content: {anomalies[:100]}...")

        # Growth Analysis (only for annual view) - Moved to be last
        if view_type == "Anual":
            st.subheader("📊 Análise de Crescimento")
            growth_cols = [col for col in display_df.columns if '_growth' in col]
            if growth_cols:
                fig_growth = go.Figure()
                
                # Translation mapping for metric names
                metric_translations = {
                    'revenue': 'Receita',
                    'variable_costs': 'Custos Variáveis',
                    'net_profit': 'Lucro Líquido',
                    'fixed_costs': 'Custos Fixos',
                    'operational_costs': 'Custos Operacionais'
                }
                
                for col in growth_cols:
                    metric_key = col.replace('_growth', '')
                    metric_name = metric_translations.get(metric_key, metric_key.title())
                    fig_growth.add_trace(go.Scatter(
                        x=display_df['year'],
                        y=display_df[col],
                        mode='lines+markers',
                        name=metric_name,
                        line=dict(width=3)
                    ))
                fig_growth.update_layout(
                    title="Taxa de Crescimento Anual (%)",
                    xaxis_title="Ano",
                    yaxis_title="Crescimento (%)",
                    height=400,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                st.plotly_chart(fig_growth, use_container_width=True, key="growth_chart_standard")

        # Data table
        with st.expander("📋 Ver Dados Detalhados"):
            st.dataframe(display_df, use_container_width=True)

    else:
        st.info("👆 Por favor, carregue arquivos na aba 'Upload' primeiro.")