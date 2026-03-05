import os
import sys

# adiciona diretório raiz ao path para imports absolutos funcionarem
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

import streamlit as st
import yfinance as yf
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import re

# Importando a conexão do seu arquivo database.py
from core.database.database import get_market_connection, get_user_connection, init_databases
# scheduler ajuda a manter o banco com dados frescos
from scripts.scheduler import start_scheduler
# AI assistant
from core.engines.ai_assistant import get_ai_recommendation
from core.data.market_data import get_stock_data
from core.indicators.technical import add_indicators
from core.models.ml_model import train_model
from core.engines.regime_engine import detect_regime


# ==========================================
# 1. CONFIGURAÇÃO VISUAL E INTERFACE CLEAN
# ==========================================
st.set_page_config(page_title="Quant IA Brasil", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #a3a8b8; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Courier New', monospace; font-weight: 300; }
    div[data-testid="metric-container"] {
        background-color: #161b22; border: 1px solid #30363d;
        padding: 15px; border-radius: 4px;
    }
    div[data-testid="metric-container"] > div > div > div { color: #00ffa3 !important; }
    .titulo-secao {
        color: #8b949e; font-size: 12px; font-weight: bold; letter-spacing: 2px;
        margin-bottom: 15px; margin-top: 25px; text-transform: uppercase;
        border-bottom: 1px solid #30363d; padding-bottom: 5px;
    }
    .alerta-ia {
        background-color: #161b22; padding: 15px; border-left: 3px solid #00ffa3;
        border-radius: 2px; margin-bottom: 10px; font-size: 13px; color: #c9d1d9;
    }
    .login-box {
        max-width: 400px; margin: 60px auto; padding: 40px;
        background-color: #161b22; border-radius: 4px; border: 1px solid #30363d;
    }
    .bola-neve-box {
        background-color: #1c2128; padding: 15px; border-radius: 6px; 
        border: 1px solid #444c56; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GESTÃO DE SESSÃO
# ==========================================
# garante que o banco exista e as tabelas estejam criadas. O próprio
# create_connection já faz `CREATE TABLE IF NOT EXISTS` quando chamado.
init_databases()

# inicia o coletor em segundo plano apenas uma vez por execução do Streamlit
if 'scheduler_started' not in st.session_state:
    start_scheduler()
    st.session_state['scheduler_started'] = True

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'usuario_atual' not in st.session_state:
    st.session_state['usuario_atual'] = None
if 'nome_usuario' not in st.session_state:
    st.session_state['nome_usuario'] = None
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'dashboard'
if 'tela_auth' not in st.session_state:
    st.session_state['tela_auth'] = 'login'
if 'novo_ticker_input' not in st.session_state:
    st.session_state['novo_ticker_input'] = ""

# ==========================================
# 3. FUNÇÕES DE BANCO DE DADOS
# ==========================================
import bcrypt

def cadastrar_usuario_db(nome, username, password):
    """Armazena usuário com senha hashed em bcrypt.

    A senha recebida é codificada e um salt aleatório adicionado antes de
    persistir no banco. Caso o nome de usuário já exista, retorna False.
    """
    try:
        conn = get_user_connection()
        cursor = conn.cursor()
        # geramos hash seguro; armazenamos como string utf-8
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('INSERT INTO usuarios (nome, username, password) VALUES (?, ?, ?)',
                       (nome, username, hashed))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verificar_login_db(usuario, senha):
    conn = get_user_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password, nome FROM usuarios WHERE username = ?", (usuario,))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        senha_hash_db, nome = resultado
        import bcrypt
        # Verifica se a senha bate com o hash (ou texto puro se for legado)
        try:
            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_db):
                return nome
        except ValueError:
            # Fallback caso tenha salvo a senha em texto puro antes de usar bcrypt
            if senha == senha_hash_db:
                return nome
    return None

def cadastrar_usuario_db(nome, usuario, senha):
    import bcrypt
    conn = get_user_connection()
    cursor = conn.cursor()
    
    # Gera o hash seguro da senha
    salt = bcrypt.gensalt()
    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), salt)
    
    try:
        cursor.execute("INSERT INTO usuarios (nome, username, password) VALUES (?, ?, ?)", 
                       (nome, usuario, senha_hash))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False # Usuário já existe
    finally:
        conn.close()
        
    return sucesso

def carregar_carteira(username):
    """
    Carrega a carteira do usuário do banco de dados relacional.

    Args:
        username (str): Nome do usuário.

    Returns:
        pd.DataFrame: DataFrame com ticker, quantidade, preco_medio.
    """
    conn = get_user_connection()
    
    # A nova query liga a tabela portfolio à tabela usuarios para encontrar as ações certas
    query = """
        SELECT p.ticker, p.quantidade, p.preco_medio 
        FROM portfolio p
        JOIN usuarios u ON p.user_id = u.id
        WHERE u.username = ?
    """
    
    df = pd.read_sql(query, conn, params=(username,))
    conn.close()
    return df

