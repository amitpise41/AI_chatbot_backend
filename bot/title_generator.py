from bot.prompts import get_heading_prompt
from bot.chat_bot import create_llm
import os


def create_heading(llm, messages):
    prompt = get_heading_prompt(messages=messages)
    result = llm.invoke(prompt)
    return result.content


if __name__ == "__main__":
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    messages = []
    if messages:
        heading = create_heading(OPENAI_API_KEY, messages)