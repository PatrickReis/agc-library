"""
AWS-based vector storage providers
Supports OpenSearch, Kendra, and S3+FAISS
"""

import os
import json
from typing import List, Dict, Any, Optional
from ..base_provider import CloudVectorStoreProvider, Document, SearchResult, StorageType

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    boto3 = None
    ClientError = Exception

try:
    from langchain_aws import AmazonKendraRetriever
    KENDRA_AVAILABLE = True
except ImportError:
    KENDRA_AVAILABLE = False

try:
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False

class AWSVectorProvider(CloudVectorStoreProvider):
    """
    AWS-based vector storage with multiple backend options:
    - OpenSearch (recommended for production)
    - Kendra (for enterprise search)
    - S3 + FAISS (cost-effective for large datasets)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        if not AWS_AVAILABLE:
            raise ImportError("AWS dependencies not available. Install with: pip install boto3")

        self.storage_type = StorageType(config.get('storage_type', 'aws_opensearch'))
        self.region = config.get('region', os.getenv('AWS_REGION', 'us-east-1'))
        self.collection_name = config.get('collection_name', 'agentcore-vectors')

        # AWS credentials
        self.aws_access_key = config.get('aws_access_key_id') or os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = config.get('aws_secret_access_key') or os.getenv('AWS_SECRET_ACCESS_KEY')

        # Initialize AWS session
        self.session = self._create_session()

        # Initialize specific provider
        if self.storage_type == StorageType.AWS_OPENSEARCH:
            self._init_opensearch()
        elif self.storage_type == StorageType.AWS_KENDRA:
            self._init_kendra()
        elif self.storage_type == StorageType.AWS_S3_FAISS:
            self._init_s3_faiss()

    def _create_session(self):
        """Create AWS session with credentials"""
        session_kwargs = {'region_name': self.region}

        if self.aws_access_key and self.aws_secret_key:
            session_kwargs.update({
                'aws_access_key_id': self.aws_access_key,
                'aws_secret_access_key': self.aws_secret_key
            })

        return boto3.Session(**session_kwargs)

    def _init_opensearch(self):
        """Initialize OpenSearch backend"""
        if not OPENSEARCH_AVAILABLE:
            raise ImportError("OpenSearch dependencies not available. Install: pip install opensearch-py requests-aws4auth")

        self.opensearch_endpoint = self.config.get('opensearch_endpoint')
        if not self.opensearch_endpoint:
            raise ValueError("OpenSearch endpoint required for AWS OpenSearch storage")

        # Configure AWS authentication
        credentials = self.session.get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.region,
            'es',
            session_token=credentials.token
        )

        self.client = OpenSearch(
            hosts=[{'host': self.opensearch_endpoint.replace('https://', ''), 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

    def _init_kendra(self):
        """Initialize Kendra backend"""
        if not KENDRA_AVAILABLE:
            raise ImportError("Kendra dependencies not available. Install: pip install langchain-aws")

        self.kendra_index_id = self.config.get('kendra_index_id')
        if not self.kendra_index_id:
            raise ValueError("Kendra index ID required for AWS Kendra storage")

        self.kendra_client = self.session.client('kendra')

    def _init_s3_faiss(self):
        """Initialize S3 + FAISS backend"""
        self.s3_bucket = self.config.get('s3_bucket')
        self.s3_prefix = self.config.get('s3_prefix', 'agentcore-vectors/')

        if not self.s3_bucket:
            raise ValueError("S3 bucket required for S3+FAISS storage")

        self.s3_client = self.session.client('s3')

    def initialize(self) -> bool:
        """Initialize the vector store connection"""
        try:
            if self.storage_type == StorageType.AWS_OPENSEARCH:
                # Test OpenSearch connection
                self.client.cluster.health()

            elif self.storage_type == StorageType.AWS_KENDRA:
                # Test Kendra connection
                self.kendra_client.describe_index(Id=self.kendra_index_id)

            elif self.storage_type == StorageType.AWS_S3_FAISS:
                # Test S3 connection
                self.s3_client.head_bucket(Bucket=self.s3_bucket)

            self.is_initialized = True
            return True

        except Exception as e:
            raise ConnectionError(f"Failed to initialize AWS vector store: {str(e)}")

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to AWS storage"""
        if self.storage_type == StorageType.AWS_OPENSEARCH:
            return self._add_to_opensearch(documents)
        elif self.storage_type == StorageType.AWS_KENDRA:
            return self._add_to_kendra(documents)
        elif self.storage_type == StorageType.AWS_S3_FAISS:
            return self._add_to_s3_faiss(documents)

    def _add_to_opensearch(self, documents: List[Document]) -> List[str]:
        """Add documents to OpenSearch"""
        doc_ids = []

        for i, doc in enumerate(documents):
            doc_id = doc.doc_id or f"doc_{i}_{hash(doc.content)}"

            body = {
                'content': doc.content,
                'metadata': doc.metadata,
                'embedding': doc.embedding
            }

            self.client.index(
                index=self.collection_name,
                id=doc_id,
                body=body
            )
            doc_ids.append(doc_id)

        # Refresh index
        self.client.indices.refresh(index=self.collection_name)
        return doc_ids

    def _add_to_kendra(self, documents: List[Document]) -> List[str]:
        """Add documents to Kendra"""
        # Kendra requires different approach - usually documents are indexed via data sources
        # This is a simplified implementation
        doc_ids = []

        for i, doc in enumerate(documents):
            doc_id = doc.doc_id or f"kendra_doc_{i}"

            # Upload document content to S3 first (Kendra requirement)
            s3_key = f"kendra-docs/{doc_id}.txt"

            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=doc.content.encode('utf-8'),
                Metadata=doc.metadata
            )

            doc_ids.append(doc_id)

        return doc_ids

    def _add_to_s3_faiss(self, documents: List[Document]) -> List[str]:
        """Add documents to S3 + FAISS"""
        # This would require FAISS integration
        # Simplified implementation
        doc_ids = []

        for i, doc in enumerate(documents):
            doc_id = doc.doc_id or f"s3_doc_{i}"

            # Store document in S3
            s3_key = f"{self.s3_prefix}documents/{doc_id}.json"

            doc_data = {
                'content': doc.content,
                'metadata': doc.metadata,
                'embedding': doc.embedding
            }

            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json.dumps(doc_data).encode('utf-8')
            )

            doc_ids.append(doc_id)

        return doc_ids

    def search(self,
               query: str,
               k: int = 5,
               filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents"""

        if self.storage_type == StorageType.AWS_OPENSEARCH:
            return self._search_opensearch(query, k, filters)
        elif self.storage_type == StorageType.AWS_KENDRA:
            return self._search_kendra(query, k, filters)
        elif self.storage_type == StorageType.AWS_S3_FAISS:
            return self._search_s3_faiss(query, k, filters)

    def _search_opensearch(self, query: str, k: int, filters: Optional[Dict]) -> List[SearchResult]:
        """Search in OpenSearch"""
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "metadata.*"]
                }
            },
            "size": k
        }

        if filters:
            search_body["query"] = {
                "bool": {
                    "must": [search_body["query"]],
                    "filter": [{"term": {key: value}} for key, value in filters.items()]
                }
            }

        response = self.client.search(
            index=self.collection_name,
            body=search_body
        )

        results = []
        for i, hit in enumerate(response['hits']['hits']):
            doc = Document(
                content=hit['_source']['content'],
                metadata=hit['_source']['metadata'],
                doc_id=hit['_id'],
                embedding=hit['_source'].get('embedding')
            )

            results.append(SearchResult(
                document=doc,
                score=hit['_score'],
                rank=i + 1
            ))

        return results

    def _search_kendra(self, query: str, k: int, filters: Optional[Dict]) -> List[SearchResult]:
        """Search in Kendra"""
        response = self.kendra_client.query(
            IndexId=self.kendra_index_id,
            QueryText=query,
            PageSize=k
        )

        results = []
        for i, result in enumerate(response.get('ResultItems', [])):
            doc = Document(
                content=result.get('DocumentExcerpt', {}).get('Text', ''),
                metadata={
                    'title': result.get('DocumentTitle', {}).get('Text', ''),
                    'uri': result.get('DocumentURI', ''),
                    'type': result.get('Type', '')
                },
                doc_id=result.get('Id', f"kendra_{i}")
            )

            results.append(SearchResult(
                document=doc,
                score=result.get('ScoreAttributes', {}).get('ScoreConfidence', 0),
                rank=i + 1
            ))

        return results

    def _search_s3_faiss(self, query: str, k: int, filters: Optional[Dict]) -> List[SearchResult]:
        """Search in S3 + FAISS (simplified)"""
        # This would require proper FAISS implementation
        # Returning empty for now
        return []

    def search_by_vector(self,
                        vector: List[float],
                        k: int = 5,
                        filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search using vector similarity"""
        if self.storage_type == StorageType.AWS_OPENSEARCH:
            return self._vector_search_opensearch(vector, k, filters)
        # Other implementations...
        return []

    def _vector_search_opensearch(self, vector: List[float], k: int, filters: Optional[Dict]) -> List[SearchResult]:
        """Vector search in OpenSearch"""
        search_body = {
            "query": {
                "knn": {
                    "embedding": {
                        "vector": vector,
                        "k": k
                    }
                }
            },
            "size": k
        }

        response = self.client.search(
            index=self.collection_name,
            body=search_body
        )

        results = []
        for i, hit in enumerate(response['hits']['hits']):
            doc = Document(
                content=hit['_source']['content'],
                metadata=hit['_source']['metadata'],
                doc_id=hit['_id'],
                embedding=hit['_source'].get('embedding')
            )

            results.append(SearchResult(
                document=doc,
                score=hit['_score'],
                rank=i + 1
            ))

        return results

    def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            if self.storage_type == StorageType.AWS_OPENSEARCH:
                for doc_id in doc_ids:
                    self.client.delete(index=self.collection_name, id=doc_id)
                self.client.indices.refresh(index=self.collection_name)

            elif self.storage_type == StorageType.AWS_S3_FAISS:
                for doc_id in doc_ids:
                    s3_key = f"{self.s3_prefix}documents/{doc_id}.json"
                    self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)

            return True
        except Exception:
            return False

    def update_document(self, doc_id: str, document: Document) -> bool:
        """Update a document"""
        try:
            if self.storage_type == StorageType.AWS_OPENSEARCH:
                body = {
                    'content': document.content,
                    'metadata': document.metadata,
                    'embedding': document.embedding
                }

                self.client.update(
                    index=self.collection_name,
                    id=doc_id,
                    body={'doc': body}
                )

            return True
        except Exception:
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        if self.storage_type == StorageType.AWS_OPENSEARCH:
            try:
                stats = self.client.indices.stats(index=self.collection_name)
                return {
                    'total_documents': stats['indices'][self.collection_name]['total']['docs']['count'],
                    'storage_size': stats['indices'][self.collection_name]['total']['store']['size_in_bytes'],
                    'storage_type': self.storage_type.value
                }
            except Exception:
                return {'storage_type': self.storage_type.value}

        return {'storage_type': self.storage_type.value}

    def create_collection(self, name: str, **kwargs) -> bool:
        """Create a new collection/index"""
        if self.storage_type == StorageType.AWS_OPENSEARCH:
            try:
                mapping = {
                    "mappings": {
                        "properties": {
                            "content": {"type": "text"},
                            "metadata": {"type": "object"},
                            "embedding": {
                                "type": "knn_vector",
                                "dimension": kwargs.get('embedding_dimension', 1536)
                            }
                        }
                    }
                }

                self.client.indices.create(index=name, body=mapping)
                return True
            except Exception:
                return False

        return False

    def delete_collection(self, name: str) -> bool:
        """Delete a collection/index"""
        if self.storage_type == StorageType.AWS_OPENSEARCH:
            try:
                self.client.indices.delete(index=name)
                return True
            except Exception:
                return False

        return False

    def get_usage_metrics(self) -> Dict[str, Any]:
        """Get AWS usage metrics"""
        # Implementation would depend on CloudWatch integration
        return {
            'provider': 'aws',
            'storage_type': self.storage_type.value,
            'region': self.region
        }

    def set_scaling_config(self, config: Dict[str, Any]) -> bool:
        """Configure auto-scaling for AWS services"""
        # Implementation would depend on specific service
        return True