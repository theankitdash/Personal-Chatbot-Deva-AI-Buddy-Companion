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
    description="Your SALAAR is here, Always for you!",
    theme="soft",  # Clean soft colors
)

# Launch Gradio app
if __name__ == "__main__":
    chatbot.launch(share=True) 