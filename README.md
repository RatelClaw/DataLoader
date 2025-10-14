vector-dataloader
vector-dataloader is a robust and extensible Python library for loading CSV data from local files or S3 into vector stores (Postgres, FAISS, Chroma) with embedding generation. It supports multiple embedding providers (AWS Bedrock, Google Gemini, Sentence-Transformers, OpenAI) and offers flexible embedding modes for scalable data processing.
🚀 Features

Data Sources: Load data from local CSV files or AWS S3.
Embedding Modes: Supports combined or separated embedding generation.
Embedding Providers: AWS Bedrock, Google Gemini, Sentence-Transformers, OpenAI.
Vector Stores: Postgres (with pgvector), FAISS (in-memory), Chroma (persistent).
Data Updates: Handles new, updated, or removed rows with soft delete support.
Scalability: Batch processing, retries, and connection pooling for efficient operations.
Extensibility: Modular plugin-style architecture for providers and stores.
Validation: Enforces schema, type, and null checks for data integrity.

📦 Installation
Prerequisites

Python: Version 3.8 or higher.
Visual Studio Build Tools: Required for C++ dependencies (e.g., FAISS). Download from Visual Studio Build Tools and ensure the "Desktop development with C++" workload is installed.
pip or uv: Package manager for installing dependencies.

Step-by-Step Installation

Install the Core PackageInstall the minimal package without optional dependencies:
pip install vector-dataloader
# or
uv add vector-dataloader


Install Optional DependenciesInstall only the dependencies for the providers and stores you need. Use the following combinations:



Combination
Command
Notes



ChromaDB
pip install vector-dataloader[chroma]
Required for ChromaVectorStore.


FAISS
pip install vector-dataloader[faiss]
Required for FaissVectorStore.


Google Gemini
pip install vector-dataloader[gemini]
Required for GeminiEmbeddingProvider.


Sentence-Transformers
pip install vector-dataloader[sentence-transformers]
Required for SentenceTransformersProvider.


OpenAI
pip install vector-dataloader[openai]
Required for OpenAIProvider.


AWS Bedrock
pip install vector-dataloader[bedrock]
Required for BedrockEmbeddingProvider.


All Features
pip install vector-dataloader[all]
Installs all optional dependencies.


Example: To use Chroma with Gemini:
pip install vector-dataloader[chroma,gemini]


Verify InstallationConfirm the package is installed:
pip show vector-dataloader



⚙️ Usage
Below are example scripts demonstrating how to use vector-dataloader with different vector stores and embedding providers. Ensure the input CSV file (e.g., data_to_load/sample.csv or data_to_load/sample_2.csv) exists with appropriate columns (e.g., id, name, description or Index, Name, Description).
All examples use asynchronous execution for efficiency. Retrieval examples are commented out but can be uncommented for testing search functionality after data loading.
Example 1: Chroma with Google Gemini
This example loads data into a persistent Chroma vector store using Gemini embeddings.
# Install required dependencies
pip install vector-dataloader[chroma,gemini]

import asyncio
from dataload.infrastructure.vector_stores.chroma_store import ChromaVectorStore
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.gemini_provider import (
    GeminiEmbeddingProvider,
)
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase


async def main():
    # Initialize Chroma vector store in persistent mode (saves to disk)
    repo = ChromaVectorStore(
        mode="persistent", path="./gemni_croma"
    )  # or mode='in-memory'
    # Initialize Gemini embedding provider
    embedding = GeminiEmbeddingProvider()
    # Initialize local data loader
    loader = LocalLoader()
    # Create use case instance
    use_case = dataloadUseCase(repo, embedding, loader)

    # Execute data loading
    await use_case.execute(
        "data_to_load/sample.csv",
        "test_table",
        ["name", "description"],
        ["id"],
        create_table_if_not_exists=True,
        embed_type="separated",  # or 'combined'
    )

    # # Example for loading another dataset (commented)
    # await use_case.execute(
    #     'data_to_load/sample_2.csv',
    #     'test_table_v2_pg_st',
    #     ['Name', 'Description'],
    #     ['Index'],
    #     create_table_if_not_exists=True,
    #     embed_type=  'combined' #'separated'  # or 'combined'
    # )

    # # Retrieval example (commented)
    # query_text = "Final test row"
    # query_embedding = embedding.get_embeddings([query_text])[0]
    # results = await repo.search('test_table', query_embedding, top_k=1,embed_column='description_enc')  # For separated mode
    # print("Retrieval results:")
    # for result in results:
    #     print(f"ID: {result['id']}, Document: {result['document']}, Distance: {result['distance']}, Metadata: {result['metadata']}")


if __name__ == "__main__":
    asyncio.run(main())

Example 2: Chroma with Sentence-Transformers
This example loads data into a persistent Chroma vector store using Sentence-Transformers embeddings.
# Install required dependencies
pip install vector-dataloader[chroma,sentence-transformers]

import asyncio
from dataload.infrastructure.vector_stores.chroma_store import ChromaVectorStore
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.sentence_transformers_provider import (
    SentenceTransformersProvider,
)
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase


async def main():
    # Initialize Chroma vector store in persistent mode (saves to disk)
    repo = ChromaVectorStore(
        mode="persistent", path="./my_chroma_db"
    )  # or mode='in-memory'
    # Initialize Sentence-Transformers embedding provider
    embedding = SentenceTransformersProvider()
    # Initialize local data loader
    loader = LocalLoader()
    # Create use case instance
    use_case = dataloadUseCase(repo, embedding, loader)

    # Execute data loading
    await use_case.execute(
        "data_to_load/sample_2.csv",
        "test_table",
        ["Name", "Description"],
        ["Index"],
        create_table_if_not_exists=True,
        embed_type="separated",  # or 'combined'
    )

    # # Retrieval example (commented)
    # query_text = "example query"
    # query_embedding = embedding.get_embeddings([query_text])[0]
    # results = await repo.search('test_table', query_embedding, top_k=5, embed_column='Description_enc')  # For separated mode
    # print("Retrieval results:")
    # for result in results:
    #     print(f"ID: {result['id']}, Document: {result['document']}, Distance: {result['distance']}, Metadata: {result['metadata']}")


if __name__ == "__main__":
    asyncio.run(main())

Example 3: FAISS with Google Gemini
This example loads data into an in-memory FAISS vector store using Gemini embeddings.
# Install required dependencies
pip install vector-dataloader[faiss,gemini]

import asyncio
from dataload.infrastructure.vector_stores.faiss_store import FaissVectorStore
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.gemini_provider import (
    GeminiEmbeddingProvider,
)
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase


async def main():
    # Initialize FAISS vector store (in-memory with persistence support)
    repo = FaissVectorStore()
    # Initialize Gemini embedding provider
    embedding = GeminiEmbeddingProvider()
    # Initialize local data loader
    loader = LocalLoader()
    # Create use case instance
    use_case = dataloadUseCase(repo, embedding, loader)

    # Execute data loading
    await use_case.execute(
        "data_to_load/sample_2.csv",
        "test_table_v2_com_pg_st",
        ["Name", "Description"],
        ["Index"],
        create_table_if_not_exists=True,
        embed_type="separated",  #'separated'  # or 'combined'
    )

    # # Retrieval example (commented) - For separated mode
    # query_text = "Final test"
    # query_embedding = embedding.get_embeddings([query_text])[0]
    # results = await repo.search(
    #     'test_table_v2_pg_st', # Corrected to match the name used in execute()
    #     query_embedding,
    #     top_k=1,
    #     embed_column='Description_enc'
    # )

    # # Retrieval example (commented) - For combined mode
    # query_text = "Final test"
    # query_embedding = embedding.get_embeddings([query_text])[0]
    # results = await repo.search(
    #     'test_table_v2_com_pg_st', # Corrected to match the name used in execute()
    #     query_embedding,
    #     top_k=1,
    # )

    # # Print retrieval results (commented)
    # print("\nRetrieval results:")
    # if not results:
    #     print("No results found.")
    # for result in results:
    #     # The document text retrieved will be the content of the 'description' column
    #     print(f"ID: {result.get('id', 'N/A')}, Document: {result.get('document', 'N/A')}, Distance: {result.get('distance', 'N/A')}, Metadata: {result.get('metadata', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())

