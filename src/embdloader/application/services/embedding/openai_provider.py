import os
from typing import List

from openai import OpenAI

from src.embdloader.interfaces.embedding_provider import EmbeddingProviderInterface
from src.embdloader.config import logger
from src.embdloader.domain.entities import EmbeddingError


class OpenAIEmbeddingProvider(EmbeddingProviderInterface):
    """Embedding provider using OpenAI API."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EmbeddingError("OPENAI_API_KEY is not set in environment variables")
        self.client = OpenAI(api_key=api_key)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI.

        Args:
            texts (List[str]): List of input strings.

        Returns:
            List[List[float]]: List of embeddings, one per text.
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small", input=texts
            )
            results = [item.embedding for item in response.data]

            logger.info(f"Generated {len(results)} embeddings with OpenAI")
            return results

        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise EmbeddingError(f"OpenAI embedding failed: {e}")
