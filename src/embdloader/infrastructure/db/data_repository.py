from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Optional
from asyncpg.exceptions import PostgresError
from src.embdloader.domain.entities import (
    TableSchema,
    DBOperationError,
    DataValidationError,
)
from src.embdloader.infrastructure.db.db_connection import DBConnection
from src.embdloader.config import logger, DEFAULT_DIMENTION
from tenacity import retry, stop_after_attempt, wait_fixed


class DataRepositoryInterface(ABC):
    @abstractmethod
    async def get_table_schema(self, table_name: str) -> TableSchema:
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
    async def add_column(self, table_name: str, column_name: str, column_type: str):
        pass


class PostgresDataRepository(DataRepositoryInterface):
    """Postgres implementation of data repository using asyncpg."""

    EXTRA_COLUMNS = [
        "embed_columns_names",
        "embed_columns_value",
        "embeddings",
        "is_active",
    ]

    def __init__(self, db_connection: DBConnection):
        self.db = db_connection

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def get_table_schema(self, table_name: str) -> TableSchema:
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = $1;
        """
        async with self.db.get_connection() as conn:
            rows = await conn.fetch(query, table_name)
        if not rows:
            raise DBOperationError(f"Table {table_name} not found")
        columns = {row["column_name"]: row["data_type"] for row in rows}
        nullables = {row["column_name"]: row["is_nullable"] == "YES" for row in rows}
        return TableSchema(columns=columns, nullables=nullables)

    async def create_table(
        self,
        table_name: str,
        df: pd.DataFrame,
        pk_columns: List[str],
        embed_type: str = "combined",
        embed_columns_names: List[str] = [],
    ) -> Dict[str, str]:
        """Create table based on DataFrame schema and additional columns, return column types."""
        # Validate primary key columns
        if not all(col in df.columns for col in pk_columns):
            raise DataValidationError(
                f"Primary key columns {pk_columns} not in DataFrame columns {list(df.columns)}"
            )
        for col in pk_columns:
            if df[col].isnull().any():
                raise DataValidationError(
                    f"Primary key column {col} contains null values"
                )

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
        column_types = {}
        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            # Check if column contains lists (e.g., project_type, source_urls)
            if df[col].apply(lambda x: isinstance(x, list)).any():
                pg_type = "text[]"
            else:
                # Force text for ID columns
                if "id" in col.lower():
                    pg_type = "text"
                else:
                    # For object columns, check if they are numeric-like
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
                                pg_type = (
                                    "bigint"
                                    if non_null.astype(float).max() > 2**31 - 1
                                    else "integer"
                                )
                            else:
                                pg_type = "text"
                        except (ValueError, TypeError):
                            pg_type = "text"
                    else:
                        pg_type = pd_to_pg.get(dtype, "text")
            not_null = " NOT NULL" if col in pk_columns else ""
            columns.append(f"{col} {pg_type}{not_null}")
            column_types[col] = pg_type
        # Add embed_columns_names always
        columns.append("embed_columns_names text[]")
        column_types["embed_columns_names"] = "text[]"
        if embed_type == "combined":
            columns.append("embed_columns_value text")
            columns.append(f"embeddings vector({DEFAULT_DIMENTION})")
            column_types["embed_columns_value"] = "text"
            column_types["embeddings"] = f"vector({DEFAULT_DIMENTION})"
        elif embed_type == "separated":
            for col in embed_columns_names:
                enc_col = f"{col}_enc"
                columns.append(f"{enc_col} vector({DEFAULT_DIMENTION})")
                column_types[enc_col] = f"vector({DEFAULT_DIMENTION})"
        columns.append("is_active boolean DEFAULT true")
        column_types["is_active"] = "boolean"
        # Add primary key constraint
        columns.append(f"PRIMARY KEY ({', '.join(pk_columns)})")

        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        try:
            async with self.db.get_connection() as conn:
                async with conn.transaction():
                    await conn.execute(query)
            return column_types
        except PostgresError as e:
            logger.error(f"Table creation error: {e}")
            raise DBOperationError(f"Failed to create table {table_name}: {e}")

    async def add_column(self, table_name: str, column_name: str, column_type: str):
        query = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
        try:
            async with self.db.get_connection() as conn:
                async with conn.transaction():
                    await conn.execute(query)
        except PostgresError as e:
            logger.error(f"Add column error: {e}")
            raise DBOperationError(
                f"Failed to add column {column_name} to {table_name}: {e}"
            )

    async def insert_data(
        self, table_name: str, df: pd.DataFrame, pk_columns: List[str]
    ):
        if df.empty:
            return
        columns = list(df.columns)
        # Get column types from schema (or created table)
        try:
            schema = await self.get_table_schema(table_name)
            column_types = schema.columns
        except DBOperationError:
            raise DBOperationError(
                f"Table {table_name} must be created before insertion"
            )

        # Convert DataFrame values to match Postgres types
        df_converted = df.copy()
        for col in columns:
            pg_type = column_types.get(col, "text")
            if pg_type in ("integer", "bigint"):
                df_converted[col] = (
                    pd.to_numeric(df_converted[col], errors="coerce")
                    .fillna(0)
                    .astype("int64")
                )
                nan_count = df[col].isnull().sum()
                if nan_count > 0:
                    logger.warning(
                        f"Column {col} had {nan_count} NaN values converted to 0"
                    )
            elif pg_type == "date":
                df_converted[col] = pd.to_datetime(df_converted[col], errors="coerce")
                df_converted[col] = df_converted[col].apply(
                    lambda x: x if pd.notnull(x) else None
                )
            elif pg_type == "text[]":
                df_converted[col] = df_converted[col].apply(
                    lambda x: x if isinstance(x, list) else []
                )
            elif pg_type == "boolean":
                df_converted[col] = df_converted[col].apply(
                    lambda x: bool(x) if pd.notnull(x) else None
                )
            elif pg_type == "text":
                df_converted[col] = df_converted[col].apply(
                    lambda x: str(x) if pd.notnull(x) else None
                )
            elif pg_type == f"vector({DEFAULT_DIMENTION})":
                df_converted[col] = df_converted[col].apply(
                    lambda x: [float(v) for v in x] if x is not None else None
                )

        values = [tuple(row) for row in df_converted.itertuples(index=False, name=None)]
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(f'${i+1}' for i in range(len(columns)))})"
        try:
            async with self.db.get_connection() as conn:
                async with conn.transaction():
                    await conn.executemany(query, values)
        except PostgresError as e:
            logger.error(f"Data insertion error: {e}")
            raise DBOperationError(f"Failed to insert data into {table_name}: {e}")

    async def update_data(
        self, table_name: str, df: pd.DataFrame, pk_columns: List[str]
    ):
        if df.empty:
            return
        columns = list(df.columns)
        set_clause = ", ".join(
            [f"{col} = EXCLUDED.{col}" for col in columns if col not in pk_columns]
        )
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(f'${i+1}' for i in range(len(columns)))})
        ON CONFLICT ({', '.join(pk_columns)}) DO UPDATE SET {set_clause}
        """
        # Convert DataFrame values as in insert_data
        schema = await self.get_table_schema(table_name)
        column_types = schema.columns
        df_converted = df.copy()
        for col in columns:
            pg_type = column_types.get(col, "text")
            if pg_type in ("integer", "bigint"):
                df_converted[col] = (
                    pd.to_numeric(df_converted[col], errors="coerce")
                    .fillna(0)
                    .astype("int64")
                )
                nan_count = df[col].isnull().sum()
                if nan_count > 0:
                    logger.warning(
                        f"Column {col} had {nan_count} NaN values converted to 0"
                    )
            elif pg_type == "date":
                df_converted[col] = pd.to_datetime(df_converted[col], errors="coerce")
                df_converted[col] = df_converted[col].apply(
                    lambda x: x if pd.notnull(x) else None
                )
            elif pg_type == "text[]":
                df_converted[col] = df_converted[col].apply(
                    lambda x: x if isinstance(x, list) else []
                )
            elif pg_type == "boolean":
                df_converted[col] = df_converted[col].apply(
                    lambda x: bool(x) if pd.notnull(x) else None
                )
            elif pg_type == "text":
                df_converted[col] = df_converted[col].apply(
                    lambda x: str(x) if pd.notnull(x) else None
                )
            elif pg_type == f"vector({DEFAULT_DIMENTION})":
                df_converted[col] = df_converted[col].apply(
                    lambda x: [float(v) for v in x] if x is not None else None
                )

        values = [tuple(row) for row in df_converted.itertuples(index=False, name=None)]
        async with self.db.get_connection() as conn:
            async with conn.transaction():
                await conn.executemany(query, values)

    async def set_inactive(
        self, table_name: str, pks: List[tuple], pk_columns: List[str]
    ):
        if not pks:
            return
        query = f"UPDATE {table_name} SET is_active = FALSE WHERE ({', '.join(pk_columns)}) IN (VALUES ($1{', $2' * (len(pk_columns)-1)})) AND is_active"
        async with self.db.get_connection() as conn:
            async with conn.transaction():
                for pk in pks:
                    await conn.execute(query, *pk)

    async def get_active_data(
        self, table_name: str, columns: List[str]
    ) -> pd.DataFrame:
        query = f"SELECT {', '.join(columns)} FROM {table_name} WHERE is_active"
        async with self.db.get_connection() as conn:
            rows = await conn.fetch(query)
        return pd.DataFrame(rows, columns=columns)

    async def get_embed_columns_names(self, table_name: str) -> List[str]:
        query = f"SELECT embed_columns_names FROM {table_name} WHERE is_active LIMIT 1"
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(query)
        if row:
            return row["embed_columns_names"]  # array as list
        raise DBOperationError(f"No active rows in {table_name}")

    async def get_data_columns(self, table_name: str) -> List[str]:
        schema = await self.get_table_schema(table_name)
        return [
            col
            for col in schema.columns
            if col not in self.EXTRA_COLUMNS and not col.endswith("_enc")
        ]
