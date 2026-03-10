# 🤖 Funcionalidades de IA do Quant IA Brasil

## 📋 Índice
1. [🆕 Análise Automática do Mercado Brasileiro](#análise-automática-do-mercado-brasileiro)
2. [Análise Automática de Carteira](#análise-automática-de-carteira)
3. [Alertas Inteligentes no Dashboard](#alertas-inteligentes-no-dashboard)
4. [Busca de Recomendações para Qualquer Ativo](#busca-de-recomendações-para-qualquer-ativo)
5. [Sistema de Pontuação (Score 0-100)](#sistema-de-pontuação-score-0-100)
6. [Indicadores e Análises Utilizados](#indicadores-e-análises-utilizados)
7. [Categorias de Recomendação](#categorias-de-recomendação)

---

## 🆕 1. Análise Automática do Mercado Brasileiro

### 📍 Localização
Na página **"Dashboard Analítico"**, seção **"📈 Oportunidades no Mercado Brasileiro"**.

### 🎯 O que faz?
A IA analisa automaticamente **os principais ativos da B3** (ações, fundos imobiliários e índices) para identificar as melhores oportunidades de investimento no mercado brasileiro.

### 🔍 Ativos Incluídos (50 tickers):

#### 🏢 Blue Chips B3 (30 ações):
- **Petrobras**: PETR4.SA, PETR3.SA
- **Vale**: VALE3.SA, VALE5.SA
- **Bancos**: ITUB4.SA, BBDC4.SA, BBAS3.SA, ITSA4.SA
- **Varejo**: ABEV3.SA, MGLU3.SA
- **Indústria**: WEGE3.SA, EMBR3.SA, RENT3.SA
- **Mineração/Siderurgia**: GGBR4.SA, CSNA3.SA, USIM5.SA, BRAP4.SA
- **Energia**: EQTL3.SA, CMIG4.SA, ELET3.SA, CPLE6.SA
- **Outros**: B3SA3.SA, SUZB3.SA, JBSS3.SA, RAIL3.SA, HAPV3.SA, CSAN3.SA, RADL3.SA, PRIO3.SA, KLBN11.SA, VIVT3.SA

#### 🏠 Fundos Imobiliários (10 FIIs):
- MXRF11.SA, HGLG11.SA, KNRI11.SA, XPML11.SA, VISC11.SA
- BTLG11.SA, HGRU11.SA, BCFF11.SA, KNCR11.SA, RBRR11.SA

#### 📊 Small/Mid Caps (10 ações):
- AZUL4.SA, GOAU4.SA, COGN3.SA, TOTS3.SA, QUAL3.SA
- BRFS3.SA, MRFG3.SA, BEEF3.SA, LWSA3.SA

### 🎛️ Como usar?

1. **Selecione quantos ativos analisar:**
   - Use o slider: 10, 20, 30, 40 ou 50 ativos
   - **Recomendado:** 20 ativos (equilíbrio entre abrangência e velocidade)

2. **Clique em "🔍 Analisar Mercado":**
   - A IA começará a análise
   - Barra de progresso mostra o andamento
   - Análise é salva em cache (não precisa refazer toda hora)

3. **Explore os resultados em 3 abas:**

#### 🎯 Aba 1: Melhores Oportunidades
- **Top 10 Oportunidades** do mercado brasileiro
- Ordenadas por **Score** (maior primeiro)
- Medalhas para os 3 primeiros: 🥇🥈🥉
- **Cards expandíveis** com análise completa de cada ativo
- **Botão "➕ Adicionar à Carteira"** em cada card

**Informações em cada card:**
- 💰 Preço Atual
- 📊 RSI (Índice de Força Relativa)
- 🤖 Probabilidade ML de Alta
- 🎯 Acurácia do Modelo
- 📈 EMA50 e EMA200
- 🎯 Ação Recomendada
- 🌍 Regime de Mercado
- 📊 Lista de Alertas (Golden Cross, Volume, etc.)

#### 📊 Aba 2: Tabela Completa
- **Todos os ativos analisados** em tabela
- Colunas: Ticker, Recomendação, Score, Preço, RSI, Prob. Alta, Regime
- Ordenação automática por Score (maior → menor)
- **Botão "📥 Baixar Análise em CSV"**
  - Exporta para Excel/Google Sheets
  - Nome do arquivo: `analise_mercado_brasileiro_YYYYMMDD_HHMM.csv`

#### ⚠️ Aba 3: Riscos
- Ativos com recomendação **EVITAR** ou **VENDA**
- Ordenados por Score (menor → maior = maior risco)
- Alertas de **sinais negativos** destacados
- Útil para evitar armadilhas do mercado

### 📊 Resumo Visual
No topo da seção, 5 métricas rápidas:
- 🚀 **Compra Forte**: Quantidade de ativos com score 70-100
- 🟢 **Compra**: Quantidade com score 50-69
- 🟡 **Neutro**: Quantidade com score 35-49
- ⚠️ **Evitar**: Quantidade com score 20-34
- 🔴 **Venda**: Quantidade com score 0-19

### 💡 Exemplo de Uso Prático

**Cenário:** Investidor quer encontrar boas oportunidades na B3

```
1. Dashboard → Seção "Oportunidades no Mercado Brasileiro"

2. Seleciona "30 ativos" no slider

3. Clica "🔍 Analisar Mercado"

4. Aguarda 2-3 minutos (IA analisando...)

5. Resultados aparecem:
   📊 Resumo:
   - 🚀 Compra Forte: 4 ativos
   - 🟢 Compra: 8 ativos
   - 🟡 Neutro: 12 ativos
   - ⚠️ Evitar: 4 ativos
   - 🔴 Venda: 2 ativos

6. Abre "Melhores Oportunidades":
   🥇 #1 - VALE3.SA | Score: 82 | COMPRA FORTE 🚀🟢
   🥈 #2 - WEGE3.SA | Score: 78 | COMPRA FORTE 🚀🟢
   🥉 #3 - PETR4.SA | Score: 75 | COMPRA FORTE 🚀🟢

7. Clica em "VALE3.SA" para ver detalhes:
   💰 Preço: R$ 62.45
   📊 RSI: 45.2
   🤖 Prob. Alta: 72.3%
   🎯 Acurácia: 86.1%
   
   🎯 Ação: Comprar ou aumentar posição
   🌍 Regime: Alta - Ibovespa +1.8%
   
   📊 Alertas:
   - 🟢 Golden Cross (EMA50 > EMA200)
   - 🟢 RSI em zona de compra
   - 🟢 Volume 2.1x acima da média

8. Clica "➕ Adicionar VALE3.SA à Carteira"
   → Sistema redireciona para "Gerenciar Posições"
   → VALE3.SA já pré-selecionado
   → Insere quantidade e preço
   → Registra operação!

9. Volta ao Dashboard e baixa CSV:
   "📥 Baixar Análise em CSV"
   → Abre no Excel para análise offline
```

### 🔄 Atualização da Análise
- **Cache automático**: Análise fica salva para economizar tempo
- **Refazer análise**: Clique novamente em "🔍 Analisar Mercado"
- **Recomendado**: Refazer 1x por dia (dados mudam ao longo do pregão)

### ⚡ Performance
| Quantidade | Tempo Estimado |
|------------|----------------|
| 10 ativos  | ~30 segundos   |
| 20 ativos  | ~1 minuto      |
| 30 ativos  | ~2 minutos     |
| 40 ativos  | ~3 minutos     |
| 50 ativos  | ~4 minutos     |

*Tempos variam conforme velocidade da internet e processamento*

---

## 2. Análise Automática de Carteira

### 📊 O que faz?
A IA analisa **automaticamente** todos os ativos da sua carteira ao acessar a página "Gerenciar Posições".

### 🔍 Informações fornecidas para cada ativo:
- ✅ **Score de 0 a 100**: Pontuação geral baseada em múltiplos indicadores
- ✅ **Recomendação**: COMPRA FORTE 🟢 | COMPRA 🟢 | NEUTRO 🟡 | EVITAR ⚠️ | VENDA 🔴
- ✅ **Preço Atual**: Valor de mercado em tempo real
- ✅ **RSI**: Índice de Força Relativa (sobrevenda/sobrecompra)
- ✅ **EMA 50 e EMA 200**: Médias móveis exponenciais
- ✅ **Probabilidade ML de Alta**: % de chance de subida segundo o modelo de Machine Learning
- ✅ **Acurácia do Modelo**: Confiabilidade da previsão
- ✅ **Regime de Mercado**: Contexto macro (Alta, Baixa, Lateral)
- ✅ **Lista de Alertas**: Sinais específicos detectados (Golden Cross, Death Cross, Volume anormal, etc.)

### 💡 Sugestões Personalizadas
Para cada ativo, a IA entrega uma sugestão específica:
- **COMPRA FORTE**: "Considere AUMENTAR sua posição. Indicadores muito favoráveis!"
- **COMPRA**: "Bom momento para fazer aportes."
- **VENDA**: "Considere REDUZIR ou ZERAR posição para proteger capital."
- **EVITAR**: "NÃO faça novos aportes. Aguarde reversão da tendência."
- **NEUTRO**: "MANTENHA posição e continue monitorando."

---

## 2. Alertas Inteligentes no Dashboard

### 📍 Localização
Na página **"Dashboard Analítico"**, seção **"🤖 ALERTAS INTELIGENTES DA IA"**.

### 🎯 O que mostra?
Todos os ativos da sua carteira são analisados e **categorizados automaticamente**:

#### 🟢 Oportunidades (Coluna Esquerda):
- **COMPRA FORTE**: Ativos com sinais técnicos e ML muito favoráveis
- **COMPRA**: Ativos com boa probabilidade de valorização

#### 🔴 Riscos (Coluna Direita):
- **EVITAR**: Ativos em tendência de baixa - não fazer novos aportes
- **VENDA**: Ativos com sinais críticos - considerar liquidação

#### 🟡 Neutros:
- **NEUTRO**: Ativos sem sinais claros - manter e monitorar

### 📊 Resumo Geral
Exibe métricas consolidadas:
- Total de ativos analisados
- Quantidade de ativos com COMPRA FORTE
- Quantidade de ativos com COMPRA
- Quantidade de ativos com RISCO (Evitar + Venda)

---

## 3. Busca de Recomendações para Qualquer Ativo

### 📍 Localização
Na página **"Gerenciar Posições"**, seção **"🔍 Buscar Recomendação IA para Qualquer Ativo"**.

### 🔎 Como usar?
1. Digite o ticker do ativo que deseja analisar
   - Exemplos: `PETR4.SA` (Petrobras), `BTC-USD` (Bitcoin), `VALE3.SA` (Vale)
2. Clique em **"🔎 Analisar com IA"**
3. Receba análise completa em segundos!

### 📈 Resultado da Análise
A IA retorna um relatório completo com:

#### 🎨 Header Visual
- Recomendação principal destacada com cores
- Score geral (0-100) em formato visual
- Cor verde para compra, amarelo para neutro, vermelho para venda

#### 📊 Métricas Principais
**Coluna 1:**
- Preço Atual
- RSI (Índice de Força Relativa)

**Coluna 2:**
- EMA 50 (Média Móvel Exponencial 50 dias)
- EMA 200 (Média Móvel Exponencial 200 dias)

**Coluna 3:**
- Probabilidade ML de Alta (%)
- Acurácia do Modelo (%)

#### 🎯 Análise Detalhada
**Lado Esquerdo:**
- **Ação Recomendada**: Descrição textual clara (Comprar, Vender, Aguardar)
- **Regime de Mercado**: Contexto macro atual (Alta 🟢, Baixa 🔴, Lateral 🟡)

**Lado Direito:**
- **Sinais e Indicadores**: Lista de todos os alertas detectados
  - 🟢 Sinais positivos (subida, compra, golden cross)
  - 🔴 Sinais negativos (queda, venda, death cross)
  - 🟡 Sinais neutros (volume normal, lateralização)

#### 💡 Análise Final
Resumo executivo da recomendação com:
- Explicação da recomendação
- Justificativa baseada nos indicadores
- Score final
- Probabilidade ML
- Tendência de mercado

#### ➕ Ação Rápida
Se a recomendação for **COMPRA** ou **COMPRA FORTE**, aparece um botão:
- **"➕ Adicionar [TICKER] à Minha Carteira"**
- Clique para adicionar instantaneamente o ativo

---

## 4. Sistema de Pontuação (Score 0-100)

### 🎯 Como funciona?
O score é calculado combinando múltiplos fatores com pesos diferentes:

### 📊 Componentes do Score

| Indicador | Peso | Pontos Máximos | Critérios |
|-----------|------|----------------|-----------|
| **Probabilidade ML** | 40% | 40 pontos | Modelo RandomForest prevê valorização |
| **RSI** | 20% | 20 pontos | Zona de sobrevenda (< 30): +20<br>Neutro (30-70): +10<br>Sobrecompra (> 70): +0 |
| **Tendência EMA** | 20% | 20 pontos | EMA50 > EMA200 (Tendência de alta): +20<br>Golden Cross recente: +bonus<br>EMA50 < EMA200: +5 |
| **MACD** | 10% | 10 pontos | MACD > Signal (Momentum positivo): +10<br>MACD < Signal: +0 |
| **Volume** | 10% | 10 pontos | Volume > 1.5x média: +10<br>Volume normal: +5<br>Volume baixo: +0 |

### 📈 Interpretação do Score

| Score | Categoria | Significado |
|-------|-----------|-------------|
| **70-100** | 🟢 COMPRA FORTE | Múltiplos indicadores favoráveis, alta probabilidade de valorização |
| **50-69** | 🟢 COMPRA | Indicadores positivos, boa oportunidade de entrada |
| **35-49** | 🟡 NEUTRO | Sinais mistos, aguardar definição |
| **20-34** | ⚠️ EVITAR | Indicadores desfavoráveis, não fazer novos aportes |
| **0-19** | 🔴 VENDA | Múltiplos sinais negativos, considerar saída |

---

## 5. Indicadores e Análises Utilizados

### 🤖 Machine Learning (40% do Score)
**Modelo:** Random Forest Classifier
**Features:** RSI, EMA50, EMA200, MACD, Volume Ratio, Volatilidade
**Treinamento:** Dados históricos de 6 meses
**Output:** Probabilidade de alta nos próximos dias

### 📊 Indicadores Técnicos

#### 1. RSI - Índice de Força Relativa (20% do Score)
- **Cálculo:** Média de ganhos vs média de perdas em 14 períodos
- **Interpretação:**
  - RSI < 30: Sobrevenda - Possível reversão de alta
  - RSI 30-70: Zona neutra
  - RSI > 70: Sobrecompra - Possível correção

#### 2. EMA - Médias Móveis Exponenciais (20% do Score)
- **EMA 50**: Tendência de curto/médio prazo
- **EMA 200**: Tendência de longo prazo
- **Golden Cross**: EMA50 cruza acima da EMA200 → Sinal de compra
- **Death Cross**: EMA50 cruza abaixo da EMA200 → Sinal de venda

#### 3. MACD - Moving Average Convergence Divergence (10% do Score)
- **Linha MACD**: EMA12 - EMA26
- **Linha Signal**: EMA9 do MACD
- **Interpretação:**
  - MACD > Signal: Momentum de alta
  - MACD < Signal: Momentum de baixa

#### 4. Volume Ratio (10% do Score)
- **Cálculo:** Volume atual / Média de volume (20 dias)
- **Interpretação:**
  - Ratio > 1.5: Volume alto - Confirmação de movimento
  - Ratio 0.8-1.5: Volume normal
  - Ratio < 0.8: Volume baixo - Falta de interesse

#### 5. Volatilidade
- **Cálculo:** Desvio padrão de retornos em 20 dias
- **Uso:** Ajuste de risco nas recomendações

### 🌍 Regime de Mercado
**Indicadores Macro:**
- IBOV (Ibovespa)
- USD/BRL (Dólar)
- BTC-USD (Bitcoin)
- ETH-USD (Ethereum)

**Categorias:**
- **Alta**: Índices em tendência positiva
- **Baixa**: Índices em tendência negativa
- **Lateral**: Mercado sem direção definida

**Impacto:** O regime influencia o peso dado aos sinais individuais

---

## 6. Categorias de Recomendação

### 🟢 COMPRA FORTE
**Critérios:**
- Score ≥ 70
- Probabilidade ML ≥ 60%
- RSI na zona de compra
- Golden Cross ou EMA50 > EMA200
- MACD positivo
- Volume acima da média

**Ação Sugerida:**
- ✅ Iniciar nova posição
- ✅ Aumentar posição existente
- ✅ Alocar % significativa da carteira

**Exemplo de Mensagem:**
> "PETR4.SA apresenta sinais técnicos e fundamentais muito positivos. É um excelente momento para **iniciar posição** ou **aumentar exposição**."

---

### 🟢 COMPRA
**Critérios:**
- Score 50-69
- Probabilidade ML 50-59%
- Indicadores majoritariamente positivos
- Tendência de alta confirmada

**Ação Sugerida:**
- ✅ Fazer aportes regulares
- ✅ Iniciar posição conservadora
- ⚠️ Monitorar evolução dos indicadores

**Exemplo de Mensagem:**
> "VALE3.SA mostra boas oportunidades de entrada. Indicadores apontam para valorização."

---

### 🟡 NEUTRO
**Critérios:**
- Score 35-49
- Sinais técnicos mistos
- Sem tendência definida
- Mercado lateral

**Ação Sugerida:**
- 🔒 Manter posições atuais
- ⏸️ Não fazer novos aportes
- 👁️ Acompanhar evolução dos indicadores

**Exemplo de Mensagem:**
> "ITUB4.SA está em momento de indefinição. **MANTENHA** suas posições atuais e aguarde sinais mais claros."

---

### ⚠️ EVITAR
**Critérios:**
- Score 20-34
- Probabilidade ML < 40%
- Indicadores desfavoráveis
- Tendência de baixa

**Ação Sugerida:**
- 🚫 NÃO fazer novos aportes
- 🔒 Manter stop loss ativo
- 👁️ Aguardar reversão de tendência

**Exemplo de Mensagem:**
> "MGLU3.SA não apresenta condições favoráveis para entrada. **NÃO** faça novos aportes até reversão dos sinais."

---

### 🔴 VENDA
**Critérios:**
- Score < 20
- Probabilidade ML muito baixa
- Death Cross ou EMA50 << EMA200
- MACD negativo
- Volume em queda

**Ação Sugerida:**
- ❌ Reduzir exposição
- ❌ Zerar posição se possível
- 💰 Proteger capital

**Exemplo de Mensagem:**
> "AMER3.SA apresenta sinais de risco elevado. Se você possui este ativo, considere **reduzir** ou **zerar** a posição."

---

## 🎓 Exemplo Prático de Uso

### Cenário: Investidor quer analisar PETR4.SA

#### 1️⃣ Acessa "Gerenciar Posições"
#### 2️⃣ Vai até "🔍 Buscar Recomendação IA"
#### 3️⃣ Digite `PETR4.SA` e clica em "🔎 Analisar com IA"

#### 4️⃣ Recebe o resultado:

```
🟢 PETR4.SA
COMPRA FORTE 🚀🟢
Score: 78/100

💰 Preço Atual: R$ 38.45
📊 RSI: 42.3
📈 EMA 50: R$ 36.80
📉 EMA 200: R$ 32.15
🤖 Probabilidade Alta (ML): 68.5%
🎯 Acurácia: 85.2%

🎯 Ação Recomendada:
Comprar ou aumentar posição. Múltiplos indicadores favoráveis.

🌍 Regime de Mercado:
🟢 Alta - Ibovespa +2.3%, Dólar estável

📊 Sinais e Indicadores:
🟢 Golden Cross detectado (EMA50 cruzou EMA200 para cima)
🟢 RSI em zona de compra (não sobrecomprado)
🟢 MACD indica momentum de alta
🟢 Volume 1.8x acima da média (forte interesse)
🟡 Volatilidade em 15% (moderada)

💡 Análise Final e Sugestão:
✅ RECOMENDAÇÃO: COMPRA FORTE

PETR4.SA apresenta sinais técnicos e fundamentais muito positivos.
É um excelente momento para iniciar posição ou aumentar exposição.

- Score: 78/100 (Muito Favorável)
- Probabilidade ML de Alta: 68.5%
- Tendência: Alta

[➕ Adicionar PETR4.SA à Minha Carteira]
```

#### 5️⃣ Investidor clica no botão e o ativo é adicionado instantaneamente!

---

## 🔄 Atualização dos Dados

### Frequência de Atualização:
- **Preços**: Tempo real (via yfinance/Binance)
- **Indicadores Técnicos**: Calculados on-the-fly
- **Modelo ML**: Treinado a cada análise com últimos 6 meses
- **Regime de Mercado**: Atualizado em tempo real
- **Notícias**: A cada 15 minutos (via scheduler)

### Cache:
- Traduções de notícias: 1 hora
- Cotações explorar: 10 minutos
- Análises IA: Sem cache (sempre atualizada)

---

## ⚙️ Configurações Técnicas

### Modelos de Machine Learning:
```python
Random Forest Classifier
- n_estimators: 100
- max_depth: 10
- min_samples_split: 5
- Features: rsi, ema50, ema200, macd, volume_ratio, volatility
- Target: price_up (preço sobe em 1 dia)
```

### Indicadores Técnicos:
```python
RSI: ta.momentum.RSIIndicator(close, window=14)
EMA50: close.ewm(span=50).mean()
EMA200: close.ewm(span=200).mean()
MACD: ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
Volume Ratio: volume / volume.rolling(20).mean()
Volatility: returns.rolling(20).std()
```

---

## 🎯 Melhores Práticas

### ✅ Fazer:
- Use a análise IA como **ferramenta de apoio** à decisão
- Combine com análise fundamentalista
- Considere seu perfil de risco e objetivos
- Analise múltiplos ativos antes de decidir
- Respeite stops loss e estratégia de saída

### ❌ Evitar:
- Confiar apenas na IA sem análise própria
- Ignorar contexto macroeconômico
- Investir mais do que pode perder
- Fazer operações emocionais
- Desconsiderar custos de transação

---

## 📞 Suporte

Dúvidas ou problemas com as funcionalidades de IA?
- Verifique se está usando a versão mais recente
- Consulte o [QUICKSTART.md](QUICKSTART.md) para configuração inicial
- Revise o [CHANGELOG.md](CHANGELOG.md) para últimas atualizações

---

## 🚀 Próximas Melhorias

### Em desenvolvimento:
- [ ] Notificações push quando score de um ativo muda drasticamente
- [ ] Sistema de backtesting para validar recomendações históricas
- [ ] Recomendações de rebalanceamento de carteira
- [ ] Análise de correlação entre ativos
- [ ] Alertas personalizáveis por usuário
- [ ] Relatórios PDF exportáveis com análises

---

**Última Atualização:** {{DATE}}
**Versão:** 2.0 - IA 100% Funcional 🚀