def gerir_ativo_db(username, ticker, qtd_nova, pm_novo):
    """
    Gerencia adição ou atualização de ativo na carteira usando user_id relacional.
    """
    from core.database.database import get_user_connection
    conn = get_user_connection()
    cursor = conn.cursor()
    
    # 1. Primeiro pega o ID do usuário usando o username
    cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    user_id = cursor.fetchone()[0]

    # 2. Verifica se o ativo já existe na carteira DESTE usuário
    cursor.execute('SELECT quantidade, preco_medio FROM portfolio WHERE user_id = ? AND ticker = ?', (user_id, ticker))
    resultado = cursor.fetchone()
    
    if resultado:
        qtd_atual, pm_atual = resultado
        qtd_total = qtd_atual + qtd_nova
        if qtd_total > 0:
            pm_calculado = ((qtd_atual * pm_atual) + (qtd_nova * pm_novo)) / qtd_total
            cursor.execute('UPDATE portfolio SET quantidade = ?, preco_medio = ? WHERE user_id = ? AND ticker = ?', (qtd_total, pm_calculado, user_id, ticker))
        else:
            cursor.execute('DELETE FROM portfolio WHERE user_id = ? AND ticker = ?', (user_id, ticker))
    else:
        # 3. Insere um novo ativo vinculado ao user_id (sem a coluna dividendo_por_cota antiga)
        cursor.execute('INSERT INTO portfolio (user_id, ticker, quantidade, preco_medio) VALUES (?, ?, ?, ?)', (user_id, ticker.upper(), qtd_nova, pm_novo))
        
    conn.commit()
    conn.close()

def remover_ativo_db(username, ticker):
    """
    Remove totalmente um ativo da carteira usando user_id relacional.
    """
    from core.database.database import get_user_connection
    conn = get_user_connection()
    cursor = conn.cursor()
    
    # 1. Pega o ID do usuário
    cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    user_id = cursor.fetchone()[0]
    
    # 2. Deleta usando o user_id
    cursor.execute('DELETE FROM portfolio WHERE user_id = ? AND ticker = ?', (user_id, ticker))
    conn.commit()
    conn.close()

def atualizar_ticker():
    """Callback para converter input para maiúsculas em tempo real."""
    """Callback para converter input para maiúsculas em tempo real"""
    st.session_state['novo_ticker_input'] = st.session_state['novo_ticker_input'].upper()

# ==========================================
# 4. MOTORES DE DADOS (APIs) E CÁLCULOS
# ==========================================
@st.cache_data(ttl=1800)
def buscar_dados_macro():
    tickers = {"IBOV": "^BVSP", "USD/BRL": "USDBRL=X", "BTC": "BTC-USD", "IFIX": "^IFIX", "EUR/BRL": "EURBRL=X", "ETH": "ETH-USD"}
    dados = {}
    for nome, tk in tickers.items():
        try:
            hist = yf.Ticker(tk).history(period="2d")
            if not hist.empty and len(hist) >= 2:
                hoje, ontem = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                dados[nome] = {"valor": hoje, "var": ((hoje - ontem) / ontem) * 100}
            else:
                dados[nome] = {"valor": 0, "var": 0}
        except:
            dados[nome] = {"valor": 0, "var": 0}
    return dados

def buscar_dados_ticker_completo(ticker):
    """Busca cotação atual e dividendo anual estimado via Yahoo Finance.
    
    Tenta obter trailingAnnualDividendRate; se zero, usa dividendYield × preço.
    Retorna tupla (preco, dividendo) ou (0.0, 0.0) em caso de erro.
    """
    try:
        acao = yf.Ticker(ticker)
        hist = acao.history(period="5d")
        if hist.empty:
            print(f"[AVISO] sem histórico para {ticker}")
            return 0.0, 0.0
            
        preco_atual = float(hist['Close'].iloc[-1])
        
        # prioridade: trailing annual dividend
        div_anual = acao.info.get('trailingAnnualDividendRate', 0.0)
        if div_anual == 0.0:
            # fallback: yield × preço
            dy = acao.info.get('dividendYield', 0.0)
            div_anual = preco_atual * dy if dy else 0.0
            
        return preco_atual, div_anual
    except Exception as e:
        print(f"[ERRO] falha ao buscar {ticker}: {str(e)}")
        return 0.0, 0.0

