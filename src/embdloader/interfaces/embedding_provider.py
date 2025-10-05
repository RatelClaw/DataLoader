from abc import ABC, abstractmethod
from typing import List

class EmbeddingProviderInterface(ABC):
    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass