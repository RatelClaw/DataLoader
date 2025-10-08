import json
import base64
import boto3
import asyncpg
from asyncio import TimeoutError  

from contextlib import asynccontextmanager
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pgvector.asyncpg import register_vector
from dataload.config import (
    AWS_REGION, SECRET_NAME, logger,
    LOCAL_POSTGRES_HOST, LOCAL_POSTGRES_PORT,
    LOCAL_POSTGRES_DB, LOCAL_POSTGRES_USER, LOCAL_POSTGRES_PASSWORD
)
from dataload.domain.entities import DBOperationError

class DBConnection:
    """Manages the PostgreSQL connection pool with pgvector and AWS Secrets support."""
    
    def __init__(self, minconn: int = 1, maxconn: int = 20, creds: dict = None, use_aws: bool = False):
        self.minconn = minconn
        self.maxconn = maxconn
        self.use_aws = use_aws
        self.creds = creds or self._get_db_credentials()
        self.pool = None

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception) # Retries on any exception during cred retrieval
    )
    def _get_db_credentials(self) -> dict:
        """Retrieves database credentials from AWS Secrets Manager or local env."""
        if self.use_aws:
            logger.info("Retrieving DB credentials from AWS Secrets Manager...")
            client = boto3.client("secretsmanager", region_name=AWS_REGION)
            response = client.get_secret_value(SecretId=SECRET_NAME)
            
            if "SecretString" in response:
                return json.loads(response["SecretString"])
            if "SecretBinary" in response:
                return json.loads(base64.b64decode(response["SecretBinary"]))
            
            raise DBOperationError("Invalid secret format from AWS Secrets Manager.")
        
        logger.info("Using local environment variables for DB credentials.")
        return {
            "host": LOCAL_POSTGRES_HOST,
            "port": LOCAL_POSTGRES_PORT,
            "dbname": LOCAL_POSTGRES_DB,
            "user": LOCAL_POSTGRES_USER,
            "password": LOCAL_POSTGRES_PASSWORD,
        }

    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_exponential(multiplier=1, min=4, max=20),
        retry=retry_if_exception_type(asyncpg.PostgresError) # Retry on DB specific errors
    )
    async def initialize(self):
        """Initializes the asyncpg connection pool and pgvector extension."""
        if self.pool:
            return # Already initialized

        logger.info(f"Connecting to Postgres at {self.creds['host']}:{self.creds['port']}")
        
        self.pool = await asyncpg.create_pool(
            database=self.creds["dbname"],
            user=self.creds["user"],
            password=self.creds["password"],
            host=self.creds["host"],
            port=self.creds["port"],
            min_size=self.minconn,
            max_size=self.maxconn,
            timeout=10 # Add timeout for robustness
        )
        
        # FIX: Ensure vector extension is present and registered
        async with self.pool.acquire() as conn:
            # Check if extension exists before trying to create it (safer)
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            await register_vector(conn)
            
        logger.info("DB pool initialized and pgvector registered.")

    @asynccontextmanager
    async def get_connection(self):
        """Provides an asynchronous connection, ensuring pgvector is registered on the connection."""
        conn = None
        try:
            # FIX: Use a simple retry for pool acquisition in case of momentary pool exhaustion
            conn = await self.pool.acquire(timeout=5)
            await register_vector(conn) # Re-register for safety per connection
            yield conn
        except TimeoutError as e:
            logger.error("DB connection pool acquisition timed out.")
            raise DBOperationError(f"DB pool acquisition failed: {e}")

        except asyncpg.PostgresError as e:
            logger.error(f"DB transaction error (rolling back): {e}")
            if conn:
                await conn.execute("ROLLBACK")
            raise DBOperationError(f"DB operation failed: {e}")
        finally:
            if conn:
                await self.pool.release(conn)
                
    async def close(self):
        """Closes the connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("DB pool closed.")
