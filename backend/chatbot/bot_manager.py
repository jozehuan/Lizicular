from typing import Type

from .manager.base_manager import BaseManagerAgent
from .manager.main_manager import MainManagerAgent
from .models import BotSettings
from llama_index.core.llms import ChatMessage

from dotenv import load_dotenv
load_dotenv(override=True)

class BotManager:
    def __init__(self, settings: BotSettings = None, class_manager: Type[BaseManagerAgent] = MainManagerAgent):
        self.manager_agent = class_manager(settings)
        self.agent = self.manager_agent.init_main_agent()

    async def run_agent(self, question: str, chat_history: list[ChatMessage] = []):
        response = await self.agent.achat(question, chat_history=chat_history)
        return str(response)