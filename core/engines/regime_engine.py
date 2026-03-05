import sqlite3
import pandas as pd
import numpy as np
from core.database.database import get_market_connection

def get_latest_data(symbol):
    conn = get_market_connection()

    df = pd.read_sql(f"""
        SELECT * FROM global_markets
        WHERE symbol = '{symbol}'
        ORDER BY date ASC
    """, conn)

    conn.close()
    return df

def calculate_trend(df):

    if len(df) < 20:
        return "DADOS INSUFICIENTES"

    df['ma20'] = df['close'].rolling(20).mean()
    df['ma50'] = df['close'].rolling(50).mean()

    last_ma20 = df['ma20'].iloc[-1]
    last_ma50 = df['ma50'].iloc[-1]

    if np.isnan(last_ma20) or np.isnan(last_ma50):
        return "NEUTRO"

    if last_ma20 > last_ma50:
        return "ALTA"
    elif last_ma20 < last_ma50:
        return "BAIXA"
    else:
        return "LATERAL"

def detect_regime():
    """
    Detecta o regime de mercado baseado em tendências e volatilidade.

    Returns:
        dict: Dados do regime (trend_sp500, trend_ibov, volatility, vix_level).
    """

    sp500 = get_latest_data("SP500")
    ibov = get_latest_data("IBOVESPA")
    vix = get_latest_data("VIX")

    trend_sp = calculate_trend(sp500)
    trend_ibov = calculate_trend(ibov)

    if not vix.empty and not np.isnan(vix['close'].iloc[-1]):
        latest_vix = float(vix['close'].iloc[-1])
    else:
        latest_vix = 20.0

    if latest_vix > 25:
        volatility = "ALTA"
    elif latest_vix < 18:
        volatility = "BAIXA"
    else:
        volatility = "MODERADA"

    regime = {
        "trend_sp500": trend_sp,
        "trend_ibov": trend_ibov,
        "volatility": volatility,
        "vix_level": latest_vix
    }

    return regime

if __name__ == "__main__":
    print(detect_regime())