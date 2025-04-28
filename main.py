import gradio as gr
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

# Buddy Response Function
def buddy_response(message, history):
    # Simple basic response
    reply = f"I am your AI Buddy! How can I help you today?"
    return reply

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