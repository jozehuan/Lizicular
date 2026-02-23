from ..models import EngineType
from .builders.azure_openai_builder import AzureOpenAIBuilder

# Factory class to get the data processor
class EngineAIFactory:

    @staticmethod
    def get_engine(engine_type):
        if engine_type == EngineType.AZURE:
            return AzureOpenAIBuilder()
        else:
            raise ValueError(f"Unknown or unsupported engine type: {engine_type}")