# 🇧🇷 Análise Automática do Mercado Brasileiro

## 🎯 O que é?

Uma funcionalidade que **analisa automaticamente até 50 ativos da B3** (ações, fundos imobiliários e índices) usando **Machine Learning** e **Indicadores Técnicos** para encontrar as **melhores oportunidades de investimento**.

## 🚀 Como usar?

### Passo a Passo:

1. **Acesse o Dashboard:**
   ```
   python start.py
   ```
   Login: `demo` / Senha: `demo123`

2. **Vá para "Dashboard Analítico"**

3. **Na seção "📈 Oportunidades no Mercado Brasileiro":**
   - Escolha quantos ativos analisar (10, 20, 30, 40 ou 50)
   - Clique em **"🔍 Analisar Mercado"**
   - Aguarde a análise (barra de progresso aparecerá)

4. **Explore os resultados em 3 abas:**
   - 🎯 **Melhores Oportunidades**: Top 10 do mercado
   - 📊 **Tabela Completa**: Todos os ativos + Download CSV
   - ⚠️ **Riscos**: Ativos para evitar

## 📊 O que a IA analisa?

### 50 Ativos Brasileiros:

#### 🏢 Blue Chips (30):
- **Petróleo/Gás**: PETR4.SA, PETR3.SA, PRIO3.SA
- **Mineração**: VALE3.SA, VALE5.SA, GGBR4.SA, CSNA3.SA, USIM5.SA, BRAP4.SA
- **Bancos**: ITUB4.SA, BBDC4.SA, BBAS3.SA, ITSA4.SA
- **Varejo**: ABEV3.SA, MGLU3.SA
- **Indústria**: WEGE3.SA, EMBR3.SA, RENT3.SA, SUZB3.SA, RAIL3.SA
- **Energia**: EQTL3.SA, CMIG4.SA, ELET3.SA, CPLE6.SA
- **Alimentos**: JBSS3.SA, BRFS3.SA, MRFG3.SA, BEEF3.SA
- **Outros**: B3SA3.SA, HAPV3.SA, CSAN3.SA, RADL3.SA, KLBN11.SA, VIVT3.SA

#### 🏠 Fundos Imobiliários (10):
MXRF11, HGLG11, KNRI11, XPML11, VISC11, BTLG11, HGRU11, BCFF11, KNCR11, RBRR11

#### 📊 Small/Mid Caps (10):
AZUL4, GOAU4, COGN3, TOTS3, QUAL3, LWSA3, CSAN3

## 🤖 Como funciona a análise?

Para cada ativo, a IA verifica:

### 1. Machine Learning (40% do Score)
- Modelo Random Forest treinado com 6 meses de histórico
- Probabilidade de alta nos próximos dias

### 2. Indicadores Técnicos (60% do Score)
- **RSI**: Zona de sobrevenda/sobrecompra
- **EMA 50/200**: Golden Cross / Death Cross
- **MACD**: Momentum de alta/baixa
- **Volume**: Confirmação de movimentos

### 3. Regime de Mercado
- Análise macro: IBOV, Dólar, BTC, ETH
- Contexto: Alta 🟢, Baixa 🔴, Lateral 🟡

## 📈 Resultado da Análise

### Score de 0 a 100:
- **70-100**: 🚀 COMPRA FORTE - Múltiplos sinais favoráveis
- **50-69**: 🟢 COMPRA - Boa oportunidade
- **35-49**: 🟡 NEUTRO - Aguardar definição
- **20-34**: ⚠️ EVITAR - Não fazer aportes
- **0-19**: 🔴 VENDA - Considerar saída

### Para cada ativo você recebe:
✅ Preço Atual  
✅ RSI (Índice de Força Relativa)  
✅ EMA50 e EMA200  
✅ Probabilidade ML de Alta  
✅ Acurácia do Modelo  
✅ Regime de Mercado  
✅ Lista de Alertas (Golden Cross, Volume alto, etc.)  
✅ Recomendação Final (Comprar/Vender/Aguardar)

## 🏆 Top 10 Melhores Oportunidades

Exemplo de resultado:

