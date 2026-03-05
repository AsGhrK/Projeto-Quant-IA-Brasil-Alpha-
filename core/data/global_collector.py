import yfinance as yf
from core.database.database import get_market_connection
import pandas as pd

def collect_global_data():
    markets = {
        "^BVSP": "IBOVESPA",
        "^GSPC": "SP500",
        "^IXIC": "NASDAQ",
        "^DJI": "DOWJONES",
        "^VIX": "VIX",
        "BRL=X": "USD/BRL",
        "EURBRL=X": "EUR/BRL",
        "JPYBRL=X": "JPY/BRL",
        "GBPBRL=X": "GBP/BRL",
        "DX-Y.NYB": "DOLAR",
        "GC=F": "OURO",
        "CL=F": "PETROLEO",
        "^FTSE": "FTSE100",
        "^N225": "NIKKEI",
        "^HSI": "HANGSENG"
    }

    conn = get_market_connection()
    cursor = conn.cursor()

    for ticker, name in markets.items():
        try:
            print(f"Coletando {name}...")
            data = yf.download(
                ticker, period="6mo", interval="1d",
                auto_adjust=True, progress=False, threads=False
            )

            if data.empty:
                continue

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            data = data.reset_index()

            for _, row in data.iterrows():
                close_value = row.get("Close")
                volume_value = row.get("Volume", 0)

                if pd.isna(close_value):
                    continue

                cursor.execute("""
                    INSERT OR IGNORE INTO global_markets 
                    (symbol, date, close, volume)
                    VALUES (?, ?, ?, ?)
                """, (
                    name, str(row["Date"]), float(close_value),
                    float(volume_value) if not pd.isna(volume_value) else 0
                ))
            print(f"Dados coletados para {name}")
        except Exception as e:
            print(f"Erro ao coletar {name}: {e}")
            continue

    conn.commit()
    conn.close()
    print("Coleta global concluída.")