import os
from typing import List
import numpy as np

from dataload.interfaces.embedding_provider import EmbeddingProviderInterface
from dataload.config import logger
from dataload.domain.entities import EmbeddingError


class GeminiEmbeddingProvider(EmbeddingProviderInterface):
    """Embedding provider using Google Gemini (Generative AI)."""

    DEFAULT_MODEL = "text-embedding-004"

    def __init__(self):
        # --- LAZY IMPORT google-genai HERE ---
        try:
            from google import genai
            from google.genai import (
                types,
            )  # Keep this import here for client instantiation
        except ImportError:
            raise EmbeddingError(
                "The 'gemini' extra is required to use GeminiEmbeddingProvider. "
                "Install with: pip install vector-dataloader[gemini]"
            )
        # ------------------------------------

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EmbeddingError("GOOGLE_API_KEY is not set in environment variables")
        self.client = genai.Client(api_key=api_key)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Gemini.
        """
        try:
            from google.genai import types
        except ImportError:
            # Should not happen, but a safe guard
            raise EmbeddingError("Gemini dependencies failed to load.")

        try:
            resp = self.client.models.embed_content(
                model=self.DEFAULT_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
            )

            embeddings = [e.values for e in resp.embeddings]

            # The dimension is determined by the model, which we've now set to 768.
            if embeddings and len(embeddings[0]) != 768:
                logger.warning(
                    f"Model {self.DEFAULT_MODEL} returned dimension {len(embeddings[0])}. Expected 768."
                )

            logger.info(f"Generated {len(embeddings)} embeddings with Gemini")
            return embeddings

        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise EmbeddingError(f"Gemini embedding failed: {e}")
