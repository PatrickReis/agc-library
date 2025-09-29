"""
Vector Store Factory - Unified interface for all storage providers
"""

import os
from typing import Dict, Any, Optional, Type
from .base_provider import VectorStoreProvider, StorageType
from ..logger.logger import get_logger

logger = get_logger("vector_store_factory")

class VectorStoreFactory:
    """
    Factory for creating vector store providers with unified configuration
    """

    @staticmethod
    def create_provider(storage_type: str,
                       config: Optional[Dict[str, Any]] = None,
                       **kwargs) -> VectorStoreProvider:
        """
        Create a vector store provider instance

        Args:
            storage_type: Type of storage (see StorageType enum)
            config: Configuration dictionary
            **kwargs: Additional configuration parameters

        Returns:
            Configured vector store provider

        Examples:
            # AWS OpenSearch
            store = VectorStoreFactory.create_provider(
                "aws_opensearch",
                {
                    "opensearch_endpoint": "https://search-example.us-east-1.es.amazonaws.com",
                    "region": "us-east-1",
                    "collection_name": "my-vectors"
                }
            )

            # Qdrant Cloud
            store = VectorStoreFactory.create_provider(
                "qdrant_cloud",
                {
                    "url": "https://example.qdrant.io",
                    "api_key": "your-api-key",
                    "collection_name": "my-collection"
                }
            )

            # Local ChromaDB
            store = VectorStoreFactory.create_provider(
                "chroma_local",
                {
                    "persist_directory": "./chroma_db",
                    "collection_name": "my-collection"
                }
            )
        """

        # Merge config with kwargs
        final_config = config or {}
        final_config.update(kwargs)

        # Normalize storage type
        try:
            storage_enum = StorageType(storage_type.lower())
        except ValueError:
            raise ValueError(f"Unsupported storage type: {storage_type}")

        # Import and create provider based on type
        if storage_enum in [StorageType.AWS_OPENSEARCH, StorageType.AWS_KENDRA, StorageType.AWS_S3_FAISS]:
            from .providers.aws_provider import AWSVectorProvider
            final_config['storage_type'] = storage_enum
            return AWSVectorProvider(final_config)

        elif storage_enum in [StorageType.QDRANT_CLOUD, StorageType.QDRANT_LOCAL]:
            from .providers.qdrant_provider import QdrantVectorProvider
            final_config['storage_type'] = storage_enum
            return QdrantVectorProvider(final_config)

        elif storage_enum in [StorageType.CHROMA_LOCAL, StorageType.CHROMA_CLOUD]:
            from .providers.chroma_provider import ChromaVectorProvider
            final_config['storage_type'] = storage_enum
            return ChromaVectorProvider(final_config)

        elif storage_enum == StorageType.PINECONE:
            from .providers.pinecone_provider import PineconeVectorProvider
            return PineconeVectorProvider(final_config)

        elif storage_enum == StorageType.FAISS_LOCAL:
            from .providers.faiss_provider import FAISSVectorProvider
            return FAISSVectorProvider(final_config)

        elif storage_enum == StorageType.WEAVIATE:
            from .providers.weaviate_provider import WeaviateVectorProvider
            return WeaviateVectorProvider(final_config)

        else:
            raise ValueError(f"Provider not implemented for storage type: {storage_enum}")

    @staticmethod
    def get_available_providers() -> Dict[str, Dict[str, Any]]:
        """
        Get information about available providers

        Returns:
            Dictionary with provider information
        """
        return {
            "aws_opensearch": {
                "description": "AWS OpenSearch Service with vector search capabilities",
                "type": "cloud",
                "features": ["vector_search", "full_text_search", "scalable", "managed"],
                "requirements": ["boto3", "opensearch-py", "requests-aws4auth"]
            },
            "aws_kendra": {
                "description": "AWS Kendra intelligent search service",
                "type": "cloud",
                "features": ["enterprise_search", "ml_powered", "managed"],
                "requirements": ["boto3", "langchain-aws"]
            },
            "aws_s3_faiss": {
                "description": "S3 storage with FAISS indexing",
                "type": "hybrid",
                "features": ["cost_effective", "scalable", "custom"],
                "requirements": ["boto3", "faiss-cpu"]
            },
            "qdrant_cloud": {
                "description": "Qdrant Cloud vector database",
                "type": "cloud",
                "features": ["vector_search", "fast", "managed", "real_time"],
                "requirements": ["qdrant-client"]
            },
            "qdrant_local": {
                "description": "Self-hosted Qdrant instance",
                "type": "self_hosted",
                "features": ["vector_search", "fast", "control", "privacy"],
                "requirements": ["qdrant-client"]
            },
            "chroma_local": {
                "description": "Local ChromaDB instance",
                "type": "local",
                "features": ["easy_setup", "development", "local"],
                "requirements": ["chromadb"]
            },
            "chroma_cloud": {
                "description": "ChromaDB Cloud service",
                "type": "cloud",
                "features": ["managed", "easy_setup", "scalable"],
                "requirements": ["chromadb"]
            },
            "pinecone": {
                "description": "Pinecone vector database",
                "type": "cloud",
                "features": ["vector_search", "managed", "fast", "popular"],
                "requirements": ["pinecone-client"]
            },
            "faiss_local": {
                "description": "Local FAISS index",
                "type": "local",
                "features": ["fast", "memory_efficient", "research"],
                "requirements": ["faiss-cpu"]
            },
            "weaviate": {
                "description": "Weaviate vector database",
                "type": "hybrid",
                "features": ["vector_search", "graph", "flexible", "open_source"],
                "requirements": ["weaviate-client"]
            }
        }

    @staticmethod
    def recommend_provider(use_case: str,
                          environment: str = "production",
                          budget: str = "medium") -> List[str]:
        """
        Recommend providers based on use case

        Args:
            use_case: Use case (e.g., "enterprise", "development", "research", "cost_sensitive")
            environment: Environment (production, development, testing)
            budget: Budget level (low, medium, high)

        Returns:
            List of recommended provider names
        """

        recommendations = {
            "enterprise": {
                "production": {
                    "high": ["aws_opensearch", "qdrant_cloud", "pinecone"],
                    "medium": ["aws_opensearch", "qdrant_cloud"],
                    "low": ["aws_s3_faiss", "qdrant_local"]
                },
                "development": {
                    "high": ["aws_opensearch", "chroma_cloud"],
                    "medium": ["chroma_local", "qdrant_local"],
                    "low": ["chroma_local", "faiss_local"]
                }
            },
            "research": {
                "production": {
                    "high": ["qdrant_cloud", "weaviate"],
                    "medium": ["qdrant_local", "chroma_cloud"],
                    "low": ["faiss_local", "chroma_local"]
                },
                "development": {
                    "high": ["chroma_local", "faiss_local"],
                    "medium": ["chroma_local", "faiss_local"],
                    "low": ["chroma_local", "faiss_local"]
                }
            },
            "cost_sensitive": {
                "production": {
                    "high": ["aws_s3_faiss", "qdrant_local"],
                    "medium": ["aws_s3_faiss", "qdrant_local"],
                    "low": ["faiss_local", "chroma_local"]
                },
                "development": {
                    "high": ["chroma_local", "faiss_local"],
                    "medium": ["chroma_local", "faiss_local"],
                    "low": ["chroma_local", "faiss_local"]
                }
            },
            "development": {
                "production": {
                    "high": ["chroma_cloud", "qdrant_cloud"],
                    "medium": ["chroma_local", "qdrant_local"],
                    "low": ["chroma_local", "faiss_local"]
                },
                "development": {
                    "high": ["chroma_local", "faiss_local"],
                    "medium": ["chroma_local", "faiss_local"],
                    "low": ["chroma_local", "faiss_local"]
                }
            }
        }

        return recommendations.get(use_case, {}).get(environment, {}).get(budget, ["chroma_local"])

