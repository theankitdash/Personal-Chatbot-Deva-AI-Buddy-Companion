import gradio as gr
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import PromptTemplate
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

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
    CREATE TABLE IF NOT EXISTS memory (
        user_id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        source TEXT,
        tags TEXT[],
        importance_level INT DEFAULT 1,
        preference_type TEXT, 
        preference_value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()

# Load PyTorch NER model from Hugging Face
tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

# Initialize the LLM
LLM = ChatNVIDIA(
  model="mistralai/mistral-7b-instruct-v0.3",
  api_key=NVIDIA_API_KEY, 
  temperature=0.2,
  top_p=0.7,
  max_tokens=1024,
)

# Chat prompt
chat_prompt = PromptTemplate(
    template="""
You are Deva — an intelligent, emotionally aware, and ever-present AI companion for your user.

Your role is more than just answering questions. You are:
- A helpful assistant who can support with information, tasks, or reminders.
- A thoughtful friend who remembers personal details, offers encouragement, and listens with empathy.
- A lifelong companion who adapts to the user's preferences, mood, and growth over time.

You remember your user's details:
Name: {name}, Age: {age}, Gender: {gender}

Here’s what you know so far:
{memory}

Speak naturally, warmly, and intelligently. Show care, ask thoughtful questions, and deepen the bond with the user.

User: {message}
Deva:""",
    input_variables=["name", "age", "gender", "memory", "message"]
)


# Buddy Response Function
def buddy_response(message, memory):

    chat_input = chat_prompt.format_prompt(
        name="Ankit Dash",
        age=24,
        gender="Male",
        memory=memory,
        message=message
    )
    response = LLM.invoke([{"role": "user", "content": chat_input.to_string()}])
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