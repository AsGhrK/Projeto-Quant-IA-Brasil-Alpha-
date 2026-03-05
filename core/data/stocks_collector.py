import yfinance as yf
import pandas as pd
from core.database.database import get_market_connection

def collect_stock_data(ticker):
    """
    Coleta dados intraday de ações via yfinance e salva no banco de mercado.
    """
    data = yf.download(ticker, period="5d", interval="1h")

    if data.empty:
        print(f"Sem dados para {ticker}")
        return

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data[['Close', 'Volume']].dropna()

    conn = get_market_connection()
    cursor = conn.cursor()

    for index, row in data.iterrows():
        close = float(row['Close'])
        volume = float(row['Volume'])
        
        cursor.execute("""
            INSERT OR IGNORE INTO stocks (ticker, date, close, volume)
            VALUES (?, ?, ?, ?)
        """, (ticker, str(index), close, volume))

    conn.commit()
    conn.close()
    print(f"Sucesso: {len(data)} registros de {ticker} atualizados.")