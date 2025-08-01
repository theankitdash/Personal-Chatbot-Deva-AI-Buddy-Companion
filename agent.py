from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.agents import create_tool_calling_agent
from langchain.agents.agent import RunnableAgent
from langchain_core.runnables import RunnableMap
from prompts import prompt, get_memory_text
from db import load_chat_history
from tools import tools
import os

LLM = ChatNVIDIA(
    model="mistralai/mistral-7b-instruct-v0.3",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.2,
    top_p=0.7,
    max_completion_tokens=1024,
)

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