import numpy as np

def detect_regime(df):
    latest = df.iloc[-1]

    trend = "Alta" if latest["ma50"] > latest["ma200"] else "Baixa"

    historical_vol_mean = df["volatility"].mean()
    volatility = "Alta" if latest["volatility"] > historical_vol_mean else "Baixa"

    if trend == "Alta" and volatility == "Baixa":
        regime = "Expansivo"
    elif trend == "Alta" and volatility == "Alta":
        regime = "Aquecido"
    elif trend == "Baixa" and volatility == "Baixa":
        regime = "Lateral"
    else:
        regime = "Defensivo"

    return {
        "trend": trend,
        "volatility": volatility,
        "regime": regime
    }