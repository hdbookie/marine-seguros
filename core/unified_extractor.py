import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import re
from core.extractors.revenue_extractor import RevenueExtractor
from core.extractors.variable_cost_extractor import VariableCostExtractor
from core.extractors.fixed_cost_extractor import FixedCostExtractor
from core.extractors.non_operational_cost_extractor import NonOperationalCostExtractor
from core.extractors.tax_extractor import TaxExtractor
from core.extractors.commission_extractor import CommissionExtractor
from core.extractors.administrative_expense_extractor import AdministrativeExpenseExtractor
from core.extractors.marketing_expense_extractor import MarketingExpenseExtractor
from core.extractors.financial_expense_extractor import FinancialExpenseExtractor
from core.profit_extractor import ProfitExtractor

class UnifiedFinancialExtractor:
    def __init__(self):
        self.revenue_extractor = RevenueExtractor()
        self.variable_cost_extractor = VariableCostExtractor()
        self.fixed_cost_extractor = FixedCostExtractor()
        self.non_operational_cost_extractor = NonOperationalCostExtractor()
        self.tax_extractor = TaxExtractor()
        self.commission_extractor = CommissionExtractor()
        self.administrative_expense_extractor = AdministrativeExpenseExtractor()
        self.marketing_expense_extractor = MarketingExpenseExtractor()
        self.financial_expense_extractor = FinancialExpenseExtractor()
        self.profit_extractor = ProfitExtractor()

    def extract_from_excel(self, file_path: str) -> Dict[int, Dict]:
        extracted_data = {}
        try:
            excel_file = pd.ExcelFile(file_path)
            year_sheets = {}
            for sheet_name in excel_file.sheet_names:
                year = self._identify_year(sheet_name, file_path)
                if not year:
                    continue
                if year not in year_sheets:
                    year_sheets[year] = []
                year_sheets[year].append(sheet_name)
            
            for year, sheets in year_sheets.items():
                def sheet_priority(sheet_name):
                    sheet_lower = sheet_name.lower()
                    if 'resultado' in sheet_lower and 'previsão' not in sheet_lower:
                        return 0
                    elif sheet_name.isdigit():
                        return 1
                    elif 'previsão' in sheet_lower:
                        return 2
                    else:
                        return 3
                
                sorted_sheets = sorted(sheets, key=sheet_priority)
                
                for sheet_name in sorted_sheets:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    financial_data = self._extract_unified_data(df, year)
                    if financial_data:
                        has_core_data = (
                            ('revenue' in financial_data and financial_data['revenue']) or
                            ('costs' in financial_data and financial_data['costs'])
                        )
                        has_line_items = 'line_items' in financial_data and len(financial_data['line_items']) > 0
                        if has_core_data or has_line_items:
                            extracted_data[year] = financial_data
                            break
        except Exception as e:
            pass
        return extracted_data

    def _identify_year(self, sheet_name: str, file_path: str) -> Optional[int]:
        year_match = re.search(r'20\d{2}', sheet_name)
        if year_match:
            year = int(year_match.group())
            if 2018 <= year <= 2025:
                return year
        if sheet_name.isdigit() and 2018 <= int(sheet_name) <= 2025:
            return int(sheet_name)
        if '_' not in file_path or not re.search(r'20\d{2}_20\d{2}', file_path):
            year_match = re.search(r'20\d{2}', file_path)
            if year_match:
                year = int(year_match.group())
                if 2018 <= year <= 2025:
                    return year
        return None

    def _extract_unified_data(self, df: pd.DataFrame, year: int) -> Dict:
        revenue_data = self.revenue_extractor.extract_revenue(df, year)
        variable_costs_data = self.variable_cost_extractor.extract_costs(df, year)
        fixed_costs_data = self.fixed_cost_extractor.extract_fixed_costs(df, year)
        non_operational_costs_data = self.non_operational_cost_extractor.extract(df)
        tax_data = self.tax_extractor.extract(df)
        commission_data = self.commission_extractor.extract(df)
        admin_expense_data = self.administrative_expense_extractor.extract(df)
        marketing_expense_data = self.marketing_expense_extractor.extract(df)
        financial_expense_data = self.financial_expense_extractor.extract(df)
        profit_data = self.profit_extractor.extract_profits(df, year)

        line_items = {
            **revenue_data.get('line_items', {}),
            **variable_costs_data.get('line_items', {}),
            **fixed_costs_data.get('line_items', {}),
            **non_operational_costs_data.get('line_items', {}),
            **tax_data.get('line_items', {}),
            **commission_data.get('line_items', {}),
            **admin_expense_data.get('line_items', {}),
            **marketing_expense_data.get('line_items', {}),
            **financial_expense_data.get('line_items', {}),
            **profit_data.get('line_items', {})
        }

        categories = {
            'revenue': list(revenue_data.get('line_items', {}).keys()),
            'variable_costs': list(variable_costs_data.get('line_items', {}).keys()),
            'fixed_costs': list(fixed_costs_data.get('line_items', {}).keys()),
            'non_operational_costs': list(non_operational_costs_data.get('line_items', {}).keys()),
            'taxes': list(tax_data.get('line_items', {}).keys()),
            'commissions': list(commission_data.get('line_items', {}).keys()),
            'administrative_expenses': list(admin_expense_data.get('line_items', {}).keys()),
            'marketing_expenses': list(marketing_expense_data.get('line_items', {}).keys()),
            'financial_expenses': list(financial_expense_data.get('line_items', {}).keys()),
            'profits': list(profit_data.get('line_items', {}).keys())
        }

        return {
            'year': year,
            'revenue': revenue_data,
            'variable_costs': variable_costs_data,
            'fixed_costs': fixed_costs_data,
            'non_operational_costs': non_operational_costs_data,
            'taxes': tax_data,
            'commissions': commission_data,
            'administrative_expenses': admin_expense_data,
            'marketing_expenses': marketing_expense_data,
            'financial_expenses': financial_expense_data,
            'profits': profit_data,
            'line_items': line_items,
            'categories': categories,
            'monthly_data': {},
            'hierarchy': []
        }