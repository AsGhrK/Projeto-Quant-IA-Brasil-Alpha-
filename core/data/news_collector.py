import os
import requests
from textblob import TextBlob
from dotenv import load_dotenv
from core.database.database import get_market_connection

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def analyze_sentiment(text):
    if not text: return 0.0
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def collect_news(query="brazil stock market"):
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        articles = response.json().get("articles", [])
    except Exception as e:
        print(f"Erro na NewsAPI: {e}")
        return

    conn = get_market_connection()
    cursor = conn.cursor()

    for art in articles:
        sentiment_score = analyze_sentiment(art.get("description", ""))
        
        cursor.execute("""
            INSERT OR IGNORE INTO news (title, published_at, source, description, sentiment)
            VALUES (?, ?, ?, ?, ?)
        """, (art["title"], art["publishedAt"], art.get("source", {}).get("name", "Desconhecido"), art.get("description", ""), sentiment_score))

    conn.commit()
    conn.close()
    print(f"Notícias sobre '{query}' coletadas com sucesso.")