Example 4: FAISS with Sentence-Transformers
This example loads data into an in-memory FAISS vector store using Sentence-Transformers embeddings.
# Install required dependencies
pip install vector-dataloader[faiss,sentence-transformers]

import asyncio
from dataload.infrastructure.vector_stores.faiss_store import FaissVectorStore
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.sentence_transformers_provider import (
    SentenceTransformersProvider,
)
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase


async def main():
    # Initialize FAISS vector store (in-memory with persistence support)
    repo = FaissVectorStore()
    # Initialize Sentence-Transformers embedding provider
    embedding = SentenceTransformersProvider()
    # Initialize local data loader
    loader = LocalLoader()
    # Create use case instance
    use_case = dataloadUseCase(repo, embedding, loader)

    # Execute data loading
    await use_case.execute(
        "data_to_load/sample_2.csv",
        "test_table_faiss_st_v7",
        ["Name", "Description"],
        ["Index"],
        create_table_if_not_exists=True,
        embed_type="combined",  # or 'separated'
    )

    # # Retrieval example (commented) - For combined mode
    # query_text = "example query"
    # query_embedding = embedding.get_embeddings([query_text])[0]
    # results = await repo.search("test_table_faiss_st_v7", query_embedding, top_k=5)

    # # Retrieval example (commented) - For separated mode
    # # results = await repo.search('test_table_faiss_v4', query_embedding, top_k=5, embed_column='embeddings')  # For separated mode
    # print("Retrieval results:")
    # for result in results:
    #     print(
    #         f"ID: {result['id']}, Document: {result['document']}, Distance: {result['distance']}, Metadata: {result['metadata']}"
    #     )


if __name__ == "__main__":
    asyncio.run(main())

Example 5: Postgres with Google Gemini
This example loads data into a Postgres vector store using Gemini embeddings. Ensure to close the DB connection after use.
# Install required dependencies
pip install vector-dataloader[gemini]

import asyncio
from dataload.infrastructure.db.db_connection import DBConnection
from dataload.infrastructure.db.data_repository import PostgresDataRepository
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.gemini_provider import (
    GeminiEmbeddingProvider,
)
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase


async def main():
    # Initialize DB connection
    db_conn = DBConnection()
    await db_conn.initialize()
    # Initialize Postgres repository
    repo = PostgresDataRepository(db_conn)
    # Initialize Gemini embedding provider
    embedding = GeminiEmbeddingProvider()
    # Initialize local data loader
    loader = LocalLoader()
    # Create use case instance
    use_case = dataloadUseCase(repo, embedding, loader)

    # # Example for loading data in combined mode (commented)
    # await use_case.execute(
    #     'data_to_load/sample_2.csv',
    #     'test_table_com_pg_gemini_st',
    #     ['Name', 'Description'],
    #     ['Index'],
    #     create_table_if_not_exists=True,
    #     embed_type=  'combined' #'separated'  # or 'combined'
    # )

    # # Example for loading data in separated mode (commented)
    # await use_case.execute(
    #     'data_to_load/sample.csv',
    #     'test_table_v4',
    #     ['name', 'description'],
    #     ['id'],
    #     create_table_if_not_exists=True,
    #     embed_type='separated'  # or 'combined'
    # )

    # # Retrieval example (commented) - For combined mode
    # query_text = "example project description"
    # query_embedding = embedding.get_embeddings([query_text])[0]
    # results = await repo.search("test_table_com_pg_gemini_st", query_embedding, top_k=5)
    # print("Combined mode retrieval results:")
    # for result in results:
    #     print(
    #         f"ID: {result['id']}, Document: {result['document']}, Distance: {result['distance']}, Metadata: {result['metadata']}"
    #     )

    # # Retrieval example (commented) - For separated mode
    # # results = await repo.search('test_table_v4', query_embedding, top_k=2, embed_column='description_enc')
    # # print("Separated mode retrieval results (description_enc):")
    # # for result in results:
    # #     print(f"ID: {result['id']}, Document: {result['document']}, Distance: {result['distance']}, Metadata: {result['metadata']}")

    # Close DB connection
    await db_conn.close()


