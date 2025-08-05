import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

def setup_tables():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            memory_type TEXT,
            title TEXT,
            content TEXT,
            tags TEXT[],
            importance INTEGER DEFAULT 1,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            memory_time TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task TEXT,
            remind_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed BOOLEAN DEFAULT FALSE
        );
    """)
    conn.commit()

def save_memory(title, content, tags=None, importance=1, memory_time=None):
    cursor.execute("""
        INSERT INTO memory (memory_type, title, content, tags, importance, memory_time)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('thought', title, content, tags or [], importance, memory_time))
    conn.commit()

def get_memories(limit=10):
    cursor.execute("SELECT title, content FROM memory ORDER BY timestamp DESC LIMIT %s", (limit,))
    return cursor.fetchall()

def add_reminder(task, remind_at):
    cursor.execute("INSERT INTO reminders (task, remind_at) VALUES (%s, %s)", (task, remind_at))
    conn.commit()

def get_reminders():
    cursor.execute("SELECT task, remind_at, completed FROM reminders ORDER BY remind_at ASC")
    return cursor.fetchall()