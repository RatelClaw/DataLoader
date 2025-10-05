import logging
from logging import Formatter
import json
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# AWS-related configs
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
SECRET_NAME = os.environ.get("SECRET_NAME", "postgres/db-credentials")

# Embedding configs
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
CONTENT_TYPE = os.environ.get("CONTENT_TYPE", "application/json")
DEFAULT_DIMENTION = int(
    os.environ.get("DEFAULT_DIMENTION", 3072)
)  # matches Gemini embedding output

DEFAULT_VECTOR_VALUE = float(os.environ.get("DEFAULT_VECTOR_VALUE", 0.0))
MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 4000))
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0.7))
TITLE_SIMILARITY_THRESHOLD = float(os.environ.get("TITLE_SIMILARITY_THRESHOLD", 0.77))
DESC_SIMILARITY_THRESHOLD = float(os.environ.get("DESC_SIMILARITY_THRESHOLD", 0.77))
BEDROCK_ANTHROPIC_VERSION = os.environ.get(
    "BEDROCK_ANTHROPIC_VERSION", "bedrock-2023-05-31"
)

# Local Postgres configs
LOCAL_POSTGRES_HOST = os.environ.get("LOCAL_POSTGRES_HOST", "localhost")
LOCAL_POSTGRES_PORT = int(os.environ.get("LOCAL_POSTGRES_PORT", 5432))
LOCAL_POSTGRES_DB = os.environ.get("LOCAL_POSTGRES_DB", "DB_name")
LOCAL_POSTGRES_USER = os.environ.get("LOCAL_POSTGRES_USER", "postgres")
LOCAL_POSTGRES_PASSWORD = os.environ.get("LOCAL_POSTGRES_PASSWORD", "DB_password")

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class JSONFormatter(Formatter):
    def format(self, record):
        return json.dumps(
            {
                "time": self.formatTime(record),
                "name": record.name,
                "level": record.levelname,
                "msg": record.msg,
            }
        )
