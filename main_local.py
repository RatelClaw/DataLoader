import asyncio
from embdloader.infrastructure.vector_stores.chroma_store import ChromaVectorStore
from embdloader.infrastructure.storage.loaders import LocalLoader
from embdloader.application.services.embedding.sentence_transformers_provider import SentenceTransformersProvider
from embdloader.application.use_cases.data_loader_use_case import DataLoaderUseCase

async def main():
    repo = ChromaVectorStore(mode='persistent', path='./my_chroma_db')  # or mode='in-memory'
    embedding = SentenceTransformersProvider()
    loader = LocalLoader()
    use_case = DataLoaderUseCase(repo, embedding, loader)

    await use_case.execute(
        'data_to_load/sample.csv',
        'test_table',
        ['name', 'description'],
        ['id'],
        create_table_if_not_exists=True,
        embed_type='separated'  # or 'combined'
    )

    # Retrieval example (commented)
    # query_text = "example query"
    # query_embedding = embedding.get_embeddings([query_text])[0]
    # results = await repo.search('test_table', query_embedding, top_k=5, embed_column='description_enc')  # For separated mode
    # print("Retrieval results:")
    # for result in results:
    #     print(f"ID: {result['id']}, Document: {result['document']}, Distance: {result['distance']}, Metadata: {result['metadata']}")

if __name__ == '__main__':
    asyncio.run(main())
