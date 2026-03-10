import sys
import os
# Adiciona diretório raiz ao path
root = os.path.abspath(os.path.dirname(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

import pandas as pd
import yfinance as yf
import math
from core.database.database import get_user_connection

def gerar_conselho_estrategico():
    print("🧠 IA processando sua carteira e cruzando com o mercado de hoje...\n")
    
    try:
        conn = get_user_connection()
        carteira_df = pd.read_sql("SELECT * FROM portfolio", conn)
        conn.close()
    except Exception as e:
        print("Erro ao ler o banco de dados. Rode o setup_carteira.py primeiro.")
        return

    if carteira_df.empty:
        print("🤖 Sua carteira está vazia. Comece adicionando ativos no banco de dados para eu poder ajudar.")
        return

    insights_positivos = []
    alertas_risco = []
    foco_aporte = []

    for i, row in carteira_df.iterrows():
        ticker = row['ticker']
        qtd_atual = row['quantidade']
        pm = row['preco_medio']
        div_por_cota = row['dividendo_por_cota']

        # 1. A IA "olha" para o gráfico recente do ativo
        try:
            hist = yf.Ticker(ticker).history(period="1mo")
            preco_atual = hist['Close'].iloc[-1]
            preco_inicio_mes = hist['Close'].iloc[0]
            maxima_mes = hist['High'].max()
            
            # Cálculo de tendência simples (Price Action)
            tendencia = "ALTA" if preco_atual > preco_inicio_mes else "BAIXA"
            # evita divisão por zero
            distancia_topo = ((maxima_mes - preco_atual) / maxima_mes * 100) if maxima_mes > 0 else 0
        except (KeyError, IndexError) as e:
            print(f"[AVISO] sem dados reais para {ticker}, usando fallback")
            continue
        except Exception as e:
            print(f"[ERRO] falha ao buscar histórico de {ticker}: {str(e)}")
            continue

        # 2. A IA avalia a sua rentabilidade
        rentabilidade = ((preco_atual - pm) / pm) * 100

        # 3. A IA calcula a sua Bola de Neve (com validação contra divisão por zero)
        if div_por_cota > 0:
            magico = math.ceil(preco_atual / div_por_cota)
            faltam = magico - qtd_atual
            # evita divisão por zero
            progresso = (qtd_atual / max(magico, 1)) * 100 if magico > 0 else 0
        else:
            magico = 0
            faltam = 0
            progresso = 0

        # ==========================================
        # 🧠 O CÉREBRO DA IA: REGRAS DE ESTRATÉGIA
        # ==========================================

        # Regra 1: Ativo já se paga sozinho
        if faltam <= 0 and div_por_cota > 0:
            insights_positivos.append(f"✅ **{ticker}**: Efeito Bola de Neve ATINGIDO. O ativo gera fluxo de caixa livre. Deixe os juros compostos trabalharem e use os dividendos para diversificar em outros ativos.")

        # Regra 2: Foco de Aporte (Falta pouco + Tendência boa)
        elif progresso >= 70 and tendencia == "ALTA":
            foco_aporte.append(f"🔥 **{ticker}**: FOCO MÁXIMO. Faltam apenas {faltam} cotas para a bola de neve. Como o ativo está em tendência de ALTA, compre o quanto antes para travar o preço e atingir a meta.")

        # Regra 3: Oportunidade de baixar o Preço Médio
        elif tendencia == "BAIXA" and rentabilidade < -5:
            foco_aporte.append(f"💡 **{ticker}**: OPORTUNIDADE. O ativo caiu no último mês e você está negativo em {rentabilidade:.1f}%. É um excelente momento para comprar mais barato, abaixar seu preço médio e acelerar a bola de neve.")

        # Regra 4: Alerta de Realização de Lucro / Cautela
        elif tendencia == "ALTA" and rentabilidade > 20 and distancia_topo < 2:
            alertas_risco.append(f"⚠️ **{ticker}**: ATENÇÃO. Você tem {rentabilidade:.1f}% de lucro e o ativo está no topo do mês. Evite comprar agora (está caro). Guarde o caixa para quando houver uma correção.")

    # ==========================================
    # 📝 GERAÇÃO DO RELATÓRIO FINAL
    # ==========================================
    print("="*60)
    print("🤖 RELATÓRIO DO GESTOR QUANT IA")
    print("="*60 + "\n")

    if foco_aporte:
        print("🎯 ONDE FOCAR SEU DINHEIRO ESTE MÊS:")
        for dica in foco_aporte:
            print(f"  {dica}")
        print("")

    if alertas_risco:
        print("🛑 AVISOS DE RISCO E CAUTELA:")
        for alerta in alertas_risco:
            print(f"  {alerta}")
        print("")

    if insights_positivos:
        print("🏆 SUAS CONQUISTAS:")
        for insight in insights_positivos:
            print(f"  {insight}")
        print("")
        
    if not foco_aporte and not alertas_risco:
        print("🟡 STATUS NEUTRO: Sua carteira está balanceada. Apenas mantenha a constância e aguarde movimentos mais claros do mercado.")

if __name__ == "__main__":
    gerar_conselho_estrategico()