# vector-dataloader: Embedding Loader Package

**vector-dataloader** is a robust, extensible Python library for loading CSV data from S3 or local files into vector stores (**Postgres**, **FAISS**, **Chroma**) with embedding generation. It supports multiple embedding providers (**AWS Bedrock**, **Google Gemini**, **Sentence-Transformers**, **OpenAI**) and two embedding modes:

- **Combined**: Concatenated text with a single embedding.
- **Separated**: Individual embeddings per column.

## 🚀 Features

- **Data Loading**: From S3 or local CSV files.
- **Embedding Generation**: Combined or separated modes.
- **Embedding Providers**: AWS Bedrock, Google Gemini, Sentence-Transformers, OpenAI.
- **Vector Stores**: Postgres (with pgvector), FAISS (in-memory), Chroma (persistent).
- **Update Support**: Detects new/updated/removed rows, handles soft deletes.
- **Scalability**: Batch operations, retries, connection pooling.
- **Extensibility**: Plugin-style for providers and stores.
- **Validation**: Schema, type, null checks.

---## Setup Instructions

To use this repo:

`````bash
git clone <repo-url>
cd DataLoader
uv venv
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate   # On Linux/Mac
uv pip install -r requirements.txt
uv pip install -e .[all,dev]

uv run main_local.py
# or
uv run main.py

## 📦 Installation

Install via pip or uv:

````bash
pip install vector-dataloader
# or
uv add vector-dataloader

Install optional dependencies for specific providers/stores:
pip install vector-dataloader[chroma,gemini]
# or
uv add vector-dataloader[chroma,gemini]

Available extras: gemini, sentence-transformers, openai, faiss, chroma, all.
⚙️ Usage
Below are example scripts for different combinations of vector stores and embedding providers. Save these as separate files (e.g., main_chroma_gemni.py) and run with uv run <filename>.py or python <filename>.py.
Chroma with Gemini
import asyncio
from dataload.infrastructure.vector_stores.chroma_store import ChromaVectorStore
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.gemini_provider import GeminiEmbeddingProvider
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    repo = ChromaVectorStore(mode='persistent', path='./my_chroma_db')
    embedding = GeminiEmbeddingProvider()
    loader = LocalLoader()
    use_case = dataloadUseCase(repo, embedding, loader)

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

Chroma with Sentence-Transformers
import asyncio
from dataload.infrastructure.vector_stores.chroma_store import ChromaVectorStore
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.sentence_transformers_provider import SentenceTransformersProvider
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    repo = ChromaVectorStore(mode='persistent', path='./my_chroma_db')
    embedding = SentenceTransformersProvider()
    loader = LocalLoader()
    use_case = dataloadUseCase(repo, embedding, loader)

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

FAISS with Gemini
import asyncio
from dataload.infrastructure.vector_stores.faiss_store import FaissVectorStore
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.gemini_provider import GeminiEmbeddingProvider
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    repo = FaissVectorStore()
    embedding = GeminiEmbeddingProvider()
    loader = LocalLoader()
    use_case = dataloadUseCase(repo, embedding, loader)

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

FAISS with Sentence-Transformers
import asyncio
from dataload.infrastructure.vector_stores.faiss_store import FaissVectorStore
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.sentence_transformers_provider import SentenceTransformersProvider
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    repo = FaissVectorStore()
    embedding = SentenceTransformersProvider()
    loader = LocalLoader()
    use_case = dataloadUseCase(repo, embedding, loader)

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

Postgres with Gemini
import asyncio
from dataload.infrastructure.db.db_connection import DBConnection
from dataload.infrastructure.db.data_repository import PostgresDataRepository
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.gemini_provider import GeminiEmbeddingProvider
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    db_conn = DBConnection()
    await db_conn.initialize()
    repo = PostgresDataRepository(db_conn)
    embedding = GeminiEmbeddingProvider()
    loader = LocalLoader()
    use_case = dataloadUseCase(repo, embedding, loader)

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

Postgres with Sentence-Transformers
import asyncio
from dataload.infrastructure.db.db_connection import DBConnection
from dataload.infrastructure.db.data_repository import PostgresDataRepository
from dataload.infrastructure.storage.loaders import LocalLoader
from dataload.application.services.embedding.sentence_transformers_provider import SentenceTransformersProvider
from dataload.application.use_cases.data_loader_use_case import dataloadUseCase

async def main():
    db_conn = DBConnection()
    await db_conn.initialize()
    repo = PostgresDataRepository(db_conn)
    embedding = SentenceTransformersProvider()
    loader = LocalLoader()
    use_case = dataloadUseCase(repo, embedding, loader)

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
