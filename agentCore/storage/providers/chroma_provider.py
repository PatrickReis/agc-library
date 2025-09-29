"""
ChromaDB provider for local vector storage
"""

from typing import List, Dict, Any, Optional
from ..base_provider import VectorStoreProvider, Document, SearchResult
from ...logger.logger import get_logger

logger = get_logger("chroma_provider")

class ChromaVectorProvider(VectorStoreProvider):
    """ChromaDB implementation for local vector storage"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.persist_directory = config.get("persist_directory", "./chroma_db")
        self.collection_name = config.get("collection_name", "default")
        self.client = None
        self.collection = None

    def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            import chromadb
            from chromadb.config import Settings

            # Create client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Using existing ChromaDB collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(name=self.collection_name)
                logger.info(f"Created new ChromaDB collection: {self.collection_name}")

        except ImportError:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")

    def add_documents(self, documents: List[str], metadatas: Optional[List[Dict]] = None):
        """Add documents to the collection"""
        if not self.collection:
            self.initialize()

        ids = [f"doc_{i}" for i in range(len(documents))]
        metadatas = metadatas or [{} for _ in documents]

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Added {len(documents)} documents to ChromaDB")

    def similarity_search(self, query: str, k: int = 5) -> List[SearchResult]:
        """Search for similar documents"""
        if not self.collection:
            self.initialize()

        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )

        search_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i] if results['distances'] else 0.0
                score = max(0.0, 1.0 - distance)  # Convert distance to similarity score

                metadata = results['metadatas'][0][i] if results['metadatas'] else {}

                document = Document(content=doc, metadata=metadata)
                search_result = SearchResult(document=document, score=score)
                search_results.append(search_result)

        return search_results

    def create_collection(self, name: str):
        """Create a new collection"""
        if not self.client:
            self.initialize()
        return self.client.create_collection(name=name)

    def delete_collection(self, name: str):
        """Delete a collection"""
        if not self.client:
            self.initialize()
        self.client.delete_collection(name=name)

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        if not self.collection:
            self.initialize()

        count = self.collection.count()
        return {
            "name": self.collection_name,
            "count": count,
            "persist_directory": self.persist_directory
        }

    def search(self, query: str, k: int = 5) -> List[SearchResult]:
        """Alias for similarity_search"""
        return self.similarity_search(query, k)

    def search_by_vector(self, vector: List[float], k: int = 5) -> List[SearchResult]:
        """Search by vector"""
        if not self.collection:
            self.initialize()

        results = self.collection.query(
            query_embeddings=[vector],
            n_results=k
        )

        search_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i] if results['distances'] else 0.0
                score = max(0.0, 1.0 - distance)

                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                document = Document(content=doc, metadata=metadata)
                search_result = SearchResult(document=document, score=score)
                search_results.append(search_result)

        return search_results

    def update_document(self, doc_id: str, content: str, metadata: Optional[Dict] = None):
        """Update a document"""
        if not self.collection:
            self.initialize()

        self.collection.update(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata or {}]
        )

    def delete_documents(self, doc_ids: List[str]):
        """Delete documents by IDs"""
        if not self.collection:
            self.initialize()

        self.collection.delete(ids=doc_ids)
        logger.info(f"Deleted {len(doc_ids)} documents from ChromaDB")