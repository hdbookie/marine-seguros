import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')
from core.unified_extractor import UnifiedFinancialExtractor

class FinancialProcessor:
    def __init__(self):
        self.months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        self.financial_data = {}
        
    def load_excel_files(self, files: List[str]) -> Dict:
        """Load and process multiple Excel files"""
        all_data = {}
        
        for file in files:
            try:
                excel_file = pd.ExcelFile(file)
                file_data = {}
                
                for sheet in excel_file.sheet_names:
                    df = pd.read_excel(file, sheet_name=sheet)
                    file_data[sheet] = df
                    
                all_data[file] = file_data
            except Exception as e:
                print(f"Error loading {file}: {e}")
                
        return all_data
    
    def extract_yearly_data(self, df: pd.DataFrame, year: int) -> Dict:
        """Extract financial data from a yearly sheet"""
        financial_metrics = {
            'year': year,
            'monthly_data': {},
            'annual_totals': {}
        }
        
        # Find revenue row (FATURAMENTO)
        revenue_row = None
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and 'FATURAMENTO' in str(row.iloc[0]):
                revenue_row = idx
                break
        
        if revenue_row is None:
            return financial_metrics
        
        # Extract monthly revenue data
        for i, month in enumerate(self.months):
            col_idx = i * 2 + 1  # Each month has value and percentage columns
            if col_idx < len(df.columns):
                value = df.iloc[revenue_row, col_idx]
                if pd.notna(value):
                    # Convert to float if it's a string number
                    try:
                        if isinstance(value, str):
                            value = float(value.replace(',', '.'))
                        financial_metrics['monthly_data'][month] = float(value)
                    except:
                        financial_metrics['monthly_data'][month] = 0
        
        # Extract key metrics
        metric_mappings = {
            'CUSTOS VARIÁVEIS': 'variable_costs',
            'MARGEM DE CONTRIBUIÇÃO': 'contribution_margin',
            'DESPESAS ADMINISTRATIVAS': 'admin_expenses',
            'DESPESAS OPERACIONAIS': 'operational_expenses',
            'RESULTADO OPERACIONAL': 'operational_result',
            'LUCRO LÍQUIDO': 'net_profit',
            'Margem de lucro': 'profit_margin'
        }
        
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]):
                row_name = str(row.iloc[0]).strip()
                for key, metric_name in metric_mappings.items():
                    if key in row_name:
                        # Get annual total (usually in 'Anual' column)
                        for col_idx, col in enumerate(df.columns):
                            if 'Anual' in str(col):
                                value = df.iloc[idx, col_idx]
                                if pd.notna(value):
                                    try:
                                        if isinstance(value, str):
                                            value = float(value.replace(',', '.'))
                                        financial_metrics['annual_totals'][metric_name] = float(value)
                                    except:
                                        pass
                                break
        
        # Calculate annual revenue
        if financial_metrics['monthly_data']:
            financial_metrics['annual_totals']['revenue'] = sum(financial_metrics['monthly_data'].values())
        
        return financial_metrics
    
    def consolidate_all_years_flexible(self, excel_data: Dict) -> Tuple[pd.DataFrame, Dict]:
        """Legacy method - now just calls consolidate_all_years for compatibility"""
        return self.consolidate_all_years(excel_data)
    
    def consolidate_all_years(self, excel_data: Dict, include_monthly: bool = False) -> Tuple[pd.DataFrame, Dict]:
        """Consolidate financial data from all years into a single DataFrame"""
        extractor = UnifiedFinancialExtractor()
        all_data = {}
        for file in excel_data.keys():
            file_data = extractor.extract_from_excel(file)
            if file_data:
                all_data.update(file_data)

        consolidated_data = []
        for year, year_data in all_data.items():
            revenue = year_data.get('revenue', {}).get('annual', 0)
            variable_costs = year_data.get('variable_costs', {}).get('annual', 0)
            fixed_costs = year_data.get('fixed_costs', {}).get('annual', 0)
            non_operational_costs = year_data.get('non_operational_costs', {}).get('annual', 0)
            taxes = year_data.get('taxes', {}).get('annual', 0)
            commissions = year_data.get('commissions', {}).get('annual', 0)
            admin_expenses = year_data.get('administrative_expenses', {}).get('annual', 0)
            marketing_expenses = year_data.get('marketing_expenses', {}).get('annual', 0)
            financial_expenses = year_data.get('financial_expenses', {}).get('annual', 0)

            # Get the actual profit from RESULTADO if available
            profit_annual = year_data.get('profits', {}).get('annual', 0)
            
            # Only calculate if we don't have extracted profit
            if profit_annual != 0:
                net_profit = profit_annual
            else:
                # Fallback calculation
                total_costs = variable_costs + fixed_costs + non_operational_costs + taxes + commissions + admin_expenses + marketing_expenses + financial_expenses
                net_profit = revenue - total_costs
            
            profit_margin = (net_profit / revenue) * 100 if revenue > 0 else 0

            contribution_margin = revenue - variable_costs

            row = {
                'year': year,
                'revenue': revenue,
                'variable_costs': variable_costs,
                'fixed_costs': fixed_costs,
                'operational_costs': fixed_costs, # For compatibility
                'non_operational_costs': non_operational_costs,
                'taxes': taxes,
                'commissions': commissions,
                'admin_expenses': admin_expenses,
                'marketing_expenses': marketing_expenses,
                'financial_expenses': financial_expenses,
                'contribution_margin': contribution_margin,
                'net_profit': net_profit,
                'profit_margin': profit_margin,
                'gross_profit': net_profit, # For compatibility
                'gross_margin': profit_margin # For compatibility
            }
            consolidated_data.append(row)

        if not consolidated_data:
            return pd.DataFrame(), {}

        df = pd.DataFrame(consolidated_data)
        return df, all_data
    
    def get_monthly_data(self, excel_data: Dict) -> pd.DataFrame:
        """Get monthly financial data from all years"""
        extractor = UnifiedFinancialExtractor()
        all_data = {}
        for file_path in excel_data.keys():
            if os.path.exists(file_path):
                file_data = extractor.extract_from_excel(file_path)
                if file_data:
                    all_data.update(file_data)

        monthly_rows = []
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        for year in sorted(all_data.keys()):
            year_data = all_data[year]
            monthly_revenue = year_data.get('revenue', {}).get('monthly', {})
            for i, month in enumerate(months):
                if month in monthly_revenue:
                    revenue = monthly_revenue[month]
                    variable_costs = year_data.get('variable_costs', {}).get('monthly', {}).get(month, 0)
                    fixed_costs = year_data.get('fixed_costs', {}).get('monthly', {}).get(month, 0)
                    non_operational_costs = year_data.get('non_operational_costs', {}).get('monthly', {}).get(month, 0)
                    taxes = year_data.get('taxes', {}).get('monthly', {}).get(month, 0)
                    commissions = year_data.get('commissions', {}).get('monthly', {}).get(month, 0)
                    admin_expenses = year_data.get('administrative_expenses', {}).get('monthly', {}).get(month, 0)
                    marketing_expenses = year_data.get('marketing_expenses', {}).get('monthly', {}).get(month, 0)
                    financial_expenses = year_data.get('financial_expenses', {}).get('monthly', {}).get(month, 0)

                    # Get actual monthly profit from RESULTADO if available
                    monthly_profit = year_data.get('profits', {}).get('monthly', {}).get(month, 0)
                    
                    if monthly_profit != 0:
                        net_profit = monthly_profit
                    else:
                        # Fallback calculation
                        total_costs = variable_costs + fixed_costs + non_operational_costs + taxes + commissions + admin_expenses + marketing_expenses + financial_expenses
                        net_profit = revenue - total_costs
                    profit_margin = (net_profit / revenue) * 100 if revenue > 0 else 0
                    contribution_margin = revenue - variable_costs

                    row = {
                        'year': year,
                        'month': month,
                        'month_num': i + 1,
                        'date': pd.Timestamp(year, i + 1, 1),
                        'revenue': revenue,
                        'variable_costs': variable_costs,
                        'fixed_costs': fixed_costs,
                        'operational_costs': fixed_costs, # For compatibility
                        'non_operational_costs': non_operational_costs,
                        'taxes': taxes,
                        'commissions': commissions,
                        'admin_expenses': admin_expenses,
                        'marketing_expenses': marketing_expenses,
                        'financial_expenses': financial_expenses,
                        'contribution_margin': contribution_margin,
                        'net_profit': net_profit,
                        'profit_margin': profit_margin
                    }
                    monthly_rows.append(row)
        
        if not monthly_rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(monthly_rows)
        return df.sort_values(['year', 'month_num'])
    
    def calculate_growth_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate year-over-year growth rates"""
        # Check if DataFrame is empty or missing 'year' column
        if df.empty:
            print("Warning: Empty DataFrame provided to calculate_growth_metrics")
            return pd.DataFrame()
        
        if 'year' not in df.columns:
            print(f"Warning: 'year' column missing. Available columns: {df.columns.tolist()}")
            return df
        
        df = df.sort_values('year').copy()
        
        # Calculate YoY growth for key metrics with proper handling
        growth_columns = ['revenue', 'variable_costs', 'net_profit']
        
        for col in growth_columns:
            if col in df.columns:
                # Create growth column with safer calculation
                df[f'{col}_growth'] = 0.0
                
                for i in range(1, len(df)):
                    prev_val = df[col].iloc[i-1]
                    curr_val = df[col].iloc[i]
                    
                    # Handle edge cases
                    if pd.isna(prev_val) or pd.isna(curr_val):
                        df.loc[df.index[i], f'{col}_growth'] = np.nan
                    elif abs(prev_val) < 0.01:  # Previous value is essentially zero
                        if abs(curr_val) < 0.01:
                            df.loc[df.index[i], f'{col}_growth'] = 0
                        else:
                            # Cap extreme growth at 1000% when coming from near-zero
                            df.loc[df.index[i], f'{col}_growth'] = min(1000, abs(curr_val) * 100)
                    else:
                        # Normal percentage calculation
                        growth = ((curr_val - prev_val) / abs(prev_val)) * 100
                        # Cap growth between -100% and 1000%
                        df.loc[df.index[i], f'{col}_growth'] = max(-100, min(1000, growth))
        
        # Recalculate profit margin to ensure consistency
        if 'revenue' in df.columns and 'net_profit' in df.columns:
            df['profit_margin'] = df.apply(
                lambda row: (row['net_profit'] / row['revenue'] * 100) if row['revenue'] > 0 else 0,
                axis=1
            )
        
        # Calculate operational efficiency
        if 'operational_expenses' in df.columns and 'revenue' in df.columns:
            df['operational_efficiency'] = (df['operational_expenses'] / df['revenue']) * 100
        
        return df
    
    def get_financial_summary(self, df: pd.DataFrame) -> Dict:
        """Generate financial summary statistics"""
        summary = {
            'total_years': len(df),
            'years_range': f"{df['year'].min()}-{df['year'].max()}",
            'metrics': {}
        }
        
        # Calculate summary statistics for key metrics
        for metric in ['revenue', 'net_profit', 'profit_margin']:
            if metric in df.columns:
                summary['metrics'][metric] = {
                    'total': df[metric].sum(),
                    'average': df[metric].mean(),
                    'min': df[metric].min(),
                    'max': df[metric].max(),
                    'std': df[metric].std(),
                    'cagr': self.calculate_cagr(df, metric)
                }
        
        return summary
    
    def calculate_cagr(self, df: pd.DataFrame, metric: str) -> float:
        """Calculate Compound Annual Growth Rate"""
        if metric not in df.columns or len(df) < 2:
            return 0
        
        df_sorted = df.sort_values('year')
        start_value = df_sorted[metric].iloc[0]
        end_value = df_sorted[metric].iloc[-1]
        years = df_sorted['year'].iloc[-1] - df_sorted['year'].iloc[0]
        
        if start_value > 0 and years > 0:
            cagr = (pow(end_value / start_value, 1/years) - 1) * 100
            return round(cagr, 2)
        return 0
    
    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect anomalies in financial data"""
        anomalies = []
        
        # Check for extreme growth rates
        growth_columns = [col for col in df.columns if '_growth' in col]
        
        for col in growth_columns:
            if col in df.columns:
                mean_growth = df[col].mean()
                std_growth = df[col].std()
                
                for idx, row in df.iterrows():
                    if pd.notna(row[col]):
                        if abs(row[col] - mean_growth) > 2 * std_growth:
                            anomalies.append({
                                'year': row['year'],
                                'metric': col,
                                'value': row[col],
                                'type': 'Extreme growth rate'
                            })
        
        return anomalies