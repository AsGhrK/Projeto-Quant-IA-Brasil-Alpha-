import sys
import os
# Adiciona diretório raiz ao path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.database.database import get_user_connection, init_databases
import bcrypt

def criar_carteira_simulada():
    """
    Cria uma carteira simulada com dados de exemplo para demonstração.
    Inicializa os bancos de dados e cria um usuário de teste.
    """
    print("Inicializando bancos de dados...")
    init_databases()
    
    print("Criando usuário de teste e carteira simulada (Modo Bola de Neve)...")
    conn = get_user_connection()
    cursor = conn.cursor()

    # Criando usuário de teste se não existir
    cursor.execute("SELECT id FROM usuarios WHERE username = ?", ('demo',))
    user = cursor.fetchone()
    
    if user is None:
        # Senha padrão: demo123
        senha_hash = bcrypt.hashpw('demo123'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
            INSERT INTO usuarios (nome, username, password)
            VALUES (?, ?, ?)
        ''', ('Usuário Demo', 'demo', senha_hash))
        user_id = cursor.lastrowid
        print("✅ Usuário de teste criado: username='demo', senha='demo123'")
    else:
        user_id = user[0]
        print("ℹ️  Usuário de teste já existe")

    # Limpa carteira anterior do usuário demo
    cursor.execute('DELETE FROM portfolio WHERE user_id = ?', (user_id,))

    # Inserindo dados: Ticker, Cotas que você tem, Preço Médio Pago, Dividendo por Cota (Simulado)
    # Ex: MXRF11 custa perto de R$10 e paga uns R$0,10 por mês.
    ativos_teste = [
        (user_id, 'PETR4.SA', 30, 32.50, 1.20),   # Paga aprox 1.20 por trimestre
        (user_id, 'MXRF11.SA', 85, 10.20, 0.10),  # Paga aprox 0.10 por mês
        (user_id, 'VALE3.SA', 15, 65.00, 2.50)    # Paga aprox 2.50 por semestre
    ]

    cursor.executemany('''
        INSERT INTO portfolio (user_id, ticker, quantidade, preco_medio, dividendo_por_cota)
        VALUES (?, ?, ?, ?, ?)
    ''', ativos_teste)

    conn.commit()
    conn.close()
    print("✅ Carteira simulada criada para o usuário demo!")
    print("📊 3 ativos adicionados: PETR4.SA, MXRF11.SA, VALE3.SA")

if __name__ == "__main__":
    criar_carteira_simulada()