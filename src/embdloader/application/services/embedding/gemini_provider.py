import os
from typing import List
import numpy as np

from google import genai
from google.genai import types

from src.embdloader.interfaces.embedding_provider import EmbeddingProviderInterface
from src.embdloader.config import logger
from src.embdloader.domain.entities import EmbeddingError


class GeminiEmbeddingProvider(EmbeddingProviderInterface):
    """Embedding provider using Google Gemini (Generative AI)."""

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EmbeddingError("GOOGLE_API_KEY is not set in environment variables")
        self.client = genai.Client(api_key=api_key)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Gemini.

        Args:
            texts (List[str]): List of input strings.

        Returns:
            List[List[float]]: List of embeddings, one per text.
        """
        try:
            resp = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
            )

            embeddings = [np.array(e.values).tolist() for e in resp.embeddings]

            logger.info(f"Generated {len(embeddings)} embeddings with Gemini")
            return embeddings

        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise EmbeddingError(f"Gemini embedding failed: {e}")
