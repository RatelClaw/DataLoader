# EmbLoader: Embedding Loader Package

**EmbLoader** is a robust, extensible Python library for loading CSV data from S3 or local files into vector stores (**Postgres, FAISS, Chroma**) with embedding generation.  
It supports multiple embedding providers (**Bedrock, Gemini, Sentence-Transformers, OpenAI**) and two embedding modes:

- **Combined**: Concatenated text with a single embedding.
- **Separated**: Individual embeddings per column.

---

## 🚀 Features

- **Data Loading**: From S3 or local CSV files.
- **Embedding Generation**: Combined or separated modes.
- **Embedding Providers**: AWS Bedrock, Google Gemini, Sentence-Transformers (local), OpenAI.
- **Vector Stores**: Postgres (with pgvector), FAISS (in-memory), Chroma (persistent).
- **Update Support**: Detects new/updated/removed rows, handles soft deletes.
- **Scalability**: Batch operations, retries, connection pooling.
- **Extensibility**: Plugin-style for providers and stores.
- **Validation**: Schema, type, null checks.

---

## 📦 Installation

```bash
pip install embdloader
```

---

## ⚙️ Configuring Local Postgres / AWS / Env Vars

EmbLoader uses **environment variables** for configuration. For convenience, store them in a `.env` file at the **project root** (same level as `setup.py` and `README.md`).

### Example `.env`

```env
# Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# Local Postgres DB config
LOCAL_POSTGRES_HOST=localhost
LOCAL_POSTGRES_PORT=5432
LOCAL_POSTGRES_DB=DBname
LOCAL_POSTGRES_USER=postgres
LOCAL_POSTGRES_PASSWORD=password

# Optional AWS configs (for Bedrock/S3)
AWS_REGION=ap-southeast-1
SECRET_NAME=abc

etc

```

### How it works

- The library automatically reads `.env` using [`python-dotenv`](https://pypi.org/project/python-dotenv/).
- If `.env` is missing, it falls back to system environment variables.
- For production (AWS), set `use_aws=True` in `DBConnection` to fetch secrets from AWS Secrets Manager instead of `.env`.
- Embedding providers: Gemini, OpenAI, Bedrock, Sentence-Transformers
- Vector stores: Postgres (with pgvector), FAISS (in-memory), Chroma (persistent)

---

## 📚 License

This project is licensed under the **MIT License**:
MIT License

Copyright (c) 2025 Shashwat Roy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
