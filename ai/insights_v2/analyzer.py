"""
Enhanced AI Analyzer with Gemini Pro and advanced features
"""

import google.generativeai as genai
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import hashlib
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor

class EnhancedAIAnalyzer:
    """
    Advanced AI analyzer with Gemini Pro, caching, and specialized analysis modes
    """
    
    def __init__(self, api_key: str, language: str = "pt-br", use_pro: bool = True):
        """
        Initialize the enhanced analyzer
        
        Args:
            api_key: Google Gemini API key
            language: Output language (pt-br or en)
            use_pro: Use Gemini Pro (True) or Flash (False)
        """
        self.api_key = api_key
        self.language = language
        self.use_pro = use_pro
        
        genai.configure(api_key=self.api_key)
        
        # Select model based on preference
        model_name = 'gemini-1.5-pro' if use_pro else 'gemini-1.5-flash'
        self.model = genai.GenerativeModel(model_name)
        
        # Initialize cache
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    def _get_cache_key(self, data: Any, analysis_type: str) -> str:
        """Generate cache key from data and analysis type"""
        data_str = json.dumps(str(data), sort_keys=True)
        return hashlib.md5(f"{data_str}_{analysis_type}".encode()).hexdigest()
    
    @lru_cache(maxsize=32)
    def _get_language_instruction(self) -> str:
        """Get language instruction for prompts"""
        if self.language == "en":
            return "Please provide the analysis in English."
        return "Por favor, forneça a análise em português do Brasil."
    
    async def analyze_financial_health_structured(self, df: pd.DataFrame, structured_data: Dict, context: Dict = None) -> Dict[str, Any]:
        """
        Comprehensive financial health analysis with structured data
        
        Args:
            df: Financial data DataFrame
            structured_data: Pre-processed structured data with detailed metrics
            context: Additional context (industry, company size, etc.)
        
        Returns:
            Dictionary with health score, insights, and recommendations
        """
        cache_key = self._get_cache_key(structured_data, 'financial_health_structured')
        
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return cached_result
        
        # Use structured data for better prompts
        prompt = f"""
        {self._get_language_instruction()}
        
        Você é um analista financeiro sênior especializado em seguros. Analise os dados financeiros detalhados e forneça insights específicos e acionáveis.
        
        **Dados Estruturados da Empresa:**
        {json.dumps(structured_data, indent=2, ensure_ascii=False)}
        
        **Contexto:**
        Setor: Seguros (Marine Seguros)
        Período: {context.get('period', 'Não especificado') if context else 'Não especificado'}
        
        Forneça uma análise estruturada com NÚMEROS ESPECÍFICOS:
        
        1. **Score de Saúde Financeira** (0-100):
           - Score geral com justificativa baseada nos dados
           - Breakdown: liquidez (0-25), rentabilidade (0-25), crescimento (0-25), eficiência (0-25)
           - Status: "Excelente" (80+), "Bom" (60-79), "Atenção Necessária" (40-59), "Crítico" (<40)
        
        2. **Performance Específica** (com valores exatos):
           - Crescimento de receita: valor e percentual
           - Evolução da margem: pontos percentuais
           - Eficiência de custos: ratio e benchmark
           - Tendência: crescente/decrescente/estável
        
        3. **Principais Pontos Fortes** (3 itens com dados):
           - Métrica específica que está performando bem
           - Comparação com média do setor de seguros
           - Impacto financeiro quantificado
        
        4. **Riscos Críticos** (3 itens com severidade):
           - Área de preocupação com métrica específica
           - Impacto potencial em reais
           - Prazo para mitigação: imediato/curto prazo/médio prazo
        
        5. **Recomendações Acionáveis** (5 ações específicas):
           - Ação concreta (não genérica)
           - Impacto esperado em R$ ou %
           - Prazo de implementação
           - Prioridade: Alta/Média/Baixa
        
        6. **Outlook** (próximos 6-12 meses):
           - Projeção de receita baseada na tendência
           - Riscos e oportunidades quantificados
           - Cenário mais provável com probabilidade
        
        7. **Insights Ocultos** (padrões não óbvios em gráficos):
           - Analise os 'hidden_patterns' fornecidos
           - Destaque correlações inesperadas
           - Identifique pontos de inflexão e mudanças estruturais
           - Aponte ineficiências operacionais não óbvias
           - Detecte padrões sazonais e cíclicos
           - Calcule economias potenciais específicas
        
        IMPORTANTE: 
        - Use os valores EXATOS dos dados fornecidos. Não invente números.
        - Priorize insights dos 'hidden_patterns' que revelam problemas ou oportunidades não óbvias
        - Quantifique SEMPRE o impacto financeiro de cada descoberta
        Formato: JSON estruturado para fácil parsing.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.model.generate_content,
                prompt
            )
            
            result = self._parse_json_response(response.text)
            
            # Ensure we have all required fields
            if 'health_score' not in result:
                result['health_score'] = self._calculate_health_score_from_data(structured_data)
            
            if 'performance' not in result:
                result['performance'] = self._extract_performance_metrics(structured_data)
            
            if 'outlook' not in result:
                result['outlook'] = "Análise baseada em " + structured_data.get('summary_metrics', {}).get('data_period', 'dados históricos')
            
            # Cache the result
            self._cache[cache_key] = (result, datetime.now())
            
            return result
            
        except Exception as e:
            # Return meaningful fallback based on actual data
            return self._generate_fallback_analysis(structured_data, str(e))
    
    def _calculate_health_score_from_data(self, structured_data: Dict) -> int:
        """Calculate health score from structured data"""
        score = 50  # Base score
        
        # Adjust based on growth
        growth_analysis = structured_data.get('growth_analysis', {})
        if 'total_growth' in growth_analysis and growth_analysis['total_growth'] != "N/A":
            growth_value = float(growth_analysis['total_growth'].replace('%', ''))
            if growth_value > 20:
                score += 15
            elif growth_value > 10:
                score += 10
            elif growth_value < 0:
                score -= 10
        
        # Adjust based on margin
        if 'summary_metrics' in structured_data:
            margin_str = structured_data['summary_metrics'].get('average_margin', '0%')
            if margin_str != 0:
                margin_value = float(margin_str.replace('%', ''))
                if margin_value > 30:
                    score += 15
                elif margin_value > 20:
                    score += 10
                elif margin_value < 10:
                    score -= 10
        
        # Adjust based on cost structure
        cost_structure = structured_data.get('cost_structure', {})
        if 'fixed_percentage' in cost_structure:
            fixed_pct = float(cost_structure['fixed_percentage'].replace('%', ''))
            if fixed_pct < 40:
                score += 10
            elif fixed_pct > 60:
                score -= 10
        
        return max(0, min(100, score))
    
    def _extract_performance_metrics(self, structured_data: Dict) -> Dict:
        """Extract performance metrics from structured data"""
        metrics = {}
        
        if 'growth_analysis' in structured_data:
            metrics['revenue_growth'] = structured_data['growth_analysis'].get('total_growth', 'N/A')
            metrics['cagr'] = structured_data['growth_analysis'].get('revenue_cagr', 'N/A')
        
        if 'summary_metrics' in structured_data:
            metrics['total_revenue'] = structured_data['summary_metrics'].get('total_revenue', 'N/A')
            metrics['average_margin'] = structured_data['summary_metrics'].get('average_margin', 'N/A')
        
        if 'trends' in structured_data:
            metrics['growth_trend'] = structured_data['trends'].get('average_growth_rate', 'N/A')
            metrics['margin_trend'] = structured_data['trends'].get('margin_trend', 'N/A')
        
        return metrics
    
    def _generate_fallback_analysis(self, structured_data: Dict, error: str) -> Dict:
        """Generate fallback analysis when AI fails"""
        return {
            'health_score': self._calculate_health_score_from_data(structured_data),
            'performance': self._extract_performance_metrics(structured_data),
            'insights': structured_data.get('top_insights', []),
            'outlook': f"Análise baseada em {structured_data.get('summary_metrics', {}).get('years_analyzed', 0)} anos de dados",
            'error': f"Análise simplificada devido a: {error}"
        }
    
    async def analyze_financial_health(self, df: pd.DataFrame, context: Dict = None) -> Dict[str, Any]:
        """
        Comprehensive financial health analysis
        
        Args:
            df: Financial data DataFrame
            context: Additional context (industry, company size, etc.)
        
        Returns:
            Dictionary with health score, insights, and recommendations
        """
        cache_key = self._get_cache_key(df.to_dict(), 'financial_health')
        
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return cached_result
        
        # Calculate key metrics
        metrics = self._calculate_financial_metrics(df)
        
        prompt = f"""
        {self._get_language_instruction()}
        
        You are a senior financial analyst. Analyze the following financial data and provide a comprehensive health assessment.
        
        **Financial Metrics:**
        {json.dumps(metrics, indent=2)}
        
        **Data Summary:**
        {df.describe().to_string()}
        
        **Context:**
        Industry: {context.get('industry', 'Not specified') if context else 'Not specified'}
        Company Size: {context.get('size', 'Not specified') if context else 'Not specified'}
        
        Provide a structured analysis with:
        
        1. **Financial Health Score** (0-100):
           - Overall score with justification
           - Breakdown by category (liquidity, profitability, growth, efficiency)
        
        2. **Key Strengths** (top 3):
           - Specific metrics that are performing well
           - Competitive advantages identified
        
        3. **Critical Risks** (top 3):
           - Areas of concern with severity levels
           - Potential impact on business
        
        4. **Trend Analysis**:
           - Revenue trend and projection
           - Cost management effectiveness
           - Margin evolution
        
        5. **Actionable Recommendations** (5 specific actions):
           - Priority level (High/Medium/Low)
           - Expected impact
           - Implementation timeline
        
        Format the response as a JSON structure for easy parsing.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.model.generate_content,
                prompt
            )
            
            result = self._parse_json_response(response.text)
            
            # Cache the result
            self._cache[cache_key] = (result, datetime.now())
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'health_score': 0,
                'insights': 'Analysis failed'
            }
    
    def _calculate_financial_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate key financial metrics from dataframe"""
        metrics = {}
        
        if 'revenue' in df.columns:
            metrics['total_revenue'] = df['revenue'].sum()
            metrics['avg_revenue'] = df['revenue'].mean()
            metrics['revenue_growth'] = self._calculate_growth_rate(df['revenue'])
        
        if 'net_profit' in df.columns:
            metrics['total_profit'] = df['net_profit'].sum()
            metrics['avg_profit'] = df['net_profit'].mean()
            metrics['profit_growth'] = self._calculate_growth_rate(df['net_profit'])
        
        if 'profit_margin' in df.columns:
            metrics['avg_margin'] = df['profit_margin'].mean()
            metrics['margin_trend'] = 'improving' if df['profit_margin'].iloc[-1] > df['profit_margin'].iloc[0] else 'declining'
        
        if 'variable_costs' in df.columns and 'revenue' in df.columns:
            metrics['cost_revenue_ratio'] = (df['variable_costs'].sum() / df['revenue'].sum()) * 100
        
        return metrics
    
    def _calculate_growth_rate(self, series: pd.Series) -> float:
        """Calculate CAGR for a series"""
        if len(series) < 2 or series.iloc[0] <= 0:
            return 0
        
        years = len(series) - 1
        return ((series.iloc[-1] / series.iloc[0]) ** (1/years) - 1) * 100
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parse JSON from AI response"""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: structure the text response
                return {
                    'raw_insights': text,
                    'health_score': 75,  # Default score
                    'parsed': False
                }
        except:
            return {'raw_insights': text, 'parsed': False}
    
    async def predict_future_trends(self, df: pd.DataFrame, periods: int = 4) -> Dict[str, Any]:
        """
        Predict future financial trends using AI
        
        Args:
            df: Historical financial data
            periods: Number of periods to forecast
        
        Returns:
            Predictions with confidence intervals
        """
        prompt = f"""
        {self._get_language_instruction()}
        
        As a financial forecasting expert, analyze this historical data and predict future trends.
        
        **Historical Data:**
        {df.to_string()}
        
        **Task:**
        1. Forecast the next {periods} periods for:
           - Revenue
           - Costs
           - Profit margins
        
        2. Identify:
           - Seasonal patterns
           - Growth trajectory
           - Risk factors that could impact forecasts
        
        3. Provide confidence levels (High/Medium/Low) for each prediction
        
        4. Suggest 3 scenarios:
           - Best case (optimistic)
           - Base case (most likely)
           - Worst case (conservative)
        
        Format as structured JSON with numerical predictions.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.model.generate_content,
                prompt
            )
            
            return self._parse_json_response(response.text)
            
        except Exception as e:
            return {'error': str(e), 'predictions': None}
    
    async def detect_anomalies(self, df: pd.DataFrame, line_items: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Detect anomalies and unusual patterns in financial data
        
        Args:
            df: Aggregated financial data
            line_items: Detailed line items for deep analysis
        
        Returns:
            Anomalies with severity and explanations
        """
        line_items_section = ""
        if line_items is not None:
            line_items_section = f"**Detailed Line Items (Top 50 by value):**\n{line_items.nlargest(50, 'valor_anual').to_string()}"
        
        prompt = f"""
        {self._get_language_instruction()}
        
        You are a forensic financial analyst. Detect anomalies and unusual patterns in this data.
        
        **Financial Summary:**
        {df.to_string()}
        
        {line_items_section}
        
        Identify:
        
        1. **Statistical Anomalies**:
           - Unusual spikes or drops
           - Values outside expected ranges
           - Pattern breaks
        
        2. **Business Anomalies**:
           - Unusual expense categories
           - Suspicious cost patterns
           - Revenue inconsistencies
        
        3. **Temporal Anomalies**:
           - Seasonal irregularities
           - Trend reversals
           - Timing issues
        
        For each anomaly provide:
        - Severity (Critical/High/Medium/Low)
        - Confidence level
        - Business impact
        - Recommended investigation steps
        
        Format as JSON with clear categorization.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.model.generate_content,
                prompt
            )
            
            return self._parse_json_response(response.text)
            
        except Exception as e:
            return {'error': str(e), 'anomalies': []}
    
    async def generate_competitive_insights(self, df: pd.DataFrame, industry_benchmarks: Dict = None) -> Dict[str, Any]:
        """
        Generate competitive insights and benchmarking analysis
        
        Args:
            df: Company financial data
            industry_benchmarks: Industry average metrics
        
        Returns:
            Competitive positioning and recommendations
        """
        benchmarks = industry_benchmarks or {
            'avg_profit_margin': 15,
            'avg_growth_rate': 10,
            'avg_cost_ratio': 65
        }
        
        prompt = f"""
        {self._get_language_instruction()}
        
        As a competitive intelligence analyst, compare this company's performance against industry standards.
        
        **Company Data:**
        {df.to_string()}
        
        **Industry Benchmarks:**
        {json.dumps(benchmarks, indent=2)}
        
        Provide:
        
        1. **Competitive Position**:
           - Overall ranking (Top tier/Average/Below average)
           - Key differentiators
           - Competitive gaps
        
        2. **Performance vs Industry**:
           - Metrics above/below industry average
           - Percentile rankings where possible
        
        3. **Strategic Opportunities**:
           - Areas to gain competitive advantage
           - Quick wins vs long-term initiatives
        
        4. **Threat Assessment**:
           - Vulnerability areas
           - Competitive risks
        
        5. **Recommendations**:
           - Top 3 actions to improve competitive position
           - Resource allocation suggestions
        
        Format as structured JSON.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.model.generate_content,
                prompt
            )
            
            return self._parse_json_response(response.text)
            
        except Exception as e:
            return {'error': str(e), 'competitive_position': 'Unknown'}
    
    async def analyze_scenario(self, df: pd.DataFrame, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform what-if scenario analysis
        
        Args:
            df: Base financial data
            scenario: Scenario parameters (e.g., {'revenue_change': 10, 'cost_change': -5})
        
        Returns:
            Impact analysis and recommendations
        """
        prompt = f"""
        {self._get_language_instruction()}
        
        As a strategic planning expert, analyze the impact of this business scenario.
        
        **Current Financial State:**
        {df.to_string()}
        
        **Proposed Scenario:**
        {json.dumps(scenario, indent=2)}
        
        Analyze:
        
        1. **Financial Impact**:
           - Revenue implications
           - Cost structure changes
           - Profitability impact
           - Cash flow effects
        
        2. **Risk Assessment**:
           - Implementation risks
           - Market risks
           - Operational risks
        
        3. **Success Factors**:
           - Key requirements for success
           - Critical milestones
           - Success metrics
        
        4. **Alternative Scenarios**:
           - Suggest 2 alternative approaches
           - Compare outcomes
        
        5. **Implementation Roadmap**:
           - Phase 1-3 breakdown
           - Timeline estimates
           - Resource requirements
        
        Format as structured JSON with quantified impacts where possible.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.model.generate_content,
                prompt
            )
            
            return self._parse_json_response(response.text)
            
        except Exception as e:
            return {'error': str(e), 'scenario_impact': 'Analysis failed'}
    
    def clear_cache(self):
        """Clear the analysis cache"""
        self._cache.clear()
    
    def __del__(self):
        """Cleanup executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)