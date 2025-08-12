import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def connect_db():
    conn = await asyncpg.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

    await conn.execute("""

        CREATE TABLE IF NOT EXISTS user_details (
            name TEXT PRIMARY KEY,
            embedding_path TEXT 
        );

    """)

    await conn.execute("""

        CREATE TABLE IF NOT EXISTS memory (
            memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            memory_type TEXT NOT NULL,
            title TEXT,
            content TEXT,
            tags TEXT[],
            importance INTEGER DEFAULT 1,

            embedding_id TEXT,  -- ID or filename for FAISS vector

            memory_time TIMESTAMP,
            remind_at TIMESTAMP,
            repeat_interval INTERVAL,
            completed BOOLEAN DEFAULT FALSE,
            priority INTEGER DEFAULT 1,

            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

    """)
    return conn
