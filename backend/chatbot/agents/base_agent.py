from abc import ABC, abstractmethod
from typing import List
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import FunctionCallingAgent

class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""
    

    @abstractmethod
    def get_tools(self) -> List[FunctionTool]:
        """
        Returns the list of tools that this agent can use.
        
        Returns:
            List[FunctionTool]: List of function tools available to the agent
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Returns the system prompt that defines the agent's behavior.
        
        Returns:
            str: The system prompt for the agent
        """
        pass
    
    def create_agent(self) -> FunctionCallingAgent:
        """
        Creates a FunctionCallingAgent instance with this agent's tools and system prompt.
        
        Args:
            max_function_calls: Maximum number of function calls allowed
            
        Returns:
            FunctionCallingAgent: Configured agent instance
        """
        return FunctionCallingAgent.from_tools(
            tools=self.get_tools(),
            system_prompt=self.get_system_prompt(),
            verbose=True,
            max_function_calls=20 if self.max_function_calls is None else self.max_function_calls
        ) 