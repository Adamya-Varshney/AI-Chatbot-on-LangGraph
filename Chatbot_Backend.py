from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

if not os.getenv("OPENAI_API_KEY"):
    try:
        import streamlit as st
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

llm = ChatOpenAI()

def generate_title(user_msg: str, ai_msg: str) -> str:
    prompt = [
        SystemMessage(content=(
            "You create very short titles for chat conversations. "
            "Given the first user message and the assistant's reply, return a concise "
            "title of at most 5 words capturing the topic. Return ONLY the title text — "
            "no quotes, no trailing punctuation, no preamble."
        )),
        HumanMessage(content=f"User: {user_msg}\n\nAssistant: {ai_msg[:1000]}"),
    ]
    result = llm.invoke(prompt)
    title = result.content.strip().strip('"').strip()
    return title or "New Chat"

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState, config):
    messages = state['messages']

    cfg = config.get('configurable', {}) if config else {}
    location = cfg.get('user_location')
    timezone = cfg.get('user_timezone')
    local_time = cfg.get('local_time')

    bits = []
    if location:
        bits.append(f"The user's location is {location}.")
    if timezone:
        bits.append(f"The user's time zone is {timezone}.")
    if local_time:
        bits.append(f"The user's current local date and time is {local_time}.")

    if bits:
        system_msg = SystemMessage(content="User context (use when relevant): " + " ".join(bits))
        response = llm.invoke([system_msg] + messages)
    else:
        response = llm.invoke(messages)

    return {"messages": [response]}

# Checkpointer
checkpointer = InMemorySaver()

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)