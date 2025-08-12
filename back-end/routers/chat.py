from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.chat_history import InMemoryChatMessageHistory
from db import (
    save_memory, 
    add_reminder,
    get_memories
)
import dateparser
import os   
from dotenv import load_dotenv

load_dotenv()

LLM = ChatNVIDIA(
    model="mistralai/mistral-7b-instruct-v0.3",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.2,
    top_p=0.7,
    max_completion_tokens=1024,
)

def memory_tool(info: str) -> str:
    title = info[:50]
    save_memory(title, info)
    return f"Saved to memory with title: '{title}'"

def reminder_tool(task_and_time: str) -> str:
    try:
        task, time_str = task_and_time.split("|")
        remind_at = dateparser.parse(time_str.strip())
        if not remind_at:
            return "Failed to parse date. Please use a format like 'YYYY-MM-DD HH:MM'."
        add_reminder(task.strip(), remind_at)
        return f"Reminder set for '{task.strip()}' at {remind_at.strftime('%Y-%m-%d %H:%M')}"
    except Exception as e:
        return f"Failed to set reminder: {e}"

chat_history = InMemoryChatMessageHistory()        

def chat_with_bot(message: str):

    try:
        # Add user message to in-memory history
        chat_history.add_user_message(message)

        # Convert to conversation string
        conversation_history = "\n".join(
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
            for msg in chat_history.messages
        )

        # Load memory
        memory_items = get_memories(limit=10)
        memory = "\n".join(f"- {title.strip()}: {content.strip()}" for title, content in memory_items)


        # Prompt Template 
        prompt_template = ChatPromptTemplate.from_template(""" 
            You are Deva — an intelligent, emotionally aware, and ever-present companion for your user.
            Your role is more than just answering questions. You are:
            - A helpful assistant who can support with information, tasks, or reminders.
            - A thoughtful friend who remembers personal details, offers encouragement, and listens with empathy.
            - A lifelong companion who adapts to the user's preferences, mood, and growth over time.
            
            *User Profile*:
            Name: Ankit Dash, DOB: 08-11-2000, Gender: Male

            *Your Memory*:
            {memory}

            *Conversation History*:
            {conversation_history}

            *User's Current Message*:
            {user_message}
                
            Speak naturally, warmly, and intelligently. Show care, ask thoughtful questions, and deepen the bond with the user.

            """)
        
        chain = prompt_template | LLM

        bot_response = chain.invoke({
            "memory": memory,
            "conversation_history": conversation_history,
            "user_message": message
        })

        # Get and save AI response
        if isinstance(bot_response, BaseMessage):
            response = bot_response.content
        else:
            response = str(bot_response)

        chat_history.add_message(AIMessage(content=response))

        return {"bot_response": response}

    except Exception as e:
        print(f"Error in chat function: {e}")
        return {"error": str(e)}            