def get_vector_store(storage_type: Optional[str] = None,
                    config: Optional[Dict[str, Any]] = None,
                    **kwargs) -> VectorStoreProvider:
    """
    Convenience function to get a vector store provider

    Args:
        storage_type: Storage type (if None, uses environment variable or default)
        config: Configuration dictionary
        **kwargs: Additional configuration

    Returns:
        Configured and initialized vector store provider

    Environment Variables:
        VECTOR_STORE_TYPE: Default storage type
        VECTOR_STORE_CONFIG: JSON string with configuration

    Examples:
        # Use environment configuration
        store = get_vector_store()

        # Specify type and config
        store = get_vector_store(
            "aws_opensearch",
            {"opensearch_endpoint": "https://..."}
        )

        # Quick setup for development
        store = get_vector_store("chroma_local")
    """

    # Determine storage type
    if not storage_type:
        storage_type = os.getenv('VECTOR_STORE_TYPE', 'chroma_local')

    # Merge configurations
    env_config = {}
    env_config_str = os.getenv('VECTOR_STORE_CONFIG')
    if env_config_str:
        import json
        try:
            env_config = json.loads(env_config_str)
        except json.JSONDecodeError:
            logger.warning("Invalid VECTOR_STORE_CONFIG environment variable")

    final_config = {}
    final_config.update(env_config)
    final_config.update(config or {})
    final_config.update(kwargs)

    # Create provider
    provider = VectorStoreFactory.create_provider(storage_type, final_config)

    # Initialize provider
    try:
        provider.initialize()
        logger.success(f"Vector store initialized: {storage_type}")
        return provider
    except Exception as e:
        logger.error(f"Failed to initialize vector store {storage_type}: {str(e)}")
        raise

def auto_configure_vector_store(use_case: str = "development",
                               environment: str = "development",
                               budget: str = "low") -> VectorStoreProvider:
    """
    Automatically configure and return the best vector store for your needs

    Args:
        use_case: Your use case (enterprise, development, research, cost_sensitive)
        environment: Environment (production, development, testing)
        budget: Budget level (low, medium, high)

    Returns:
        Configured vector store provider

    Example:
        # For development
        store = auto_configure_vector_store("development", "development", "low")

        # For production enterprise
        store = auto_configure_vector_store("enterprise", "production", "high")
    """

    recommendations = VectorStoreFactory.recommend_provider(use_case, environment, budget)

    # Try recommendations in order
    for storage_type in recommendations:
        try:
            logger.info(f"Trying to configure {storage_type}")

            # Get default config for this provider
            default_configs = {
                "chroma_local": {"persist_directory": "./chroma_db"},
                "faiss_local": {"index_path": "./faiss_index"},
                "qdrant_local": {"url": "http://localhost:6333"},
            }

            config = default_configs.get(storage_type, {})
            config["collection_name"] = f"agentcore_{use_case}"

            provider = get_vector_store(storage_type, config)
            logger.success(f"Auto-configured vector store: {storage_type}")
            return provider

        except Exception as e:
            logger.warning(f"Failed to configure {storage_type}: {str(e)}")
            continue

    # Fallback to simplest option
    logger.warning("All recommendations failed, falling back to local Chroma")
    return get_vector_store("chroma_local", {
        "persist_directory": "./chroma_db_fallback",
        "collection_name": "agentcore_fallback"
    })