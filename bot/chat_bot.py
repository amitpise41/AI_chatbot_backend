from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
import uuid
import os
from dotenv import load_dotenv
from bot.prompts import AGENT_PROMPT

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --------------------
# LLM factory
# --------------------
def create_llm(api_key: str, temperature: float = 1.0) -> ChatOpenAI:
    return ChatOpenAI(
        openai_api_key=api_key,
        openai_api_base="http://127.0.0.1:1234/v1",
        model="qwen2-7b-instruct@q5_0",
        temperature=temperature
    )

# --------------------
# State
# --------------------
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --------------------
# Agent node factory
# --------------------
def create_agent_node(llm):
    def agent_node(state: State):
        messages = [AGENT_PROMPT, *state["messages"]]
        response = llm.invoke(messages)
        return {
            "messages": state["messages"] + [
                {
                    "role": "assistant",
                    "content": response.content
                }
            ]
        }
    return agent_node

# --------------------
# Graph builder
# --------------------
def build_graph(agent_node):
    builder = StateGraph(State)
    builder.add_node("agent", agent_node)
    builder.add_edge(START, "agent")
    builder.add_edge("agent", END)
    return builder

# --------------------
# Runner
# --------------------
async def run_graph(messages: str, thread_id=None):
    llm = create_llm(OPENAI_API_KEY)
    agent_node = create_agent_node(llm)

    graph = build_graph(agent_node).compile(
        checkpointer=InMemorySaver()
    )

    if thread_id is None:
        thread_id = uuid.uuid4()

    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {"messages": messages},
        config
    )

    return result

# --------------------
# Entry point
# --------------------
if __name__ == "__main__":
    user_input = input("Enter your question: ")
    thread_id = uuid.uuid4()
    result = run_graph(
            messages=[user_input],
            thread_id=thread_id
        )
    print(result["messages"][-1].content)
