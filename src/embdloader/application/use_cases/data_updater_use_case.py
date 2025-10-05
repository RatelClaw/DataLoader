import pandas as pd
from typing import List, Optional
from src.embdloader.domain.entities import DataValidationError
from src.embdloader.interfaces.embedding_provider import EmbeddingProviderInterface
from src.embdloader.infrastructure.db.data_repository import DataRepositoryInterface
from src.embdloader.interfaces.storage_loader import StorageLoaderInterface
from src.embdloader.config import logger, DEFAULT_DIMENTION


class DataUpdaterUseCase:
    """Use case for updating existing data."""

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
        pk_columns: List[str],
        new_embed_columns_names: Optional[List[str]] = None,
        embed_type: str = "combined",
    ):
        if embed_type not in ["combined", "separated"]:
            raise DataValidationError(
                f"Invalid embed_type: {embed_type}. Must be 'combined' or 'separated'."
            )

        df_new = self.storage_loader.load_csv(s3_uri)
        embed_columns_names = (
            new_embed_columns_names
            or await self.repo.get_embed_columns_names(table_name)
        )
        await self._validate_schema(df_new, table_name, embed_columns_names)
        df_new["embed_columns_names"] = [embed_columns_names] * len(df_new)
        if embed_type == "combined":
            df_new["embed_columns_value"] = df_new[embed_columns_names].apply(
                lambda row: self._format_embed_value(row, embed_columns_names), axis=1
            )
            df_new["is_active"] = True

            data_columns = await self.repo.get_data_columns(table_name)
            fetch_columns = pk_columns + data_columns + ["embed_columns_value"]
            df_existing = await self.repo.get_active_data(table_name, fetch_columns)

            # Removed
            removed_pks = self._get_removed_pks(df_existing, df_new, pk_columns)
            if removed_pks:
                logger.info(f"Setting {len(removed_pks)} rows inactive")
                await self.repo.set_inactive(table_name, removed_pks, pk_columns)

            # New and updated
            df_to_insert = df_new[
                ~df_new.set_index(pk_columns).index.isin(
                    df_existing.set_index(pk_columns).index
                )
            ]
            df_common_new = df_new[
                df_new.set_index(pk_columns).index.isin(
                    df_existing.set_index(pk_columns).index
                )
            ]
            df_common_existing = df_existing[
                df_existing.set_index(pk_columns).index.isin(
                    df_common_new.set_index(pk_columns).index
                )
            ]

            # Find changed
            changed_mask = (
                df_common_new[data_columns + ["embed_columns_value"]]
                != df_common_existing[data_columns + ["embed_columns_value"]]
            ).any(axis=1)
            df_changed = df_common_new[changed_mask].copy()

            # Always recompute embeddings for new and changed (or all if new_embed)
            texts_to_embed = pd.concat(
                [df_to_insert["embed_columns_value"], df_changed["embed_columns_value"]]
            )
            if new_embed_columns_names:  # Recompute all common if new config
                texts_to_embed = pd.concat(
                    [
                        texts_to_embed,
                        df_common_new[~changed_mask]["embed_columns_value"],
                    ]
                )
                df_unchanged = df_common_new[~changed_mask].copy()
                df_changed = pd.concat([df_changed, df_unchanged])

            if not texts_to_embed.empty:
                embeddings = self.embedding_service.get_embeddings(
                    texts_to_embed.tolist()
                )
                df_to_insert["embeddings"] = embeddings[: len(df_to_insert)]
                df_changed["embeddings"] = embeddings[len(df_to_insert) :]

            # Insert new, update changed
            df_upsert = pd.concat([df_to_insert, df_changed])
            if not df_upsert.empty:
                logger.info(f"Upserting {len(df_upsert)} rows (new + updated)")
                await self.repo.update_data(table_name, df_upsert, pk_columns)
        else:  # separated
            df_new["is_active"] = True

            data_columns = await self.repo.get_data_columns(table_name)
            fetch_columns = pk_columns + data_columns
            df_existing = await self.repo.get_active_data(table_name, fetch_columns)

            # Removed
            removed_pks = self._get_removed_pks(df_existing, df_new, pk_columns)
            if removed_pks:
                logger.info(f"Setting {len(removed_pks)} rows inactive")
                await self.repo.set_inactive(table_name, removed_pks, pk_columns)

            # If new_embed_columns_names, add new _enc columns
            schema = await self.repo.get_table_schema(table_name)
            current_enc_cols = [col for col in schema.columns if col.endswith("_enc")]
            current_embed_cols = [col[:-4] for col in current_enc_cols]
            embed_columns_names = new_embed_columns_names or current_embed_cols
            for col in embed_columns_names:
                enc_col = f"{col}_enc"
                if enc_col not in schema.columns:
                    await self.repo.add_column(
                        table_name, enc_col, f"vector({DEFAULT_DIMENTION})"
                    )

            # New and updated
            df_to_insert = df_new[
                ~df_new.set_index(pk_columns).index.isin(
                    df_existing.set_index(pk_columns).index
                )
            ]
            df_common_new = df_new[
                df_new.set_index(pk_columns).index.isin(
                    df_existing.set_index(pk_columns).index
                )
            ]
            df_common_existing = df_existing[
                df_existing.set_index(pk_columns).index.isin(
                    df_common_new.set_index(pk_columns).index
                )
            ]

            # Find changed
            changed_mask = (
                df_common_new[data_columns] != df_common_existing[data_columns]
            ).any(axis=1)
            df_changed = df_common_new[changed_mask].copy()

            # Always recompute embeddings for new and changed (or all if new_embed)
            df_recompute = pd.concat([df_to_insert, df_changed])
            if new_embed_columns_names:  # Recompute all common if new config
                df_unchanged = df_common_new[~changed_mask].copy()
                df_recompute = pd.concat([df_recompute, df_unchanged])

            if not df_recompute.empty:
                for col in embed_columns_names:
                    texts = df_recompute[col].astype(str).tolist()
                    embeddings = self.embedding_service.get_embeddings(texts)
                    df_recompute[f"{col}_enc"] = embeddings

            # Insert new, update changed
            df_upsert = df_recompute
            if not df_upsert.empty:
                logger.info(f"Upserting {len(df_upsert)} rows (new + updated)")
                await self.repo.update_data(table_name, df_upsert, pk_columns)

    def _get_removed_pks(
        self, df_existing: pd.DataFrame, df_new: pd.DataFrame, pk_columns: List[str]
    ) -> List[tuple]:
        existing_index = df_existing.set_index(pk_columns).index
        new_index = df_new.set_index(pk_columns).index
        removed_index = existing_index.difference(new_index)
        return [tuple(idx) for idx in removed_index]

    async def _validate_schema(
        self, df: pd.DataFrame, table_name: str, embed_columns_names: List[str]
    ):
        # Same as in loader
        schema = await self.repo.get_table_schema(table_name)
        data_columns = await self.repo.get_data_columns(table_name)
        if set(df.columns) != set(data_columns):
            raise DataValidationError(
                f"CSV columns {list(df.columns)} do not match table data columns {data_columns}"
            )
        if not set(embed_columns_names).issubset(data_columns):
            raise DataValidationError(
                f"embed_columns_names not in data columns {data_columns}"
            )
        pd_to_pg = {"object": "text", "float64": "double precision", "int64": "bigint"}
        for col in data_columns:
            pd_type = str(df[col].dtype)
            expected_pg = schema.columns[col]
            if pd_to_pg.get(pd_type) != expected_pg:
                raise DataValidationError(
                    f"Type mismatch for {col}: {pd_type} vs {expected_pg}"
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
