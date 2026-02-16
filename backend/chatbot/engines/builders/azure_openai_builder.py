from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from ..engine_ai import EngineAI
from dotenv import load_dotenv
import os

    # import nest_asyncio
    # nest_asyncio.apply()

class AzureOpenAIBuilder(EngineAI):
    def __init__(
        self, 
        engine="ai-model-gpt4-o", 
        model="gpt-4o", 
        temperature=0.01, 
        embedding_model="text-embedding-ada-002",
        deployment_name="text-embedding-ada-002",
    ):
        load_dotenv()
        api_key=os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version=os.getenv("OPENAI_API_VERSION")

        # Inicializar el LLM
        self.llm = AzureOpenAI(
            deployment_name=engine,
            model=model,
            temperature=temperature,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )

        # Inicializar el modelo de embeddings
        self.embed_model = AzureOpenAIEmbedding(
            embedding_model=embedding_model,
            deployment_name=deployment_name,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
        )

        self.num_output = 512
        self.context_window = 3900

    def get_config(self):
        return {
            "llm": self.llm,
            "embed_model": self.embed_model,
            "num_output": self.num_output,
            "context_window": self.context_window,
            "embed_dim": 1536
        }
