"""Time-related tools for the RAG assistant."""
from datetime import datetime

from langchain_core.tools import tool

@tool
def get_current_time(time_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Return the current date and time in ISO 8601 format.
    Use this when the user asks about the current date, time, or day of week."""
    return datetime.now().strftime(time_format)