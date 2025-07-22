# Marine Seguros - Financial Analytics Platform

Uma plataforma de análise financeira inteligente com IA para Marine Seguros, cobrindo dados de 2018-2025.

## 🚀 Funcionalidades

- **📊 Dashboard Interativo**: Visualizações dinâmicas de receita, lucro e margens
- **🤖 Insights com IA**: Análises automáticas usando Google Gemini
- **📈 Previsões**: Projeções financeiras e análise de cenários
- **📁 Upload Flexível**: Suporte para múltiplos arquivos Excel
- **📥 Exportação**: Relatórios em PDF e Excel
- **⚡ Integração Make.com**: Atualização automática via webhooks

## 🛠️ Instalação

### 1. Clone o repositório
```bash
cd marine-seguros
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite .env e adicione sua chave API do Gemini
```

### 4. Execute a aplicação
```bash
streamlit run app.py
```

## 📋 Como Usar

### 1. Upload de Dados
- Faça upload dos arquivos Excel ou use os arquivos existentes
- Formatos suportados: .xlsx, .xls

### 2. Visualize o Dashboard
- Métricas principais
- Gráficos de evolução
- Análise de crescimento
- Detecção de anomalias

### 3. Gere Insights com IA
- Insira sua chave API do Gemini
- Clique em "Gerar Insights"
- Receba análises detalhadas em português

### 4. Exporte Relatórios
- PDF: Relatório completo formatado
- Excel: Dados estruturados em múltiplas abas

## 🔗 Integração Make.com

### Configuração do Webhook

1. Crie um cenário no Make.com
2. Adicione um webhook trigger
3. Configure as conexões bancárias (Plaid/TrueLayer)
4. Use o template fornecido

### Fluxo de Automação
```
Banco → Make.com → Webhook → App → Análise → Relatório
```

## 📊 Estrutura dos Dados

### Arquivos Excel Esperados:
- `Análise de Resultado Financeiro 2018_2023.xlsx`
- `Resultado Financeiro - 2024.xlsx`
- `Resultado Financeiro - 2025.xlsx`

### Métricas Analisadas:
- Faturamento (Receita)
- Custos Variáveis
- Margem de Contribuição
- Despesas Operacionais
- Lucro Líquido
- Margem de Lucro

## 🌐 Deploy

### Opção 1: Streamlit Cloud (Grátis)
1. Faça fork do repositório
2. Conecte ao Streamlit Cloud
3. Configure os secrets

### Opção 2: Docker
```bash
docker build -t marine-financial .
docker run -p 8501:8501 marine-financial
```

### Opção 3: Heroku
```bash
heroku create marine-financial
git push heroku main
```

## 💰 Custos Estimados

- **Gemini API**: ~R$ 0,50-2,00/mês
- **Make.com**: Plano gratuito suficiente
- **Hosting**: Streamlit Cloud (grátis)

## 🔒 Segurança

- Chaves API armazenadas em variáveis de ambiente
- Dados processados localmente
- Sem armazenamento permanente de dados sensíveis

## 📞 Suporte

Para dúvidas ou problemas:
- Email: suporte@marineseguros.com.br
- Documentação: [Link para docs]

## 🚀 Próximas Funcionalidades

- [ ] Análise preditiva avançada
- [ ] Benchmarking com mercado
- [ ] Dashboard mobile
- [ ] Alertas automáticos
- [ ] Integração com mais bancos

---

Desenvolvido com ❤️ para Marine Seguros