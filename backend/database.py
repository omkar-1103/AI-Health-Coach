import sqlite3
import bcrypt
import json

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            profile TEXT
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password, profile_data=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if user exists
    c.execute('SELECT username FROM users WHERE username = ?', (username,))
    if c.fetchone():
        conn.close()
        return False, "Username already exists"
    
    # Hash password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Profile to JSON
    p_json = json.dumps(profile_data) if profile_data else "{}"
    
    try:
        c.execute('INSERT INTO users (username, password, profile) VALUES (?, ?, ?)', 
                  (username, hashed, p_json))
        conn.commit()
        conn.close()
        return True, "User registered successfully"
    except Exception as e:
        conn.close()
        return False, str(e)

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('SELECT password, profile FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        stored_hash = result[0]
        profile_json = result[1]
        
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True, json.loads(profile_json)
    
    return False, None

def update_profile(username, profile_data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    p_json = json.dumps(profile_data)
    c.execute('UPDATE users SET profile = ? WHERE username = ?', (p_json, username))
    conn.commit()
    conn.close()
