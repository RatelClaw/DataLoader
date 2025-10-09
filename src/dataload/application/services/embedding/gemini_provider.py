import os
from typing import List
import numpy as np

from google import genai
from google.genai import types

from dataload.interfaces.embedding_provider import EmbeddingProviderInterface
from dataload.config import logger
from dataload.domain.entities import EmbeddingError


class GeminiEmbeddingProvider(EmbeddingProviderInterface):
    """Embedding provider using Google Gemini (Generative AI)."""
    
    # 💡 Note: The official recommended model for general embeddings is often text-embedding-004.
    # It reliably outputs 768 dimensions, which is below the 2000 dimension pgvector limit.
    DEFAULT_MODEL = "text-embedding-004" 

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EmbeddingError("GOOGLE_API_KEY is not set in environment variables")
        self.client = genai.Client(api_key=api_key)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Gemini.
        """
        try:
            resp = self.client.models.embed_content(
                # ✅ FIX: Switched to a model with a lower output dimension (768)
                model=self.DEFAULT_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
            )

            # Note: The 'e.values' list/array is what holds the embedding.
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

# import os
# from typing import List
# import numpy as np

# from google import genai
# from google.genai import types

# from src.dataload.interfaces.embedding_provider import EmbeddingProviderInterface
# from src.dataload.config import logger
# from src.dataload.domain.entities import EmbeddingError


# class GeminiEmbeddingProvider(EmbeddingProviderInterface):
#     """Embedding provider using Google Gemini (Generative AI)."""

#     def __init__(self):
#         api_key = os.getenv("GOOGLE_API_KEY")
#         if not api_key:
#             raise EmbeddingError("GOOGLE_API_KEY is not set in environment variables")
#         self.client = genai.Client(api_key=api_key)

#     def get_embeddings(self, texts: List[str]) -> List[List[float]]:
#         """
#         Generate embeddings for a list of texts using Gemini.

#         Args:
#             texts (List[str]): List of input strings.

#         Returns:
#             List[List[float]]: List of embeddings, one per text.
#         """
#         try:
#             resp = self.client.models.embed_content(
#                 model="gemini-embedding-001",
#                 contents=texts,
#                 config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
#             )

#             embeddings = [np.array(e.values).tolist() for e in resp.embeddings]

#             logger.info(f"Generated {len(embeddings)} embeddings with Gemini")
#             return embeddings

#         except Exception as e:
#             logger.error(f"Gemini embedding error: {e}")
#             raise EmbeddingError(f"Gemini embedding failed: {e}")
