
**vector-dataloader** is a robust, extensible Python library for loading CSV data from S3 or local files into vector stores (**Postgres**, **FAISS**, **Chroma**) with embedding generation. It supports multiple embedding providers (**AWS Bedrock**, **Google Gemini**, **Sentence-Transformers**, **OpenAI**) and two embedding modes.

## 🚀 Features

- **Data Loading**: From S3 or local CSV files.
- **Embedding Generation**: Combined or separated modes.
- **Embedding Providers**: AWS Bedrock, Google Gemini, Sentence-Transformers, OpenAI.
- **Vector Stores**: Postgres (with pgvector), FAISS (in-memory), Chroma (persistent).
- **Update Support**: Detects new/updated/removed rows, handles soft deletes.
- **Scalability**: Batch operations, retries, connection pooling.
- **Extensibility**: Plugin-style for providers and stores.
- **Validation**: Schema, type, null checks.

---
## 📦 Installation (Lazy Imports Enabled!)

You only need to install the core package and the optional dependencies for the providers and stores you actually use.

Install the core package:


All Features	
Installs all optional dependencies.
````bash
pip install vector-dataloader[all]
pip install vector-dataloader
# or
uv add vector-dataloader


Optional Dependencies (Extras)
Use the following commands to install required extras.

Combination	Pip Install Command	Notes
ChromaDB only	pip install vector-dataloader[chroma]	Required for ChromaVectorStore.
FAISS only	pip install vector-dataloader[faiss]	Required for FaissVectorStore.
Google Gemini	pip install vector-dataloader[gemini]	Required for GeminiEmbeddingProvider.
Sentence-Transformers	pip install vector-dataloader[sentence-transformers]	Required for SentenceTransformersProvider.
OpenAI	pip install vector-dataloader[openai]	Required for OpenAIProvider.
All Features	pip install vector-dataloader[all]	Installs all optional dependencies.

Export to Sheets
Example: To use Postgres (core package) with the Gemini provider:

Bash

pip install vector-dataloader[gemini]
Example: To use ChromaDB with Sentence-Transformers:

Bash

pip install vector-dataloader[chroma,sentence-transformers]
⚙️ Usage
Below are example scripts for different combinations. Note that Postgres tests require setting up the connection parameters in a .env file.

Chroma with Gemini
Bash

# PIP INSTALL REQUIRED:
pip install vector-dataloader[chroma,gemini]
Python

import asyncio
# Imports now use the package name 'vector_dataloader'
from vector_dataloader.infrastructure.vector_stores.chroma_store import ChromaVectorStore
from vector_dataloader.infrastructure.storage.loaders import LocalLoader
from vector_dataloader.application.services.embedding.gemini_provider import GeminiEmbeddingProvider
from vector_dataloader.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    repo = ChromaVectorStore(mode='persistent', path='./my_chroma_db')
    embedding = GeminiEmbeddingProvider()
    loader = LocalLoader()
    use_case = dataloadUseCase(repo, embedding, loader)

    await use_case.execute(
        'data_to_load/sample.csv',
        'test_table_chroma_gemini',
        ['name', 'description'],
        ['id'],
        create_table_if_not_exists=True,
        embed_type='separated'
    )

if __name__ == '__main__':
    asyncio.run(main())
FAISS with Sentence-Transformers
Bash

# PIP INSTALL REQUIRED:
pip install vector-dataloader[faiss,sentence-transformers]
Python

import asyncio
from vector_dataloader.infrastructure.vector_stores.faiss_store import FaissVectorStore
from vector_dataloader.infrastructure.storage.loaders import LocalLoader
from vector_dataloader.application.services.embedding.sentence_transformers_provider import SentenceTransformersProvider
from vector_dataloader.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    repo = FaissVectorStore()
    embedding = SentenceTransformersProvider()
    loader = LocalLoader()
    use_case = dataloadUseCase(repo, embedding, loader)

    await use_case.execute(
        'data_to_load/sample.csv',
        'test_table_faiss_st',
        ['name', 'description'],
        ['id'],
        create_table_if_not_exists=True,
        embed_type='separated'
    )

if __name__ == '__main__':
    asyncio.run(main())
Postgres with Gemini
Bash

# PIP INSTALL REQUIRED:
pip install vector-dataloader[gemini]
Python

import asyncio
from vector_dataloader.infrastructure.db.db_connection import DBConnection
from vector_dataloader.infrastructure.db.data_repository import PostgresDataRepository
from vector_dataloader.infrastructure.storage.loaders import LocalLoader
from vector_dataloader.application.services.embedding.gemini_provider import GeminiEmbeddingProvider
from vector_dataloader.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    db_conn = DBConnection()
    await db_conn.initialize()
    repo = PostgresDataRepository(db_conn)
    embedding = GeminiEmbeddingProvider()
    loader = LocalLoader()
    use_case = dataloadUseCase(repo, embedding, loader)

    await use_case.execute(
        'data_to_load/sample.csv',
        'test_table_pg_gemini',
        ['name', 'description'],
        ['id'],
        create_table_if_not_exists=True,
        embed_type='separated'
    )
    # Don't forget to close the connection
    await db_conn.close()

if __name__ == '__main__':
    asyncio.run(main())


⚙️ Configuring Environment Variables
dataload uses environment variables for configuration, loaded from a .env file or system variables.
Example .env
# Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# Local Postgres DB config
LOCAL_POSTGRES_HOST=localhost
LOCAL_POSTGRES_PORT=5432
LOCAL_POSTGRES_DB=your_db_name
LOCAL_POSTGRES_USER=postgres
LOCAL_POSTGRES_PASSWORD=your_password

# Optional AWS configs (for Bedrock/S3)
AWS_REGION=ap-southeast-1
SECRET_NAME=your_secret_name

Notes

The .env file should be at the project root.
For AWS (Bedrock/S3), set use_aws=True in DBConnection to use AWS Secrets Manager.
Ensure data_to_load/sample.csv exists with columns id, name, description.

📚 License
MIT License
Copyright (c) 2025 Shashwat Roy
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.```
`````
