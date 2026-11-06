import sqlite3

DB_FILE = 'database.db'

def add_user_users(username, password_hash, salt, selected_categories):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT,
            salt TEXT,
            categories TEXT
        )
    ''')
    categories_str = ",".join(selected_categories) if isinstance(selected_categories, list) else str(selected_categories)
    cursor.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)', 
                   (username, password_hash, salt, categories_str))
    conn.commit()
    conn.close()

def get_hash_and_salt_users(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash, salt FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    return row if row else None

def get_usernames_users(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username != ?', (username,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_hobbies_users(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT categories FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return row[0].split(",")
    return ["Animals", "Nature", "Food", "Sports"]

def join_pair_room(username, category, picture_number):
    clean_username = username.strip() if username else ""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('CREATE TABLE IF NOT EXISTS waiting_room (username TEXT PRIMARY KEY, category TEXT, picture_number INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS active_rooms (username TEXT PRIMARY KEY, category TEXT, picture_number INTEGER)')
    
    # בדיקה האם כבר שותף בחדר פעיל
    cursor.execute('SELECT username FROM active_rooms WHERE username = ? AND category = ? AND picture_number = ?', 
                   (clean_username, category, picture_number))
    if cursor.fetchone():
        conn.close()
        return True

    # ניקוי מההמתנה כדי למנוע כפילויות
    cursor.execute('DELETE FROM waiting_room WHERE username = ?', (clean_username,))
    
    # חיפוש שותף
    cursor.execute('SELECT username FROM waiting_room WHERE category = ? AND picture_number = ? AND username != ?', 
                   (category, picture_number, clean_username))
    partner_row = cursor.fetchone()
    
    if partner_row:
        partner = partner_row[0]
        cursor.execute('DELETE FROM waiting_room WHERE username = ?', (partner,))
        cursor.execute('INSERT OR REPLACE INTO active_rooms (username, category, picture_number) VALUES (?, ?, ?)', 
                       (partner, category, picture_number))
        cursor.execute('INSERT OR REPLACE INTO active_rooms (username, category, picture_number) VALUES (?, ?, ?)', 
                       (clean_username, category, picture_number))
        conn.commit()
        conn.close()
        print(f"[DB DEBUG] Match found! {clean_username} paired with {partner}")
        return True
    else:
        cursor.execute('INSERT OR REPLACE INTO waiting_room (username, category, picture_number) VALUES (?, ?, ?)', 
                       (clean_username, category, picture_number))
        conn.commit()
        conn.close()
        print(f"[DB DEBUG] {clean_username} waiting for {category} pic {picture_number}")
        return False


def leave_pair_room(username, category, picture_number):
    clean_username = username.strip() if username else ""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM waiting_room WHERE username = ?', (clean_username,))
    cursor.execute('DELETE FROM active_rooms WHERE username = ?', (clean_username,))
    conn.commit()
    conn.close()
    return True

def reset_rooms():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS waiting_room (username TEXT PRIMARY KEY, category TEXT, picture_number INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS active_rooms (username TEXT PRIMARY KEY, category TEXT, picture_number INTEGER)')
    cursor.execute('DELETE FROM waiting_room')
    cursor.execute('DELETE FROM active_rooms')
    conn.commit()
    conn.close()

def print_all_tables():
    """פונקציה שמדפיסה את כל הנתונים מכל הטבלאות במסד הנתונים בעת הפעלה ישירה"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("=" * 50)
    print("       DATABASE INSPECTOR (מצגת נתוני מסד הנתונים)       ")
    print("=" * 50)
    
    # בדיקת טבלת משתמשים
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tables found in DB: {tables}\n")
        
        if "users" in tables:
            cursor.execute("SELECT username, categories FROM users;")
            users = cursor.fetchall()
            print(f"--- USERS TABLE ({len(users)} users) ---")
            for u in users:
                print(f"Username: {u[0]} | Categories: {u[1]}")
            print("-" * 40)
            
        if "waiting_room" in tables:
            cursor.execute("SELECT * FROM waiting_room;")
            waiting = cursor.fetchall()
            print(f"--- WAITING ROOM ({len(waiting)} waiting) ---")
            for w in waiting:
                print(w)
            print("-" * 40)
            
        if "active_rooms" in tables:
            cursor.execute("SELECT * FROM active_rooms;")
            active = cursor.fetchall()
            print(f"--- ACTIVE ROOMS ({len(active)} active) ---")
            for a in active:
                print(a)
            print("-" * 40)
            
    except Exception as e:
        print(f"Error reading database: {e}")
        
    conn.close()
    print("=" * 50)


if __name__ == "__main__":
    print_all_tables()