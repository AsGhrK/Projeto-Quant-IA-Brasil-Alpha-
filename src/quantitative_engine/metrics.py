import pandas as pd
import numpy as np

def calculate_returns(df):
    df['returns'] = df['close'].pct_change()
    return df

def calculate_volatility(df, window=21):
    df['volatility'] = df['returns'].rolling(window).std() * np.sqrt(252)
    return df

def calculate_moving_averages(df):
    df['ma50'] = df['close'].rolling(50).mean()
    df['ma200'] = df['close'].rolling(200).mean()
    return df