```
🥇 #1 - VALE3.SA | Score: 82 | COMPRA FORTE 🚀
   💰 Preço: R$ 62.45
   📊 RSI: 45.2 (Zona de compra)
   🤖 ML: 72.3% de chance de alta
   🎯 Acurácia: 86.1%
   
   📊 Alertas:
   🟢 Golden Cross (EMA50 > EMA200)
   🟢 Volume 2.1x acima da média
   🟢 MACD indica momentum de alta
   
   💡 Sugestão: Comprar ou aumentar posição

🥈 #2 - WEGE3.SA | Score: 78 | COMPRA FORTE 🚀
   💰 Preço: R$ 42.30
   📊 RSI: 38.7 (Sobrevenda)
   🤖 ML: 68.9% de chance de alta
   🎯 Acurácia: 84.5%
   
   📊 Alertas:
   🟢 RSI em zona de sobrevenda (oportunidade)
   🟢 EMA50 acima de EMA200
   🟡 Volume normal
   
   💡 Sugestão: Ótimo ponto de entrada

🥉 #3 - PETR4.SA | Score: 75 | COMPRA FORTE 🚀
   💰 Preço: R$ 38.45
   ...
```

## 📥 Exportar Análise

Na aba "📊 Tabela Completa", clique em:

**"📥 Baixar Análise em CSV"**

Você receberá um arquivo Excel com:
- Ticker | Recomendação | Score | Preço | RSI | Prob. Alta | Regime

Útil para:
- Análise offline
- Compartilhar com assessor
- Manter histórico de análises

## ⚡ Performance

| Ativos | Tempo    |
|--------|----------|
| 10     | ~30seg   |
| 20     | ~1min    |
| 30     | ~2min    |
| 40     | ~3min    |
| 50     | ~4min    |

**Dica:** Comece com 20 ativos (bom equilíbrio)

## 💡 Exemplo de Uso Real

### Cenário: Investidor busca oportunidades

```
Situação: Tenho R$ 10.000 para investir na B3

1. Acesso Dashboard → "Análise do Mercado Brasileiro"

2. Seleciono "30 ativos" no slider

3. Clico "🔍 Analisar Mercado"

4. Após 2 minutos, vejo:
   📊 Resumo:
   - 🚀 COMPRA FORTE: 4 ativos
   - 🟢 COMPRA: 8 ativos
   - 🟡 NEUTRO: 12 ativos
   - ⚠️ EVITAR: 4 ativos
   - 🔴 VENDA: 2 ativos

5. Abro aba "Melhores Oportunidades"
   - 🥇 VALE3.SA | Score: 82
   - 🥈 WEGE3.SA | Score: 78
   - 🥉 PETR4.SA | Score: 75

6. Clico em cada uma para ver detalhes

7. Decido:
   - R$ 4.000 em VALE3.SA (Score 82)
   - R$ 3.000 em WEGE3.SA (Score 78)
   - R$ 3.000 em PETR4.SA (Score 75)

8. Clico "➕ Adicionar à Carteira" em cada uma

9. Registro as operações em "Gerenciar Posições"

10. Baixo CSV para manter registro
```

### Resultado:
✅ Portfólio diversificado (3 setores diferentes)  
✅ Todos com Score > 75  
✅ Baseado em ML + Indicadores Técnicos  
✅ Registro completo mantido

## ⚠️ Avisos Importantes

### ✅ Use como ferramenta de apoio:
- A IA ajuda na decisão, mas não substitui análise fundamentalista
- Considere seu perfil de risco
- Não invista mais do que pode perder

### ❌ Não confie cegamente:
- Mercado é imprevisível
- Análise técnica tem limitações
- Sempre use stop loss

## 🔄 Quando Analisar?

**Recomendado:**
- 1x por dia (dados mudam no pregão)
- Antes de fazer aportes
- Quando quiser descobrir novas oportunidades

**Cache:**
- Análise fica salva para economizar tempo
- Para refazer, clique novamente em "🔍 Analisar Mercado"

## 📞 Precisa de Ajuda?

Consulte a documentação completa:
- [FUNCIONALIDADES_IA.md](FUNCIONALIDADES_IA.md) - Todas as funcionalidades
- [QUICKSTART.md](QUICKSTART.md) - Instalação e configuração
- [CHANGELOG.md](CHANGELOG.md) - Histórico de mudanças

---

**Desenvolvido com 🤖 IA + 📊 Análise Técnica para investidores brasileiros**

**Versão:** 2.1 - Análise Completa do Mercado Brasileiro
**Data:** Março 2026