@st.cache_data(ttl=3600)
def buscar_historico_carteira(tickers):
    """Busca o histórico de preços de fechamento (últimos 6 meses) para gerar o gráfico"""
    df_historico = pd.DataFrame()
    for tk in tickers:
        try:
            hist = yf.Ticker(tk).history(period="6mo")
            if not hist.empty:
                # Remove o timezone para evitar bugs no Plotly
                hist.index = hist.index.tz_localize(None)
                df_historico[tk] = hist['Close']
        except Exception as e:
            print(f"[AVISO] sem histórico para {tk}: {str(e)}")
            continue
    return df_historico

def processar_carteira_tempo_real(carteira_df):
    if carteira_df.empty:
        return carteira_df, 0.0
    
    precos_atuais = []
    valores_totais = []
    dividendos_anuais = []
    patrimonio_total = 0.0
    
    for _, row in carteira_df.iterrows():
        preco_hoje, div_anual = buscar_dados_ticker_completo(row['ticker'])
        
        if preco_hoje == 0.0:
            preco_hoje = row['preco_medio']
            
        valor_posicao = preco_hoje * row['quantidade']
        
        precos_atuais.append(preco_hoje)
        valores_totais.append(valor_posicao)
        dividendos_anuais.append(div_anual)
        
        patrimonio_total += valor_posicao
        
    carteira_df['Preço Atual API'] = precos_atuais
    carteira_df['Valor Total'] = valores_totais
    carteira_df['Dividendo Anual (API)'] = dividendos_anuais
    return carteira_df, patrimonio_total

def buscar_dados_macro():
    """Busca os dados macroeconômicos mais recentes do banco de dados"""
    conn = get_market_connection()
    dados = {
        'IBOV': {'valor': 0.0, 'var': 0.0},
        'BTC': {'valor': 0.0, 'var': 0.0},
        'USD/BRL': {'valor': 0.0, 'var': 0.0},
        'EUR/BRL': {'valor': 0.0, 'var': 0.0},
        'ETH': {'valor': 0.0, 'var': 0.0}
    }
    
    
    try:
        # IBOV
        ibov_df = pd.read_sql("SELECT close FROM global_markets WHERE symbol = 'IBOVESPA' ORDER BY date DESC LIMIT 2", conn)
        if len(ibov_df) >= 2:
            dados['IBOV']['valor'] = ibov_df.iloc[0]['close']
            dados['IBOV']['var'] = ((ibov_df.iloc[0]['close'] - ibov_df.iloc[1]['close']) / ibov_df.iloc[1]['close']) * 100
        
        # BTC
        btc_df = pd.read_sql("SELECT close FROM crypto WHERE symbol = 'BTCUSDT' ORDER BY date DESC LIMIT 2", conn)
        if len(btc_df) >= 2:
            dados['BTC']['valor'] = btc_df.iloc[0]['close']
            dados['BTC']['var'] = ((btc_df.iloc[0]['close'] - btc_df.iloc[1]['close']) / btc_df.iloc[1]['close']) * 100
        
        # USD/BRL
        usd_df = pd.read_sql("SELECT close FROM global_markets WHERE symbol = 'USD/BRL' ORDER BY date DESC LIMIT 2", conn)
        if len(usd_df) >= 2:
            dados['USD/BRL']['valor'] = usd_df.iloc[0]['close']
            dados['USD/BRL']['var'] = ((usd_df.iloc[0]['close'] - usd_df.iloc[1]['close']) / usd_df.iloc[1]['close']) * 100
        
        # EUR/BRL
        eur_df = pd.read_sql("SELECT close FROM global_markets WHERE symbol = 'EUR/BRL' ORDER BY date DESC LIMIT 2", conn)
        if len(eur_df) >= 2:
            dados['EUR/BRL']['valor'] = eur_df.iloc[0]['close']
            dados['EUR/BRL']['var'] = ((eur_df.iloc[0]['close'] - eur_df.iloc[1]['close']) / eur_df.iloc[1]['close']) * 100
        
        # ETH
        eth_df = pd.read_sql("SELECT close FROM crypto WHERE symbol = 'ETHUSDT' ORDER BY date DESC LIMIT 2", conn)
        if len(eth_df) >= 2:
            dados['ETH']['valor'] = eth_df.iloc[0]['close']
            dados['ETH']['var'] = ((eth_df.iloc[0]['close'] - eth_df.iloc[1]['close']) / eth_df.iloc[1]['close']) * 100
    
    except Exception as e:
        print(f"[AVISO] Erro ao buscar dados macro: {e}")
    finally:
        conn.close()
    
    return dados

