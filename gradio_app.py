import gradio as gr
from db import save_chat_message
from agent import agent_chain

def gradio_chat_fn(message, history=None):
    save_chat_message("human", message)
    result = agent_chain.invoke({"input": message})
    response = result.return_values["output"]
    save_chat_message("ai", response)
    return {"role": "assistant", "content": response}

def launch_app():
    with gr.Blocks() as app:
        gr.Markdown("# Deva: Your Buddy Companion")
        chatbox = gr.ChatInterface(
            fn=gradio_chat_fn,
            title="Deva",
            description="Always for you Buddy!",
            theme="soft",
            type="messages"
        )
    app.launch(share=True)