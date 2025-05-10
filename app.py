import streamlit as st
import sqlite3
import hashlib
import re
import pandas as pd
from logic import Wuzzle
from word_generator import WordGenerator
from ai_solver import AISolver
from archive import init_archive_db, archive_guess, get_user_archive

if 'word_generator' not in st.session_state:
    st.session_state.word_generator = WordGenerator()

if 'ai_solver' not in st.session_state:
    st.session_state.ai_solver = AISolver(st.session_state.word_generator.valid_words)

if 'game' not in st.session_state:
    new_word = st.session_state.word_generator.generate_word()
    st.session_state.game = Wuzzle(new_word)

if 'guess_history' not in st.session_state:
    st.session_state.guess_history = []

if 'game_over' not in st.session_state:
    st.session_state.game_over = False

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'username' not in st.session_state:
    st.session_state.username = ""

if 'auth_page' not in st.session_state:
    st.session_state.auth_page = "login"

def init_db():
    conn = sqlite3.connect('wuzzle_users.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users
    (username TEXT PRIMARY KEY, password TEXT, games_played INTEGER, games_won INTEGER)
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard
    (username TEXT PRIMARY KEY, 
     games_played INTEGER DEFAULT 0, 
     games_won INTEGER DEFAULT 0, 
     score INTEGER DEFAULT 0,
     last_update DATETIME DEFAULT CURRENT_TIMESTAMP,
     FOREIGN KEY (username) REFERENCES users(username))
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect('wuzzle_users.db')
    c = conn.cursor()
    
    try:
        hashed_pass = hash_password(password)
        c.execute("INSERT INTO users (username, password, games_played, games_won) VALUES (?, ?, 0, 0)", 
                 (username, hashed_pass))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    
    conn.close()
    return result

def authenticate_user(username, password):
    conn = sqlite3.connect('wuzzle_users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0] == hash_password(password):
        return True
    return False

def update_user_stats(username, won=False):
    conn = sqlite3.connect('wuzzle_users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET games_played = games_played + 1 WHERE username = ?", (username,))
    if won:
        c.execute("UPDATE users SET games_won = games_won + 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    
    update_leaderboard(username, won)

def get_user_stats(username):
    conn = sqlite3.connect('wuzzle_users.db')
    c = conn.cursor()
    c.execute("SELECT games_played, games_won FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {"games_played": result[0], "games_won": result[1]}
    return {"games_played": 0, "games_won": 0}

def update_leaderboard(username, won=False):
    conn = sqlite3.connect('wuzzle_users.db')
    c = conn.cursor()
    
    score_to_add = 10 if won else 1
    
    c.execute("SELECT username FROM leaderboard WHERE username = ?", (username,))
    user_exists = c.fetchone()
    
    if user_exists:
        c.execute("""
            UPDATE leaderboard 
            SET games_played = games_played + 1, 
                games_won = games_won + CASE WHEN ? THEN 1 ELSE 0 END,
                score = score + ?,
                last_update = CURRENT_TIMESTAMP
            WHERE username = ?
        """, (won, score_to_add, username))
    else:
        c.execute("""
            INSERT INTO leaderboard (username, games_played, games_won, score)
            VALUES (?, 1, ?, ?)
        """, (username, 1 if won else 0, score_to_add))
    
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    conn = sqlite3.connect('wuzzle_users.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT username, games_played, games_won, score, last_update
        FROM leaderboard
        ORDER BY score DESC
        LIMIT ?
    """, (limit,))
    
    results = c.fetchall()
    conn.close()
    
    return results

def restart_game():
    new_word = st.session_state.word_generator.generate_word()
    st.session_state.game = Wuzzle(new_word)
    st.session_state.guess_history = []
    st.session_state.game_over = False

init_db()
init_archive_db()      

def show_login_page():
    st.title("🔐 Login to Wuzzle")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Login"):
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with col2:
        if st.button("Create Account"):
            st.session_state.auth_page = "signup"
            st.rerun()

def show_signup_page():
    st.title("📝 Create Wuzzle Account")
    
    username = st.text_input("Choose Username")
    password = st.text_input("Choose Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Create Account"):
            if not username or not password:
                st.error("Username and password are required.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
                st.error("Username must be 3-20 characters and contain only letters, numbers, and underscores.")
            else:
                if create_user(username, password):
                    st.success("Account created successfully!")
                    st.session_state.auth_page = "login"
                    st.rerun()
                else:
                    st.error("Username already exists. Please choose another.")
    
    with col2:
        if st.button("Back to Login"):
            st.session_state.auth_page = "login"
            st.rerun()

def show_game_page():
    st.title("🟨🟩 Wuzzle Word Game")
    
    tab1, tab2 = st.tabs(["Game", "🏆 Leaderboard"])
    
    with tab1:
        user_stats = get_user_stats(st.session_state.username)
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.info(f"👤 {st.session_state.username}")
        
        with col2:
            st.info(f"🎮 Games: {user_stats['games_played']}")
        
        with col3:
            win_rate = 0 if user_stats['games_played'] == 0 else round((user_stats['games_won'] / user_stats['games_played']) * 100)
            st.info(f"🏆 Win rate: {win_rate}%")
        
        with st.sidebar:
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.rerun()
        
        with st.expander("📋 Game Rules"):
            st.markdown("""
            ### How to Play Wuzzle:
            
            1. **Objective:** Guess the secret 5-letter word within 6 attempts.
            
            2. **Making a Guess:** Enter a valid 5-letter word and submit your guess.
            
            3. **Feedback:**
               - 🟩 Green: Letter is correct and in the right position
               - 🟨 Yellow: Letter is in the word but in the wrong position
               - ⬜ Gray: Letter is not in the word
            
            4. **Strategy:** Use the feedback from previous guesses to narrow down possibilities.
            
            5. **Winning:** Guess the correct word within 6 attempts to win!
            
            6. **Losing:** If you don't guess the word within 6 attempts, the game is over and the secret word will be revealed.
            """)

        guess_input = st.text_input(
            "Enter your guess (5-letter word):",
            max_chars=5,
            disabled=st.session_state.game_over,
            key='guess_input'
        )

        if st.button("Submit Guess", disabled=st.session_state.game_over):
            if len(guess_input) != st.session_state.game.max_word_length:
                st.warning(f"Guess must be exactly {st.session_state.game.max_word_length} letters.")
            elif not st.session_state.game.can_attempt():
                st.warning("No attempts remaining or game already solved!")
            else:
                st.session_state.game.attempt(guess_input)
                result = st.session_state.game.guess(guess_input.upper())

                result_line = ""
                for letter in result:
                    color = "🟩" if letter.in_position else "🟨" if letter.in_word else "⬜"
                    result_line += f"{color} {letter.character.upper()} "

                st.session_state.guess_history.append(result_line)
                archive_guess(st.session_state.username, guess_input.upper(), st.session_state.game.secret)

                if st.session_state.game.is_solved():
                    st.balloons()
                    st.success("🎉 Correct! You've solved the puzzle!")
                    st.session_state.game_over = True
                    update_user_stats(st.session_state.username, won=True)
                elif not st.session_state.game.can_attempt():
                    st.error(f"Game Over! The word was {st.session_state.game.secret}")
                    st.session_state.game_over = True
                    update_user_stats(st.session_state.username, won=False)

        if st.session_state.game_over:
            if st.button("Play Again"):
                restart_game()
                st.rerun()

        st.subheader("Your Guesses:")
        for line in st.session_state.guess_history:
            st.write(line)

        st.markdown(f"**Attempts Remaining:** {st.session_state.game.remaining_attempts()}")
        if st.session_state.game.attempts:
            st.markdown(f"**Attempts Made:** {', '.join(st.session_state.game.attempts)}")

        st.divider()
        st.header("🧠 AI Solver Lab")

        target_word = st.text_input(
            "Enter a 5-letter word for the AI to solve:",
            max_chars=5,
            key='target_word'
        )

        if st.button("Run AI Solver"):
            if len(target_word) != 5:
                st.warning("Please enter exactly 5 letters")
            else:
                st.session_state.ai_solver.reset()
                solution = st.session_state.ai_solver.solve(target_word.upper())
                
                st.subheader(f"🧠 AI Solution for: {target_word.upper()}")
                
                for i, step in enumerate(solution, 1):
                    with st.expander(f"Move {i}: {step['guess']}", expanded=i==1):
                        cols = st.columns(2)
                        cols[0].metric("Possible Words Remaining", step['remaining'])
                        
                        explanation_lines = step['explanation'].split('\n')
                        for line in explanation_lines:
                            if line.startswith("🎯"):
                                st.success(line)
                            elif line.startswith("📊"):
                                st.markdown(f"**{line}**")
                            elif line.startswith("🏆"):
                                st.markdown(f"**{line}**")
                            elif line.startswith(("1.", "2.", "3.")):
                                parts = line.split("(")
                                st.markdown(f"**{parts[0]}**")
                                st.caption(parts[1].replace(")", ""))
                            elif ":" in line and not line.startswith(" "):
                                key, value = line.split(":", 1)
                                st.markdown(f"**{key}:** {value}")
                            else:
                                st.write(line)
                        
                        if step['guess'] == target_word.upper():
                            st.balloons()
                            st.success(f"✅ Solved in {i} moves!")

    with tab2:
        st.header("🏆 Leaderboard")
        leaderboard_data = get_leaderboard(limit=20)
        
        if leaderboard_data:
            leaderboard_df = pd.DataFrame(
                leaderboard_data, 
                columns=["Player", "Games", "Wins", "Score", "Last Game"]
            )
            
            leaderboard_df["Win Rate"] = leaderboard_df.apply(
                lambda row: f"{round((row['Wins'] / row['Games']) * 100)}%" if row['Games'] > 0 else "0%", 
                axis=1
            )
            
            leaderboard_df["Last Game"] = pd.to_datetime(leaderboard_df["Last Game"]).dt.strftime("%Y-%m-%d")
            
            leaderboard_df = leaderboard_df[["Player", "Score", "Games", "Wins", "Win Rate", "Last Game"]]
            
            if len(leaderboard_df) >= 1:
                leaderboard_df.loc[0, "Player"] = "🥇 " + leaderboard_df.loc[0, "Player"]
            if len(leaderboard_df) >= 2:
                leaderboard_df.loc[1, "Player"] = "🥈 " + leaderboard_df.loc[1, "Player"]
            if len(leaderboard_df) >= 3:
                leaderboard_df.loc[2, "Player"] = "🥉 " + leaderboard_df.loc[2, "Player"]
                
            st.dataframe(
                leaderboard_df,
                height=400,
                use_container_width=True,
                hide_index=True
            )
            
            current_user_rank = None
            for i, player in enumerate(leaderboard_data):
                if player[0] == st.session_state.username:
                    current_user_rank = i + 1
                    break
            
            if current_user_rank:
                st.info(f"Your current rank: #{current_user_rank} of {len(leaderboard_data)}")
            
        else:
            st.info("Be the first to join the leaderboard by playing a game!")

def main():
    if not st.session_state.authenticated:
        if st.session_state.auth_page == "login":
            show_login_page()
        else:
            show_signup_page()
    else:
        show_game_page()

if __name__ == "__main__":
    main()