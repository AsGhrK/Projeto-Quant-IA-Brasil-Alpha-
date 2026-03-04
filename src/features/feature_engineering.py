def add_features(df):

    df = df.copy()

    # Médias móveis
    df["ma50"] = df["close"].rolling(window=50).mean()
    df["ma200"] = df["close"].rolling(window=200).mean()

    # Remove apenas linhas onde ma200 ainda não existe
    df = df[df["ma200"].notna()]

    return df