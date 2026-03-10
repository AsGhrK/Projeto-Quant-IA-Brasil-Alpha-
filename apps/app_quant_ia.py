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
from deep_translator import GoogleTranslator

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
            senha_hash_bytes = senha_hash_db.encode('utf-8') if isinstance(senha_hash_db, str) else senha_hash_db
            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_bytes):
                return nome
        except (ValueError, TypeError):
            # Fallback caso tenha salvo a senha em texto puro antes de usar bcrypt
            if senha == senha_hash_db:
                return nome
    return None

def cadastrar_usuario_db(nome, usuario, senha):
    conn = get_user_connection()
    cursor = conn.cursor()
    
    # Gera o hash seguro da senha
    salt = bcrypt.gensalt()
    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), salt)
    
    try:
        cursor.execute("INSERT INTO usuarios (nome, username, password) VALUES (?, ?, ?)",
                   (nome, usuario, senha_hash.decode('utf-8')))
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
    """Callback para converter input para maiúsculas em tempo real"""
    st.session_state['novo_ticker_input'] = st.session_state['novo_ticker_input'].upper()

@st.cache_data(ttl=3600)
def traduzir_texto(texto, idioma_destino='pt'):
    """
    Traduz texto para o idioma especificado usando Google Translate.
    Cache de 1 hora para evitar traduções repetidas.
    """
    if not texto or len(texto.strip()) == 0:
        return texto
    try:
        tradutor = GoogleTranslator(source='auto', target=idioma_destino)
        # Limita o texto a 5000 caracteres (limite da API)
        texto_limitado = texto[:4999] if len(texto) > 5000 else texto
        return tradutor.translate(texto_limitado)
    except Exception:
        # Se falhar, retorna o texto original
        return texto

# Lista dos principais ativos do mercado brasileiro (Top 50 B3 + FIIs + Índices)
ATIVOS_MERCADO_BRASILEIRO = [
    # Blue Chips B3
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA",
    "ABEV3.SA", "WEGE3.SA", "RENT3.SA", "B3SA3.SA", "SUZB3.SA",
    "JBSS3.SA", "RAIL3.SA", "GGBR4.SA", "CSNA3.SA", "USIM5.SA",
    "EMBR3.SA", "HAPV3.SA", "CSAN3.SA", "BRAP4.SA", "EQTL3.SA",
    "RADL3.SA", "PRIO3.SA", "KLBN11.SA", "VIVT3.SA", "CMIG4.SA",
    "ELET3.SA", "CPLE6.SA", "PETR3.SA", "VALE5.SA", "ITSA4.SA",
    # Fundos Imobiliários
    "MXRF11.SA", "HGLG11.SA", "KNRI11.SA", "XPML11.SA", "VISC11.SA",
    "BTLG11.SA", "HGRU11.SA", "BCFF11.SA", "KNCR11.SA", "RBRR11.SA",
    # Small/Mid Caps
    "MGLU3.SA", "AZUL4.SA", "GOAU4.SA", "COGN3.SA", "TOTS3.SA",
    "QUAL3.SA", "BRFS3.SA", "MRFG3.SA", "BEEF3.SA", "LWSA3.SA"
]

