from pydantic import BaseModel
from typing import List, Optional, Dict


class TableSchema(BaseModel):
    columns: Dict[str, str]  # column: type
    nullables: Dict[str, bool]  # column: is_nullable


class DataValidationError(Exception):
    pass


class DBOperationError(Exception):
    pass


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""

    pass
