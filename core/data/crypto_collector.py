from binance.client import Client
from core.database.database import get_market_connection
from datetime import datetime

client = Client()

CRYPTO_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "XRPUSDT", "DOGEUSDT"]

def collect_crypto_data():
    """
    Coleta dados de criptomoedas via Binance API e salva no banco de mercado.
    """
    conn = get_market_connection()
    cursor = conn.cursor()

    for symbol in CRYPTO_SYMBOLS:
        klines = client.get_klines(
            symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=120
        )

        for k in klines:
            open_time = datetime.fromtimestamp(k[0] / 1000)
            close_price = float(k[4])
            volume = float(k[5])

            cursor.execute("""
                INSERT OR IGNORE INTO crypto (symbol, date, close, volume)
                VALUES (?, ?, ?, ?)
            """, (symbol, str(open_time), close_price, volume))

        print(f"Cripto coletado: {symbol}")

    conn.commit()
    conn.close()