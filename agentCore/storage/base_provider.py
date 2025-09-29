"""
Base classes for vector storage providers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

@dataclass
class Document:
    """Document representation for vector storage"""
    content: str
    metadata: Dict[str, Any]
    doc_id: Optional[str] = None
    embedding: Optional[List[float]] = None

@dataclass
class SearchResult:
    """Search result from vector store"""
    document: Document
    score: float
    rank: int

class StorageType(Enum):
    """Supported storage types"""
    AWS_OPENSEARCH = "aws_opensearch"
    AWS_KENDRA = "aws_kendra"
    AWS_S3_FAISS = "aws_s3_faiss"
    QDRANT_CLOUD = "qdrant_cloud"
    QDRANT_LOCAL = "qdrant_local"
    CHROMA_LOCAL = "chroma_local"
    CHROMA_CLOUD = "chroma_cloud"
    PINECONE = "pinecone"
    FAISS_LOCAL = "faiss_local"
    WEAVIATE = "weaviate"

class VectorStoreProvider(ABC):
    """Abstract base class for vector storage providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the vector store connection"""
        pass

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store

        Args:
            documents: List of documents to add

        Returns:
            List of document IDs
        """
        pass

    @abstractmethod
    def search(self,
               query: str,
               k: int = 5,
               filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search for similar documents

        Args:
            query: Search query
            k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    def search_by_vector(self,
                        vector: List[float],
                        k: int = 5,
                        filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search using a vector

        Args:
            vector: Query vector
            k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        Delete documents by IDs

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def update_document(self, doc_id: str, document: Document) -> bool:
        """
        Update a document

        Args:
            doc_id: Document ID to update
            document: New document content

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection/index

        Returns:
            Dictionary with collection metadata
        """
        pass

    @abstractmethod
    def create_collection(self, name: str, **kwargs) -> bool:
        """
        Create a new collection/index

        Args:
            name: Collection name
            **kwargs: Provider-specific parameters

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection/index

        Args:
            name: Collection name

        Returns:
            True if successful
        """
        pass

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the vector store

        Returns:
            Dictionary with health status
        """
        try:
            info = self.get_collection_info()
            return {
                "status": "healthy",
                "provider": self.__class__.__name__,
                "info": info
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.__class__.__name__,
                "error": str(e)
            }

class CloudVectorStoreProvider(VectorStoreProvider):
    """Base class for cloud-based vector stores"""

    @abstractmethod
    def get_usage_metrics(self) -> Dict[str, Any]:
        """Get usage metrics from cloud provider"""
        pass

    @abstractmethod
    def set_scaling_config(self, config: Dict[str, Any]) -> bool:
        """Configure auto-scaling settings"""
        pass

class LocalVectorStoreProvider(VectorStoreProvider):
    """Base class for local vector stores"""

    @abstractmethod
    def backup(self, backup_path: str) -> bool:
        """Create a backup of the local store"""
        pass

    @abstractmethod
    def restore(self, backup_path: str) -> bool:
        """Restore from a backup"""
        pass

    @abstractmethod
    def get_storage_size(self) -> Dict[str, Any]:
        """Get local storage usage information"""
        pass