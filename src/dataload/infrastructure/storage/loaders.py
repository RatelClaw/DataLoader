import os
import pandas as pd
import boto3
from io import StringIO

from src.dataload.interfaces.storage_loader import StorageLoaderInterface
from src.dataload.config import logger
from src.dataload.domain.entities import DBOperationError


class S3Loader(StorageLoaderInterface):
    """Loads CSV files from AWS S3."""

    def __init__(self):
        self.s3 = boto3.client("s3")

    def load_csv(self, uri: str) -> pd.DataFrame:
        if not uri.startswith("s3://"):
            raise ValueError("URI must start with s3://")

        try:
            bucket, key = uri[5:].split("/", 1)
            obj = self.s3.get_object(Bucket=bucket, Key=key)
            df = pd.read_csv(StringIO(obj["Body"].read().decode("utf-8")))
            logger.info(f"Loaded CSV from S3: {bucket}/{key}, rows={len(df)}")
            return df
        except Exception as e:
            logger.error(f"S3 load error for {uri}: {e}")
            raise DBOperationError(f"Failed to load CSV from S3: {e}")


class LocalLoader(StorageLoaderInterface):
    """Loads CSV files from the local filesystem."""

    def __init__(self):
        pass

    def load_csv(self, path: str) -> pd.DataFrame:
        if not os.path.exists(path):
            raise ValueError(f"Local file not found: {path}")

        try:
            df = pd.read_csv(path)
            logger.info(f"Loaded local CSV: {path}, rows={len(df)}")
            return df
        except Exception as e:
            logger.error(f"Local load error for {path}: {e}")
            raise DBOperationError(f"Failed to load local CSV: {e}")
