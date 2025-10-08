import pandas as pd
from typing import List
from dataload.domain.entities import DataValidationError, TableSchema
from dataload.interfaces.embedding_provider import EmbeddingProviderInterface
from dataload.infrastructure.db.data_repository import DataRepositoryInterface
from dataload.interfaces.storage_loader import StorageLoaderInterface
from dataload.config import logger


class dataloadUseCase:
    """Use case for loading new data."""

    def __init__(
        self,
        repo: DataRepositoryInterface,
        embedding_service: EmbeddingProviderInterface,
        storage_loader: StorageLoaderInterface,
    ):
        self.repo = repo
        self.embedding_service = embedding_service
        self.storage_loader = storage_loader

    async def execute(
        self,
        s3_uri: str,
        table_name: str,
        embed_columns_names: List[str],
        pk_columns: List[str],
        create_table_if_not_exists: bool = True,
        embed_type: str = "combined",
    ):
        if embed_type not in ["combined", "separated"]:
            raise DataValidationError(
                f"Invalid embed_type: {embed_type}. Must be 'combined' or 'separated'."
            )

        df = self.storage_loader.load_csv(s3_uri)
        # Validate primary key and embed columns
        if not all(col in df.columns for col in pk_columns):
            raise DataValidationError(
                f"Primary key columns {pk_columns} not in DataFrame columns {list(df.columns)}"
            )
        if not all(col in df.columns for col in embed_columns_names):
            raise DataValidationError(
                f"Embed columns {embed_columns_names} not in DataFrame columns {list(df.columns)}"
            )

        # Validate data types
        column_types = {}
        if create_table_if_not_exists:
            column_types = await self.repo.create_table(
                table_name, df, pk_columns, embed_type, embed_columns_names
            )
        else:
            schema = await self.repo.get_table_schema(table_name)
            column_types = schema.columns
            await self._validate_schema(df, table_name, embed_columns_names)

        # Convert DataFrame to match Postgres types
        df_converted = df.copy()
        for col in df.columns:
            pg_type = column_types.get(col, "text")
            if pg_type in ("integer", "bigint"):
                try:
                    df_converted[col] = (
                        pd.to_numeric(df_converted[col], errors="coerce")
                        .fillna(0)
                        .astype("int64")
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to convert column {col} to numeric: {e}. Setting to 0."
                    )
                    df_converted[col] = 0
            elif pg_type == "date":
                df_converted[col] = pd.to_datetime(df_converted[col], errors="coerce")
            elif pg_type == "text[]":
                df_converted[col] = df_converted[col].apply(
                    lambda x: x if isinstance(x, list) else []
                )
            elif pg_type == "boolean":
                df_converted[col] = df_converted[col].apply(
                    lambda x: bool(x) if pd.notnull(x) else None
                )
            elif pg_type == "text":
                df_converted[col] = df_converted[col].astype(str).replace("nan", None)

        df_converted["embed_columns_names"] = [embed_columns_names] * len(df_converted)
        if embed_type == "combined":
            df_converted["embed_columns_value"] = df_converted[
                embed_columns_names
            ].apply(
                lambda row: self._format_embed_value(row, embed_columns_names), axis=1
            )
            embeddings = self.embedding_service.get_embeddings(
                df_converted["embed_columns_value"].tolist()
            )
            df_converted["embeddings"] = embeddings
        else:  # separated
            for col in embed_columns_names:
                texts = df_converted[col].astype(str).tolist()
                embeddings = self.embedding_service.get_embeddings(texts)
                df_converted[f"{col}_enc"] = embeddings
        df_converted["is_active"] = True
        logger.info(f"Inserting {len(df_converted)} rows into {table_name}")
        await self.repo.insert_data(table_name, df_converted, pk_columns)

    async def _validate_schema(
        self, df: pd.DataFrame, table_name: str, embed_columns_names: List[str]
    ):
        schema = await self.repo.get_table_schema(table_name)
        data_columns = await self.repo.get_data_columns(table_name)
        if set(df.columns) != set(data_columns):
            raise DataValidationError(
                f"CSV columns {list(df.columns)} do not match table data columns {data_columns}"
            )
        if not set(embed_columns_names).issubset(data_columns):
            raise DataValidationError(
                f"embed_columns_names {embed_columns_names} not in data columns {data_columns}"
            )
        # Type mapping
        pd_to_pg = {
            "object": "text",
            "float64": "double precision",
            "float32": "double precision",
            "int64": "bigint",
            "int32": "integer",
            "bool": "boolean",
            "datetime64": "date",
            "timedelta64": "interval",
        }
        for col in data_columns:
            dtype = str(df[col].dtype)
            # Handle array types
            if df[col].apply(lambda x: isinstance(x, list)).any():
                expected_pg = "text[]"
            else:
                # Check if numeric-like
                non_null = df[col].dropna()
                if dtype == "object" and len(non_null) > 0:
                    try:
                        if (
                            non_null.apply(
                                lambda x: isinstance(x, (str, float))
                                and str(x).replace(".", "").isdigit()
                            ).all()
                            and not non_null.apply(
                                lambda x: isinstance(x, str) and len(x) > 20
                            ).any()
                        ):
                            expected_pg = (
                                "bigint"
                                if non_null.astype(float).max() > 2**31 - 1
                                else "integer"
                            )
                        else:
                            expected_pg = "text"
                    except (ValueError, TypeError):
                        expected_pg = "text"
            actual_pg = schema.columns.get(col, "text")
            if expected_pg != actual_pg:
                raise DataValidationError(
                    f"Type mismatch for {col}: expected {expected_pg}, got {actual_pg}"
                )
            if not schema.nullables[col] and df[col].isnull().any():
                raise DataValidationError(f"Non-nullable column {col} has nulls")

    def _format_embed_value(
        self, row: pd.Series, embed_columns_names: List[str]
    ) -> str:
        """Format embed_columns_value with column names and handle diverse types."""
        parts = []
        for col in embed_columns_names:
            value = row[col]
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            elif isinstance(value, (int, float)):
                value = str(value)
            elif value is None:
                value = ""
            else:
                value = str(value)
            parts.append(f"{col}='{value}'")
        return ", ".join(parts)
