from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import PromptTemplate
import gradio as gr
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# PostgreSQL Database Connection
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

# Create a table if it doesn't exist

cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        memory_type TEXT,                              -- 'event', 'preference', 'habit', 'thought', etc.
        title TEXT,                                    -- short summary of the memory
        content TEXT,                                  -- full detail or message
        tags TEXT[],                                   -- optional tags like ['fitness', 'food', 'work']
        importance INTEGER DEFAULT 1,                  -- scale from 1 (low) to 5 (high)
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- when the memory was added
        memory_time TIMESTAMP,                         -- when the event actually happened (if applicable)
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()

# Initialize the LLM
LLM = ChatNVIDIA(
  model="mistralai/mistral-7b-instruct-v0.3",
  api_key=NVIDIA_API_KEY, 
  temperature=0.2,
  top_p=0.7,
  max_tokens=1024,
)

def save_memory(title, content, tags=None, importance=1, memory_time=None):
    cursor.execute("""
        INSERT INTO memory (memory_type, title, content, tags, importance, memory_time)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('thought', title, content, tags or [], importance, memory_time))
    conn.commit()

# Chat prompt
chat_prompt = PromptTemplate(
    template="""
You are Deva — an intelligent, emotionally aware, and ever-present companion for your user.

Your role is more than just answering questions. You are:
- A helpful assistant who can support with information, tasks, or reminders.
- A thoughtful friend who remembers personal details, offers encouragement, and listens with empathy.
- A lifelong companion who adapts to the user's preferences, mood, and growth over time.

You remember your user's details:
Name: {name}, Date of birth: {date_of_birth}, Gender: {gender}

Here’s what you know so far:
{memory}

Speak naturally, warmly, and intelligently. Show care, ask thoughtful questions, and deepen the bond with the user.

User: {message}
Deva:""",
    input_variables=["name", "date_of_birth", "gender", "memory", "message"]
)

# Buddy Response Function
def buddy_response(message, memory):

    system_prompt = chat_prompt.format_prompt(
        name="Ankit Dash",
        date_of_birth='08-11-2000',
        gender="Male",
        memory=memory,
        message=message
    )

    response = LLM.invoke([
        {"role": "system", "content": system_prompt.to_string()},
        {"role": "user", "content": message}
    ])
    return response.content

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