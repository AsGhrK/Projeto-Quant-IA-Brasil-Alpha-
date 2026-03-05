import pandas as pd
import sys
import os

def get_ai_recommendation(ticker, ml_prob, accuracy, regime_status, df=None):
    """
    Gera recomendação da IA baseada em probabilidade ML, sentimento e padrões.

    Args:
        ticker (str): Símbolo do ativo.
        ml_prob (float): Probabilidade de alta do modelo.
        accuracy (float): Acurácia do modelo.
        regime_status: Dados do regime de mercado.
        df (pd.DataFrame): DataFrame com dados históricos para padrões.

    Returns:
        str: Resposta formatada da IA.
    """
    # --- REFORÇO DE CAMINHO ---
    # Garante que a raiz do projeto seja vista para importar core.engines
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    if root_path not in sys.path:
        sys.path.append(root_path)
    
    try:
        from core.engines.patterns import identify_patterns
        if df is not None and not df.empty:
            patterns = identify_patterns(df)
        else:
            patterns = ["Dados insuficientes para análise de padrões."]
    except ImportError as e:
        print(f"[AVISO] não foi possível importar patterns: {str(e)}")
        patterns = ["Análise de padrões indisponível no momento."]
    except Exception as e:
        print(f"[ERRO] ao identificar padrões: {str(e)}")
        patterns = ["Análise de padrões indisponível no momento."]
    # --------------------------

    # Busca sentimento médio das últimas notícias no banco
    from core.database.database import get_market_connection
    conn = get_market_connection()
    try:
        sentiment_df = pd.read_sql(f"SELECT sentiment FROM news ORDER BY published_at DESC LIMIT 10", conn)
        avg_sentiment = sentiment_df['sentiment'].mean() if not sentiment_df.empty else 0.0
    except Exception as e:
        print(f"[AVISO] falha ao calcular sentimento: {str(e)}")
        avg_sentiment = 0.0
    finally:
        conn.close()

    # Formatar regime
    if isinstance(regime_status, dict):
        regime_str = f"SP500: {regime_status.get('trend_sp500', 'N/A')}, IBOV: {regime_status.get('trend_ibov', 'N/A')}, Volatilidade: {regime_status.get('volatility', 'N/A')}"
    else:
        regime_str = str(regime_status)

    # Lógica de Decisão do Assistente
    if ml_prob > 0.65 and avg_sentiment > 0:
        status = "COMPRA FORTE"
        reason = "ML indica alta probabilidade e sentimento positivo."
        advice = "Considere comprar. Monitore stop-loss."
    elif ml_prob > 0.60:
        status = "COMPRA"
        reason = "Modelo identifica padrão de entrada."
        advice = "Entrada moderada recomendada."
    elif ml_prob < 0.40:
        status = "EVITAR"
        reason = "Risco elevado detectado."
        advice = "Evite exposição."
    else:
        status = "NEUTRO"
        reason = "Mercado indeciso."
        advice = "Mantenha posições. Aguarde sinais."

    # Resposta Limpa e Direta
    output = f"""
Ativo: {ticker} | Status: {status}

Razão: {reason}

Dados Técnicos:
- Probabilidade ML: {round(ml_prob*100, 2)}%
- Confiança: {round(accuracy*100, 1)}%
- Regime: {regime_str}
- Sentimento: {"Positivo" if avg_sentiment > 0.1 else "Neutro" if avg_sentiment > -0.1 else "Negativo"}

Padrões:
{chr(10).join(f"- {p}" for p in patterns)}

Recomendação: {advice}

Análise quantitativa. Não é conselho financeiro.
"""
    return output