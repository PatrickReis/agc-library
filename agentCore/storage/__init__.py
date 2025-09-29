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
from .providers.aws_provider import AWSVectorProvider
from .providers.qdrant_provider import QdrantVectorProvider
from .providers.chroma_provider import ChromaVectorProvider
from .providers.pinecone_provider import PineconeVectorProvider
from .providers.faiss_provider import FAISSVectorProvider
from .chunking.chunking_strategies import (
    ChunkingStrategy,
    RecursiveChunker,
    SemanticChunker,
    SlidingWindowChunker,
    get_chunking_strategy
)

__all__ = [
    "VectorStoreFactory",
    "get_vector_store",
    "AWSVectorProvider",
    "QdrantVectorProvider",
    "ChromaVectorProvider",
    "PineconeVectorProvider",
    "FAISSVectorProvider",
    "ChunkingStrategy",
    "RecursiveChunker",
    "SemanticChunker",
    "SlidingWindowChunker",
    "get_chunking_strategy"
]