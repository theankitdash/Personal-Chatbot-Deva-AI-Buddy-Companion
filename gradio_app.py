import gradio as gr
from chat import chat_with_bot

def gradio_chat_fn(message, history=None):
    result = chat_with_bot(message)
    return result["bot_response"]

def launch_app():
    with gr.Blocks() as app:
        gr.Markdown("# Deva: Your Buddy Companion")
        gr.ChatInterface(
            fn=gradio_chat_fn,
            title="Deva",   
            description="Always for you Buddy!",
            theme="soft",
            type="messages"
        )
    app.launch(share=True)
