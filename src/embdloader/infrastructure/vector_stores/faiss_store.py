import pandas as pd
import faiss
import numpy as np
from typing import List, Dict, Any

from src.embdloader.interfaces.vector_store import VectorStoreInterface
from src.embdloader.domain.entities import (
    DataValidationError,
    DBOperationError,
    TableSchema,
)
from src.embdloader.config import DEFAULT_DIMENTION  # Change as per embedding size


class FaissVectorStore(VectorStoreInterface):
    """FAISS in-memory vector store implementation."""

    def __init__(self):
        self.indexes: Dict[str, faiss.IndexFlatL2] = {}  # table_name -> index
        self.data: Dict[str, pd.DataFrame] = {}  # table_name -> data
        self.schemas: Dict[str, TableSchema] = {}  # table_name -> schema

    # ---------------------------
    # Core methods
    # ---------------------------
    async def create_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        pk_columns: List[str],
        embed_type: str = "combined",
        embed_columns_names: List[str] = [],
    ) -> Dict[str, str]:
        if table_name in self.indexes:
            return self.schemas[table_name].columns

        # Simulate schema
        column_types = {col: "text" for col in df.columns}
        column_types["embed_columns_names"] = "text[]"

        if embed_type == "combined":
            column_types["embed_columns_value"] = "text"
            column_types["embeddings"] = f"vector({DEFAULT_DIMENTION})"
        else:
            for col in embed_columns_names:
                column_types[f"{col}_enc"] = f"vector({DEFAULT_DIMENTION})"

        column_types["is_active"] = "boolean"

        self.schemas[table_name] = TableSchema(
            columns=column_types, nullables={col: True for col in column_types}
        )
        self.data[table_name] = pd.DataFrame(columns=list(column_types.keys()))
        self.indexes[table_name] = faiss.IndexFlatL2(DEFAULT_DIMENTION)

        return column_types

    async def insert_data(
        self, table_name: str, df: pd.DataFrame, pk_columns: List[str]
    ):
        if table_name not in self.data:
            raise DBOperationError(f"Table {table_name} not found")

        if not all(col in df.columns for col in pk_columns):
            raise DataValidationError(f"Primary keys {pk_columns} missing in DataFrame")

        # Insert into simulated table
        self.data[table_name] = pd.concat(
            [self.data[table_name], df], ignore_index=True
        )

        # Add embeddings to FAISS
        if "embeddings" in df.columns:
            embeddings = np.array(df["embeddings"].tolist()).astype("float32")
            self.indexes[table_name].add(embeddings)

    async def search(
        self, table_name: str, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if table_name not in self.indexes:
            raise DBOperationError(f"Table {table_name} not found")

        index = self.indexes[table_name]
        query = np.array([query_embedding]).astype("float32")
        distances, indices = index.search(query, top_k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.data[table_name]):
                row = self.data[table_name].iloc[idx].to_dict()
                row["distance"] = float(dist)
                results.append(row)

        return results

    # ---------------------------
    # Implement abstract methods
    # ---------------------------
    async def add_column(self, table_name: str, column_name: str, column_type: str):
        if table_name not in self.schemas:
            raise DBOperationError(f"Table {table_name} not found")
        self.schemas[table_name].columns[column_name] = column_type
        self.data[table_name][column_name] = None

    async def get_active_data(self, table_name: str):
        if table_name not in self.data:
            return pd.DataFrame()
        if "is_active" in self.data[table_name].columns:
            return self.data[table_name][self.data[table_name]["is_active"] != False]
        return self.data[table_name]

    async def get_data_columns(self, table_name: str):
        if table_name in self.schemas:
            return list(self.schemas[table_name].columns.keys())
        return []

    async def get_embed_columns_names(self, table_name: str):
        if table_name not in self.schemas:
            return []
        return [
            c
            for c in self.schemas[table_name].columns.keys()
            if "_enc" in c or c == "embeddings"
        ]

    async def set_inactive(self, table_name: str, pk_values: list):
        if table_name not in self.data or not pk_values:
            return
        pk_col = list(self.data[table_name].columns[:1])[0]  # assume first column is PK
        self.data[table_name].loc[
            self.data[table_name][pk_col].isin(pk_values), "is_active"
        ] = False

    async def update_data(self, table_name: str, df: pd.DataFrame, pk_columns: list):
        if table_name not in self.data:
            raise DBOperationError(f"Table {table_name} not found")
        # Simple replace rows with same PK
        existing = self.data[table_name]
        for pk in pk_columns:
            if pk not in df.columns or pk not in existing.columns:
                continue
            for _, row in df.iterrows():
                existing_idx = existing[existing[pk] == row[pk]].index
                if not existing_idx.empty:
                    existing.loc[existing_idx, :] = row
                else:
                    existing = pd.concat(
                        [existing, pd.DataFrame([row])], ignore_index=True
                    )
        self.data[table_name] = existing
