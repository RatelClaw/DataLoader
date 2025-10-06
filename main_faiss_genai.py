import asyncio
from dataload.infrastructure.vector_stores.faiss_store import FaissVectorStore
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.gemini_provider import GeminiEmbeddingProvider
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    # Initialize the repository, which will automatically load any saved indexes and data
    # from the previous run using the persistence logic added to FaissVectorStore.
    repo = FaissVectorStore()
    embedding = GeminiEmbeddingProvider()
    # loader = LocalLoader()
    # use_case = dataloadUseCase(repo, embedding, loader)

    # # 1. EXECUTE (Load/Insert Data) - This runs first and saves the data/index to disk.
    # print("--- Running Data Load/Insert ---")
    # await use_case.execute(
    #     'data_to_load/sample.csv',
    #     'test_table_2', # Table name used for insertion
    #     ['name', 'description'],
    #     ['id'],
    #     create_table_if_not_exists=True,
    #     embed_type='separated' 
    # )
    print("--- Data Load Complete. Running Retrieval... ---")

    # 2. RETRIEVAL (Search Data) - This will now work in the same run because the 
    # data/index is immediately available in memory after the insertion step.
    # It will also work in a subsequent run because the index is loaded from disk.
    query_text = "Final test"
    query_embedding = embedding.get_embeddings([query_text])[0]
    
    # NOTE: The table name must be 'test_table' and the embed_column must be 'description_enc' 
    # to target the correct index created in the separated mode.
    results = await repo.search(
        'test_table_2', # Corrected to match the name used in execute()
        query_embedding, 
        top_k=1, 
        embed_column='description_enc'
    )
    
    print("\nRetrieval results:")
    if not results:
        print("No results found.")
    for result in results:
        # The document text retrieved will be the content of the 'description' column
        print(f"ID: {result.get('id', 'N/A')}, Document: {result.get('document', 'N/A')}, Distance: {result.get('distance', 'N/A')}, Metadata: {result.get('metadata', 'N/A')}")
    print("--- Retrieval Complete ---")

if __name__ == '__main__':
    asyncio.run(main())