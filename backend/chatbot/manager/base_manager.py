import re, yaml, os
from typing import List, Type

from ..models import BotSettings
from ..agents.base_agent import BaseAgent
from ..engines.engine_ai_factory import EngineAIFactory
from ..agents.agent_factory import AgentFactory

from llama_index.core import Settings
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent import FunctionCallingAgent
from llama_index.core.tools import ToolMetadata

class BaseManagerAgent:
    def __init__(self, bot_settings: BotSettings = None, **kwargs):
        self.agent_list: List[QueryEngineTool] = []
        self.bot_settings = bot_settings

        self.builder_type = "azure"
        self.builder = EngineAIFactory.get_engine(self.builder_type)
        self.llm = self.builder.llm
        self.agent_factory = AgentFactory()
        
        Settings.llm = self.builder.llm
        Settings.num_output = self.builder.num_output
        Settings.embed_model = self.builder.embed_model
        # Settings.embed_model.embed_batch_size = 128 # This might not be available on all models
        Settings.context_window = self.builder.context_window
        self.user_token_active = bot_settings and bot_settings.user_token

        self.prompts = self.init_prompts(**kwargs)

    def init_prompts(self, main_agent_prompt : str = "main_agent_prompt"):
        PROMPT_FILE = "utils/prompts.yml"
        if not os.path.exists(PROMPT_FILE):
            print(f"Warning: Prompt file not found at {PROMPT_FILE}. Using default prompts.")
            return {"main_agent_prompt": "You are a helpful assistant."}
            
        with open(PROMPT_FILE, "r") as f:
            prompts = yaml.safe_load(f)
        
        if self.user_token_active:
            prompts[main_agent_prompt] = prompts[main_agent_prompt].replace("[AIGRO_API_TOOLS_START]", "").replace("[AIGRO_API_TOOLS_END]", "")
        else:
            prompts[main_agent_prompt] = re.sub(r'\[AIGRO_API_TOOLS_START\].*?\[AIGRO_API_TOOLS_END\]', '', prompts[main_agent_prompt], flags=re.DOTALL)
        return prompts[main_agent_prompt]
        
    def register_agent(self, agent_name: str, agent_desc: str, agent_class: Type[BaseAgent], return_direct: bool = False, **kwargs):
        """Register a new agent using the agent factory"""
        self.agent_factory.register_agent(agent_name, agent_class)
        # Create the agent instance using the factory
        agent_instance = self.agent_factory.create_agent(agent_name, **kwargs)
        
        # Create a QueryEngineTool wrapper for the agent
        agent_tool = QueryEngineTool(
            query_engine=agent_instance,
            metadata=ToolMetadata(
                name=f"{agent_name}",
                description=f"{agent_desc}",
                return_direct = return_direct
            ),
        )
        
        self.agent_list.append(agent_tool)

        
    def init_main_agent(self) -> FunctionCallingAgent:
        """Initialize the main agent that combines all registered agents"""
        system_prompt = self.prompts
        
        return FunctionCallingAgent.from_tools(
            tools=self.agent_list,
            llm=self.llm,
            system_prompt=system_prompt,
            verbose=True,
            max_function_calls=20,
        )




