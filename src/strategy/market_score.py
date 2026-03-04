import pandas as pd

def generate_score_series(df):

    scores = []

    for i in range(len(df)):
        if i < 200:
            scores.append(50)
            continue

        sub_df = df.iloc[:i+1]
        latest = sub_df.iloc[-1]

        score = 0

        # Tendência
        if latest["ma50"] > latest["ma200"]:
            score += 40
        else:
            score += 10

        # Momento (20 dias)
        momentum = sub_df["close"].pct_change(20).iloc[-1]
        if momentum > 0:
            score += 30
        else:
            score += 10

        # Volatilidade
        avg_vol = sub_df["volatility"].mean()
        if latest["volatility"] < avg_vol:
            score += 30
        elif latest["volatility"] <= avg_vol * 1.2:
            score += 20
        else:
            score += 10

        scores.append(score)

    return pd.Series(scores, index=df.index)