@st.cache_data(ttl=900)
def analisar_ativo_completo(ticker):
    """
    Análise completa de um ativo com ML, indicadores técnicos e regime de mercado.
    Retorna dicionário com recomendação, score, análise e alertas.
    """
    try:
        # Buscar dados históricos
        df = get_stock_data(ticker)
        if df.empty:
            return {
                'status': 'erro',
                'ticker': ticker,
                'mensagem': f'Não encontrei dados para {ticker}. Verifique se o ticker está correto (ex: PETR4.SA para ações brasileiras, BTC-USD para Bitcoin).',
                'recomendacao': 'INDISPONÍVEL',
                'score': 0
            }
        
        # Adicionar indicadores técnicos
        df = add_indicators(df)
        if df.empty or len(df) < 50:
            return {
                'status': 'erro',
                'ticker': ticker,
                'mensagem': f'{ticker} não tem histórico suficiente (requer 50+ dias de negociação). Tente outro ativo.',
                'recomendacao': 'DADOS INSUFICIENTES',
                'score': 0
            }
        
        # Treinar modelo ML
        features = ['rsi', 'ema50', 'ema200', 'macd', 'volume_ratio', 'volatility']
        model, accuracy = train_model(df)
        last_data = df[features].iloc[-1:]
        ml_prob = model.predict_proba(last_data)[0][1]  # Probabilidade de alta
        
        # Pegar última linha de indicadores
        last = df.iloc[-1]
        rsi = last['rsi']
        ema50 = last['ema50']
        ema200 = last['ema200']
        macd = last['macd']
        volume_ratio = last['volume_ratio']
        
        # Detectar regime de mercado
        try:
            regime = detect_regime()
        except Exception:
            regime = "Neutro"
        
        # Sistema de pontuação (0-100)
        score = 0
        alertas = []
        
        # Análise RSI (0-20 pontos)
        if rsi < 30:
            score += 20
            alertas.append("RSI em sobrevenda - Oportunidade de compra")
        elif rsi > 70:
            score -= 15
            alertas.append("RSI em sobrecompra - Cautela, ativo pode corrigir")
        elif 40 <= rsi <= 60:
            score += 10
            alertas.append("RSI neutro - Ativo em equilíbrio")
        
        # Análise EMA - Tendência (0-25 pontos)
        if last['Close'] > ema50 > ema200:
            score += 25
            alertas.append("Tendência de ALTA - Preço acima de EMA50 e EMA200")
        elif last['Close'] > ema50:
            score += 15
            alertas.append("Tendência de ALTA de curto prazo")
        elif last['Close'] < ema50 < ema200:
            score -= 20
            alertas.append("Tendência de BAIXA - Preço abaixo de EMA50 e EMA200")
        
        # Golden Cross / Death Cross
        if ema50 > ema200 and df.iloc[-2]['ema50'] <= df.iloc[-2]['ema200']:
            score += 20
            alertas.append("GOLDEN CROSS detectado - Sinal forte de compra")
        elif ema50 < ema200 and df.iloc[-2]['ema50'] >= df.iloc[-2]['ema200']:
            score -= 25
            alertas.append("DEATH CROSS detectado - Sinal forte de venda")
        
        # Análise MACD (0-15 pontos)
        if macd > 0:
            score += 15
            alertas.append("MACD positivo - Momentum de compra")
        else:
            score -= 10
            alertas.append("MACD negativo - Momentum de venda")
        
        # Análise de Volume (0-15 pontos)
        if volume_ratio > 1.5:
            score += 15
            alertas.append("Volume acima da média - Movimentação forte")
        elif volume_ratio < 0.5:
            score -= 5
            alertas.append("Volume baixo - Pouca liquidez")
        
        # ML Prediction (0-25 pontos)
        if ml_prob > 0.65:
            score += 25
            alertas.append(f"IA prevê alta com {ml_prob*100:.1f}% de probabilidade")
        elif ml_prob < 0.35:
            score -= 20
            alertas.append(f"IA prevê baixa com {(1-ml_prob)*100:.1f}% de probabilidade")
        
        # Ajuste por regime de mercado
        if "Alta" in regime:
            score += 10
            alertas.append("Mercado global em alta - Ambiente favorável")
        elif "Baixa" in regime:
            score -= 10
            alertas.append("Mercado global em baixa - Cautela recomendada")
        
        # Determinar recomendação final
        if score >= 70:
            recomendacao = "COMPRA FORTE"
            acao = "COMPRAR AGORA"
        elif score >= 40:
            recomendacao = "COMPRA"
            acao = "Boa oportunidade de entrada"
        elif score >= 10:
            recomendacao = "NEUTRO"
            acao = "Aguardar sinais mais claros"
        elif score >= -20:
            recomendacao = "EVITAR"
            acao = "Não recomendado para compra"
        else:
            recomendacao = "VENDA"
            acao = "Considerar reduzir posição"
        
        return {
            'status': 'sucesso',
            'ticker': ticker,
            'recomendacao': recomendacao,
            'acao': acao,
            'score': score,
            'ml_prob': ml_prob,
            'accuracy': accuracy,
            'rsi': rsi,
            'preco': last['Close'],
            'ema50': ema50,
            'ema200': ema200,
            'regime': regime,
            'alertas': alertas
        }
    
    except Exception as e:
        return {
            'status': 'erro',
            'mensagem': f'Erro ao analisar {ticker}: {str(e)}',
            'recomendacao': 'AGUARDAR',
            'score': 0
        }

# ==========================================
# 4. MOTORES DE DADOS (APIs) E CÁLCULOS
# ==========================================
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

