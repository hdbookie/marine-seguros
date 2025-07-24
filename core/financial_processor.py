import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')
from .direct_extractor import DirectDataExtractor
from .flexible_extractor import FlexibleFinancialExtractor

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
        """Consolidate financial data using flexible extractor for dynamic categories"""
        # Use flexible extractor for dynamic data extraction
        extractor = FlexibleFinancialExtractor()
        all_data = {}
        
        print(f"Processing {len(excel_data)} files with flexible extractor...")
        
        # Extract from all loaded files
        for file in excel_data.keys():
            try:
                print(f"Extracting data from: {file}")
                file_data = extractor.extract_from_excel(file)
                if file_data:
                    all_data.update(file_data)
                    print(f"✓ Extracted years from {file}: {sorted(file_data.keys())}")
                else:
                    print(f"✗ No data extracted from {file}")
            except Exception as e:
                print(f"Error extracting from {file}: {e}")
        
        # Check if we have any data
        if not all_data:
            print("Warning: No data was extracted. Returning empty DataFrame.")
            return pd.DataFrame(columns=['year']), {}
        
        # Create a summary DataFrame with key metrics
        summary_df = self._create_summary_dataframe(all_data)
        
        return summary_df, all_data
    
    def _create_summary_dataframe(self, all_data: Dict) -> pd.DataFrame:
        """Create a summary DataFrame from flexible extracted data"""
        summary_rows = []
        
        for year in sorted(all_data.keys()):
            year_data = all_data[year]
            row = {'year': year}
            
            # Extract key metrics
            for item_key, item_data in year_data['line_items'].items():
                category = item_data['category']
                
                # Map to standard names for backward compatibility
                if category == 'revenue':
                    row['revenue'] = item_data['annual']
                elif category == 'variable_costs' and 'variable_costs' not in row:
                    row['variable_costs'] = item_data['annual']
                    
                # Store all items with their original keys
                row[item_key] = item_data['annual']
            
            # Calculate derived metrics
            if 'revenue' in row:
                # Net profit (if not already in data)
                if 'net_profit' not in row:
                    total_costs = sum(
                        item_data['annual'] 
                        for item_data in year_data['line_items'].values()
                        if item_data['category'] in ['variable_costs', 'fixed_costs', 
                                                     'admin_expenses', 'operational_expenses',
                                                     'marketing_expenses', 'financial_expenses',
                                                     'tax_expenses', 'other_expenses', 'other_costs']
                    )
                    row['net_profit'] = row['revenue'] - total_costs
                
                # Profit margin
                if row['revenue'] > 0:
                    row['profit_margin'] = (row.get('net_profit', 0) / row['revenue']) * 100
                else:
                    row['profit_margin'] = 0
                    
            summary_rows.append(row)
        
        df = pd.DataFrame(summary_rows)
        print(f"Summary data shape: {df.shape}")
        print(f"Columns found: {df.columns.tolist()}")
        
        return df
    
    def consolidate_all_years(self, excel_data: Dict, include_monthly: bool = False) -> Tuple[pd.DataFrame, Dict]:
        """Consolidate financial data from all years into a single DataFrame
        
        Returns:
            Tuple[pd.DataFrame, Dict]: (consolidated_df, extracted_data)
        """
        # Use direct extractor for reliable data extraction
        extractor = DirectDataExtractor()
        all_data = {}
        
        print(f"Processing {len(excel_data)} files...")
        
        # Extract from all loaded files
        for file in excel_data.keys():
            try:
                print(f"Extracting data from: {file}")
                file_data = extractor.extract_from_excel(file)
                if file_data:
                    all_data.update(file_data)
                    print(f"✓ Extracted years from {file}: {sorted(file_data.keys())}")
                else:
                    print(f"✗ No data extracted from {file}")
            except Exception as e:
                print(f"Error extracting from {file}: {e}")
        
        # Convert to DataFrame
        consolidated_data = []
        for year in sorted(all_data.keys()):
            year_data = all_data[year]
            # Use the most appropriate profit value
            # Priority: OPERATIONAL > WITH_NON_OP > NET_FINAL > OTHER > WITHOUT_NON_OP > GROSS
            # We prioritize OPERATIONAL because it's the main business result before adjustments
            profits = year_data.get('profits', {})
            net_profit = (profits.get('OPERATIONAL') or 
                         profits.get('WITH_NON_OP') or
                         profits.get('NET_FINAL') or 
                         profits.get('OTHER') or
                         profits.get('WITHOUT_NON_OP') or
                         profits.get('NET_ADJUSTED') or
                         profits.get('GROSS') or 0)
            
            # Extract fixed_costs and operational_costs properly
            fixed_costs_data = year_data.get('fixed_costs', 0)
            operational_costs_data = year_data.get('operational_costs', 0)
            
            # If it's a dictionary, get the ANNUAL value
            if isinstance(fixed_costs_data, dict):
                fixed_costs = fixed_costs_data.get('ANNUAL', 0)
            else:
                fixed_costs = fixed_costs_data
                
            if isinstance(operational_costs_data, dict):
                operational_costs = operational_costs_data.get('ANNUAL', 0)
            else:
                operational_costs = operational_costs_data
            
            row = {
                'year': year,
                'revenue': year_data.get('revenue', {}).get('ANNUAL', 0),
                'variable_costs': year_data.get('costs', {}).get('ANNUAL', 0),
                'fixed_costs': fixed_costs,
                'operational_costs': operational_costs,
                'contribution_margin': year_data.get('contribution_margin', 0),
                'net_profit': net_profit,
                'gross_profit': year_data.get('gross_profit', profits.get('GROSS', 0)),
                'gross_margin': year_data.get('gross_margin', 0),
                'profit_margin': year_data.get('margins', {}).get('ANNUAL', 0)
            }
            
            # Use extracted profit margin if available, otherwise calculate
            if row['revenue'] > 0:
                # Only recalculate if we don't have an extracted margin
                if row['profit_margin'] == 0:
                    row['profit_margin'] = (row['net_profit'] / row['revenue']) * 100
                
                # Calculate contribution margin if not provided
                if row['contribution_margin'] == 0:
                    row['contribution_margin'] = row['revenue'] - row['variable_costs']
                    
            consolidated_data.append(row)
        
        # Check if we have any data
        if not consolidated_data:
            print("Warning: No data was consolidated. Returning empty DataFrame with expected columns.")
            # Return empty DataFrame with expected columns and empty dict
            return pd.DataFrame(columns=['year', 'revenue', 'variable_costs', 'net_profit', 'profit_margin']), {}
        
        df = pd.DataFrame(consolidated_data)
        print(f"Consolidated data shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        # Return both the consolidated DataFrame and the extracted data
        return df, all_data
    
    def get_monthly_data(self, excel_data: Dict) -> pd.DataFrame:
        """Get monthly financial data from all years"""
        # Use direct extractor for reliable data extraction
        extractor = DirectDataExtractor()
        all_data = {}
        
        print(f"Processing {len(excel_data)} files for monthly data...")
        
        # Extract from all loaded files - make sure file paths exist
        for file_path in excel_data.keys():
            try:
                # Check if file exists and extract
                if os.path.exists(file_path):
                    print(f"Extracting monthly data from: {file_path}")
                    file_data = extractor.extract_from_excel(file_path)
                    if file_data:
                        all_data.update(file_data)
                        print(f"✓ Extracted {len(file_data)} years from {file_path}")
                    else:
                        print(f"✗ No data extracted from {file_path}")
                else:
                    print(f"✗ File not found: {file_path}")
            except Exception as e:
                print(f"Error extracting from {file_path}: {e}")
                import traceback
                print(traceback.format_exc())
        
        # Convert to monthly DataFrame
        monthly_rows = []
        months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                  'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        for year in sorted(all_data.keys()):
            year_data = all_data[year]
            
            # Get monthly revenue and costs
            monthly_revenue = year_data.get('revenue', {})
            monthly_costs = year_data.get('costs', {})
            
            # Extract monthly fixed costs and operational costs
            monthly_fixed_costs = year_data.get('fixed_costs', {})
            monthly_operational_costs = year_data.get('operational_costs', {})
            contribution_margin_annual = year_data.get('contribution_margin', 0)
            
            # If we don't have monthly data, fall back to distributing annual costs
            fixed_costs_annual = monthly_fixed_costs.get('ANNUAL', 0) if isinstance(monthly_fixed_costs, dict) else monthly_fixed_costs
            operational_costs_annual = monthly_operational_costs.get('ANNUAL', 0) if isinstance(monthly_operational_costs, dict) else monthly_operational_costs
            
            # For fallback case only
            fixed_costs_monthly_fallback = fixed_costs_annual / 12 if fixed_costs_annual else 0
            operational_costs_monthly_fallback = operational_costs_annual / 12 if operational_costs_annual else 0
            
            for i, month in enumerate(months):
                if month in monthly_revenue:
                    revenue = monthly_revenue[month]
                    variable_costs = monthly_costs.get(month, 0)
                    
                    # Get actual monthly fixed costs if available, otherwise use fallback
                    if isinstance(monthly_fixed_costs, dict) and month in monthly_fixed_costs:
                        fixed_costs_this_month = monthly_fixed_costs[month]
                        operational_costs_this_month = monthly_operational_costs.get(month, fixed_costs_this_month)
                    else:
                        # Fallback to distributed annual costs
                        fixed_costs_this_month = fixed_costs_monthly_fallback
                        operational_costs_this_month = operational_costs_monthly_fallback
                    
                    # Calculate contribution margin for the month
                    contribution_margin = revenue - variable_costs
                    
                    # Calculate net profit for the month
                    net_profit = contribution_margin - fixed_costs_this_month - operational_costs_this_month
                    
                    row = {
                        'year': year,
                        'month': month,
                        'month_num': i + 1,
                        'date': pd.Timestamp(year, i + 1, 1),
                        'revenue': revenue,
                        'variable_costs': variable_costs,
                        'fixed_costs': fixed_costs_this_month,
                        'operational_costs': operational_costs_this_month,
                        'contribution_margin': contribution_margin,
                        'net_profit': net_profit,
                        'profit_margin': (net_profit / revenue * 100) if revenue > 0 else 0
                    }
                    monthly_rows.append(row)
        
        if not monthly_rows:
            print("Warning: No monthly data found")
            return pd.DataFrame()
        
        df = pd.DataFrame(monthly_rows)
        df = df.sort_values(['year', 'month_num'])
        return df
    
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