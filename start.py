"""Script de inicialização do Quant IA Brasil.

Este script:
1. Verifica se os bancos de dados existem.
2. Inicializa os bancos se necessário.
3. Coleta dados iniciais do mercado.
4. Inicia o aplicativo Streamlit.
"""
import os
import sys

# Adiciona diretório raiz ao path
root = os.path.abspath(os.path.dirname(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

from core.database.database import init_databases
import subprocess

def verificar_bancos():
    """Verifica se os bancos de dados existem"""
    market_db = os.path.join(root, 'market_data.db')
    user_db = os.path.join(root, 'user_data.db')
    
    if not os.path.exists(market_db) or not os.path.exists(user_db):
        print("Bancos de dados não encontrados. Inicializando...")
        init_databases()
        print("Bancos de dados criados com sucesso.")
        
        # Pergunta se quer criar carteira de teste
        resposta = input("\nDeseja criar uma carteira de teste? (s/n): ")
        if resposta.lower() == 's':
            try:
                from scripts.setup_carteira import criar_carteira_simulada
                criar_carteira_simulada()
            except Exception as e:
                print(f"Aviso: erro ao criar carteira de teste: {e}")
    else:
        print("Bancos de dados já existem.")

def coletar_dados_iniciais():
    """Coleta dados iniciais do mercado"""
    print("\nColetando dados iniciais do mercado...")
    print("(Isso pode levar alguns minutos na primeira vez)")
    
    try:
        from scripts.collect_all import run_collection
        run_collection()
        print("Dados coletados com sucesso.")
    except Exception as e:
        print(f"Aviso: erro na coleta: {e}")
        print("Você pode executar a coleta manualmente depois com: python scripts/collect_all.py")

def iniciar_app():
    """Inicia o aplicativo Streamlit"""
    print("\nIniciando Quant IA Brasil...")
    print("=" * 60)
    print("O aplicativo abrirá no navegador")
    print("Credenciais de teste:")
    print("   Username: demo")
    print("   Senha: demo123")
    print("=" * 60)
    print("\nPara parar o servidor, pressione Ctrl+C")
    print()
    
    # Inicia o Streamlit
    streamlit_path = os.path.join(root, 'apps', 'app_quant_ia.py')
    subprocess.run([sys.executable, '-m', 'streamlit', 'run', streamlit_path])

if __name__ == "__main__":
    print("=" * 60)
    print("QUANT IA BRASIL - Sistema de Análise Quantitativa")
    print("=" * 60)
    
    # Passo 1: Verificar/Inicializar bancos
    verificar_bancos()
    
    # Passo 2: Coletar dados iniciais
    resposta = input("\nDeseja coletar dados do mercado agora? (s/n): ")
    if resposta.lower() == 's':
        coletar_dados_iniciais()
    else:
        print("Pulando coleta inicial. O app funcionará com dados em cache.")
    
    # Passo 3: Iniciar aplicativo
    input("\nTudo pronto. Pressione ENTER para iniciar o aplicativo...")
    iniciar_app()