# ==========================================
# 5. TELAS DO SISTEMA
# ==========================================
def tela_auth():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #00ffa3 !important;'>QUANT IA ALPHA</h2>", unsafe_allow_html=True)
        
        if st.session_state['tela_auth'] == 'login':
            st.markdown("<p style='text-align: center; color: #8b949e;'>Acesso Restrito</p>", unsafe_allow_html=True)
            with st.form("form_login"):
                usuario = st.text_input("Credencial de Acesso (Usuário)")
                senha = st.text_input("Palavra-passe", type="password")
                if st.form_submit_button("Autenticar", width='stretch'):
                    nome_cliente = verificar_login_db(usuario, senha)
                    if nome_cliente:
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_atual'] = usuario
                        st.session_state['nome_usuario'] = nome_cliente
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
            if st.button("Não possui conta? Cadastre-se", width='stretch'):
                st.session_state['tela_auth'] = 'cadastro'
                st.rerun()

        elif st.session_state['tela_auth'] == 'cadastro':
            st.markdown("<p style='text-align: center; color: #8b949e;'>Novo Cadastro de Cliente</p>", unsafe_allow_html=True)
            with st.form("form_cadastro"):
                nome_novo = st.text_input("Nome Completo")
                usuario_novo = st.text_input("Nome de Usuário (Login)")
                senha_nova = st.text_input("Palavra-passe", type="password")
                if st.form_submit_button("Criar Conta", width='stretch'):
                    if nome_novo and usuario_novo and senha_nova:
                        sucesso = cadastrar_usuario_db(nome_novo, usuario_novo, senha_nova)
                        if sucesso:
                            st.success("Conta criada com sucesso! Volte ao login.")
                        else:
                            st.error("Nome de usuário já existe.")
                    else:
                        st.warning("Preencha todos os campos obrigatórios.")
            
            if st.button("Voltar ao Login", width='stretch'):
                st.session_state['tela_auth'] = 'login'
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

def renderizar_menu():
    st.sidebar.markdown("<h2 style='color:#00ffa3 !important;'>MENU DO SISTEMA</h2>", unsafe_allow_html=True)
    st.sidebar.markdown(f"Cliente: **{st.session_state['nome_usuario']}**")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Dashboard Analítico", width='stretch'):
        st.session_state['pagina_atual'] = 'dashboard'
        st.rerun()
        
    if st.sidebar.button("Gerenciar Posições", width='stretch'):
        st.session_state['pagina_atual'] = 'carteira'
        st.rerun()
        
    if st.sidebar.button("Explorar Ativos", width='stretch'):
        st.session_state['pagina_atual'] = 'explorar'
        st.rerun()
        
    st.sidebar.markdown("---")
    if st.sidebar.button("Encerrar Sessão", width='stretch'):
        st.session_state['autenticado'] = False
        st.session_state['usuario_atual'] = None
        st.session_state['nome_usuario'] = None
        st.rerun()

