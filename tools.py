from langchain_core.tools import tool
import datetime
import dateparser
from db import save_memory, add_reminder

@tool
def memory_tool(info: str) -> str:
    """Store important memory. Input should be a brief memory or fact to remember."""
    title = info[:50]
    save_memory(title, info)
    return f"Saved to memory with title: '{title}'"
@tool
def reminder_tool(task_and_time: str) -> str:
    """Set a reminder. Input should be: 'task to do | 2025-08-02 15:30'."""
    try:
        task, time_str = task_and_time.split("|")
        remind_at = datetime.strptime(time_str.strip(), "%Y-%m-%d %H:%M")
        add_reminder(task.strip(), remind_at)
        return f"Reminder set for '{task.strip()}' at {remind_at}"
    except Exception as e:
        return f"Failed to set reminder: {e}"
    
tools = [memory_tool, reminder_tool]