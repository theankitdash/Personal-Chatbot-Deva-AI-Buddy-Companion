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

# Chat prompt after onboarding
chat_prompt = PromptTemplate(
    template="""
You are Deva, a friendly and intelligent AI buddy. You remember your user's details:
Name: {name}, Age: {age}, Gender: {gender}.

Talk to the user naturally, respond helpfully, and ask thoughtful follow-up questions when possible.

User: {message}
Deva:""",
    input_variables=["name", "age", "gender", "message"]
)


# Buddy Response Function
def buddy_response(message, history):

    chat_input = chat_prompt.format_prompt(
        name="Ankit Dash",
        age=24,
        gender="Male",
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