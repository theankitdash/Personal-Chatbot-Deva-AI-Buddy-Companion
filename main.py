from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import PromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
import gradio as gr
import psycopg2
from dotenv import load_dotenv
import os
import re

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# Initialize in-memory chat history
chat_history = InMemoryChatMessageHistory()

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
    temperature=0.2,  top_p=0.7,  
    max_completion_tokens=1024,    
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

memory_map = {}

# Buddy Response Function
def buddy_response(message, state=None):
    
    # --- Remember command ---
    if message.startswith("/remember"):
        content = message.replace("/remember", "").strip()
        
        if not content:
            return "⚠️ Please provide something to remember after /remember."

        tags = []
        importance = 3  # Default importance

        # Extract user-provided tags (#tag) and importance
        tag_matches = re.findall(r"#(\w+)", content)
        if tag_matches:
            tags = tag_matches
            content = re.sub(r"#\w+", "", content).strip()

        importance_match = re.search(r"importance=(\d+)", content, re.IGNORECASE)
        if importance_match:
            importance = int(importance_match.group(1))
            content = re.sub(r"importance=\d+", "", content, flags=re.IGNORECASE).strip()

        # Use LLM to generate title and suggested tags if missing
        llm_prompt = f"""
        Summarize the following text into a short title (max 50 characters) 
        and suggest 2-4 relevant tags.

        Text: "{content}"
        Respond in JSON format like:
        {{ "title": "Short title here", "tags": ["tag1", "tag2"] }}
        """
        llm_response = LLM.invoke([{"role": "user", "content": llm_prompt}])
        
        # Parse LLM response
        import json
        try:
            llm_data = json.loads(llm_response.content)
            title = llm_data.get("title", content[:50])
            suggested_tags = llm_data.get("tags", [])
            # Combine user tags and LLM suggested tags
            tags = list(set(tags + suggested_tags))
        except Exception:
            # Fallback if LLM response is not valid JSON
            title = content[:50]

        # Save memory in DB
        save_memory(title=title, content=content, tags=tags, importance=importance)
        return f"✅ Memory saved! Title: '{title}', Tags: {tags}, Importance: {importance}"
    
    # --- List command ---
    elif message.startswith("/list"):
        cursor.execute("SELECT memory_id, title, tags, importance, memory_time FROM memory ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        if not rows:
            return "No memories found."

        # Update memory_map
        memory_map = {str(idx): row[0] for idx, row in enumerate(rows, start=1)}

        # Create numbered list
        response = "🧠 Your Memories:\n"
        for idx, row in enumerate(rows, start=1):
            _, title, tags, importance, memory_time = row
            tags_str = ",".join(tags) if tags else "None"
            response += f"{idx}. {title} | Tags: {tags_str} | Importance: {importance}\n"
        return response

    # --- Update command ---
    elif message.startswith("/update"):
        match = re.match(r"/update\s+(\d+)\s+(.+)", message)
        if not match:
            return "⚠️ Invalid format. Use: /update <number> <new content>"

        number, new_content = match.groups()
        memory_id = memory_map.get(number)
        if not memory_id:
            return "⚠️ Invalid memory number. Please use /list to see numbers."

        tags = []
        importance = None

        # Extract tags and importance
        tag_matches = re.findall(r"#(\w+)", new_content)
        if tag_matches:
            tags = tag_matches
            new_content = re.sub(r"#\w+", "", new_content).strip()

        importance_match = re.search(r"importance=(\d+)", new_content, re.IGNORECASE)
        if importance_match:
            importance = int(importance_match.group(1))
            new_content = re.sub(r"importance=\d+", "", new_content, flags=re.IGNORECASE).strip()

        # Use LLM to generate updated title and suggested tags
        llm_prompt = f"""
        Summarize the following text into a short title (max 50 characters) 
        and suggest 2-4 relevant tags.

        Text: "{new_content}"
        Respond in JSON format like:
        {{ "title": "Short title here", "tags": ["tag1", "tag2"] }}
        """
        llm_response = LLM.invoke([{"role": "user", "content": llm_prompt}])

        try:
            llm_data = json.loads(llm_response.content)
            title = llm_data.get("title", new_content[:50])
            suggested_tags = llm_data.get("tags", [])
            tags = list(set(tags + suggested_tags)) if tags else suggested_tags
        except Exception:
            title = new_content[:50]

        # Build update query
        update_fields = {"content": new_content, "title": title, "updated_at": "CURRENT_TIMESTAMP"}
        if tags:
            update_fields["tags"] = tags
        if importance is not None:
            update_fields["importance"] = importance

        set_clause = ", ".join([f"{k} = %s" if k != "updated_at" else f"{k} = {v}" for k, v in update_fields.items()])
        values = [v for k, v in update_fields.items() if k != "updated_at"]

        cursor.execute(f"UPDATE memory SET {set_clause} WHERE memory_id = %s", (*values, memory_id))
        conn.commit()

        return f"✅ Memory {number} updated! Title: '{title}', Tags: {tags}, Importance: {importance or 'unchanged'}"

    # --- Delete command ---
    elif message.startswith("/delete"):
        match = re.match(r"/delete\s+(\d+)", message)
        if not match:
            return "⚠️ Invalid format. Use: /delete <number>"
        number = match.group(1)
        memory_id = memory_map.get(number)
        if not memory_id:
            return "⚠️ Invalid memory number. Please use /list to see numbers."

        cursor.execute("DELETE FROM memory WHERE memory_id = %s", (memory_id,))
        conn.commit()
        return f"✅ Memory {number} deleted successfully!"

    # Normal chat flow
    chat_history.add_user_message(message)

    memory_text = "\n".join([f"{msg.type}: {msg.content}" for msg in chat_history.messages])

    system_prompt = chat_prompt.format_prompt(
        name="Ankit Dash",
        date_of_birth='08-11-2000',
        gender="Male",
        memory=memory_text,
        message=message
    )

    response = LLM.invoke([
        {"role": "system", "content": system_prompt.to_string()},
        {"role": "user", "content": message}
    ])

    chat_history.add_ai_message(response.content)

    return response.content

# Create Chat Interface
chatbot = gr.ChatInterface(    
    fn=buddy_response,    
    title="Deva",    
    description="Always for you Buddy!",    
    theme="soft",  # Clean soft colors
    type="messages"
)

# Launch Gradio app
if __name__ == "__main__":
    chatbot.launch(share=True) 