import numpy as np

def run_backtest(df):

    df = df.copy()

    # 🔒 Proteção contra dataframe vazio
    if df.empty:
        raise ValueError("DataFrame vazio após feature engineering.")

    df["signal"] = (df["ma50"] > df["ma200"]).astype(int)

    df["strategy_returns"] = df["signal"].shift(1) * df["returns"]

    df["cumulative_market"] = (1 + df["returns"]).cumprod()
    df["cumulative_strategy"] = (1 + df["strategy_returns"]).cumprod()

    market_return = df["cumulative_market"].iloc[-1] - 1
    strategy_return = df["cumulative_strategy"].iloc[-1] - 1

    max_drawdown = (
        df["cumulative_strategy"] /
        df["cumulative_strategy"].cummax() - 1
    ).min()

    results = {
        "market_return": float(market_return),
        "strategy_return": float(strategy_return),
        "max_drawdown": float(max_drawdown)
    }

    return results, df