@st.cache_data(ttl=1800)
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

    # ==========================================
    # ANÁLISE AUTOMÁTICA DO MERCADO BRASILEIRO
    # ==========================================
    st.markdown("---")
    st.markdown("<div class='titulo-secao'>Oportunidades no Mercado Brasileiro</div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e; font-size: 14px;'>IA analisa automaticamente os principais ativos da B3 para encontrar oportunidades de investimento.</p>", unsafe_allow_html=True)
    
    # Seletor de quantidade de ativos
    col_sel1, col_sel2 = st.columns([3, 1])
    with col_sel1:
        qtd_analise = st.select_slider(
            "Quantos ativos analisar?",
            options=[10, 20, 30, 40, 50],
            value=20,
            help="Quanto mais ativos, mais tempo levará a análise. Recomendado: 20"
        )
    with col_sel2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_analisar_mercado = st.button("Analisar Mercado", type="primary", use_container_width=True)
    
    # Usa session_state para manter análise entre reloads
    if 'analises_mercado_cache' not in st.session_state or btn_analisar_mercado:
        with st.spinner(f"IA analisando {qtd_analise} ativos do mercado brasileiro... Isso pode levar alguns minutos."):
            analises_mercado = []
            progress_bar = st.progress(0)
            for i, ticker in enumerate(ATIVOS_MERCADO_BRASILEIRO[:qtd_analise]):
                analise = analisar_ativo_completo(ticker)
                if analise.get('status') == 'sucesso':
                    analises_mercado.append(analise)
                progress_bar.progress((i + 1) / qtd_analise)
            st.session_state['analises_mercado_cache'] = analises_mercado
            progress_bar.empty()
    else:
        analises_mercado = st.session_state.get('analises_mercado_cache', [])
    
    if analises_mercado:
        # Separa por tipo de recomendação
        mercado_compra_forte = [a for a in analises_mercado if 'COMPRA FORTE' in a['recomendacao']]
        mercado_compra = [a for a in analises_mercado if a['recomendacao'] == 'COMPRA']
        mercado_neutro = [a for a in analises_mercado if 'NEUTRO' in a['recomendacao']]
        mercado_evitar = [a for a in analises_mercado if 'EVITAR' in a['recomendacao']]
        mercado_venda = [a for a in analises_mercado if 'VENDA' in a['recomendacao']]
        
        # Resumo geral
        col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
        col_r1.metric("Compra Forte", len(mercado_compra_forte))
        col_r2.metric("Compra", len(mercado_compra))
        col_r3.metric("Neutro", len(mercado_neutro))
        col_r4.metric("Evitar", len(mercado_evitar))
        col_r5.metric("Venda", len(mercado_venda))
        
        # Tabs para organizar melhor
        tab1, tab2, tab3 = st.tabs(["Melhores Oportunidades", "Tabela Completa", "Riscos"])
        
        with tab1:
            if mercado_compra_forte or mercado_compra:
                # Ordena por score (maior primeiro)
                todas_compras = sorted(mercado_compra_forte + mercado_compra, key=lambda x: x['score'], reverse=True)
                
                st.markdown("### Top 10 Oportunidades do Mercado")
                for i, a in enumerate(todas_compras[:10], 1):
                    with st.expander(f"#{i} - {a['ticker']} | Score: {a['score']} | {a['recomendacao']}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Preço", f"R$ {a['preco']:.2f}")
                            st.metric("RSI", f"{a['rsi']:.1f}")
                        with col2:
                            st.metric("Prob. Alta", f"{a['ml_prob']*100:.1f}%")
                            st.metric("Acurácia", f"{a['accuracy']*100:.1f}%")
                        with col3:
                            st.metric("EMA50", f"R$ {a['ema50']:.2f}")
                            st.metric("EMA200", f"R$ {a['ema200']:.2f}")
                        
                        st.markdown(f"**Ação:** {a['acao']}")
                        st.markdown(f"**Regime:** {a['regime']}")
                        
                        st.markdown("**Alertas:**")
                        for alerta in a['alertas']:
                            st.markdown(f"- {alerta}")
                        
                        # Botão para adicionar
                        if st.button(f"Adicionar {a['ticker']} à Carteira", key=f"add_mercado_{a['ticker']}", use_container_width=True):
                            st.session_state['novo_ticker_input'] = a['ticker']
                            st.session_state['pagina_atual'] = 'carteira'
                            st.rerun()
            else:
                st.info("Nenhuma oportunidade forte identificada no momento.")
        
        with tab2:
            # Tabela completa com todos os ativos analisados
            st.markdown("### Análise Completa do Mercado")
            
            # Cria DataFrame para exibição
            tabela_mercado = []
            for a in analises_mercado:
                tabela_mercado.append({
                    'Ticker': a['ticker'],
                    'Recomendação': a['recomendacao'],
                    'Score': a['score'],
                    'Preço (R$)': a['preco'],
                    'RSI': f"{a['rsi']:.1f}",
                    'Prob. Alta (%)': f"{a['ml_prob']*100:.1f}",
                    'Regime': a['regime']
                })
            
            df_mercado = pd.DataFrame(tabela_mercado)
            # Ordena por score
            df_mercado = df_mercado.sort_values('Score', ascending=False)
            
            st.dataframe(df_mercado, use_container_width=True, hide_index=True)
            
            # Opção de download
            csv_mercado = df_mercado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar Análise em CSV",
                data=csv_mercado,
                file_name=f"analise_mercado_brasileiro_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with tab3:
            if mercado_evitar or mercado_venda:
                st.markdown("### Ativos com Risco identificado")
                todos_riscos = sorted(mercado_evitar + mercado_venda, key=lambda x: x['score'])
                
                for a in todos_riscos:
                    with st.expander(f"{a['ticker']} | Score: {a['score']} | {a['recomendacao']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Preço", f"R$ {a['preco']:.2f}")
                            st.metric("RSI", f"{a['rsi']:.1f}")
                        with col2:
                            st.metric("Prob. Alta", f"{a['ml_prob']*100:.1f}%")
                            st.metric("Score", a['score'])
                        
                        st.warning(f"**{a['acao']}**")
                        st.markdown("**Alertas:**")
                        for alerta in a['alertas']:
                            st.markdown(f"- {alerta}")
            else:
                st.success("Nenhum ativo com risco elevado identificado!")
    else:
        st.info("Clique em 'Analisar Mercado' para iniciar a análise automática da B3.")
    
    # ==========================================
    # ALERTAS INTELIGENTES DA IA - ANÁLISE AUTOMÁTICA DA CARTEIRA
    # ==========================================
    if not carteira_df.empty:
        st.markdown("---")
        st.markdown("<div class='titulo-secao'>ALERTAS INTELIGENTES DA IA - Análise Automática da Sua Carteira</div>", unsafe_allow_html=True)
        
        with st.spinner("IA analisando todos os seus ativos com ML e indicadores técnicos..."):
            analises = []
            for ticker in carteira_df['ticker'].tolist():
                analise = analisar_ativo_completo(ticker)
                analises.append(analise)
        
        # Separa por tipo de recomendação
        compras_fortes = [a for a in analises if a.get('status') == 'sucesso' and 'COMPRA FORTE' in a['recomendacao']]
        compras = [a for a in analises if a.get('status') == 'sucesso' and a['recomendacao'] == 'COMPRA']
        neutros = [a for a in analises if a.get('status') == 'sucesso' and 'NEUTRO' in a['recomendacao']]
        evitar = [a for a in analises if a.get('status') == 'sucesso' and 'EVITAR' in a['recomendacao']]
        venda = [a for a in analises if a.get('status') == 'sucesso' and 'VENDA' in a['recomendacao']]
        
        # Exibe alertas em colunas
        col_alertas1, col_alertas2 = st.columns(2)
        
        with col_alertas1:
            # Oportunidades de Compra
            if compras_fortes or compras:
                st.markdown("### OPORTUNIDADES DE COMPRA")
                for analise in compras_fortes + compras:
                    with st.expander(f"{analise['ticker']} - {analise['recomendacao']} (Score: {analise['score']})"):
                        st.markdown(f"**Ação Recomendada:** {analise['acao']}")
                        st.markdown(f"**Preço Atual:** R$ {analise['preco']:.2f}")
                        st.markdown(f"**RSI:** {analise['rsi']:.1f}")
                        st.markdown(f"**Probabilidade de Alta (IA):** {analise['ml_prob']*100:.1f}%")
                        st.markdown(f"**Acurácia do Modelo:** {analise['accuracy']*100:.1f}%")
                        st.markdown(f"**Regime de Mercado:** {analise['regime']}")
                        st.markdown("**Alertas Detectados:**")
                        for alerta in analise['alertas']:
                            st.markdown(f"- {alerta}")
            
            # Ativos Neutros
            if neutros:
                st.markdown("### MONITORAR")
                for analise in neutros:
                    with st.expander(f"{analise['ticker']} - {analise['recomendacao']} (Score: {analise['score']})"):
                        st.markdown(f"**Ação Recomendada:** {analise['acao']}")
                        st.markdown(f"**Análise:** Ativo sem sinais claros. Continue acompanhando.")
                        st.markdown("**Principais Indicadores:**")
                        for alerta in analise['alertas'][:3]:
                            st.markdown(f"- {alerta}")
        
        with col_alertas2:
            # Alertas de Risco
            if evitar or venda:
                st.markdown("### ALERTAS DE RISCO")
                for analise in evitar + venda:
                    with st.expander(f"{analise['ticker']} - {analise['recomendacao']} (Score: {analise['score']})"):
                        st.markdown(f"**Ação Recomendada:** {analise['acao']}")
                        st.markdown(f"**Preço Atual:** R$ {analise['preco']:.2f}")
                        st.markdown(f"**RSI:** {analise['rsi']:.1f}")
                        st.markdown(f"**Probabilidade de Baixa (IA):** {(1-analise['ml_prob'])*100:.1f}%")
                        st.markdown("**Alertas Críticos:**")
                        for alerta in analise['alertas']:
                            st.markdown(f"- {alerta}")
                        if 'VENDA' in analise['recomendacao']:
                            st.error("**Sugestão:** Considere realizar lucros ou reduzir exposição neste ativo.")
            
            # Resumo Geral
            st.markdown("### RESUMO DA CARTEIRA")
            total_ativos = len(analises)
            st.metric("Total de Ativos Analisados", total_ativos)
            
            if compras_fortes:
                st.success(f"{len(compras_fortes)} ativo(s) com COMPRA FORTE")
            if compras:
                st.info(f"{len(compras)} ativo(s) com COMPRA")
            if evitar or venda:
                st.warning(f"{len(evitar + venda)} ativo(s) com RISCO")

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
        with st.expander("Análise Personalizada de Ativo"):
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
    st.markdown("<div class='titulo-secao'>IA Assistente Financeiro</div>", unsafe_allow_html=True)
    
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
                            except Exception:
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
    st.markdown("<div class='titulo-secao'>Principais Notícias (Impacto no Mercado)</div>", unsafe_allow_html=True)
    
    conn = get_market_connection()
    try:
        news_df = pd.read_sql("SELECT title, description, sentiment, published_at FROM news ORDER BY published_at DESC LIMIT 5", conn)
        if not news_df.empty:
            with st.spinner("Traduzindo notícias..."):
                for _, row in news_df.iterrows():
                    # Traduz título e descrição para português
                    titulo_traduzido = traduzir_texto(row['title'], 'pt')
                    descricao_traduzida = traduzir_texto(row['description'], 'pt')
                    
                    sentiment_color = "#00ffa3" if row['sentiment'] > 0.1 else "#ff6b6b" if row['sentiment'] < -0.1 else "#f39c12"
                    st.markdown(f"""
                    <div style='border-left: 3px solid {sentiment_color}; padding: 10px; margin-bottom: 10px; background-color: #161b22;'>
                        <strong>{titulo_traduzido}</strong><br>
                        <small style='color: #8b949e;'>{descricao_traduzida[:150]}...</small><br>
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
        carteira_df, patrimonio_total = processar_carteira_tempo_real(carteira_df_bruto)

    # ==========================================
    # 1. VISÃO GERAL E MÉTRICAS DINÂMICAS
    # ==========================================
    if not carteira_df.empty:
        # Cálculos de Rentabilidade
        carteira_df['Custo Total'] = carteira_df['quantidade'] * carteira_df['preco_medio']
        carteira_df['Lucro/Prejuízo (R$)'] = carteira_df['Valor Total'] - carteira_df['Custo Total']
        carteira_df['Rentabilidade (%)'] = ((carteira_df['Preço Atual API'] - carteira_df['preco_medio']) / carteira_df['preco_medio']) * 100
        
        lucro_total = carteira_df['Lucro/Prejuízo (R$)'].sum()
        custo_total = carteira_df['Custo Total'].sum()
        rentabilidade_geral = (lucro_total / custo_total) * 100 if custo_total > 0 else 0

        # Exibição dos Cards no Topo
        col1, col2, col3 = st.columns(3)
        col1.metric("Patrimônio Total", f"R$ {patrimonio_total:,.2f}")
        col2.metric("Lucro / Prejuízo Total", f"R$ {lucro_total:,.2f}", f"{rentabilidade_geral:.2f}%")
        
        avg_div = carteira_df['Dividendo Anual (API)'].replace(0, pd.NA).mean()
        col3.metric("Média Div. Anual/Cota", f"R$ {avg_div:.2f}" if not pd.isna(avg_div) else "R$ 0.00")
        
        # ==========================================
        # ANÁLISE IA PARA CADA ATIVO DA CARTEIRA
        # ==========================================
        st.markdown("---")
        st.markdown("<div class='titulo-secao'>Análise IA de Cada Ativo</div>", unsafe_allow_html=True)
        
        with st.spinner("IA analisando seus ativos..."):
            analises_carteira = {}
            for ticker in carteira_df['ticker'].tolist():
                analise = analisar_ativo_completo(ticker)
                analises_carteira[ticker] = analise
        
        # Adiciona coluna de recomendação IA
        carteira_df['Status IA'] = carteira_df['ticker'].map(lambda t: analises_carteira[t].get('recomendacao', 'N/A'))
        carteira_df['Score IA'] = carteira_df['ticker'].map(lambda t: analises_carteira[t].get('score', 0))
        
        st.markdown("<div class='titulo-secao'>Minhas Posições (Atualizado via B3 + IA)</div>", unsafe_allow_html=True)
        
        # Tabela Formatada com Status IA
        visao_df = carteira_df[['ticker', 'quantidade', 'preco_medio', 'Preço Atual API', 'Rentabilidade (%)', 'Lucro/Prejuízo (R$)', 'Valor Total', 'Status IA', 'Score IA']].copy()
        visao_df.columns = ['Ativo', 'Volume', 'Preço Médio', 'Preço Hoje', 'Rentabilidade (%)', 'Lucro/Prejuízo (R$)', 'Valor Total (R$)', 'Recomendação IA', 'Score']
        
        # Função para pintar os números de verde ou vermelho
        def color_negative_red(val):
            color = '#ff6b6b' if val < 0 else '#00ffa3'
            return f'color: {color}'

        st.dataframe(visao_df.style.format({
            'Volume': '{:.2f}', 
            'Preço Médio': 'R$ {:.2f}',
            'Preço Hoje': 'R$ {:.2f}',
            'Rentabilidade (%)': '{:.2f}%',
            'Lucro/Prejuízo (R$)': 'R$ {:.2f}',
            'Valor Total (R$)': 'R$ {:.2f}',
            'Score': '{:.0f}'
        }).map(color_negative_red, subset=['Rentabilidade (%)', 'Lucro/Prejuízo (R$)', 'Score']), width='stretch', hide_index=True)
        
        # Detalhes expandidos para cada ativo
        st.markdown("### Detalhes e Recomendações por Ativo")
        for ticker in carteira_df['ticker'].tolist():
            analise = analises_carteira[ticker]
            if analise.get('status') == 'sucesso':
                with st.expander(f"{ticker} - {analise['recomendacao']} | Score: {analise['score']}"):
                    col_det1, col_det2, col_det3 = st.columns(3)
                    with col_det1:
                        st.metric("Preço Atual", f"R$ {analise['preco']:.2f}")
                        st.metric("RSI", f"{analise['rsi']:.1f}")
                    with col_det2:
                        st.metric("EMA50", f"R$ {analise['ema50']:.2f}")
                        st.metric("EMA200", f"R$ {analise['ema200']:.2f}")
                    with col_det3:
                        st.metric("Prob. Alta (IA)", f"{analise['ml_prob']*100:.1f}%")
                        st.metric("Acurácia", f"{analise['accuracy']*100:.1f}%")
                    
                    st.markdown(f"**Ação Recomendada:** {analise['acao']}")
                    st.markdown(f"**Regime de Mercado:** {analise['regime']}")
                    
                    st.markdown("**Alertas e Indicadores:**")
                    for alerta in analise['alertas']:
                        st.markdown(f"- {alerta}")
                    
                    # Recomendação específica baseada na análise
                    if "COMPRA FORTE" in analise['recomendacao']:
                        st.success(f"**Sugestão:** Considere AUMENTAR sua posição em {ticker}. Os indicadores estão muito favoráveis!")
                    elif "COMPRA" in analise['recomendacao']:
                        st.info(f"**Sugestão:** Bom momento para fazer aportes em {ticker}.")
                    elif "VENDA" in analise['recomendacao']:
                        st.error(f"**Sugestão:** Considere REDUZIR ou ZERAR sua posição em {ticker} para proteger capital.")
                    elif "EVITAR" in analise['recomendacao']:
                        st.warning(f"**Sugestão:** NÃO faça novos aportes em {ticker} no momento. Aguarde reversão da tendência.")
                    else:
                        st.info(f"**Sugestão:** MANTENHA sua posição em {ticker} e continue monitorando.")
    else:
        st.info("Você ainda não possui ativos registrados na sua carteira.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==========================================
    #  BUSCAR RECOMENDAÇÃO IA PARA QUALQUER ATIVO
    # ==========================================
    st.markdown("---")
    st.markdown("<div class='titulo-secao'>Buscar Recomendação IA para Qualquer Ativo</div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e; font-size: 14px;'>Analise qualquer ativo antes de investir! Digite o ticker e receba análise completa com ML e indicadores técnicos.</p>", unsafe_allow_html=True)
    
    col_busca, col_btn = st.columns([3, 1])
    with col_busca:
        ticker_busca = st.text_input(
            "Digite o ticker do ativo (ex: PETR4.SA, BTC-USD, SANB11.SA)", 
            key="busca_ia_ticker",
            placeholder="Ex: PETR4.SA"
        ).upper()
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        buscar_btn = st.button("Analisar com IA", type="primary", use_container_width=True)
    
    if buscar_btn and ticker_busca:
        with st.spinner(f"IA analisando {ticker_busca} com ML e indicadores técnicos..."):
            analise_busca = analisar_ativo_completo(ticker_busca)
            
            if analise_busca.get('status') == 'sucesso':
                # Header com recomendação principal
                rec_cor = "#00ffa3" if "COMPRA" in analise_busca['recomendacao'] else "#ff6b6b" if "VENDA" in analise_busca['recomendacao'] or "EVITAR" in analise_busca['recomendacao'] else "#f39c12"
                
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, {rec_cor}22 0%, {rec_cor}11 100%); 
                            border-left: 4px solid {rec_cor}; 
                            padding: 20px; 
                            border-radius: 8px; 
                            margin: 20px 0;'>
                    <h2 style='margin: 0; color: {rec_cor};'>{ticker_busca}</h2>
                    <h3 style='margin: 10px 0; color: #ffffff;'>{analise_busca['recomendacao']}</h3>
                    <p style='margin: 0; font-size: 20px; color: #a3a8b8;'>Score: <strong style='color: {rec_cor};'>{analise_busca['score']}/100</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Métricas principais em 3 colunas
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Preço Atual", f"R$ {analise_busca['preco']:.2f}")
                    st.metric("RSI", f"{analise_busca['rsi']:.1f}")
                with col_m2:
                    st.metric("EMA 50", f"R$ {analise_busca['ema50']:.2f}")
                    st.metric("EMA 200", f"R$ {analise_busca['ema200']:.2f}")
                with col_m3:
                    st.metric("Probabilidade Alta (ML)", f"{analise_busca['ml_prob']*100:.1f}%")
                    st.metric("Acurácia do Modelo", f"{analise_busca['accuracy']*100:.1f}%")
                
                # Informações detalhadas
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.markdown("### Ação Recomendada")
                    st.info(analise_busca['acao'])
                    
                    st.markdown("### Regime de Mercado")
                    st.markdown(analise_busca['regime'])
                
                with col_info2:
                    st.markdown("### Sinais e Indicadores")
                    for alerta in analise_busca['alertas']:
                        st.markdown(f"- {alerta}")
                
                # Recomendação final personalizada
                st.markdown("---")
                st.markdown("### Análise Final e Sugestão")
                
                if "COMPRA FORTE" in analise_busca['recomendacao']:
                    st.success(f"""
                    **RECOMENDAÇÃO: COMPRA FORTE**
                    
                    {ticker_busca} apresenta sinais técnicos e fundamentais muito positivos. 
                    É um excelente momento para **iniciar posição** ou **aumentar exposição**.
                    
                    - Score: {analise_busca['score']}/100 (Muito Favorável)
                    - Probabilidade ML de Alta: {analise_busca['ml_prob']*100:.1f}%
                    - Tendência: {analise_busca['regime']}
                    """)
                elif "COMPRA" in analise_busca['recomendacao']:
                    st.info(f"""
                    **RECOMENDAÇÃO: COMPRA**
                    
                    {ticker_busca} mostra boas oportunidades de entrada. Indicadores apontam para valorização.
                    
                    - Score: {analise_busca['score']}/100 (Favorável)
                    - Probabilidade ML de Alta: {analise_busca['ml_prob']*100:.1f}%
                    - Tendência: {analise_busca['regime']}
                    """)
                elif "VENDA" in analise_busca['recomendacao']:
                    st.error(f"""
                    **RECOMENDAÇÃO: VENDA**
                    
                    {ticker_busca} apresenta sinais de risco elevado. Se você possui este ativo, considere **reduzir** ou **zerar** a posição.
                    
                    - Score: {analise_busca['score']}/100 (Desfavorável)
                    - Probabilidade ML de Alta: {analise_busca['ml_prob']*100:.1f}%
                    - Tendência: {analise_busca['regime']}
                    """)
                elif "EVITAR" in analise_busca['recomendacao']:
                    st.warning(f"""
                    **RECOMENDAÇÃO: EVITAR**
                    
                    {ticker_busca} não apresenta condições favoráveis para entrada. **NÃO** faça novos aportes até reversão dos sinais.
                    
                    - Score: {analise_busca['score']}/100 (Desfavorável)
                    - Probabilidade ML de Alta: {analise_busca['ml_prob']*100:.1f}%
                    - Tendência: {analise_busca['regime']}
                    """)
                else:
                    st.info(f"""
                    **RECOMENDAÇÃO: NEUTRO**
                    
                    {ticker_busca} está em momento de indefinição. **MANTENHA** suas posições atuais e aguarde sinais mais claros.
                    
                    - Score: {analise_busca['score']}/100 (Neutro)
                    - Probabilidade ML de Alta: {analise_busca['ml_prob']*100:.1f}%
                    - Tendência: {analise_busca['regime']}
                    """)
                
                # Botão para adicionar à carteira
                if "COMPRA" in analise_busca['recomendacao']:
                    st.markdown("---")
                    if st.button(f"Adicionar {ticker_busca} à Minha Carteira", type="primary", use_container_width=True):
                        st.session_state['novo_ticker_input'] = ticker_busca
                        st.rerun()
                        
            else:
                st.error(analise_busca.get('mensagem', f"Não foi possível analisar {ticker_busca}. Verifique se o ticker está correto (ex: PETR4.SA para ações brasileiras, BTC-USD para Bitcoin)."))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==========================================
    # 2. LANÇAMENTO DE COMPRAS E VENDAS
    # ==========================================
    col_add, col_remove = st.columns(2)
    
    # Lista de ativos para o menu Dropdown
    lista_ativos_populares = [
        "PETR4.SA - Petrobras", "VALE3.SA - Vale", "ITUB4.SA - Itaú Unibanco", 
        "BBAS3.SA - Banco do Brasil", "BBDC4.SA - Bradesco", "WEGE3.SA - Weg", 
        "MGLU3.SA - Magazine Luiza", "JBSS3.SA - JBS", "ABEV3.SA - Ambev",
        "BTC-USD - Bitcoin", "ETH-USD - Ethereum", "^GSPC - S&P 500",
        "Outro (Digitar Manualmente)"
    ]
    
    with col_add:
        st.markdown("<div class='titulo-secao'>Lançamento de Operação (Compra/Adição)</div>", unsafe_allow_html=True)
        
        # Puxa o ticker que veio da tela "Explorar Ativos" (se houver)
        ticker_padrao = st.session_state.get('novo_ticker_input', '')
        index_padrao = 0
        
        if ticker_padrao:
            for i, item in enumerate(lista_ativos_populares):
                if item.startswith(ticker_padrao):
                    index_padrao = i
                    break
            # Se veio um ticker que não está na lista padrão, adiciona ele no topo
            if index_padrao == 0 and not lista_ativos_populares[0].startswith(ticker_padrao):
                lista_ativos_populares.insert(0, f"{ticker_padrao} - Selecionado do Explorar")
        
        # O novo Dropdown de Pesquisa
        selecao_dropdown = st.selectbox(
            "Busque o ativo (digite o nome ou ticker para filtrar):", 
            lista_ativos_populares,
            index=index_padrao
        )
        
        # Se escolher "Outro", abre a caixa de texto antiga para digitar livremente
        if selecao_dropdown == "Outro (Digitar Manualmente)":
            novo_ticker_cru = st.text_input("Digite o Ticker (ex: SANB11.SA):").upper()
        else:
            novo_ticker_cru = selecao_dropdown.split(" - ")[0]
        
        sugestao_preco = 0.0
        
        if novo_ticker_cru and novo_ticker_cru != "OUTRO (DIGITAR MANUALMENTE)":
            with st.spinner(f"Consultando cotação de {novo_ticker_cru}..."):
                sugestao_preco, _ = buscar_dados_ticker_completo(novo_ticker_cru)
            if sugestao_preco > 0:
                st.success(f"Ativo validado. Cotação Atual: R$ {sugestao_preco:.2f}")
            else:
                st.error("Ativo não identificado. Verifique o ticker.")
                
        # Campos de Quantidade e Preço lado a lado para poupar espaço
        col_qtd, col_preco = st.columns(2)
        with col_qtd:
            novo_qtd = st.number_input("Volume da Operação", min_value=0.0, step=1.0)
        with col_preco:
            novo_pm = st.number_input("Preço Pago (R$)", min_value=0.0, value=float(sugestao_preco), step=0.01)
        
        if st.button("Registrar Operação", type="primary", use_container_width=True):
            if novo_ticker_cru and novo_pm > 0 and novo_qtd > 0:
                gerir_ativo_db(usuario_atual, novo_ticker_cru, novo_qtd, novo_pm)
                st.session_state['novo_ticker_input'] = "" # Limpa a memória
                st.success("Operação contabilizada com sucesso.")
                st.rerun()
            else:
                st.error("Dados inconsistentes para registro. Verifique a cotação e o volume.")

    with col_remove:
        st.markdown("<div class='titulo-secao'>Liquidação de Posição</div>", unsafe_allow_html=True)
        if not carteira_df.empty:
            st.markdown("<p style='color: #8b949e; font-size: 14px;'>Selecione o ativo que deseja remover completamente da sua carteira.</p>", unsafe_allow_html=True)
            with st.form("form_remove_ativo"):
                ativo_para_remover = st.selectbox("Selecione o ativo:", carteira_df['ticker'].tolist())
                if st.form_submit_button("Liquidar Posição", use_container_width=True):
                    remover_ativo_db(usuario_atual, ativo_para_remover)
                    st.success("Posição zerada com sucesso.")
                    st.rerun()
        else:
            st.info("Nenhuma posição aberta no momento.")

# =======================================================
# NOVA FUNÇÃO DE CACHE (Busca preços rápido sem travar)
# =======================================================
@st.cache_data(ttl=600)  # Atualiza a cada 10 minutos
def obter_cotacoes_explorar():
    tickers_principais = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBAS3.SA", "WEGE3.SA", "BTC-USD", "ETH-USD", "USDBRL=X", "^GSPC"]
    dados = {}
    for tk in tickers_principais:
        try:
            hist = yf.Ticker(tk).history(period="2d")
            if len(hist) >= 2:
                preco = float(hist['Close'].iloc[-1])
                ontem = float(hist['Close'].iloc[-2])
                var = ((preco - ontem) / ontem) * 100
                dados[tk] = {'preco': preco, 'var': var}
            elif not hist.empty:
                dados[tk] = {'preco': float(hist['Close'].iloc[-1]), 'var': 0.0}
            else:
                dados[tk] = {'preco': 0.0, 'var': 0.0}
        except Exception:
            dados[tk] = {'preco': 0.0, 'var': 0.0}
    return dados


# =======================================================
# NOVA TELA EXPLORAR ATIVOS (Substitui a antiga)
# =======================================================
def tela_explorar_ativos():
    renderizar_menu()
    st.markdown("<h1>EXPLORAR ATIVOS</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("Explore os ativos em destaque. Clique no botão **Adicionar** para ser levado à sua carteira com o ativo já selecionado.")
    
    # Busca os preços em tempo real com spinner
    with st.spinner("Sincronizando cotações globais..."):
        cotacoes = obter_cotacoes_explorar()

    # Organizando os ativos por blocos/setores para ficar elegante
    categorias = {
        "Ações Brasileiras (Top B3)": [
            {"Nome": "Petrobras", "Ticker": "PETR4.SA"},
            {"Nome": "Vale", "Ticker": "VALE3.SA"},
            {"Nome": "Itaú Unibanco", "Ticker": "ITUB4.SA"},
            {"Nome": "Banco do Brasil", "Ticker": "BBAS3.SA"},
            {"Nome": "Weg Indústria", "Ticker": "WEGE3.SA"},
        ],
        "Criptomoedas e Global": [
            {"Nome": "Bitcoin", "Ticker": "BTC-USD"},
            {"Nome": "Ethereum", "Ticker": "ETH-USD"},
            {"Nome": "S&P 500", "Ticker": "^GSPC"},
            {"Nome": "Dólar Comercial", "Ticker": "USDBRL=X"},
        ]
    }

    # Desenhando os Cards na tela
    for cat_nome, ativos in categorias.items():
        st.markdown(f"<div class='titulo-secao'>{cat_nome}</div>", unsafe_allow_html=True)
        
        # Cria as linhas (Máximo de 4 cards por linha)
        for i in range(0, len(ativos), 4):
            cols = st.columns(4)
            linha_atual = ativos[i:i+4]
            
            for j, ativo in enumerate(linha_atual):
                tk = ativo["Ticker"]
                info = cotacoes.get(tk, {'preco': 0.0, 'var': 0.0})
                
                # Definição de cores baseada na variação
                cor_var = "#00ffa3" if info['var'] >= 0 else "#ff6b6b"
                sinal = "+" if info['var'] > 0 else ""

                with cols[j]:
                    with st.container(border=True):  # Cria a bordinha do Card
                        st.markdown(f"<span style='color:#8b949e; font-size:12px;'>{ativo['Nome']}</span>", unsafe_allow_html=True)
                        st.markdown(f"<h4 style='margin:0; padding:0; color:#ffffff;'>{tk}</h4>", unsafe_allow_html=True)
                        
                        if info['preco'] > 0:
                            # Formatação: Se for Dólar/Ação mostra R$, se for Cripto/Índice mostra $
                            simbolo = "$" if "USD" in tk or "^" in tk else "R$"
                            st.markdown(f"<h3 style='margin:0; padding-top:5px; font-size:22px; color:#c9d1d9;'>{simbolo} {info['preco']:,.2f}</h3>", unsafe_allow_html=True)
                            st.markdown(f"<span style='color:{cor_var}; font-size:14px; font-weight:bold;'>{sinal}{info['var']:.2f}%</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<p style='color:#8b949e; padding-top:10px;'>Sem cotação</p>", unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # O grande botão mágico!
                        if st.button("Adicionar", key=f"btn_add_{tk}", use_container_width=True):
                            # Salva o ticker escolhido e troca de página instantaneamente
                            st.session_state['novo_ticker_input'] = tk
                            st.session_state['pagina_atual'] = 'carteira'
                            st.rerun()
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




