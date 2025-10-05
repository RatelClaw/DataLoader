from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict


class VectorStoreInterface(ABC):

    @abstractmethod
    async def create_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        pk_columns: List[str],
        embed_type: str = "combined",
        embed_columns_names: List[str] = [],
    ) -> Dict[str, str]:
        pass

    @abstractmethod
    async def insert_data(
        self, table_name: str, df: pd.DataFrame, pk_columns: List[str]
    ):
        pass

    @abstractmethod
    async def update_data(
        self, table_name: str, df: pd.DataFrame, pk_columns: List[str]
    ):
        pass

    @abstractmethod
    async def set_inactive(
        self, table_name: str, pks: List[tuple], pk_columns: List[str]
    ):
        pass

    @abstractmethod
    async def get_active_data(
        self, table_name: str, columns: List[str]
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    async def get_embed_columns_names(self, table_name: str) -> List[str]:
        pass

    @abstractmethod
    async def get_data_columns(self, table_name: str) -> List[str]:
        pass

    @abstractmethod
    async def add_column(self, table_name: str, column_name: str, column_type: str):
        pass
