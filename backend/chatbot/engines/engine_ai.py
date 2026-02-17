from abc import ABC, abstractmethod

class EngineAI(ABC):
    @abstractmethod
    def __init__(self):
        pass

    # ingest data into an index from a given datapath of documents
    @abstractmethod
    def get_config(self):
        pass