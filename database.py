import sqlite3
from datetime import datetime, timedelta

def get_db():
    conn = sqlite3.connect('reaction_bot.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        added_by INTEGER,
        added_date TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS premium (
        user_id INTEGER PRIMARY KEY,
        plan TEXT,
        start_date TEXT,
        end_date TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        days INTEGER,
        price REAL,
        features TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS reactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        channel_id INTEGER,
        emojis TEXT,
        count INTEGER DEFAULT 1)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_username TEXT,
        channel_id INTEGER,
        added_by INTEGER)''')
    
    # Insert default plans if empty
    cursor.execute("SELECT COUNT(*) FROM plans")
    if cursor.fetchone()[0] == 0:
        default_plans = [
            ("Basic", 30, 49, "1 Channel Auto Reaction"),
            ("Pro", 90, 99, "3 Channels Auto Reaction"),
            ("Premium", 365, 299, "Unlimited Channels Auto Reaction")
        ]
        cursor.executemany("INSERT INTO plans (name, days, price, features) VALUES (?,?,?,?)", default_plans)
    
    conn.commit()
    conn.close()

# Helper functions
def is_admin(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None or user_id == int(os.environ.get("OWNER_ID", "0"))

def is_premium(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM premium WHERE user_id=? AND end_date > ?", 
                   (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    result = cursor.fetchone()
    conn.close()
    return result is not None
