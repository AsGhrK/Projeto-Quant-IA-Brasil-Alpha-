# 🌐 Quant IA Brasil - Plataforma Quantitativa de Análise de Investimentos

> Uma plataforma de análise quantitativa integrada com inteligência artificial para otimizar decisões de investimento no Brasil.

## ⚡ Início Rápido

### 🚀 Como Executar (Método Simples)

```bash
# 1. Ative o ambiente virtual (se ainda não estiver ativo)
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Execute o script de inicialização
python start.py
```

O script `start.py` irá:
- ✅ Verificar e criar os bancos de dados
- ✅ Oferecer criação de carteira de teste
- ✅ Coletar dados iniciais do mercado
- ✅ Iniciar o aplicativo Streamlit automaticamente

### 🔐 Credenciais de Teste

Após iniciar, faça login com:
- **Username:** `demo`
- **Senha:** `demo123`

### 📚 Documentação Completa

Para instruções detalhadas, consulte [QUICKSTART.md](QUICKSTART.md)

---

## 📊 O que é Quant IA Brasil?

Um ecossistema completo que combina:

- **📈 Coleta Automática de Dados**: Ações (B3), Cripto (Binance: BTC, ETH), Mercados Globais (IBOV, USD/BRL, EUR/BRL, etc.), Notícias financeiras com análise de sentimento
- **🤖 Análise com ML**: Modelos de previsão (RandomForest) e detecção de padrões técnicos (RSI, EMA, MACD, etc.)
- **🌐 APIs em tempo real**: Consulta a dados de mercado via yfinance e Binance, notícias via NewsAPI, com cache para performance
- **🧠 IA Assistente**: Assistente conversacional que extrai tickers de perguntas, analisa ML, sentimento e regime de mercado para recomendações (comprar/evitar/neutro)
- **💼 Gestão de Carteira**: Acompanhamento de posições com cálculo de dividendos, efeito bola de neve e projeções
- **📱 Interface Streamlit**: Dashboard com métricas em tempo real (IBOV, BTC, ETH, USD/BRL, EUR/BRL), gráficos históricos, notícias e IA integrada

---

## 📁 Estrutura do Projeto (v2.0)

```
quant-ia-brasil/
├── apps/                          # 🎨 Aplicações Streamlit
│   ├── app_quant_ia.py           # App principal: Dashboard + Carteira
│   └── dashboard.py              # Análise de Bola de Neve
│
├── core/                          # 🔧 Núcleo do projeto
│   ├── database/
│   │   └── database.py           # Gerenciador de banco de dados
│   ├── data/
│   │   ├── crypto_collector.py   # Coleta de criptomoedas (Binance)
│   │   ├── global_collector.py   # Mercados globais (yfinance)
│   │   ├── market_data.py        # Utilitários de dados
│   │   ├── news_collector.py     # Análise de sentimento de notícias
│   │   └── stocks_collector.py   # Coleta de ações (B3)
│   ├── models/
│   │   └── ml_model.py           # RandomForest para previsão
│   ├── indicators/
│   │   └── technical.py          # RSI, EMA, MACD, Volatilidade
│   └── engines/
│       ├── ai_assistant.py       # IA conversacional
│       ├── patterns.py           # Detecção de padrões
│       ├── regime_engine.py      # Análise de regime de mercado
│       └── decision_engine.py    # Lógica de decisões estratégicas
│
├── scripts/                       # 🔄 Automação e utilitários
│   ├── scheduler.py              # Coleta automática a cada 15 min
│   ├── collect_all.py            # Orquestrador de coleta
│   ├── setup_carteira.py         # Inicialização com dados de exemplo
│   └── test_assistant.py         # Testes de ponta-a-ponta
│
├── legacy/                        # 📦 Arquivos deprecados
│   ├── app_principal.py
│   ├── market_scanner.py
│   └── main.py
│
├── market_data.db                # 💾 Banco SQLite
├── requirements.txt              # Dependências Python
├── ORGANIZACAO.md                # Guia de estrutura do projeto
└── README.md                     # Este arquivo
```

---

## 🚀 Como Usar

### 1️⃣ Instalação

```bash
# 1. Clonar o repositório
git clone <seu-repositorio>
cd Projeto-Quant-IA-Brasil-Alpha-

# 2. Criar e ativar ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate    # Linux/Mac

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
# Copie .env.example para .env e adicione sua NewsAPI key
cp .env.example .env
# Edite o arquivo .env com sua API key
```

### 2️⃣ Inicialização

**Método Simples (Recomendado):**
```bash
python start.py
```

**Método Manual:**
```bash
# Criar bancos e carteira de teste
python scripts/setup_carteira.py

# Coletar dados do mercado
python scripts/collect_all.py

# Iniciar o Dashboard
streamlit run apps/app_quant_ia.py
```

