import gradio as gr
from langchain_ollama.llms import OllamaLLM
import psycopg2

# PostgreSQL Database Connection
conn = psycopg2.connect(
    dbname="buddy_db",
    user="postgres",
    password="Chiku@4009",
    host="localhost",  
    port="5432"        
)
cursor = conn.cursor()

# Create a table if it doesn't exist

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        age INT,
        gender TEXT,
        preferences JSONB
    );
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES user_profile(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        source TEXT,
        tags TEXT[],
        importance_level INT DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()

# Initialize the LLM
LLM = OllamaLLM(model="phi:latest")

# Buddy Response Function
def buddy_response(message, history):
    # Simple basic response
    response = LLM.invoke(message)
    return response

# Create Chat Interface
chatbot = gr.ChatInterface(
    fn=buddy_response,
    title="Deva",
    description="Always for you Buddy!",
    theme="soft",  # Clean soft colors
)

# Launch Gradio app
if __name__ == "__main__":
    chatbot.launch(share=True) 