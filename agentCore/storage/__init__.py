"""
Storage module for AgentCore - Multi-provider vector storage

This module provides a unified interface for various vector storage backends:
- AWS (OpenSearch, Kendra, S3 + FAISS)
- Qdrant (cloud and self-hosted)
- ChromaDB (local and cloud)
- Pinecone
- Weaviate
- FAISS (local and distributed)
"""

from .vector_store_factory import VectorStoreFactory, get_vector_store
from .base_provider import VectorStoreProvider, StorageType, Document, SearchResult

# Only import providers that exist
try:
    from .providers.aws_provider import AWSVectorProvider
except ImportError:
    AWSVectorProvider = None

__all__ = [
    "VectorStoreFactory",
    "get_vector_store",
    "VectorStoreProvider",
    "StorageType",
    "Document",
    "SearchResult"
]

if AWSVectorProvider:
    __all__.append("AWSVectorProvider")