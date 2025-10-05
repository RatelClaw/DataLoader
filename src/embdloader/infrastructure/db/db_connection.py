import json
import base64
import boto3
import asyncpg
from asyncpg import create_pool
from asyncpg.exceptions import PostgresError
from tenacity import retry, stop_after_attempt, wait_exponential
from src.embdloader.config import (
    AWS_REGION,
    SECRET_NAME,
    logger,
    LOCAL_POSTGRES_HOST,
    LOCAL_POSTGRES_PORT,
    LOCAL_POSTGRES_DB,
    LOCAL_POSTGRES_USER,
    LOCAL_POSTGRES_PASSWORD,
)
from contextlib import asynccontextmanager
from pgvector.asyncpg import register_vector
from src.embdloader.domain.entities import DBOperationError


class DBConnection:
    """Manages async Postgres connection pool with local credentials or AWS Secrets Manager."""

    def __init__(self, minconn=1, maxconn=20, creds: dict = None, use_aws=False):
        """
        :param minconn: min pool size
        :param maxconn: max pool size
        :param creds: dict override for credentials
        :param use_aws: whether to fetch from AWS Secrets Manager
        """
        self.minconn = minconn
        self.maxconn = maxconn
        self.use_aws = use_aws
        self.creds = creds or self._get_db_credentials()
        self.pool = None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _get_db_credentials(self):
        if self.use_aws:
            client = boto3.client("secretsmanager", region_name=AWS_REGION)
            response = client.get_secret_value(SecretId=SECRET_NAME)
            if "SecretString" in response:
                return json.loads(response["SecretString"])
            if "SecretBinary" in response:
                return json.loads(base64.b64decode(response["SecretBinary"]))
            raise ValueError("Invalid secret format")
        else:
            # fallback: local env variables
            return {
                "host": LOCAL_POSTGRES_HOST,
                "port": LOCAL_POSTGRES_PORT,
                "dbname": LOCAL_POSTGRES_DB,
                "user": LOCAL_POSTGRES_USER,
                "password": LOCAL_POSTGRES_PASSWORD,
            }

    async def initialize(self):
        """Initialize the connection pool."""
        try:
            self.pool = await create_pool(
                database=self.creds["dbname"],
                user=self.creds["user"],
                password=self.creds["password"],
                host=self.creds["host"],
                port=self.creds["port"],
                min_size=self.minconn,
                max_size=self.maxconn,
            )
            async with self.pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                await register_vector(conn)
        except PostgresError as e:
            logger.error(f"DB pool init error: {e}")
            raise DBOperationError(f"DB pool init failed: {e}")

    @asynccontextmanager
    async def get_connection(self):
        conn = None
        try:
            conn = await self.pool.acquire()
            await register_vector(conn)
            yield conn
        except PostgresError as e:
            logger.error(f"DB connection error: {e}")
            if conn:
                await conn.execute("ROLLBACK")
            raise DBOperationError(f"DB connection failed: {e}")
        finally:
            if conn:
                await self.pool.release(conn)
