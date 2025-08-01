from langchain_core.tools import tool
import re
import datetime
from db import save_memory, add_reminder

@tool
def memory_tool(input: str) -> str:
    """Save important info to memory if user requests."""
    if 'remember' in input.lower() or 'important' in input.lower():
        title = input[:50]
        save_memory(title, input)
        return "Saved to memory!"
    return "No memory saved."

@tool
def reminder_tool(input: str) -> str:
    """Set a reminder if user requests."""
    match = re.search(r"remind me to (.+) at ([\d\w :,-]+)", input, re.I)
    if match:
        task = match.group(1)
        time_str = match.group(2)
        try:
            remind_at = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except Exception:
            remind_at = datetime.datetime.now() + datetime.timedelta(hours=1)
        add_reminder(task, remind_at)
        return f"Reminder set for '{task}' at {remind_at}"
    return "No reminder set."

tools = [memory_tool, reminder_tool]