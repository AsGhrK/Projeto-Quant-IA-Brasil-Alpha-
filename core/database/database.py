import sqlite3
import os

# ==========================================
# CAMINHOS DOS BANCOS (Isolamento de Dados)
# ==========================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
MARKET_DB_PATH = os.path.join(BASE_DIR, 'market_data.db')
USER_DB_PATH = os.path.join(BASE_DIR, 'user_data.db')

def get_market_connection():
    """Conexão APENAS para dados de mercado (Ações, Cripto, Notícias)."""
    return sqlite3.connect(MARKET_DB_PATH)

def get_user_connection():
    """Conexão APENAS para dados sensíveis (Usuários, Senhas, Carteiras)."""
    return sqlite3.connect(USER_DB_PATH)

def init_databases():
    """Inicializa os dois bancos de dados com suas respectivas tabelas."""
    
    # ---------------------------------------------------------
    # 1. BANCO DE MERCADO (Pode ser apagado e recriado sem dor)
    # ---------------------------------------------------------
    conn_market = get_market_connection()
    c_market = conn_market.cursor()

    c_market.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        ticker TEXT,
        date TEXT,
        close REAL,
        volume REAL,
        PRIMARY KEY (ticker, date)
    )
    """)

    c_market.execute("""
    CREATE TABLE IF NOT EXISTS global_markets (
        symbol TEXT,
        date TEXT,
        close REAL,
        volume REAL,
        PRIMARY KEY (symbol, date)
    )
    """)

    c_market.execute("""
    CREATE TABLE IF NOT EXISTS crypto (
        symbol TEXT,
        date TEXT,
        close REAL,
        volume REAL,
        PRIMARY KEY (symbol, date)
    )
    """)

    c_market.execute("""
    CREATE TABLE IF NOT EXISTS news (
        title TEXT,
        published_at TEXT,
        source TEXT,
        description TEXT,
        sentiment REAL,
        PRIMARY KEY (title, published_at)
    )
    """)
    conn_market.commit()
    conn_market.close()

    # ---------------------------------------------------------
    # 2. BANCO DE USUÁRIOS (Dados Sensíveis e Protegidos)
    # ---------------------------------------------------------
    conn_user = get_user_connection()
    c_user = conn_user.cursor()

    c_user.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    c_user.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        quantidade REAL NOT NULL,
        preco_medio REAL NOT NULL,
        FOREIGN KEY(user_id) REFERENCES usuarios(id)
    )
    """)
    
    conn_user.commit()
    conn_user.close()

if __name__ == "__main__":
    init_databases()
    print("✅ SEGURANÇA APLICADA: Bancos 'market_data.db' e 'user_data.db' criados e isolados com sucesso!")