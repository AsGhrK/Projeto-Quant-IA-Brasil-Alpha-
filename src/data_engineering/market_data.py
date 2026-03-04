import yfinance as yf
import pandas as pd

def get_data(ticker, start="2010-01-01"):

    df = yf.download(ticker, start=start)

    df = df.rename(columns={
        "Close": "close"
    })

    df["returns"] = df["close"].pct_change()

    df.dropna(inplace=True)

    return df