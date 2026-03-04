import matplotlib.pyplot as plt
from src.data_engineering.market_data import get_data
from src.features.feature_engineering import add_features
from src.strategy.backtest_engine import run_backtest

def main():

    print("Baixando dados...")
    df = get_data("BOVA11.SA")

    print("Criando features...")
    df = add_features(df)

    print("Rodando backtest...")
    results, df = run_backtest(df)

    print("\n===== RESULTADOS =====")
    print(f"Retorno Mercado: {results['market_return']:.2f}")
    print(f"Retorno Estratégia: {results['strategy_return']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}")

    # Plot
    plt.figure()
    plt.plot(df["cumulative_market"])
    plt.plot(df["cumulative_strategy"])
    plt.title("Estratégia vs Mercado")
    plt.show()


if __name__ == "__main__":
    main()