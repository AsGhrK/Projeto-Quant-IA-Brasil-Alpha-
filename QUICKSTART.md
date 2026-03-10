# 🚀 Guia de Início Rápido - Quant IA Brasil

## 📋 Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Conexão com internet (para coleta de dados)

## ⚡ Instalação Rápida

### 1. Clone o repositório (se ainda não fez)
```bash
git clone <seu-repositorio>
cd Projeto-Quant-IA-Brasil-Alpha-
```

### 2. Crie e ative o ambiente virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione sua chave da NewsAPI (obtenha gratuitamente em https://newsapi.org):
```
NEWS_API_KEY=sua_chave_aqui
```

### 5. Inicie o sistema

**Opção 1: Usando o script de inicialização (Recomendado)**
```bash
python start.py
```

Este script irá:
- Verificar e criar os bancos de dados
- Oferecer criação de carteira de teste
- Coletar dados iniciais do mercado
- Iniciar o aplicativo Streamlit

**Opção 2: Inicialização manual**
```bash
# Criar bancos de dados e carteira de teste
python scripts/setup_carteira.py

# Coletar dados do mercado
python scripts/collect_all.py

# Iniciar o aplicativo
streamlit run apps/app_quant_ia.py
```

## 🔐 Login no Sistema

Após a inicialização, use as credenciais de teste:
- **Username:** demo
- **Senha:** demo123

## 📊 Funcionalidades Disponíveis

### 1. Dashboard Principal
- Visualização de métricas em tempo real (IBOV, BTC, ETH, USD/BRL)
- Gráficos interativos com indicadores técnicos
- Notícias do mercado com análise de sentimento

### 2. Chat com IA
- Faça perguntas sobre ativos específicos
- Receba recomendações baseadas em ML e análise técnica
- Exemplo: "Qual sua análise sobre PETR4?"

### 3. Gestão de Carteira
- Adicione e edite seus ativos
- Calcule a "Bola de Neve" (quantas cotas para viver de dividendos)
- Acompanhe rentabilidade e progresso

### 4. Portfolio Advisor
Execute análise estratégica da sua carteira:
```bash
python portfolio_advisor.py
```

## 🔧 Scripts Úteis

### Coletar dados do mercado manualmente
```bash
python scripts/collect_all.py
```

### Iniciar coleta automática (a cada 15 minutos)
```bash
python scripts/scheduler.py
```

### Testar o assistente de IA
```bash
python scripts/test_assistant.py
```

### Resetar carteira de teste
```bash
python scripts/setup_carteira.py
```

## 🗄️ Estrutura dos Bancos de Dados

O projeto usa dois bancos SQLite isolados:

- **market_data.db**: Dados públicos do mercado (ações, criptos, notícias)
- **user_data.db**: Dados sensíveis (usuários, senhas, carteiras)

## 🔄 Coleta de Dados

Os dados são coletados de:
- **Yahoo Finance** (yfinance): Ações B3 e mercados globais
- **Binance API**: Criptomoedas (BTC, ETH)
- **NewsAPI**: Notícias financeiras com análise de sentimento

## ⚠️ Troubleshooting

### Erro: "ModuleNotFoundError"
Certifique-se de que o ambiente virtual está ativado e as dependências instaladas:
```bash
pip install -r requirements.txt
```

### Erro: "API Key inválida"
Verifique se configurou corretamente a `NEWS_API_KEY` no arquivo `.env`

### Erro: "No data found"
Execute a coleta de dados manualmente:
```bash
python scripts/collect_all.py
```

### Aplicativo não abre no navegador
Acesse manualmente: http://localhost:8501

## 📝 Notas Importantes

- A primeira coleta de dados pode levar alguns minutos
- Os dados são atualizados automaticamente se o scheduler estiver rodando
- A carteira de teste inclui: PETR4.SA, MXRF11.SA, VALE3.SA
- As senhas são armazenadas com hash bcrypt para segurança

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verifique os logs no terminal
2. Consulte o arquivo ORGANIZACAO.md para detalhes da estrutura
3. Execute os scripts de teste para diagnosticar

## 🔐 Segurança

- Nunca commite o arquivo `.env` (já está no .gitignore)
- Use senhas fortes em produção
- Os dados sensíveis ficam isolados em `user_data.db`
- As API keys devem ser mantidas em variáveis de ambiente

## 📚 Próximos Passos

1. Adicione seus próprios ativos na carteira
2. Configure alertas personalizados
3. Explore as análises de ML e padrões técnicos
4. Acompanhe as recomendações da IA

---

**Desenvolvido com ❤️ para o mercado brasileiro**
