import pandas as pd
from typing import List, Dict, Any
import chromadb
import json
from chromadb.config import Settings
from src.dataload.interfaces.vector_store import VectorStoreInterface
from src.dataload.domain.entities import (
    DataValidationError,
    DBOperationError,
    TableSchema,
)
from src.dataload.config import DEFAULT_DIMENTION, logger


class ChromaVectorStore(VectorStoreInterface):
    """ChromaDB vector store implementation with persistent and in-memory modes."""

    def __init__(self, mode: str = "persistent", path: str = "./chroma_db"):
        """
        Initialize ChromaVectorStore.

        Args:
            mode (str): 'persistent' for disk-based storage or 'in-memory' for RAM-only.
            path (str): Directory for persistent storage (ignored in 'in-memory' mode).
        """
        self.mode = mode
        self.path = path if mode == "persistent" else None
        self.client = self._create_client()
        self.collections: Dict[str, Any] = {}  # table_name -> collection
        self.schemas: Dict[str, TableSchema] = {}
        self.data: Dict[str, pd.DataFrame] = {}  # For simulating relational data
        if self.mode == "persistent":
            self._load_existing_collections()
    
    

    def _load_existing_collections(self):
        """Load all existing collection objects from the persistent client."""
        try:
            list_collections = self.client.list_collections()
            for collection_info in list_collections:
                name = collection_info.name
                # Get the actual collection object from the client
                collection = self.client.get_collection(name=name)
                self.collections[name] = collection
                logger.info(f"Loaded existing Chroma collection: {name}")

            # Note: Schemas and in-memory data (`self.data`) are not persisted
            # in this implementation, which might lead to other issues if you rely 
            # on them being present on a fresh run without calling `execute` again.

        except Exception as e:
            logger.warning(f"Failed to load existing collections: {e}")

    def _create_client(self):
        """Create Chroma client based on mode."""
        try:
            if self.mode == "persistent":
                logger.info(f"Creating persistent Chroma client at {self.path}")
                return chromadb.PersistentClient(
                    path=self.path, settings=Settings(anonymized_telemetry=False)
                )
            elif self.mode == "in-memory":
                logger.info("Creating in-memory Chroma client")
                return chromadb.Client(settings=Settings(anonymized_telemetry=False))
            else:
                raise ValueError(
                    f"Invalid mode: {self.mode}. Must be 'persistent' or 'in-memory'."
                )
        except Exception as e:
            logger.error(f"Failed to create Chroma client: {e}")
            raise DBOperationError(f"Chroma client initialization failed: {e}")

    def _serialize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize complex metadata values to strings for Chroma compatibility."""
        serialized = {}
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                serialized[key] = json.dumps(
                    value
                )  # Convert lists/dicts to JSON strings
            elif value is None:
                serialized[key] = ""
            elif isinstance(value, (str, int, float, bool)):
                serialized[key] = value
            else:
                serialized[key] = str(value)
        return serialized

    async def create_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        pk_columns: List[str],
        embed_type: str = "combined",
        embed_columns_names: List[str] = [],
    ) -> Dict[str, str]:
        """Create a table (collection) with schema."""
        if table_name in self.collections:
            logger.info(f"Table {table_name} already exists, returning schema")
            return self.schemas[table_name].columns

        if not all(col in df.columns for col in pk_columns):
            raise DataValidationError(
                f"Primary key columns {pk_columns} not in DataFrame"
            )

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
        try:
            self.collections[table_name] = self.client.get_or_create_collection(
                name=table_name
            )
            logger.info(f"Created Chroma collection {table_name}")
        except Exception as e:
            logger.error(f"Failed to create Chroma collection {table_name}: {e}")
            raise DBOperationError(f"Failed to create collection {table_name}: {e}")

        return column_types

    async def insert_data(
        self, table_name: str, df: pd.DataFrame, pk_columns: List[str]
    ):
        """Insert data into Chroma collection and in-memory DataFrame."""
        if table_name not in self.collections:
            raise DBOperationError(f"Table {table_name} not found")

        if not all(col in df.columns for col in pk_columns):
            raise DataValidationError(f"Primary keys {pk_columns} missing in DataFrame")

        self.data[table_name] = pd.concat(
            [self.data[table_name], df], ignore_index=True
        )

        # Prepare data for Chroma
        ids = [
            f"{row[pk_columns[0]]}" for _, row in df.iterrows()
        ]  # Extend for composite PKs
        metadatas = [
            self._serialize_metadata(row.to_dict()) for _, row in df.iterrows()
        ]
        enc_cols = [col for col in df.columns if col.endswith("_enc")]

        try:
            if "embeddings" in df.columns:
                # Combined mode
                embeddings = df["embeddings"].tolist()
                documents = df.get(
                    "embed_columns_value", pd.Series([""] * len(df))
                ).tolist()
                self.collections[table_name].add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )
            elif enc_cols:
                # Separated mode: create a collection per _enc column
                for enc_col in enc_cols:
                    collection_name = f"{table_name}_{enc_col}"
                    collection = self.client.get_or_create_collection(
                        name=collection_name
                    )
                    embeddings = df[enc_col].tolist()
                    documents = (
                        df[enc_col.replace("_enc", "")].astype(str).tolist()
                    )  # Original column as document
                    self.collections[collection_name] = collection
                    collection.add(
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids,
                    )
                    logger.info(
                        f"Inserted data into Chroma collection {collection_name}"
                    )
            else:
                logger.warning(
                    f"No embeddings found for {table_name}, inserting metadata only"
                )
                self.collections[table_name].add(
                    documents=df[pk_columns[0]].astype(str).tolist(),
                    metadatas=metadatas,
                    ids=ids,
                )
        except Exception as e:
            logger.error(f"Chroma insert error for {table_name}: {e}")
            raise DBOperationError(f"Failed to insert data into {table_name}: {e}")

    async def update_data(
        self, table_name: str, df: pd.DataFrame, pk_columns: List[str]
    ):
        """Update data in Chroma collection and in-memory DataFrame."""
        if table_name not in self.collections:
            raise DBOperationError(f"Table {table_name} not found")

        # Update in-memory DataFrame
        for _, row in df.iterrows():
            mask = self.data[table_name][pk_columns[0]] == row[pk_columns[0]]
            if mask.any():
                self.data[table_name].loc[mask, :] = row
            else:
                self.data[table_name] = pd.concat(
                    [self.data[table_name], pd.DataFrame([row])], ignore_index=True
                )

        # Update Chroma
        ids = [f"{row[pk_columns[0]]}" for _, row in df.iterrows()]
        metadatas = [
            self._serialize_metadata(row.to_dict()) for _, row in df.iterrows()
        ]
        enc_cols = [col for col in df.columns if col.endswith("_enc")]

        try:
            if "embeddings" in df.columns:
                embeddings = df["embeddings"].tolist()
                documents = df.get(
                    "embed_columns_value", pd.Series([""] * len(df))
                ).tolist()
                self.collections[table_name].upsert(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )
            elif enc_cols:
                for enc_col in enc_cols:
                    collection_name = f"{table_name}_{enc_col}"
                    collection = self.collections.get(
                        collection_name,
                        self.client.get_or_create_collection(name=collection_name),
                    )
                    embeddings = df[enc_col].tolist()
                    documents = df[enc_col.replace("_enc", "")].astype(str).tolist()
                    collection.upsert(
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids,
                    )
                    self.collections[collection_name] = collection
                    logger.info(f"Updated data in Chroma collection {collection_name}")
            else:
                self.collections[table_name].upsert(
                    documents=df[pk_columns[0]].astype(str).tolist(),
                    metadatas=metadatas,
                    ids=ids,
                )
        except Exception as e:
            logger.error(f"Chroma update error for {table_name}: {e}")
            raise DBOperationError(f"Failed to update data in {table_name}: {e}")

    async def set_inactive(
        self, table_name: str, pks: List[tuple], pk_columns: List[str]
    ):
        """Mark records as inactive by deleting from Chroma."""
        if table_name not in self.collections:
            raise DBOperationError(f"Table {table_name} not found")

        ids = [f"{pk[0]}" for pk in pks]  # Extend for composite PKs
        if "is_active" in self.data[table_name].columns:
            self.data[table_name].loc[
                self.data[table_name][pk_columns[0]].isin([pk[0] for pk in pks]),
                "is_active",
            ] = False
        try:
            self.collections[table_name].delete(ids=ids)
            # Delete from separated collections
            for collection_name in self.collections:
                if (
                    collection_name.startswith(f"{table_name}_")
                    and collection_name != table_name
                ):
                    self.collections[collection_name].delete(ids=ids)
        except Exception as e:
            logger.error(f"Chroma delete error for {table_name}: {e}")
            raise DBOperationError(f"Failed to delete data from {table_name}: {e}")

    async def get_active_data(
        self, table_name: str, columns: List[str]
    ) -> pd.DataFrame:
        """Retrieve active data from in-memory DataFrame."""
        if table_name not in self.data:
            return pd.DataFrame(columns=columns)
        if "is_active" in self.data[table_name].columns:
            return self.data[table_name][self.data[table_name]["is_active"] != False][
                columns
            ].reset_index(drop=True)
        return self.data[table_name][columns].reset_index(drop=True)

    async def get_embed_columns_names(self, table_name: str) -> List[str]:
        """Get embedding column names from schema."""
        if table_name not in self.schemas:
            raise DBOperationError(f"Table {table_name} not found")
        return json.loads(
            self.schemas[table_name].columns.get("embed_columns_names", "[]")
        )

    async def get_data_columns(self, table_name: str) -> List[str]:
        """Get data columns excluding extra and embedding columns."""
        if table_name in self.schemas:
            return [
                col
                for col in self.schemas[table_name].columns
                if col not in self.EXTRA_COLUMNS and not col.endswith("_enc")
            ]
        return []

    async def add_column(self, table_name: str, column_name: str, column_type: str):
        """Add a column to the schema and DataFrame."""
        if table_name not in self.schemas:
            raise DBOperationError(f"Table {table_name} not found")
        self.schemas[table_name].columns[column_name] = column_type
        self.data[table_name][column_name] = None

    async def search(
        self,
        table_name: str,
        query_embedding: List[float],
        top_k: int = 5,
        embed_column: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in the collection.

        Args:
            table_name (str): Name of the table/collection.
            query_embedding (List[float]): Query embedding vector.
            top_k (int): Number of results to return.
            embed_column (str, optional): Specific _enc column for separated mode (e.g., 'name_enc').

        Returns:
            List[Dict[str, Any]]: List of results with id, document, metadata, and distance.
        """
        if table_name not in self.collections:
            raise DBOperationError(f"Table {table_name} not found")

        collection_name = table_name
        if embed_column and embed_column.endswith("_enc"):
            collection_name = f"{table_name}_{embed_column}"
            if collection_name not in self.collections:
                raise DBOperationError(
                    f"Embedding column {embed_column} not found in {table_name}"
                )

        try:
            results = self.collections[collection_name].query(
                query_embeddings=[query_embedding], n_results=top_k
            )
            output = []
            for id_, doc, dist, meta in zip(
                results["ids"][0],
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0],
            ):
                # Deserialize metadata and exclude embedding columns
                deserialized_meta = {
                    k: json.loads(v) if k == "embed_columns_names" else v
                    for k, v in meta.items()
                }
                filtered_meta = {
                    k: v
                    for k, v in deserialized_meta.items()
                    if not k.endswith("_enc") and k != "embeddings"
                }
                output.append(
                    {
                        "id": id_,
                        "document": doc,
                        "metadata": filtered_meta,
                        "distance": dist,
                    }
                )
            logger.info(f"Retrieved {len(output)} results from {collection_name}")
            return output
        except Exception as e:
            logger.error(f"Chroma search error for {collection_name}: {e}")
            raise DBOperationError(f"Failed to search {collection_name}: {e}")
