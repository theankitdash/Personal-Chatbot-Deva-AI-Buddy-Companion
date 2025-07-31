from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableMap, RunnableSequence
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_tool_calling_agent
from langchain.agents.agent import RunnableAgent
import gradio as gr
import psycopg2
from dotenv import load_dotenv
import os
import datetime
import re

# --- Load Environment Variables ---
load_dotenv()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# --- PostgreSQL Setup ---
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cursor = conn.cursor()

# --- Create Tables ---
cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        chat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        role TEXT CHECK (role IN ('human', 'ai')) NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)


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

# --- DB Functions ---
def save_chat_message(role, message):
    cursor.execute("""
        INSERT INTO chat_history (role, message) VALUES (%s, %s)
    """, (role, message))
    conn.commit()

def load_chat_history(limit=20):
    cursor.execute("""
        SELECT role, message FROM chat_history
        ORDER BY timestamp ASC
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()
    messages = []
    for role, msg in rows:
        if role == 'human':
            messages.append(HumanMessage(content=msg))
        elif role == 'ai':
            messages.append(AIMessage(content=msg))
    return messages
    
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

# --- Tools ---
@tool
def memory_tool(input: str) -> str:
    """Save important info to memory if user requests."""
    if 'remember' in input.lower() or 'important' in input.lower():
        title = input[:50]
        save_memory(title, input)
        return "Saved to memory!"
    return "No memory saved."

@tool
def reminder_tool(input: str) -> str:
    """Set a reminder if user requests."""
    match = re.search(r"remind me to (.+) at ([\d\w :,-]+)", input, re.I)
    if match:
        task = match.group(1)
        time_str = match.group(2)
        try:
            remind_at = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except Exception:
            remind_at = datetime.datetime.now() + datetime.timedelta(hours=1)
        add_reminder(task, remind_at)
        return f"Reminder set for '{task}' at {remind_at}"
    return "No reminder set."

tools = [memory_tool, reminder_tool]

# --- LLM Setup ---
LLM = ChatNVIDIA(
    model="mistralai/mistral-7b-instruct-v0.3",
    api_key=NVIDIA_API_KEY,
    temperature=0.2,
    top_p=0.7,
    max_completion_tokens=1024,
)

# --- Prompt Template ---
def get_memory_text():
    mems = get_memories()
    return "\n".join([f"{t}: {c}" for t, c in mems])

prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are Deva — an intelligent, emotionally aware, and ever-present companion for your user.
Your role is more than just answering questions. You are:
- A helpful assistant who can support with information, tasks, or reminders.
- A thoughtful friend who remembers personal details, offers encouragement, and listens with empathy.
- A lifelong companion who adapts to the user's preferences, mood, and growth over time.
You remember your user's details:
Name: Ankit Dash, DOB: 08-11-2000, Gender: Male
Here’s what you know so far:
{memory}
Speak naturally, warmly, and intelligently. Show care, ask thoughtful questions, and deepen the bond with the user.
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# --- Create Runnable Agent Chain ---
def create_agent_runnable():
    agent_runnable: RunnableAgent = create_tool_calling_agent(
        llm=LLM,
        tools=tools,
        prompt=prompt
    )

    full_chain = RunnableMap({
        "memory": lambda _: get_memory_text(),
        "chat_history": lambda _: load_chat_history(limit=20),
        "intermediate_steps": lambda _: [],
        "input": lambda x: x["input"]
    }) | agent_runnable

    return full_chain

agent_chain = create_agent_runnable()

# --- Gradio App ---
def gradio_chat_fn(message, history=None):
    save_chat_message("human", message)
    result = agent_chain.invoke({"input": message})
    response = result.return_values["output"]
    save_chat_message("ai", response)
    return {"role": "assistant", "content": response}

with gr.Blocks() as app:
    gr.Markdown("# Deva: Your Buddy Companion")
    chatbox = gr.ChatInterface(
        fn=gradio_chat_fn,
        title="Deva",
        description="Always for you Buddy!",
        theme="soft",
        type="messages"
    )

if __name__ == "__main__":
    app.launch(share=True)
