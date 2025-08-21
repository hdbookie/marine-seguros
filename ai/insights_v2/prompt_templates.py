"""
Specialized prompt templates for different types of financial analysis
"""

from typing import Dict, Any, List
import json

class PromptTemplates:
    """
    Collection of specialized prompt templates for financial analysis
    """
    
    def __init__(self, language: str = "pt-br"):
        self.language = language
        self._language_instruction = self._get_language_instruction()
    
    def _get_language_instruction(self) -> str:
        """Get language instruction for prompts"""
        if self.language == "en":
            return "Please provide the analysis in English."
        return "Por favor, forneça a análise em português do Brasil."
    
    def executive_summary(self, metrics: Dict, context: Dict = None) -> str:
        """Generate executive summary prompt"""
        return f"""
        {self._language_instruction}
        
        Você é o CFO de uma empresa de seguros. Crie um resumo executivo conciso e impactante.
        
        **Métricas Principais:**
        {json.dumps(metrics, indent=2, ensure_ascii=False)}
        
        **Contexto do Negócio:**
        Setor: {context.get('industry', 'Seguros') if context else 'Seguros'}
        Período: {context.get('period', 'Últimos 12 meses') if context else 'Últimos 12 meses'}
        
        Forneça um resumo executivo estruturado em:
        
        1. **Snapshot Executivo** (3 bullets):
           - Principal achievement do período
           - Maior desafio enfrentado
           - Métrica mais crítica para acompanhar
        
        2. **Performance Highlights**:
           - Revenue performance vs expectativas
           - Eficiência operacional
           - Saúde financeira geral (score 0-100)
        
        3. **Decisões Críticas Necessárias** (top 3):
           - Ação requerida
           - Impacto esperado
           - Prazo recomendado
        
        4. **Outlook** (próximos 6 meses):
           - Cenário mais provável
           - Principais riscos
           - Oportunidades-chave
        
        Formato: JSON estruturado para fácil parsing.
        Tom: Executivo, direto, orientado a ação.
        """
    
    def cost_optimization(self, expenses_df: str, categories: List[str]) -> str:
        """Generate cost optimization analysis prompt"""
        return f"""
        {self._language_instruction}
        
        Você é um especialista em otimização de custos e eficiência operacional.
        
        **Dados de Despesas:**
        {expenses_df}
        
        **Categorias Principais:**
        {', '.join(categories)}
        
        Realize uma análise profunda de otimização:
        
        1. **Quick Wins** (implementação < 30 dias):
           - 5 ações específicas
           - Economia estimada para cada
           - Complexidade (Baixa/Média/Alta)
           - Risco de impacto operacional
        
        2. **Otimizações Estratégicas** (3-6 meses):
           - 3 iniciativas transformacionais
           - ROI esperado
           - Investimento necessário
           - Riscos e mitigações
        
        3. **Análise de Desperdício**:
           - Duplicações identificadas
           - Ineficiências recorrentes
           - Gastos desnecessários
           - Potencial total de economia (%)
        
        4. **Benchmarking**:
           - Comparação com melhores práticas do setor
           - Gaps identificados
           - Metas recomendadas por categoria
        
        5. **Plano de Ação Prioritizado**:
           - Sequência recomendada
           - Quick wins vs transformação
           - Métricas de acompanhamento
        
        Formato: JSON com valores numéricos específicos.
        """
    
    def commission_analysis(self, commission_data: Dict, context: Dict = None) -> str:
        """Generate commission and transfer analysis prompt for insurance"""
        return f"""
        {self._language_instruction}
        
        Você é um especialista em análise de comissões e repasses no setor de seguros.
        
        **Dados de Comissões:**
        {json.dumps(commission_data, indent=2, ensure_ascii=False)}
        
        **Contexto:**
        Setor: Seguros
        Período: {context.get('period', 'Últimos 12 meses') if context else 'Últimos 12 meses'}
        
        Realize uma análise completa de comissões:
        
        1. **Análise de Estrutura de Comissões**:
           - Taxa média de comissão
           - Variação entre produtos/linhas
           - Comparação com benchmarks do setor
           - Tendências mensais
        
        2. **Eficiência de Repasses**:
           - Tempo médio de repasse
           - Custos de processamento
           - Oportunidades de automação
           - Redução de atrasos
        
        3. **Análise de Rentabilidade**:
           - Comissões vs Prêmios
           - ROI por canal/corretor
           - Produtos mais rentáveis
           - Otimização de mix
        
        4. **Riscos e Compliance**:
           - Concentração de corretores
           - Conformidade regulatória
           - Riscos de inadimplência
           - Controles recomendados
        
        5. **Recomendações de Otimização**:
           - Reestruturação de tabelas
           - Incentivos por performance
           - Automação de processos
           - Economia potencial
        
        Formato: JSON estruturado com métricas específicas.
        """
    
    def cost_optimization_insurance(self, cost_data: Dict, categories: List[str]) -> str:
        """Generate insurance-specific cost optimization analysis"""
        return f"""
        {self._language_instruction}
        
        Você é um especialista em otimização de custos para seguradoras.
        
        **Breakdown de Custos:**
        {json.dumps(cost_data, indent=2, ensure_ascii=False)}
        
        **Categorias:**
        {', '.join(categories)}
        
        Análise de otimização para seguros:
        
        1. **Análise Fixo vs Variável**:
           - Proporção atual
           - Benchmark do setor
           - Flexibilidade operacional
           - Oportunidades de variabilização
        
        2. **Custos de Aquisição (CAC)**:
           - CAC por canal
           - Lifetime value vs CAC
           - Eficiência de marketing
           - Otimização de funil
        
        3. **Custos Operacionais**:
           - Sinistralidade
           - Custos de regulação
           - Processamento de claims
           - Automação potencial
        
        4. **Economia de Escala**:
           - Volume break-even
           - Custos unitários
           - Oportunidades de consolidação
           - Terceirização estratégica
        
        5. **Plano de Redução**:
           - Quick wins (30 dias)
           - Médio prazo (3-6 meses)
           - Transformação (6-12 meses)
           - Savings totais estimados
        
        Formato: JSON com valores e percentuais específicos.
        """
    
    def margin_analysis(self, margin_data: Dict, context: Dict = None) -> str:
        """Generate margin and profitability analysis for insurance"""
        return f"""
        {self._language_instruction}
        
        Você é um analista de rentabilidade especializado em seguros.
        
        **Dados de Margem:**
        {json.dumps(margin_data, indent=2, ensure_ascii=False)}
        
        **Contexto:**
        {json.dumps(context, indent=2, ensure_ascii=False) if context else "Seguros"}
        
        Análise de margem e rentabilidade:
        
        1. **Decomposição de Margem**:
           - Margem bruta por produto
           - Margem operacional
           - Margem líquida
           - Drivers de variação
        
        2. **Análise de Sinistralidade**:
           - Loss ratio atual
           - Tendências históricas
           - Provisões técnicas
           - Impacto na margem
        
        3. **Rentabilidade por Segmento**:
           - Produtos mais rentáveis
           - Segmentos deficitários
           - Mix ótimo de portfólio
           - Estratégia de pricing
        
        4. **Alavancas de Melhoria**:
           - Redução de sinistralidade
           - Otimização de custos
           - Repricing estratégico
           - Cross-selling/Upselling
        
        5. **Projeções e Metas**:
           - Margem target
           - Roadmap de melhoria
           - KPIs de acompanhamento
           - Riscos e mitigações
        
        Formato: JSON com análise quantitativa detalhada.
        """
    
    def administrative_expenses(self, admin_data: Dict) -> str:
        """Generate administrative expense analysis"""
        return f"""
        {self._language_instruction}
        
        Você é um especialista em gestão de despesas administrativas.
        
        **Dados Administrativos:**
        {json.dumps(admin_data, indent=2, ensure_ascii=False)}
        
        Análise de despesas administrativas:
        
        1. **Breakdown Detalhado**:
           - Pessoal e encargos
           - Tecnologia e sistemas
           - Instalações e utilities
           - Serviços terceirizados
        
        2. **Análise de Eficiência**:
           - Custo por colaborador
           - Despesas vs Receita (%)
           - Benchmark do setor
           - Gaps identificados
        
        3. **Oportunidades de Otimização**:
           - Digitalização de processos
           - Renegociação de contratos
           - Consolidação de fornecedores
           - Trabalho remoto/híbrido
        
        4. **Investimentos Necessários**:
           - Modernização de sistemas
           - Treinamento de equipe
           - Compliance e regulação
           - ROI esperado
        
        5. **Plano de Ação**:
           - Prioridades imediatas
           - Cronograma de implementação
           - Economia esperada
           - Métricas de sucesso
        
        Formato: JSON com valores específicos e percentuais.
        """
    
    def marketing_roi(self, marketing_data: Dict, context: Dict = None) -> str:
        """Generate marketing ROI analysis for insurance"""
        return f"""
        {self._language_instruction}
        
        Você é um especialista em marketing e aquisição de clientes em seguros.
        
        **Dados de Marketing:**
        {json.dumps(marketing_data, indent=2, ensure_ascii=False)}
        
        Análise de ROI de Marketing:
        
        1. **Performance por Canal**:
           - Digital (Google, Meta, etc)
           - Corretores e parceiros
           - Vendas diretas
           - Referências
        
        2. **Métricas de Aquisição**:
           - CAC por canal
           - Taxa de conversão
           - Lifetime value
           - Payback period
        
        3. **Análise de Campanhas**:
           - Campanhas mais efetivas
           - ROI por campanha
           - Sazonalidade
           - Otimização de budget
        
        4. **Funil de Conversão**:
           - Taxa por etapa
           - Pontos de abandono
           - Melhorias prioritárias
           - A/B testing sugerido
        
        5. **Estratégia de Otimização**:
           - Realocação de budget
           - Novos canais potenciais
           - Automação de marketing
           - Projeção de resultados
        
        Formato: JSON com métricas e ROI específicos.
        """
    
    def operational_efficiency(self, efficiency_data: Dict) -> str:
        """Generate operational efficiency analysis"""
        return f"""
        {self._language_instruction}
        
        Você é um especialista em eficiência operacional para seguradoras.
        
        **Dados de Eficiência:**
        {json.dumps(efficiency_data, indent=2, ensure_ascii=False)}
        
        Análise de eficiência operacional:
        
        1. **KPIs de Eficiência**:
           - Custo/Receita ratio
           - Produtividade por FTE
           - Tempo de processamento
           - Taxa de automação
        
        2. **Análise de Processos**:
           - Gargalos identificados
           - Redundâncias
           - Oportunidades de automação
           - Quick wins
        
        3. **Benchmark Setorial**:
           - Comparação com líderes
           - Gaps principais
           - Best practices
           - Metas recomendadas
        
        4. **Tecnologia e Inovação**:
           - Sistemas legados
           - Oportunidades de IA/ML
           - RPA potencial
           - Investimento necessário
        
        5. **Roadmap de Transformação**:
           - Fase 1: Otimização (0-3 meses)
           - Fase 2: Automação (3-6 meses)
           - Fase 3: Transformação (6-12 meses)
           - ROI esperado por fase
        
        Formato: JSON com métricas e plano detalhado.
        """
    
    def seasonality_analysis(self, time_series_data: Dict) -> str:
        """Generate seasonality and trends analysis"""
        return f"""
        {self._language_instruction}
        
        Você é um especialista em análise de séries temporais e sazonalidade.
        
        **Dados Temporais:**
        {json.dumps(time_series_data, indent=2, ensure_ascii=False)}
        
        Análise de sazonalidade e tendências:
        
        1. **Padrões Sazonais**:
           - Meses de pico
           - Períodos de baixa
           - Fatores causais
           - Impacto financeiro
        
        2. **Tendências Identificadas**:
           - Crescimento/declínio
           - Pontos de inflexão
           - Ciclos recorrentes
           - Projeções futuras
        
        3. **Análise de Volatilidade**:
           - Desvio padrão mensal
           - Meses mais voláteis
           - Fatores de risco
           - Estratégias de hedge
        
        4. **Oportunidades Sazonais**:
           - Campanhas otimizadas
           - Ajuste de recursos
           - Pricing dinâmico
           - Gestão de caixa
        
        5. **Previsões e Planejamento**:
           - Próximos 3 meses
           - Próximos 6 meses
           - Cenários possíveis
           - Ações recomendadas
        
        Formato: JSON com análise estatística e recomendações.
        """
    
    def non_operational_costs(self, non_op_data: Dict) -> str:
        """Generate non-operational costs analysis"""
        return f"""
        {self._language_instruction}
        
        Você é um especialista em gestão de custos não-operacionais.
        
        **Dados Não-Operacionais:**
        {json.dumps(non_op_data, indent=2, ensure_ascii=False)}
        
        Análise de custos não-operacionais:
        
        1. **Composição de Custos**:
           - Despesas financeiras
           - Provisões e contingências
           - Despesas extraordinárias
           - Outros custos
        
        2. **Análise de Impacto**:
           - % sobre resultado
           - Tendência histórica
           - Drivers principais
           - Previsibilidade
        
        3. **Gestão de Riscos**:
           - Contingências identificadas
           - Provisões adequadas
           - Exposições financeiras
           - Hedging recomendado
        
        4. **Oportunidades de Redução**:
           - Renegociação de dívidas
           - Otimização fiscal
           - Gestão de contingências
           - Economia potencial
        
        5. **Plano de Controle**:
           - Governança recomendada
           - KPIs de monitoramento
           - Limites de exposição
           - Reporting necessário
        
        Formato: JSON com análise quantitativa e plano de ação.
        """
    
    def tax_analysis(self, tax_data: Dict, context: Dict = None) -> str:
        """Generate tax and fiscal analysis"""
        return f"""
        {self._language_instruction}
        
        Você é um especialista em planejamento tributário para seguradoras.
        
        **Dados Tributários:**
        {json.dumps(tax_data, indent=2, ensure_ascii=False)}
        
        Análise tributária e fiscal:
        
        1. **Carga Tributária Atual**:
           - Impostos diretos
           - Impostos indiretos
           - Contribuições
           - Taxa efetiva total
        
        2. **Análise de Conformidade**:
           - Obrigações principais
           - Obrigações acessórias
           - Riscos identificados
           - Contingências fiscais
        
        3. **Oportunidades de Otimização**:
           - Incentivos fiscais
           - Créditos tributários
           - Planejamento societário
           - Economia potencial
        
        4. **Comparativo Setorial**:
           - Benchmark de carga
           - Melhores práticas
           - Estruturas eficientes
           - Gaps identificados
        
        5. **Plano de Ação Fiscal**:
           - Quick wins tributários
           - Reestruturações sugeridas
           - Cronograma de implementação
           - Economia projetada
        
        Formato: JSON com valores e oportunidades específicas.
        """
    
    def revenue_growth(self, revenue_data: Dict, market_context: Dict = None) -> str:
        """Generate revenue growth analysis prompt"""
        return f"""
        {self._language_instruction}
        
        Você é um estrategista de crescimento especializado em seguros.
        
        **Dados de Receita:**
        {json.dumps(revenue_data, indent=2, ensure_ascii=False)}
        
        **Contexto de Mercado:**
        {json.dumps(market_context, indent=2, ensure_ascii=False) if market_context else "Não disponível"}
        
        Desenvolva uma estratégia de crescimento:
        
        1. **Análise de Tendências**:
           - Padrão de crescimento identificado
           - Sazonalidade detectada
           - Pontos de inflexão
           - Projeção próximos 12 meses
        
        2. **Oportunidades de Crescimento** (rankear por potencial):
           - Expansão de produtos existentes
           - Novos segmentos de clientes
           - Upselling/Cross-selling
           - Novos canais de distribuição
           - Parcerias estratégicas
        
        3. **Análise de Portfólio**:
           - Produtos estrela (alta receita, alto crescimento)
           - Vacas leiteiras (alta receita, baixo crescimento)
           - Questionáveis (baixa receita, alto potencial)
           - Abacaxis (eliminar ou transformar)
        
        4. **Estratégia de Preços**:
           - Elasticidade estimada
           - Oportunidades de repricing
           - Impacto na competitividade
        
        5. **Roadmap de Crescimento**:
           - Q1: Ações imediatas
           - Q2-Q3: Iniciativas médio prazo
           - Q4+: Transformação estratégica
           - Meta de crescimento anual: X%
        
        Formato: JSON com projeções numéricas e confidence scores.
        """
    
    def risk_assessment(self, financial_data: Dict, historical_data: List = None) -> str:
        """Generate comprehensive risk assessment prompt"""
        return f"""
        {self._language_instruction}
        
        Você é um Chief Risk Officer experiente em gestão de riscos financeiros.
        
        **Dados Financeiros Atuais:**
        {json.dumps(financial_data, indent=2, ensure_ascii=False)}
        
        **Histórico:**
        {json.dumps(historical_data, indent=2, ensure_ascii=False) if historical_data else "Limitado"}
        
        Conduza uma avaliação de risco abrangente:
        
        1. **Riscos Financeiros**:
           - Liquidez: score (0-100) e análise
           - Alavancagem: níveis e limites
           - Concentração: cliente/produto/geografia
           - Câmbio/Juros: exposição e hedging
        
        2. **Riscos Operacionais**:
           - Dependências críticas
           - Single points of failure
           - Capacidade vs demanda
           - Riscos de compliance
        
        3. **Riscos de Mercado**:
           - Competitivos
           - Regulatórios
           - Tecnológicos
           - Macroeconômicos
        
        4. **Matriz de Riscos** (para cada risco):
           - Probabilidade (Alta/Média/Baixa)
           - Impacto (Crítico/Alto/Médio/Baixo)
           - Velocidade (Rápida/Média/Lenta)
           - Mitigação existente
           - Ação recomendada
        
        5. **Early Warning Indicators**:
           - KRIs específicos para monitorar
           - Thresholds de alerta
           - Planos de contingência
        
        6. **Score de Risco Geral**: 0-100
           - Breakdown por categoria
           - Tendência (melhorando/estável/piorando)
        
        Formato: JSON estruturado com scores numéricos.
        """
    
    def cash_flow_analysis(self, cash_data: Dict, projections: Dict = None) -> str:
        """Generate cash flow analysis and projections prompt"""
        return f"""
        {self._language_instruction}
        
        Você é um tesoureiro corporativo especializado em gestão de caixa.
        
        **Dados de Caixa:**
        {json.dumps(cash_data, indent=2, ensure_ascii=False)}
        
        **Projeções Disponíveis:**
        {json.dumps(projections, indent=2, ensure_ascii=False) if projections else "A calcular"}
        
        Análise detalhada de fluxo de caixa:
        
        1. **Situação Atual**:
           - Posição de caixa
           - Burn rate mensal
           - Runway (meses)
           - Working capital needs
        
        2. **Análise de Fluxo**:
           - Entradas: regularidade e previsibilidade
           - Saídas: fixas vs variáveis
           - Gaps temporais identificados
           - Sazonalidade do caixa
        
        3. **Projeções (6 meses)**:
           - Cenário base
           - Cenário otimista (+20% receita)
           - Cenário pessimista (-20% receita)
           - Pontos críticos de caixa
        
        4. **Otimização de Working Capital**:
           - Dias de recebimento (DSO)
           - Dias de pagamento (DPO)
           - Dias de estoque (DIO)
           - Cash conversion cycle
           - Oportunidades de melhoria
        
        5. **Estratégias de Financiamento**:
           - Necessidades identificadas
           - Opções disponíveis
           - Custo estimado
           - Timing recomendado
        
        6. **Action Plan**:
           - Prioridade 1: Ações imediatas
           - Prioridade 2: Próximos 30 dias
           - Prioridade 3: Próximos 90 dias
        
        Formato: JSON com valores numéricos e datas específicas.
        """
    
    def competitive_benchmarking(self, company_metrics: Dict, industry_data: Dict = None) -> str:
        """Generate competitive benchmarking analysis prompt"""
        return f"""
        {self._language_instruction}
        
        Você é um analista de competitive intelligence no setor de seguros.
        
        **Métricas da Empresa:**
        {json.dumps(company_metrics, indent=2, ensure_ascii=False)}
        
        **Dados do Setor:**
        {json.dumps(industry_data, indent=2, ensure_ascii=False) if industry_data else "Usar conhecimento do setor de seguros"}
        
        Análise competitiva detalhada:
        
        1. **Posicionamento Competitivo**:
           - Quartil de performance (1º/2º/3º/4º)
           - Forças competitivas principais (top 3)
           - Desvantagens críticas (top 3)
           - Overall competitive score (0-100)
        
        2. **Benchmarking de KPIs**:
           Para cada métrica principal:
           - Valor da empresa
           - Média do setor
           - Best-in-class
           - Gap análise
           - Percentil ranking
        
        3. **Análise de Eficiência**:
           - Receita por funcionário
           - Margem operacional
           - ROE/ROA
           - Combined ratio (seguros)
           - Expense ratio
        
        4. **Vantagens Competitivas Sustentáveis**:
           - Identificadas
           - Em desenvolvimento
           - Ameaçadas
           - Oportunidades não exploradas
        
        5. **Strategic Moves**:
           - O que líderes estão fazendo
           - Tendências emergentes
           - Disrupções potenciais
           - Next best actions (top 5)
        
        6. **Roadmap Competitivo**:
           - Quick wins para fechar gaps
           - Iniciativas de médio prazo
           - Transformações necessárias
           - Investimentos prioritários
        
        Formato: JSON com rankings e scores numéricos.
        """
    
    def custom_question(self, question: str, data_context: Dict) -> str:
        """Generate prompt for custom user questions"""
        return f"""
        {self._language_instruction}
        
        Você é um consultor financeiro sênior com expertise em análise de dados empresariais.
        
        **Pergunta do Usuário:**
        {question}
        
        **Contexto dos Dados Disponíveis:**
        {json.dumps(data_context, indent=2, ensure_ascii=False)}
        
        Forneça uma resposta completa e estruturada que:
        
        1. **Responda Diretamente** a pergunta feita
        2. **Use os Dados** disponíveis para fundamentar a resposta
        3. **Adicione Context** relevante quando apropriado
        4. **Sugira Follow-ups** - próximas perguntas relevantes
        5. **Forneça Recomendações** práticas e acionáveis
        
        Estruture a resposta de forma clara e profissional.
        Use números e métricas específicas sempre que possível.
        
        Formato: JSON estruturado ou texto formatado, conforme apropriado para a pergunta.
        """
    
    def monthly_analysis(self, monthly_data: Dict, month: str, comparison_month: str = None) -> str:
        """Generate monthly analysis prompt"""
        return f"""
        {self._language_instruction}
        
        Você é um controller financeiro realizando análise mensal.
        
        **Dados do Mês {month}:**
        {json.dumps(monthly_data, indent=2, ensure_ascii=False)}
        
        {f"**Mês de Comparação {comparison_month}:**" if comparison_month else ""}
        
        Análise mensal detalhada:
        
        1. **Performance do Mês**:
           - Receita vs meta
           - Custos vs orçamento
           - Margem realizada
           - Principais variações
        
        2. **Análise de Variações**:
           - Top 5 variações positivas
           - Top 5 variações negativas
           - Explicação das causas
           - Impacto no resultado
        
        3. **Indicadores de Eficiência**:
           - Produtividade
           - Utilização de recursos
           - Cost per acquisition
           - Customer lifetime value
        
        4. **Comparações**:
           - MoM (mês a mês)
           - YoY (ano a ano)
           - YTD (acumulado do ano)
           - Vs budget/forecast
        
        5. **Red Flags**:
           - Desvios preocupantes
           - Tendências negativas
           - Riscos emergentes
        
        6. **Próximos Passos**:
           - Correções imediatas
           - Ajustes de processo
           - Revisões de forecast
        
        Formato: JSON com valores e percentuais específicos.
        """