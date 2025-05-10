import sqlite3
from datetime import datetime

DB_NAME = "wuzzle_users.db"

def init_archive_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            word TEXT NOT NULL,
            realWord TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def archive_guess(username, word, realWord):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO archive (username, word, realWord) VALUES (?, ?, ?)", (username, word.upper(), realWord.upper()))
    conn.commit()
    conn.close()

def get_user_archive(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT word, timestamp FROM archive WHERE username = ? ORDER BY timestamp DESC", (username,))
    results = c.fetchall()
    conn.close()
    return results