Acesse: **http://localhost:8501**


---

## 🔑 Credenciais de Teste

O banco vem com um usuário pré-configurado para testes:

| Campo | Valor |
|-------|-------|
| **Usuário** | `demo` |
| **Senha** | `demo123` |

> ⚠️ **Importante**: Mude a senha no primeiro acesso! O hashing é feito com `bcrypt`.

---

## 🎯 Funcionalidades Principais

### 📊 Dashboard Analítico
- Métricas em tempo real: IBOV, BTC, ETH, USD/BRL, EUR/BRL
- Evolução histórica de ativos (últimos 6 meses)
- Projeção de "Efeito Bola de Neve" (dividendos gerando novas cotas)

### 💼 Gerenciamento de Posições
- Tabela de posições com preços atualizados
- Cálculo de preço médio ponderado
- Análise de cotas mágicas (quando dividendos compram 1 cota sozinho)
- Lançamento e liquidação de operações

### 🤖 IA Assistente
- Conversação estilo ChatGPT/Grok: o usuário pergunta sobre qualquer ativo e recebe resposta natural
- Integração com APIs de mercado, cripto e notícias em tempo real para capturar contexto atual
- Identificação de padrões técnicos e estatísticos antes de recomendar (comprar/evitar/neutro)
- Fornece razão breve e objetiva junto com cada sugestão, explicando indicadores, sentimento ou regime que motivou a escolha
- Permite acesso parcial à internet para consultar recursos adicionais quando necessário

### 🔄 Automação
- **Scheduler**: Coleta automática a cada 15 minutos
- **Coletores**: Stocks, Cripto, Mercados Globais, Notícias
- **Atualização de BD**: Em tempo real sem interrupção da app

---

## 🔐 Segurança

✅ **Senhas**: Hashing com `bcrypt`  
✅ **Banco de Dados**: SQLite com autenticação por usuário  
✅ **Validação**: Proteção contra divisão por zero em cálculos  
✅ **Logging**: Exceções rastreadas em tempo real  

---

## 📊 Dependências Principais

| Biblioteca | Uso |
|------------|-----|
| `streamlit` | Interface web |
| `yfinance` | Dados de ações e criptos |
| `pandas` | Manipulação de dados |
| `scikit-learn` | ML (RandomForest) |
| `ta` | Indicadores técnicos |
| `textblob` | Análise de sentimento |
| `bcrypt` | Hashing de senhas |
| `plotly` | Gráficos interativos |

Veja [requirements.txt](requirements.txt) para a lista completa.

---

## 🛠️ Desenvolvimento

### Rodar Testes
```bash
python scripts/test_assistant.py
```

### Estruturar Novo Coletor
1. Criar arquivo em `core/data/novo_collector.py`
2. Implementar função `collect_novo_data()`
3. Adicionar em `scripts/collect_all.py`

### Adicionar Novo Engine
1. Criar arquivo em `core/engines/novo_engine.py`
2. Importar em `core/engines/__init__.py`
3. Usar em `apps/app_quant_ia.py`

---

## 📈 Próximas Melhorias

- [ ] API REST (FastAPI) para integração externa
- [ ] Cache distribuído (Redis) para performance
- [ ] PostgreSQL para produção
- [ ] Dashboard com Plotly Dash (alternativa de UI)
- [ ] Backtesting de estratégias
- [ ] Alertas por email/SMS
- [ ] Deploy em Docker + AWS

---

## 📝 Documentação Adicional

- [Guia de Organização](ORGANIZACAO.md) – Mapeamento completo de pastas
- [Changelog](#) – Histórico de versões
- [API Reference](#) – Documentação de funções

---

## � Deploy e Produção

### Streamlit Cloud (Recomendado para Demo)
1. Faça upload do projeto para um repositório GitHub público
2. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte o repo
3. Configure secrets para APIs (NewsAPI, Binance) no painel do Streamlit Cloud
4. Deploy automático – pronto para uso!

### Servidor Local/Produção
- Use `gunicorn` ou similar para produção
- Configure variáveis de ambiente para chaves de API
- Para BD, considere PostgreSQL em produção (atual é SQLite para simplicidade)

---

## �👤 Autor

Desenvolvido com ❤️ para a comunidade de investidores quantitativos.

**Data**: 4 de março de 2026  
**Status**: ✅ Estrutura v2.0 finalizada

---

## 📄 Licença

Este projeto é fornecido como-é para fins educacionais.  
Use por sua conta e risco em operações reais.

---

## 🤝 Contribuições

Sugestões e melhorias são bem-vindas!  
Abra uma issue ou envie um PR.

---

**Última atualização**: 4 de março de 2026
