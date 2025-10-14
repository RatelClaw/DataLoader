from typing import Dict
from pydantic import BaseModel


class TableSchema(BaseModel):
    """Represents the schema of a data table."""

    columns: Dict[str, str]
    nullables: Dict[str, bool]


class DBOperationError(Exception):
    """Raised for errors during database/vector store operations."""

    pass


class DataValidationError(Exception):
    """Raised when input data (e.g., CSV) fails validation."""

    pass


class EmbeddingError(Exception):
    """Raised when an embedding provider fails to generate vectors."""

    pass