def tela_dashboard():
    renderizar_menu()
    st.markdown("<h1>QUANT IA BRASIL <span style='color:#30363d; font-size: 20px;'>| TERMINAL</span></h1>", unsafe_allow_html=True)
    st.markdown("---")

    dados_macro = buscar_dados_macro()
    carteira_df_bruto = carregar_carteira(st.session_state['usuario_atual'])
    
    with st.spinner("Sincronizando B3 e calculando Projeções..."):
        carteira_df, patrimonio_total = processar_carteira_tempo_real(carteira_df_bruto)

    # TOP METRICS
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("IBOV", f"{dados_macro['IBOV']['valor']:,.0f}", f"{dados_macro['IBOV']['var']:.2f}%")
    c2.metric("BTC", f"$ {dados_macro['BTC']['valor']:,.0f}", f"{dados_macro['BTC']['var']:.2f}%")
    c3.metric("ETH", f"$ {dados_macro['ETH']['valor']:,.0f}", f"{dados_macro['ETH']['var']:.2f}%")
    c4.metric("USD/BRL", f"R$ {dados_macro['USD/BRL']['valor']:.2f}", f"{dados_macro['USD/BRL']['var']:.2f}%")
    c5.metric("EUR/BRL", f"R$ {dados_macro['EUR/BRL']['valor']:.2f}", f"{dados_macro['EUR/BRL']['var']:.2f}%")

    col_esq, col_dir = st.columns([6, 4])

    # COLUNA ESQUERDA: Gráfico de Evolução dos Ativos (Linhas)
    with col_esq:
        st.markdown("<div class='titulo-secao'>Evolução dos Ativos (Últimos 6 Meses)</div>", unsafe_allow_html=True)
        if not carteira_df.empty:
            st.markdown(f"<h2 style='color: #00ffa3 !important;'>Patrimônio Total: R$ {patrimonio_total:,.2f}</h2>", unsafe_allow_html=True)
            
            # Puxa os dados históricos para o gráfico de linha
            tickers_carteira = carteira_df['ticker'].tolist()
            with st.spinner("Desenhando gráfico histórico..."):
                df_historico = buscar_historico_carteira(tickers_carteira)
            
            if not df_historico.empty:
                fig = go.Figure()
                # Adiciona uma linha para cada ativo da carteira
                for ticker in df_historico.columns:
                    fig.add_trace(go.Scatter(
                        x=df_historico.index, 
                        y=df_historico[ticker], 
                        mode='lines', 
                        name=ticker,
                        line=dict(width=2)
                    ))
                
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#a3a8b8'),
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=350,
                    xaxis=dict(showgrid=False, title="Data"),
                    yaxis=dict(showgrid=True, gridcolor='#30363d', title="Preço (R$)"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.warning("Não foi possível carregar o histórico no momento. A B3 pode estar offline.")
        else:
            st.info("Sua carteira está vazia. Cadastre ativos em 'Gerenciar Posições' para ver o gráfico de evolução.")

        # Análise Personalizada de Ativo
        with st.expander("🔍 Análise Personalizada de Ativo"):
            custom_ticker = st.text_input("Digite o ticker (ex: PETR4.SA, BTC-USD)", key="custom_ticker")
            if st.button("Analisar", key="analisar_custom"):
                if custom_ticker:
                    with st.spinner("Analisando..."):
                        try:
                            # Buscar dados
                            df = get_stock_data(custom_ticker)
                            if df.empty:
                                st.error(f"Não encontrei dados para {custom_ticker}.")
                            else:
                                df = add_indicators(df)
                                last = df.iloc[-1]
                                st.success(f"Análise de {custom_ticker.upper()}")
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Preço Atual", f"R$ {last['Close']:.2f}")
                                col2.metric("RSI", f"{last['rsi']:.1f}")
                                col3.metric("EMA50", f"{last['ema50']:.2f}")
                        except Exception as e:
                            st.error(f"Erro: {e}")
                else:
                    st.warning("Digite um ticker.")

    # COLUNA DIREITA: Efeito Bola de Neve
    with col_dir:
        st.markdown("<div class='titulo-secao'>Efeito Bola de Neve (Projeção)</div>", unsafe_allow_html=True)
        
        if not carteira_df.empty:
            renda_anual_estimada = sum(carteira_df['quantidade'] * carteira_df['Dividendo Anual (API)'])
            renda_mensal_estimada = renda_anual_estimada / 12
            
            st.markdown(f"""
                <div class='bola-neve-box'>
                    <p style='margin:0; font-size: 14px; color: #8b949e;'>Renda Passiva Estimada (Anual)</p>
                    <h3 style='margin:0; color: #00ffa3 !important;'>R$ {renda_anual_estimada:,.2f}</h3>
                    <p style='margin:0; font-size: 12px; color: #8b949e;'>Aprox. R$ {renda_mensal_estimada:,.2f} / mês</p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("<p style='font-size: 14px; margin-top: 15px; color: #a3a8b8;'><b>Análise de Cotas Mágicas:</b><br>Quantas cotas você já tem VS quantas precisa para que os dividendos comprem 1 cota sozinhos.</p>", unsafe_allow_html=True)
            
            for _, row in carteira_df.iterrows():
                tk = row['ticker']
                qtd = row['quantidade']
                preco = row['Preço Atual API']
                div = row['Dividendo Anual (API)']
                
                if div > 0:
                    cotas_magicas = preco / div
                    progresso = min((qtd / cotas_magicas) * 100, 100)
                    
                    st.markdown(f"<span style='font-size: 13px; font-weight: bold;'>{tk}</span> - <span style='font-size: 12px; color: #8b949e;'>Você tem {qtd:.0f} | Precisa de {cotas_magicas:.0f}</span>", unsafe_allow_html=True)
                    st.progress(int(progresso))
                else:
                    st.markdown(f"<span style='font-size: 13px; font-weight: bold;'>{tk}</span> - <span style='font-size: 12px; color: #8b949e;'>Ativo não paga dividendos ou dados indisponíveis.</span>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='alerta-ia' style='border-left-color: #9e9e9e;'>Adicione ativos para visualizar sua projeção de rendimentos e o efeito bola de neve.</div>", unsafe_allow_html=True)

    # SEÇÃO IA ASSISTENTE
    st.markdown("---")
    st.markdown("<div class='titulo-secao'>🤖 IA Assistente Financeiro</div>", unsafe_allow_html=True)
    
    pergunta = st.text_input("Faça uma pergunta sobre qualquer ativo (ex: 'O que acha de PETR4?' ou 'BTCUSDT')", key="pergunta_ia")
    
    if st.button("Consultar IA", type="primary"):
        if pergunta:
            with st.spinner("Analisando dados e gerando recomendação..."):
                # Extrair ticker da pergunta (simples regex para tickers brasileiros ou cripto)
                ticker_match = re.search(r'\b([A-Z0-9]{3,7}(\.SA)?|BTCUSDT|ETHUSDT)\b', pergunta.upper())
                ticker_raw = ticker_match.group(1) if ticker_match else "PETR4.SA"
                
                # Mapear tickers para yfinance
                ticker_map = {
                    'BTCUSDT': 'BTC-USD',
                    'ETHUSDT': 'ETH-USD'
                }
                ticker = ticker_map.get(ticker_raw, ticker_raw)
                
                # Adicionar .SA para ações brasileiras se não tiver
                if not ticker.endswith(('.SA', '-USD')) and ticker not in ['BTCUSDT', 'ETHUSDT']:
                    ticker += '.SA'
                
                try:
                    # Buscar dados do ticker
                    data_found = False
                    df = get_stock_data(ticker)
                    if df.empty:
                        if not ticker.endswith('.SA'):
                            ticker += '.SA'
                            df = get_stock_data(ticker)
                        if not df.empty:
                            data_found = True
                    else:
                        data_found = True
                    
                    if not data_found:
                        st.error(f"Não encontrei dados para {ticker}. Verifique o símbolo (ex: PETR4.SA para ações brasileiras).")
                    else:
                        df = add_indicators(df)
                        if df.empty:
                            st.error(f"Dados insuficientes para {ticker} (menos de 200 dias de histórico).")
                        else:
                            # Treinar modelo
                            features = ['rsi', 'ema50', 'ema200', 'macd', 'volume_ratio', 'volatility']
                            model, accuracy = train_model(df)
                            last_data = df[features].iloc[-1:]
                            prob = model.predict_proba(last_data)[0][1]
                            
                            # Regime de mercado
                            try:
                                regime = detect_regime()
                            except:
                                regime = "Indeterminado"
                            
                            # Gerar resposta
                            resposta = get_ai_recommendation(ticker, prob, accuracy, regime, df)
                            st.markdown(resposta)
                except Exception as e:
                    st.error(f"Erro na análise: {e}")
        else:
            st.warning("Digite uma pergunta para a IA.")

    # SEÇÃO NOTÍCIAS PRINCIPAIS
    st.markdown("---")
    st.markdown("<div class='titulo-secao'>📰 Principais Notícias (Impacto no Mercado)</div>", unsafe_allow_html=True)
    
    conn = get_market_connection()
    try:
        news_df = pd.read_sql("SELECT title, description, sentiment, published_at FROM news ORDER BY published_at DESC LIMIT 5", conn)
        if not news_df.empty:
            for _, row in news_df.iterrows():
                sentiment_color = "#00ffa3" if row['sentiment'] > 0.1 else "#ff6b6b" if row['sentiment'] < -0.1 else "#f39c12"
                st.markdown(f"""
                <div style='border-left: 3px solid {sentiment_color}; padding: 10px; margin-bottom: 10px; background-color: #161b22;'>
                    <strong>{row['title']}</strong><br>
                    <small style='color: #8b949e;'>{row['description'][:150]}...</small><br>
                    <small style='color: {sentiment_color};'>Sentimento: {'Positivo' if row['sentiment'] > 0.1 else 'Negativo' if row['sentiment'] < -0.1 else 'Neutro'} | {row['published_at']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma notícia recente disponível. Execute a coleta de notícias.")
    except Exception as e:
        st.error(f"Erro ao carregar notícias: {e}")
    finally:
        conn.close()

def tela_gerir_carteira():
    renderizar_menu()
    st.markdown("<h1>GERENCIAMENTO DE POSIÇÕES</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    usuario_atual = st.session_state['usuario_atual']
    carteira_df_bruto = carregar_carteira(usuario_atual)
    
    with st.spinner("Atualizando dados da B3..."):
        carteira_df, _ = processar_carteira_tempo_real(carteira_df_bruto)

    # 1. VISÃO GERAL DA CARTEIRA
    st.markdown("<div class='titulo-secao'>Tabela de Posições (Atualizado via B3)</div>", unsafe_allow_html=True)
    if not carteira_df.empty:
        # média dos dividendos por cota na carteira
        avg_div = carteira_df['Dividendo Anual (API)'].replace(0, pd.NA).mean()
        if not pd.isna(avg_div):
            st.metric("Média de Dividendo Anual por Cota", f"R$ {avg_div:.2f}")
        # incluímos também o dividendo anual por cota para saber quanto cada ação paga em média
        visao_df = carteira_df[['ticker', 'quantidade', 'preco_medio', 'Preço Atual API', 'Dividendo Anual (API)', 'Valor Total']].copy()
        visao_df.columns = ['Ativo', 'Volume', 'Preço Médio Pago', 'Preço Hoje (B3)', 'Div. Anual por Cota (R$)', 'Valor Total (R$)']
        st.dataframe(visao_df.style.format({
            'Volume': '{:.2f}', 
            'Preço Médio Pago': 'R$ {:.2f}',
            'Preço Hoje (B3)': 'R$ {:.2f}',
            'Div. Anual por Cota (R$)': 'R$ {:.2f}',
            'Valor Total (R$)': 'R$ {:.2f}'
        }), width='stretch', hide_index=True)
    else:
        st.info("Você ainda não possui ativos registrados.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. LANÇAMENTO DE COMPRAS E VENDAS
    col_add, col_remove = st.columns(2)
    
    with col_add:
        st.markdown("<div class='titulo-secao'>Lançamento de Operação (Compra/Adição)</div>", unsafe_allow_html=True)
        
        novo_ticker = st.text_input(
            "Símbolo do Ativo (Pressione ENTER para buscar)",
            key="novo_ticker_input",
            on_change=atualizar_ticker
        )
        sugestao_preco = 0.0
        
        if novo_ticker:
            with st.spinner("Consultando API B3..."):
                sugestao_preco, _ = buscar_dados_ticker_completo(novo_ticker)
            if sugestao_preco > 0:
                st.success(f"Ativo validado. Cotação Atual: R$ {sugestao_preco:.2f}")
            else:
                st.error("Ativo não identificado na base de dados.")
                
        novo_qtd = st.number_input("Volume da Operação", min_value=0.0, step=1.0)
        novo_pm = st.number_input("Preço de Execução (R$)", min_value=0.0, value=float(sugestao_preco), step=0.01)
        
        if st.button("Registrar Operação", type="primary", width='stretch'):
            if novo_ticker and novo_pm > 0 and novo_qtd > 0:
                gerir_ativo_db(usuario_atual, novo_ticker, novo_qtd, novo_pm)
                st.success("Operação contabilizada com sucesso.")
                st.rerun()
            else:
                st.error("Dados inconsistentes para registro. Verifique a cotação e o volume.")

    with col_remove:
        st.markdown("<div class='titulo-secao'>Liquidação de Posição</div>", unsafe_allow_html=True)
        if not carteira_df.empty:
            with st.form("form_remove_ativo"):
                ativo_para_remover = st.selectbox("Selecione o ativo para liquidação total:", carteira_df['ticker'].tolist())
                if st.form_submit_button("Liquidar Posição"):
                    remover_ativo_db(usuario_atual, ativo_para_remover)
                    st.success("Posição zerada com sucesso.")
                    st.rerun()
        else:
            st.info("Nenhuma posição aberta no momento.")

def tela_explorar_ativos():
    renderizar_menu()
    st.markdown("<h1>EXPLORAR ATIVOS</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("Aqui você encontra uma lista de ativos populares disponíveis para investimento. Use os tickers para adicionar à carteira ou perguntar à IA.")
    
    # Lista de ativos populares (expandida)
    ativos = [
        {"Nome": "Petrobras", "Ticker": "PETR4.SA", "Setor": "Petróleo", "Tipo": "Ação"},
        {"Nome": "Vale", "Ticker": "VALE3.SA", "Setor": "Mineração", "Tipo": "Ação"},
        {"Nome": "Itaú Unibanco", "Ticker": "ITUB4.SA", "Setor": "Bancos", "Tipo": "Ação"},
        {"Nome": "Ambev", "Ticker": "ABEV3.SA", "Setor": "Bebidas", "Tipo": "Ação"},
        {"Nome": "Banco do Brasil", "Ticker": "BBAS3.SA", "Setor": "Bancos", "Tipo": "Ação"},
        {"Nome": "Bradesco", "Ticker": "BBDC4.SA", "Setor": "Bancos", "Tipo": "Ação"},
        {"Nome": "Magazine Luiza", "Ticker": "MGLU3.SA", "Setor": "Varejo", "Tipo": "Ação"},
        {"Nome": "Weg", "Ticker": "WEGE3.SA", "Setor": "Indústria", "Tipo": "Ação"},
        {"Nome": "Itaúsa", "Ticker": "ITSA4.SA", "Setor": "Holding", "Tipo": "Ação"},
        {"Nome": "JBS", "Ticker": "JBSS3.SA", "Setor": "Alimentos", "Tipo": "Ação"},
        {"Nome": "Nubank (CDB)", "Ticker": "NUBR33.SA", "Setor": "Fintech", "Tipo": "BDR"},
        {"Nome": "Bitcoin", "Ticker": "BTC-USD", "Setor": "Cripto", "Tipo": "Criptomoeda"},
        {"Nome": "Ethereum", "Ticker": "ETH-USD", "Setor": "Cripto", "Tipo": "Criptomoeda"},
        {"Nome": "Binance Coin", "Ticker": "BNB-USD", "Setor": "Cripto", "Tipo": "Criptomoeda"},
        {"Nome": "Solana", "Ticker": "SOL-USD", "Setor": "Cripto", "Tipo": "Criptomoeda"},
        {"Nome": "Cardano", "Ticker": "ADA-USD", "Setor": "Cripto", "Tipo": "Criptomoeda"},
        {"Nome": "Polkadot", "Ticker": "DOT-USD", "Setor": "Cripto", "Tipo": "Criptomoeda"},
        {"Nome": "Chainlink", "Ticker": "LINK-USD", "Setor": "Cripto", "Tipo": "Criptomoeda"},
        {"Nome": "Litecoin", "Ticker": "LTC-USD", "Setor": "Cripto", "Tipo": "Criptomoeda"},
        {"Nome": "XRP", "Ticker": "XRP-USD", "Setor": "Cripto", "Tipo": "Criptomoeda"},
        {"Nome": "Apple", "Ticker": "AAPL", "Setor": "Tecnologia", "Tipo": "Ação EUA"},
        {"Nome": "Microsoft", "Ticker": "MSFT", "Setor": "Tecnologia", "Tipo": "Ação EUA"},
        {"Nome": "Amazon", "Ticker": "AMZN", "Setor": "Tecnologia", "Tipo": "Ação EUA"},
        {"Nome": "Google", "Ticker": "GOOGL", "Setor": "Tecnologia", "Tipo": "Ação EUA"},
        {"Nome": "Dólar Americano", "Ticker": "USDBRL=X", "Setor": "Câmbio", "Tipo": "Moeda"},
        {"Nome": "Euro", "Ticker": "EURBRL=X", "Setor": "Câmbio", "Tipo": "Moeda"},
        {"Nome": "Libra Esterlina", "Ticker": "GBPBRL=X", "Setor": "Câmbio", "Tipo": "Moeda"},
        {"Nome": "Iene Japonês", "Ticker": "JPYBRL=X", "Setor": "Câmbio", "Tipo": "Moeda"},
        {"Nome": "Ouro", "Ticker": "GC=F", "Setor": "Commodities", "Tipo": "Futuro"},
        {"Nome": "Petróleo", "Ticker": "CL=F", "Setor": "Commodities", "Tipo": "Futuro"},
        {"Nome": "S&P 500", "Ticker": "^GSPC", "Setor": "Índices", "Tipo": "Índice EUA"},
        {"Nome": "NASDAQ", "Ticker": "^IXIC", "Setor": "Índices", "Tipo": "Índice EUA"},
        {"Nome": "Dow Jones", "Ticker": "^DJI", "Setor": "Índices", "Tipo": "Índice EUA"},
        {"Nome": "FTSE 100", "Ticker": "^FTSE", "Setor": "Índices", "Tipo": "Índice UK"},
        {"Nome": "Nikkei 225", "Ticker": "^N225", "Setor": "Índices", "Tipo": "Índice Japão"},
        {"Nome": "Hang Seng", "Ticker": "^HSI", "Setor": "Índices", "Tipo": "Índice Hong Kong"},
    ]
    
    df_ativos = pd.DataFrame(ativos)
    st.dataframe(df_ativos, width='stretch', hide_index=True)
    
    st.markdown("**Dicas:**")
    st.markdown("- Para ações brasileiras, adicione '.SA' ao ticker (ex: PETR4.SA).")
    st.markdown("- Para criptos, use BTC-USD ou ETH-USD.")
    st.markdown("- Clique em um ticker para copiá-lo e usar na carteira ou IA.")

# ==========================================
# 6. CONTROLADOR DE ROTAS
# ==========================================
if not st.session_state['autenticado']:
    tela_auth()
else:
    if st.session_state['pagina_atual'] == 'dashboard':
        tela_dashboard()
    elif st.session_state['pagina_atual'] == 'carteira':
        tela_gerir_carteira()
    elif st.session_state['pagina_atual'] == 'explorar':
        tela_explorar_ativos()