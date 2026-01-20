from bot.prompts import get_title_prompt
from bot.chat_bot import create_llm
import os


def create_title(api_key: str, conversation):

    llm = create_llm(api_key=api_key)
    prompt = get_title_prompt(conversation=conversation)

    result = llm.invoke(prompt)
    
    return result.content


if __name__ == "__main__":
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    conversation = []
    if conversation:
        title = create_title(OPENAI_API_KEY, conversation)