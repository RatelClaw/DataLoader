import json
import boto3
from botocore.exceptions import ClientError
from typing import List
from dataload.interfaces.embedding_provider import EmbeddingProviderInterface
from dataload.config import (
    AWS_REGION,
    EMBEDDING_MODEL,
    CONTENT_TYPE,
    DEFAULT_VECTOR_VALUE,
    DEFAULT_DIMENSION,
    logger,
)


class BedrockEmbeddingProvider(EmbeddingProviderInterface):
    """Bedrock embedding provider."""

    def __init__(self):
        self.client = self._create_bedrock_client()

    def _create_bedrock_client(self):
        """Create Bedrock client."""
        try:
            return boto3.client("bedrock-runtime", region_name=AWS_REGION)
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
            raise

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        embeddings = []
        for text in texts:
            emb = self._create_description_embedding(text)
            embeddings.append(emb)
        return embeddings

    def _create_description_embedding(self, desc: str) -> list:
        """Create text embeddings."""
        if not desc or not isinstance(desc, str):
            logger.warning(f"Invalid description: {desc}")
            return [DEFAULT_VECTOR_VALUE] * DEFAULT_DIMENSION
        try:
            payload = {"inputText": desc}
            body = json.dumps(payload)
            response = self.client.invoke_model(
                body=body,
                modelId=EMBEDDING_MODEL,
                accept=CONTENT_TYPE,
                contentType=CONTENT_TYPE,
            )
            response_body = json.loads(response.get("body").read())
            return response_body.get(
                "embedding", [DEFAULT_VECTOR_VALUE] * DEFAULT_DIMENSION
            )
        except ClientError as e:
            logger.error(f"Error creating embedding: {str(e)}")
            return [DEFAULT_VECTOR_VALUE] * DEFAULT_DIMENSION
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode Bedrock response JSON: {str(e)}", exc_info=True
            )
            return [DEFAULT_VECTOR_VALUE] * DEFAULT_DIMENSION
        except Exception as e:
            logger.error(
                f"Unexpected error while creating embedding: {str(e)}", exc_info=True
            )
            return [DEFAULT_VECTOR_VALUE] * DEFAULT_DIMENSION
