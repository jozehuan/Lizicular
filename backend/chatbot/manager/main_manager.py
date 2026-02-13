from ..models import BotSettings
from .base_manager import BaseManagerAgent
from ..agents.agent_tools.review_agent import ReviewAgent

class MainManagerAgent(BaseManagerAgent):
    def __init__(self, bot_settings: BotSettings = None):
        super().__init__(bot_settings)
        
        # If a token is provided, it means a user is logged in.
        # Register the ReviewAgent to give the chatbot access to the user's data.
        if self.user_token_active: # This flag checks if a token exists.
            self.register_agent("review_agent",
                                "Use this agent to get information about the user's personal workspaces, tenders, and analysis results. Use it when the user asks 'what are my workspaces?' or 'show me my tenders'.",
                                ReviewAgent,
                                token=bot_settings.user_token)  