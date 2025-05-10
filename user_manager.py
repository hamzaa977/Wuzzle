import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "C:\Codes\Wuzz\wuzzle_users.db"

def init_database():
    """Initialize all database tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    #authentication
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        games_played INTEGER DEFAULT 0,
        games_won INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Leaderboard
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        username TEXT PRIMARY KEY,
        games_played INTEGER DEFAULT 0,
        games_won INTEGER DEFAULT 0,
        score INTEGER DEFAULT 0,
        last_update DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    ''')
    
    # Archive
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        word TEXT NOT NULL,
        guesses TEXT,
        won BOOLEAN DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    """Create a new user"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                      (username, hashed_password))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    finally:
        conn.close()
    
    return result

def authenticate_user(username, password):
    """Verify user credentials"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] == hash_password(password):
        return True
    return False

def update_user_stats(username, won=False):
    """Update user statistics after a game"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE users SET games_played = games_played + 1 WHERE username = ?", (username,))
    if won:
        cursor.execute("UPDATE users SET games_won = games_won + 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    
    # Also update the leaderboard
    update_leaderboard(username, won)

def update_leaderboard(username, won=False):
    """Update the leaderboard after a game"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Calculate score - simple version: 10 points per win, 1 point for playing
    score_to_add = 10 if won else 1
    
    # Check if user exists in leaderboard
    cursor.execute("SELECT username FROM leaderboard WHERE username = ?", (username,))
    user_exists = cursor.fetchone()
    
    if user_exists:
        # Update existing user
        cursor.execute("""
            UPDATE leaderboard 
            SET games_played = games_played + 1, 
                games_won = games_won + CASE WHEN ? THEN 1 ELSE 0 END,
                score = score + ?,
                last_update = CURRENT_TIMESTAMP
            WHERE username = ?
        """, (won, score_to_add, username))
    else:
        # Add new user to leaderboard
        cursor.execute("""
            INSERT INTO leaderboard (username, games_played, games_won, score)
            VALUES (?, 1, ?, ?)
        """, (username, 1 if won else 0, score_to_add))
    
    conn.commit()
    conn.close()

def get_user_stats(username):
    """Get user stats"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT games_played, games_won FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"games_played": result[0], "games_won": result[1]}
    return {"games_played": 0, "games_won": 0}

def archive_game(username, word, guesses="", won=False):
    """Archive a game result"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO archive (username, word, guesses, won)
        VALUES (?, ?, ?, ?)
    """, (username, word.upper(), guesses, won))
    
    conn.commit()
    conn.close()

def get_user_archive(username):
    """Get user's game history"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT word, guesses, won, timestamp 
        FROM archive 
        WHERE username = ? 
        ORDER BY timestamp DESC
    """, (username,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_leaderboard(limit=10):
    """Get top users by score"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, games_played, games_won, score, last_update
        FROM leaderboard
        ORDER BY score DESC
        LIMIT ?
    """, (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results