if __name__ == "__main__":
    asyncio.run(main())

Example 6: Postgres with Sentence-Transformers
This example loads data into a Postgres vector store using Sentence-Transformers embeddings. Ensure to close the DB connection after use.
# Install required dependencies
pip install vector-dataloader[sentence-transformers]

import asyncio
from dataload.infrastructure.db.db_connection import DBConnection
from dataload.infrastructure.db.data_repository import PostgresDataRepository
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.sentence_transformers_provider import (
    SentenceTransformersProvider,
)
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase


async def main():
    # Initialize DB connection
    db_conn = DBConnection()
    await db_conn.initialize()
    # Initialize Postgres repository
    repo = PostgresDataRepository(db_conn)
    # Initialize Sentence-Transformers embedding provider
    embedding = SentenceTransformersProvider()

    # # Initialize local data loader and use case (commented - uncomment for loading)
    # loader = LocalLoader()
    # use_case = dataloadUseCase(repo, embedding, loader)

    # # Example for loading data in combined mode (commented)
    # await use_case.execute(
    #     'data_to_load/sample.csv',
    #     'test_table_v4_pg_st',
    #     ['name', 'description'],
    #     ['id'],
    #     create_table_if_not_exists=True,
    #     embed_type='combined'  # or 'combined'
    # )

    # # Example for loading data in separated mode (commented)
    # await use_case.execute(
    #     'data_to_load/sample_2.csv',
    #     'test_table_v2_pg_st',
    #     ['Name', 'Description'],
    #     ['Index'],
    #     create_table_if_not_exists=True,
    #     embed_type=  'separated' #'separated'  # or 'combined'
    # )

    # # Retrieval example (commented) - For separated mode
    # query_text = "example query"
    # query_embedding = embedding.get_embeddings([query_text])[0]
    # results = await repo.search(
    #     "test_table_v2_pg_st", query_embedding, top_k=1, embed_column="Description_enc"
    # )  # For separated mode
    # print("Retrieval results:")
    # for result in results:
    #     print(
    #         f"ID: {result['id']}, Document: {result['document']}, Distance: {result['distance']}, Metadata: {result['metadata']}"
    #     )

    # Close DB connection
    await db_conn.close()


if __name__ == "__main__":
    asyncio.run(main())

🛠️ Configuration
Environment Variables
Configure the library using a .env file in your project root or system environment variables.
Example .env:
# Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# Postgres Configuration
LOCAL_POSTGRES_HOST=localhost
LOCAL_POSTGRES_PORT=5432
LOCAL_POSTGRES_DB=your_db_name
LOCAL_POSTGRES_USER=postgres
LOCAL_POSTGRES_PASSWORD=your_password

# AWS Configuration (for Bedrock/S3)
AWS_REGION=ap-southeast-1
SECRET_NAME=your_secret_name

Notes:

For AWS Bedrock or S3,

aws configure
and 
aws configure set aws_secret_access_key

should be configured in the environment

set use_aws=True in DBConnection.
Ensure the input CSV file exists and matches the expected schema.


📚 License
MIT LicenseCopyright (c) 2025 Shashwat Roy  
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.