from typing import Type
from llama_index.core.agent import FunctionCallingAgent
from .base_agent import BaseAgent

class AgentFactory:
    """Factory class for creating and managing agents."""
    
    _agent_registry = {}

    @classmethod
    def register_agent(cls, agent_name: str, agent_class: Type[BaseAgent]):
        """
        Register a new agent type with the factory.
        
        Args:
            agent_name: Unique identifier for the agent type
            agent_class: The agent class to register
        """
        cls._agent_registry[agent_name] = agent_class
    
    @classmethod
    def create_agent(cls, agent_name: str, **kwargs) -> FunctionCallingAgent:
        """
        Creates an agent instance of the specified type.
        
        Args:
            agent_name: Name of the registered agent type
            max_function_calls: Maximum number of function calls allowed
            
        Returns:
            FunctionCallingAgent: Configured agent instance
            
        Raises:
            KeyError: If the agent type is not registered
        """
        if agent_name not in cls._agent_registry:
            raise KeyError(f"Agent type '{agent_name}' is not registered")
        
        agent_class = cls._agent_registry[agent_name]
        agent_instance = agent_class(**kwargs)
        return agent_instance.create_agent()