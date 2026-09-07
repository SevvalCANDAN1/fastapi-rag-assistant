"""Central registry of all tools available to the RAG assistant."""
from tools.calculator import calculate
from tools.time_tool import get_current_time


ALL_TOOLS = [calculate, get_current_time]
