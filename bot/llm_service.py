import os
from typing import List, Dict
from app.interfaces.llm import LLMProvider
from bot.chat_bot import run_graph, create_llm
from bot.title_generator import create_heading
from dotenv import load_dotenv

load_dotenv()

class LangGraphLLMProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.llm = create_llm(api_key=self.api_key)

    async def chat(self, messages: List[Dict], thread_id: str | None = None) -> Dict:
        # run_graph expects messages.
        result = await run_graph(messages=messages, thread_id=thread_id)
        return result

    async def generate_heading(self, messages: List[Dict]) -> str:
        # We need to make this async safe or run in threadpool, 
        # but title_generator is sync right now.
        import asyncio
        loop = asyncio.get_running_loop()
        heading = await loop.run_in_executor(None, create_heading, self.llm, messages)
        return heading
