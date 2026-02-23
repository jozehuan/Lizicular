from ..models import BotSettings
from .base_manager import BaseManagerAgent
from ..agents.agent_tools.review_agent import ReviewAgent

class MainManagerAgent(BaseManagerAgent):
    def __init__(self, bot_settings: BotSettings = None):
        super().__init__(bot_settings)
        
        # If a token is provided, it means a user is logged in.
        # We instantiate ReviewAgent and add its tools and prompt to the main agent.
        if self.user_token_active: # This flag checks if a token exists.
            review_agent_instance = ReviewAgent(token=bot_settings.user_token)
            
            # Get tools and prompt from the review agent instance
            review_tools = review_agent_instance.get_tools()
            review_prompt_instructions = review_agent_instance.get_system_prompt()
            
            # Add the review agent's tools to the main agent's tool list
            self.agent_list.extend(review_tools)
            
            # Append the detailed instructions for using those tools to the main prompt
            self.prompts += "\n\n" + review_prompt_instructions