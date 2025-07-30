"""
Financial Analysis Notes Extractor
Extracts year-end financial analysis text from spreadsheets
"""

import pandas as pd
import re
from typing import Dict, Optional, List


class FinancialAnalysisExtractor:
    """Extracts financial analysis notes from Excel sheets"""
    
    def __init__(self):
        # Patterns to identify analysis sections
        self.analysis_patterns = [
            r'AN[ÁA]LISE\s*FINANCEIRA',
            r'AN[ÁA]LISE\s*DO?\s*RESULTADO',
            r'COMENT[ÁA]RIOS?\s*GERENCIAIS?',
            r'OBSERVA[ÇC][ÕO]ES?\s*FINAIS?',
            r'RESUMO\s*DO?\s*ANO',
            r'CONCLUS[ÃA]O'
        ]
        
    def extract_from_excel(self, file_path: str) -> Dict[int, str]:
        """
        Extract financial analysis notes from Excel file
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dictionary with years as keys and analysis text as values
        """
        analysis_notes = {}
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                # Extract year from sheet name
                year = self._extract_year(sheet_name)
                if not year:
                    continue
                
                # Read the sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Look for analysis text
                analysis_text = self._find_analysis_text(df)
                if analysis_text:
                    analysis_notes[year] = analysis_text
                    
        except Exception as e:
            print(f"Error extracting financial analysis: {e}")
            
        return analysis_notes
    
    def _extract_year(self, sheet_name: str) -> Optional[int]:
        """Extract year from sheet name"""
        year_match = re.search(r'20\d{2}', sheet_name)
        if year_match:
            year = int(year_match.group())
            if 2018 <= year <= 2025:
                return year
        return None
    
    def _find_analysis_text(self, df: pd.DataFrame) -> Optional[str]:
        """Find and extract analysis text from DataFrame"""
        analysis_texts = []
        
        # Look for analysis sections in all cells
        for i in range(len(df)):
            for j in range(len(df.columns)):
                try:
                    cell_value = str(df.iloc[i, j])
                    if pd.isna(df.iloc[i, j]) or cell_value == 'nan':
                        continue
                    
                    # Check if this cell contains an analysis header
                    for pattern in self.analysis_patterns:
                        if re.search(pattern, cell_value, re.IGNORECASE):
                            # Found analysis section, collect text
                            analysis_text = self._collect_analysis_text(df, i, j)
                            if analysis_text:
                                analysis_texts.append(analysis_text)
                            break
                            
                except Exception:
                    continue
        
        # Also look for text in corner areas (as mentioned by user)
        corner_text = self._check_corner_areas(df)
        if corner_text:
            analysis_texts.append(corner_text)
        
        # Combine all found texts
        if analysis_texts:
            return '\n\n'.join(analysis_texts)
        
        return None
    
    def _collect_analysis_text(self, df: pd.DataFrame, start_row: int, start_col: int) -> str:
        """Collect analysis text starting from a specific cell"""
        texts = []
        
        # Collect text from the starting cell
        cell_value = str(df.iloc[start_row, start_col])
        if cell_value and cell_value != 'nan':
            texts.append(cell_value)
        
        # Look for text in cells below and to the right
        for i in range(start_row, min(start_row + 20, len(df))):
            for j in range(start_col, min(start_col + 5, len(df.columns))):
                if i == start_row and j == start_col:
                    continue
                    
                try:
                    cell_value = str(df.iloc[i, j])
                    if pd.isna(df.iloc[i, j]) or cell_value == 'nan':
                        continue
                    
                    # Check if this looks like analysis text (not numbers)
                    if self._is_analysis_text(cell_value):
                        texts.append(cell_value)
                        
                except Exception:
                    continue
        
        return ' '.join(texts) if texts else ''
    
    def _check_corner_areas(self, df: pd.DataFrame) -> Optional[str]:
        """Check corner areas of the spreadsheet for analysis text"""
        corner_texts = []
        
        # Define corner areas to check
        corners = [
            # Top-right corner
            {'rows': range(0, min(10, len(df))), 
             'cols': range(max(0, len(df.columns)-5), len(df.columns))},
            # Bottom-right corner
            {'rows': range(max(0, len(df)-10), len(df)), 
             'cols': range(max(0, len(df.columns)-5), len(df.columns))},
            # Bottom area (full width)
            {'rows': range(max(0, len(df)-15), len(df)), 
             'cols': range(len(df.columns))}
        ]
        
        for corner in corners:
            for i in corner['rows']:
                for j in corner['cols']:
                    try:
                        cell_value = str(df.iloc[i, j])
                        if pd.isna(df.iloc[i, j]) or cell_value == 'nan':
                            continue
                        
                        # Check if this is substantial text
                        if self._is_analysis_text(cell_value) and len(cell_value) > 50:
                            corner_texts.append(cell_value)
                            
                    except Exception:
                        continue
        
        return ' '.join(corner_texts) if corner_texts else None
    
    def _is_analysis_text(self, text: str) -> bool:
        """Check if text appears to be analysis commentary"""
        # Remove whitespace
        text = text.strip()
        
        # Must have minimum length
        if len(text) < 20:
            return False
        
        # Should not be mostly numbers
        digit_count = sum(c.isdigit() for c in text)
        if digit_count > len(text) * 0.5:
            return False
        
        # Should contain some analysis keywords
        analysis_keywords = [
            'margem', 'lucro', 'despesa', 'custo', 'aumentou', 'diminuiu',
            'devido', 'porque', 'causa', 'resultado', 'impacto', 'variação',
            'comparado', 'relação', 'análise', 'observa', 'nota'
        ]
        
        text_lower = text.lower()
        keyword_found = any(keyword in text_lower for keyword in analysis_keywords)
        
        # Check for sentence-like structure
        has_spaces = ' ' in text
        
        return keyword_found or (has_spaces and len(text) > 50)
    
    def format_analysis_for_display(self, analysis_text: str) -> str:
        """Format analysis text for better display"""
        # Clean up the text
        lines = analysis_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.isspace():
                # Remove excessive whitespace
                line = ' '.join(line.split())
                cleaned_lines.append(line)
        
        # Join with proper paragraph breaks
        formatted_text = '\n\n'.join(cleaned_lines)
        
        # Add bullet points if we detect list-like structure
        if re.search(r'^\d+[\.\)]', formatted_text, re.MULTILINE):
            lines = formatted_text.split('\n')
            formatted_lines = []
            for line in lines:
                if re.match(r'^\d+[\.\)]', line):
                    line = '• ' + re.sub(r'^\d+[\.\)]\s*', '', line)
                formatted_lines.append(line)
            formatted_text = '\n'.join(formatted_lines)
        
        return formatted_text