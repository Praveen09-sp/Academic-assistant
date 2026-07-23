import sqlite3
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Name of the SQL database file that will be created automatically
SQLALCHEMY_DATABASE_URL = "sqlite:///./academic.db"

# 2. Create the SQL engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Create a SessionLocal class for handling database requests
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class that our database tables will inherit from
Base = declarative_base()

# Ensure this matches the DB name used in your main.py
DB_NAME = "study_companion.db" 
DEFAULT_USER = "admin"  # Hardcoded single user for your BCA project

def init_db():
    """Initializes the database with history and feedback tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. History Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS history 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       user_id TEXT, 
                       filename TEXT, 
                       summary TEXT, 
                       content TEXT,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 2. Feedback Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       user_id TEXT,
                       history_id INTEGER, 
                       rating INTEGER, 
                       comment TEXT, 
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY(history_id) REFERENCES history(id))''')
    
    conn.commit()
    conn.close()
    print("✅ Database Initialized.")

def save_to_history(filename, study_data_json):
    """
    Saves the full study suite tagged to the 'admin' user.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        data_dict = json.loads(study_data_json)
        summary = data_dict.get("summary", "No summary available")
        
        # We now use DEFAULT_USER instead of passing a dynamic username
        cursor.execute("INSERT INTO history (user_id, filename, summary, content) VALUES (?, ?, ?, ?)",
                       (DEFAULT_USER, filename, summary, study_data_json))
        conn.commit()
        last_id = cursor.lastrowid
        print(f"✅ Saved Session {last_id} for user: {DEFAULT_USER}")
        return last_id 
    except Exception as e:
        print(f"❌ Database Insert Error: {e}")
        return 0
    finally:
        conn.close()

def get_all_history():
    """
    Fetches the last 15 entries for the 'admin' user.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Filtered to only show admin data
        cursor.execute("""
            SELECT id, filename, summary, content 
            FROM history 
            WHERE user_id = ? 
            ORDER BY id DESC LIMIT 15
        """, (DEFAULT_USER,))
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error fetching history list: {e}")
        return []
    finally:
        conn.close()

def save_feedback(history_id, rating, comment):
    """Saves feedback tagged to the 'admin' user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO feedback (user_id, history_id, rating, comment) VALUES (?, ?, ?, ?)",
                       (DEFAULT_USER, history_id, rating, comment))
        conn.commit()
    except Exception as e:
        print(f"❌ Error saving feedback: {e}")
    finally:
        conn.close()

# Keep get_history_by_id simple as it uses the Primary Key (ID)
def get_history_by_id(history_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT filename, summary, content FROM history WHERE id = ?", (history_id,))
        return cursor.fetchone() 
    except Exception as e:
        print(f"❌ Error fetching specific history: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()