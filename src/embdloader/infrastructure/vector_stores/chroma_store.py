import pandas as pd
from typing import List, Dict, Any
import chromadb

from src.embdloader.interfaces.vector_store import VectorStoreInterface
from src.embdloader.domain.entities import DataValidationError, DBOperationError, TableSchema
from src.embdloader.config import DEFAULT_DIMENTION 

class ChromaVectorStore(VectorStoreInterface):
    """ChromaDB vector store implementation."""

    def __init__(self):
        self.client = chromadb.Client()
        self.collections: Dict[str, Any] = {}  # table_name -> collection
        self.schemas: Dict[str, TableSchema] = {}
        self.data: Dict[str, pd.DataFrame] = {}

    # ---------------------------
    # Core methods
    # ---------------------------
    async def create_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        pk_columns: List[str],
        embed_type: str = "combined",
        embed_columns_names: List[str] = []
    ) -> Dict[str, str]:
        if table_name in self.collections:
            return self.schemas[table_name].columns

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
            columns=column_types,
            nullables={col: True for col in column_types}
        )
        self.data[table_name] = pd.DataFrame(columns=list(column_types.keys()))
        self.collections[table_name] = self.client.create_collection(name=table_name)

        return column_types

    async def insert_data(self, table_name: str, df: pd.DataFrame, pk_columns: List[str]):
        if table_name not in self.collections:
            raise DBOperationError(f"Table {table_name} not found")

        if not all(col in df.columns for col in pk_columns):
            raise DataValidationError(f"Primary keys {pk_columns} missing in DataFrame")

        self.data[table_name] = pd.concat([self.data[table_name], df], ignore_index=True)

        # Insert into Chroma
        if "embeddings" in df.columns:
            self.collections[table_name].add(
                embeddings=df["embeddings"].tolist(),
                documents=df.get("embed_columns_value", pd.Series([""]*len(df))).tolist(),
                ids=[str(i) for i in df.index]
            )

    async def search(self, table_name: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if table_name not in self.collections:
            raise DBOperationError(f"Table {table_name} not found")

        results = self.collections[table_name].query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        output = []
        for ids, docs, dists in zip(results["ids"], results["documents"], results["distances"]):
            output.append({
                "id": ids,
                "document": docs,
                "distance": dists
            })
        return output

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
        return [c for c in self.schemas[table_name].columns.keys() if "_enc" in c or c == "embeddings"]

    async def set_inactive(self, table_name: str, pk_values: list):
        if table_name not in self.data or not pk_values:
            return
        pk_col = list(self.data[table_name].columns[:1])[0]  # assume first column is PK
        self.data[table_name].loc[self.data[table_name][pk_col].isin(pk_values), "is_active"] = False

    async def update_data(self, table_name: str, df: pd.DataFrame, pk_columns: list):
        if table_name not in self.data:
            raise DBOperationError(f"Table {table_name} not found")
        existing = self.data[table_name]
        for pk in pk_columns:
            if pk not in df.columns or pk not in existing.columns:
                continue
            for _, row in df.iterrows():
                existing_idx = existing[existing[pk] == row[pk]].index
                if not existing_idx.empty:
                    existing.loc[existing_idx, :] = row
                else:
                    existing = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
        self.data[table_name] = existing
