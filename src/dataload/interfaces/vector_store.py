from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import pandas as pd

# FIX: Corrected internal import
from dataload.domain.entities import TableSchema


class VectorStoreInterface(ABC):
    """Abstract interface for all Vector Store Repositories."""

    @abstractmethod
    async def get_table_schema(self, table_name: str) -> TableSchema:
        """Retrieves the schema of the specified table."""
        pass

    @abstractmethod
    async def insert_data(
        self, table_name: str, df: pd.DataFrame, pk_columns: List[str]
    ):
        """Inserts new data rows."""
        pass

    @abstractmethod
    async def update_data(
        self, table_name: str, df: pd.DataFrame, pk_columns: List[str]
    ):
        """Updates existing data or inserts new rows (upsert logic)."""
        pass

    @abstractmethod
    async def set_inactive(
        self, table_name: str, pks: List[tuple], pk_columns: List[str]
    ):
        """Soft-deletes rows by setting an 'is_active' flag to FALSE."""
        pass

    @abstractmethod
    async def get_active_data(
        self, table_name: str, columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Retrieves all active data from the table."""
        pass

    @abstractmethod
    async def get_embed_columns_names(self, table_name: str) -> List[str]:
        """Gets the list of columns used for embedding generation."""
        pass

    @abstractmethod
    async def get_data_columns(self, table_name: str) -> List[str]:
        """Gets all non-system data columns."""
        pass

    @abstractmethod
    async def create_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        pk_columns: List[str],
        embed_type: str = "combined",
        embed_columns_names: List[str] = [],
    ) -> Dict[str, str]:
        """Creates the table with necessary vector and metadata columns."""
        pass

    @abstractmethod
    async def add_column(self, table_name: str, column_name: str, column_type: str):
        """Adds a new column to an existing table."""
        pass

    @abstractmethod
    async def search(
        self,
        table_name: str,
        query_embedding: List[float],
        top_k: int = 5,
        embed_column: Optional[str] = None,
    ) -> List[Dict]:
        """Performs a similarity search."""
        pass
