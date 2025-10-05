import asyncio
from embdloader.infrastructure.db.db_connection import DBConnection
from embdloader.infrastructure.db.data_repository import PostgresDataRepository 
from embdloader.infrastructure.vector_stores.chroma_store import ChromaVectorStore
# from embdloader.infrastructure.vector_stores.faiss_store import FaissVectorStore
from embdloader.infrastructure.storage.loaders import LocalLoader
from embdloader.application.services.embedding.gemini_provider import GeminiEmbeddingProvider
from embdloader.application.use_cases.data_loader_use_case import DataLoaderUseCase

async def main():
    db_conn = DBConnection()
    await db_conn.initialize()
    
    # repo = ChromaVectorStore()
    repo = PostgresDataRepository(db_connection=db_conn)
   
    embedding = GeminiEmbeddingProvider()
    loader = LocalLoader()
    use_case = DataLoaderUseCase(repo, embedding, loader)
   
    await use_case.execute(
        'data_to_load/sample.csv',
        'test_table',
        ['name', 'description'],
        ['id'],
        create_table_if_not_exists=True,
        embed_type='separated'
    )

if __name__ == '__main__':
    asyncio.run(main())
