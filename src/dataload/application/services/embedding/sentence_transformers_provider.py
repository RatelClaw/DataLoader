from typing import List
from sentence_transformers import SentenceTransformer
from dataload.interfaces.embedding_provider import EmbeddingProviderInterface
from dataload.config import logger
from dataload.domain.entities import EmbeddingError


class SentenceTransformersProvider(EmbeddingProviderInterface):
    """Local embedding provider using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            return self.model.encode(texts, show_progress_bar=False).tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise EmbeddingError(f"Embedding failed: {e}")
