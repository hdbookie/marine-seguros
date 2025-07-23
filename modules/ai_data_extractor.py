import pandas as pd
import numpy as np
import google.generativeai as genai
import json
import re
from typing import Dict, List, Tuple, Any
from datetime import datetime

class AIDataExtractor:
    """AI-powered data extractor that intelligently understands any Excel format"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.structure_cache = {}
        
    def analyze_excel_structure(self, df: pd.DataFrame, sheet_name: str) -> Dict:
        """Use AI to understand the structure of an Excel sheet"""
        
        # Create a preview of the data
        preview = self._create_preview(df)
        
        # Check cache first
        cache_key = f"{sheet_name}_{len(df.columns)}_{df.shape[0]}"
        if cache_key in self.structure_cache:
            return self.structure_cache[cache_key]
        
        prompt = f"""
        Analyze this financial Excel sheet and identify its structure.
        
        Sheet name: {sheet_name}
        Columns: {df.columns.tolist()}
        
        First 10 rows preview:
        {preview}
        
        Please identify and return a JSON with:
        {{
            "sheet_type": "yearly|monthly|comparison|summary",
            "revenue_identifiers": ["row_index_or_name", ...],
            "cost_identifiers": ["row_index_or_name", ...],
            "month_columns": {{"JAN": "column_name", "FEV": "column_name", ...}},
            "annual_column": "column_name",
            "average_column": "column_name",
            "metric_column": "column_name_with_metric_names",
            "data_start_row": row_number,
            "number_format": "BR|US",
            "year": extracted_year_if_found,
            "key_metrics": {{"metric_name": "identifier", ...}}
        }}
        
        Notes:
        - For revenue, look for: FATURAMENTO, RECEITA, Revenue, Vendas, Comissões (row in first column)
        - For costs, look for: CUSTOS VARIÁVEIS, CUSTOS, Despesas, Expenses (row in first column)
        - Months might be: JAN/FEV/MAR/ABR/MAI/JUN/JUL/AGO/SET/OUT/NOV/DEZ
        - Numbers might use . or , as separators
        - The first column often contains metric names
        - Month columns follow the pattern: JAN, %, FEV, %, MAR, % etc.
        """
        
        try:
            response = self.model.generate_content(prompt)
            structure = json.loads(self._extract_json(response.text))
            
            # Cache the result
            self.structure_cache[cache_key] = structure
            
            return structure
        except Exception as e:
            print(f"AI analysis error: {e}")
            return self._fallback_structure_detection(df)
    
    def extract_financial_data(self, df: pd.DataFrame, structure: Dict) -> Dict:
        """Extract financial data using AI-identified structure"""
        
        data = {
            'revenue': {},
            'costs': {},
            'profits': {},
            'margins': {},
            'monthly_data': {},
            'annual_totals': {},
            'metadata': structure
        }
        
        # Extract revenue data
        if structure.get('revenue_identifiers'):
            for identifier in structure['revenue_identifiers']:
                revenue_data = self._extract_metric_data(df, identifier, structure)
                if revenue_data:
                    data['revenue'] = revenue_data
                    break
        
        # Extract cost data
        if structure.get('cost_identifiers'):
            for identifier in structure['cost_identifiers']:
                cost_data = self._extract_metric_data(df, identifier, structure)
                if cost_data:
                    data['costs'] = cost_data
                    break
        
        # Extract monthly data
        if structure.get('month_columns'):
            data['monthly_data'] = self._extract_monthly_data(df, structure)
        
        # Calculate derived metrics
        data = self._calculate_derived_metrics(data)
        
        return data
    
    def _create_preview(self, df: pd.DataFrame) -> str:
        """Create a readable preview of the dataframe"""
        # Get first 10 rows or all if less
        preview_df = df.head(10).copy()
        
        # Convert to string, handling various data types
        for col in preview_df.columns:
            preview_df[col] = preview_df[col].astype(str).str[:30]
        
        return preview_df.to_string()
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from AI response"""
        # Find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group(0)
        return "{}"
    
    def _extract_metric_data(self, df: pd.DataFrame, identifier: str, structure: Dict) -> Dict:
        """Extract data for a specific metric"""
        monthly_data = {}
        
        try:
            # Find the row containing the metric
            if identifier.isdigit():
                row_idx = int(identifier)
            else:
                # Search for the identifier in the first column
                mask = df.iloc[:, 0].astype(str).str.contains(identifier, case=False, na=False)
                if mask.any():
                    row_idx = mask.idxmax()
                else:
                    return {}
            
            # Extract monthly values
            if structure.get('month_columns'):
                for month, col_name in structure['month_columns'].items():
                    if col_name in df.columns:
                        value = df.iloc[row_idx][col_name]
                        cleaned_value = self._clean_number(value, structure.get('number_format', 'BR'))
                        if cleaned_value is not None:
                            monthly_data[month] = cleaned_value
            
            # Extract annual total
            if structure.get('annual_column') and structure['annual_column'] in df.columns:
                annual_value = df.iloc[row_idx][structure['annual_column']]
                annual_cleaned = self._clean_number(annual_value, structure.get('number_format', 'BR'))
                if annual_cleaned is not None:
                    monthly_data['ANNUAL'] = annual_cleaned
                    
        except Exception as e:
            print(f"Error extracting {identifier}: {e}")
            
        return monthly_data
    
    def _extract_monthly_data(self, df: pd.DataFrame, structure: Dict) -> Dict:
        """Extract all monthly data based on structure"""
        monthly_data = {}
        
        month_columns = structure.get('month_columns', {})
        
        for month, col_name in month_columns.items():
            if col_name in df.columns:
                # Get all numeric values in this column
                column_data = df[col_name]
                numeric_values = []
                
                for value in column_data:
                    cleaned = self._clean_number(value, structure.get('number_format', 'BR'))
                    if cleaned is not None:
                        numeric_values.append(cleaned)
                
                if numeric_values:
                    monthly_data[month] = {
                        'values': numeric_values,
                        'sum': sum(numeric_values),
                        'avg': np.mean(numeric_values),
                        'max': max(numeric_values),
                        'min': min(numeric_values)
                    }
        
        return monthly_data
    
    def _clean_number(self, value: Any, format_type: str = 'BR') -> float:
        """Clean and convert various number formats"""
        if pd.isna(value) or value == '' or value is None:
            return None
            
        # Convert to string
        value_str = str(value).strip()
        
        # Remove currency symbols and spaces
        value_str = re.sub(r'[R$\s]', '', value_str)
        
        try:
            # Handle percentage
            if '%' in value_str:
                value_str = value_str.replace('%', '')
                return float(value_str) / 100
            
            # Brazilian format: 1.234,56
            if format_type == 'BR':
                value_str = value_str.replace('.', '').replace(',', '.')
            # US format: 1,234.56
            else:
                value_str = value_str.replace(',', '')
            
            return float(value_str)
        except:
            return None
    
    def _calculate_derived_metrics(self, data: Dict) -> Dict:
        """Calculate profit margins and other derived metrics"""
        
        # Calculate profits if we have revenue and costs
        if data['revenue'] and data['costs']:
            data['profits'] = {}
            data['margins'] = {}
            
            # Monthly calculations
            for month in data['revenue']:
                if month in data['costs']:
                    revenue = data['revenue'][month]
                    cost = data['costs'][month]
                    
                    if revenue > 0:
                        profit = revenue - cost
                        margin = (profit / revenue) * 100
                        
                        data['profits'][month] = profit
                        data['margins'][month] = margin
        
        return data
    
    def _fallback_structure_detection(self, df: pd.DataFrame) -> Dict:
        """Fallback structure detection when AI fails"""
        structure = {
            'sheet_type': 'yearly',
            'revenue_identifiers': [],
            'cost_identifiers': [],
            'month_columns': {},
            'annual_column': None,
            'average_column': None,
            'metric_column': None,
            'data_start_row': 0,
            'number_format': 'BR'
        }
        
        # Look for common patterns
        months_pt = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        # Identify month columns and other special columns
        for col in df.columns:
            col_str = str(col).upper()
            # Check for months
            for month in months_pt:
                if col_str == month or (month in col_str and '.' not in col_str and '%' not in col_str):
                    structure['month_columns'][month] = col
                    break
            
            # Check for annual column
            if 'ANUAL' in col_str and '%' not in col_str:
                structure['annual_column'] = col
            elif 'MÉDIA' in col_str and '%' not in col_str:
                structure['average_column'] = col
        
        # Identify the metric column (usually first column)
        if len(df.columns) > 0:
            structure['metric_column'] = df.columns[0]
            
            # Look for revenue/cost identifiers in first column
            first_col = df.iloc[:, 0].astype(str)
            
            for idx, value in enumerate(first_col):
                value_upper = str(value).upper()
                # Revenue identifiers
                if any(rev in value_upper for rev in ['FATURAMENTO', 'RECEITA', 'COMISSÕES']):
                    structure['revenue_identifiers'].append(str(idx))
                # Cost identifiers
                elif any(cost in value_upper for cost in ['CUSTOS VARIÁVEIS', 'CUSTO VARIÁVEL', 'DESPESAS']):
                    structure['cost_identifiers'].append(str(idx))
        
        return structure

    def compare_periods(self, data1: Dict, data2: Dict, period1_name: str, period2_name: str) -> Dict:
        """AI-powered comparison between two periods"""
        
        prompt = f"""
        Compare these two financial periods and provide insights:
        
        {period1_name}:
        Revenue: {data1.get('revenue', {})}
        Costs: {data1.get('costs', {})}
        Margins: {data1.get('margins', {})}
        
        {period2_name}:
        Revenue: {data2.get('revenue', {})}
        Costs: {data2.get('costs', {})}
        Margins: {data2.get('margins', {})}
        
        Provide:
        1. Key changes (percentage and absolute)
        2. Best and worst performing months
        3. Trend analysis
        4. Potential causes for changes
        5. Recommendations
        
        Format as JSON with clear sections.
        """
        
        try:
            response = self.model.generate_content(prompt)
            insights = self._extract_json(response.text)
            return json.loads(insights) if insights else {}
        except Exception as e:
            print(f"Comparison error: {e}")
            return self._basic_comparison(data1, data2, period1_name, period2_name)
    
    def _basic_comparison(self, data1: Dict, data2: Dict, period1_name: str, period2_name: str) -> Dict:
        """Basic comparison when AI is unavailable"""
        comparison = {
            'revenue_change': {},
            'cost_change': {},
            'margin_change': {},
            'summary': {}
        }
        
        # Calculate changes
        if data1.get('revenue') and data2.get('revenue'):
            rev1_total = sum(v for v in data1['revenue'].values() if isinstance(v, (int, float)))
            rev2_total = sum(v for v in data2['revenue'].values() if isinstance(v, (int, float)))
            
            if rev1_total > 0:
                change_pct = ((rev2_total - rev1_total) / rev1_total) * 100
                comparison['summary']['revenue_change_pct'] = round(change_pct, 2)
                comparison['summary']['revenue_change_abs'] = round(rev2_total - rev1_total, 2)
        
        return comparison