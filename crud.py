import sqlite3
import pandas as pd


DATABSE_PATH = "C:/Users/anboicu/Computational Thinking/Project/stock_database.db"

# Connect to SQLite database (creates file if not exists)
conn = sqlite3.connect(DATABSE_PATH)
cursor = conn.cursor()

# Table for stock prices
cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        UNIQUE(ticker, date)
    )
''')

# Table for sentiment analysis results
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sentiment_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        sentiment_score INTEGER,
        date TEXT NOT NULL
    )
''')

# Commit changes and close connection
conn.commit()
conn.close()


def save_stock_data_to_db(ticker, data):
    conn = sqlite3.connect(DATABSE_PATH)
    cursor = conn.cursor()

    for index, row in data.iterrows():
        cursor.execute('''
            INSERT OR IGNORE INTO stock_prices (ticker, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ticker, index.strftime("%Y-%m-%d"), row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))

    conn.commit()
    conn.close()



def get_stock_data_from_db():
    conn = sqlite3.connect(DATABSE_PATH)
    df = pd.read_sql_query(f"SELECT * FROM stock_prices ORDER BY id ASC", conn)
    conn.close()
    return df


def delete_stock_data(ticker):
    conn = sqlite3.connect(DATABSE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stock_prices WHERE ticker=?", (ticker,))
    conn.commit()
    conn.close()


def truncate_stock_data():
    conn = sqlite3.connect(DATABSE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stock_prices")
    conn.commit()
    conn.close()


def save_sentiment_to_db(ticker, sentiment, sentiment_score):
    conn = sqlite3.connect(DATABSE_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO sentiment_analysis (ticker, sentiment, sentiment_score, date)
        VALUES (?, ?, ?, date('now'))
    ''', (ticker, sentiment, sentiment_score))

    conn.commit()
    conn.close()


def get_sentiment_data_from_db():
    conn = sqlite3.connect(DATABSE_PATH)
    df = pd.read_sql_query(f"SELECT * FROM sentiment_analysis ORDER BY id", conn)
    conn.close()
    return df


def delete_sentiment_data():
    conn = sqlite3.connect(DATABSE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sentiment_analysis")
    conn.commit()
    conn.close()


def clean_sentiment_data():
    conn = sqlite3.connect(DATABSE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sentiment_analysis WHERE ticker = ''")
    conn.commit()
    conn.close()