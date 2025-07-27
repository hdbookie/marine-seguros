"""
This module is responsible for interacting with the Generative AI model 
to get insights from the financial data.
"""
import google.generativeai as genai
import pandas as pd

class AIAnalyzer:
    """
    A class to analyze financial data using a generative AI model.
    """
    def __init__(self, api_key, language="pt-br"):
        """
        Initializes the AIAnalyzer.

        Args:
            api_key (str): The API key for the generative AI model.
            language (str): The language for the AI's responses.
        """
        self.api_key = api_key
        self.language = language
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _get_prompt_language(self):
        """
        Returns the prompt language instruction.
        """
        if self.language == "English":
            return "Please provide the analysis in English."
        return "Por favor, forneça a análise em português do Brasil."

    def generate_micro_analysis_insights(self, df: pd.DataFrame):
        """
        Generates insights from the micro-level data.

        Args:
            df (pd.DataFrame): The DataFrame containing the detailed line items.

        Returns:
            str: The AI-generated insights.
        """
        if df.empty:
            return "Não há dados para analisar."

        # Convert DataFrame to a more readable format for the AI
        data_string = df.to_string()

        prompt = f"""
        {self._get_prompt_language()}

        Contexto: Você é um analista financeiro especialista em contabilidade e análise de resultados.
        Sua tarefa é analisar os dados de despesas detalhadas de uma empresa e fornecer insights valiosos.

        Os dados a seguir representam uma lista de despesas e custos, com suas respectivas categorias, subcategorias e valores anuais.

        Dados:
        {data_string}

        Por favor, analise os dados acima e forneça os seguintes insights:
        1.  **Análise de Pareto (80/20):** Identifique os poucos itens (aproximadamente 20%) que representam a maior parte (aproximadamente 80%) dos custos totais. Destaque os itens mais relevantes.
        2.  **Itens Inesperados ou Incomuns:** Aponte quaisquer despesas que pareçam fora do comum, inesperadas ou que mereçam uma investigação mais aprofundada. Justifique sua escolha.
        3.  **Sugestões de Otimização:** Com base na análise, sugira de 2 a 3 áreas ou itens específicos onde a empresa poderia focar para otimizar custos sem impactar negativamente a operação.

        Apresente a resposta de forma clara e organizada.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Ocorreu um erro ao gerar os insights: {e}"

