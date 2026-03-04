from src.data_engineering.market_data import get_ibov_data
from src.features.feature_engineering import add_features
from src.strategy.market_score import generate_score_series
from src.strategy.backtest_engine import run_backtest

# 1. Baixar dados
df = get_ibov_data(period="15y")

# 2. Adicionar indicadores
df = add_features(df)

# 3. Gerar score histórico
score_series = generate_score_series(df)

# 4. Rodar backtest multifator
bt_df, bt_results = run_backtest(df, score_series)

print("Backtest Multifator:")
print(bt_results)