from .config import logger
from .application.use_cases.data_loader_use_case import dataloadUseCase 
from .application.use_cases.data_updater_use_case import DataUpdaterUseCase # Unified Use Case
from .infrastructure.storage.loaders import LocalLoader, S3Loader
from .infrastructure.vector_stores.chroma_store import ChromaVectorStore
from .infrastructure.vector_stores.faiss_store import FaissVectorStore
from .infrastructure.db.data_repository import PostgresDataRepository
from .infrastructure.db.db_connection import DBConnection
from .application.services.embedding.gemini_provider import GeminiEmbeddingProvider
from .application.services.embedding.sentence_transformers_provider import SentenceTransformersProvider
from .application.services.embedding.openai_provider import OpenAIEmbeddingProvider
from .application.services.embedding.bedrock_provider import BedrockEmbeddingProvider

__version__ = "1.2.0" # Use dunder to follow convention