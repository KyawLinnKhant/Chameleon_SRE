"""
ChromaDB vector store for Kubernetes documentation.
Stores and retrieves documentation chunks for RAG.
"""

import chromadb
from chromadb.config import Settings
from loguru import logger
from pathlib import Path

from src.config import settings


class VectorStore:
    """Manages ChromaDB vector store for K8s documentation."""
    
    def __init__(self):
        """Initialize ChromaDB client and collection."""
        self.client = None
        self.collection = None
        self._initialize()
    
    def _initialize(self):
        """Set up ChromaDB client and collection."""
        try:
            # Create persistent client
            db_path = Path(settings.chroma_db_path)
            db_path.mkdir(parents=True, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=str(db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"description": "Kubernetes documentation and troubleshooting guides"}
            )
            
            logger.info(f"✅ ChromaDB initialized: {self.collection.count()} documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str]
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of text chunks
            metadatas: List of metadata dicts (source, topic, etc.)
            ids: List of unique IDs for each chunk
        """
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def query(
        self,
        query_text: str,
        n_results: int = 5
    ) -> dict:
        """
        Search for relevant documents.
        
        Args:
            query_text: Search query
            n_results: Number of results to return
            
        Returns:
            dict: Query results with documents, metadatas, distances
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            logger.debug(f"Query returned {len(results['documents'][0])} results")
            return results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def count(self) -> int:
        """Get total number of documents in collection."""
        return self.collection.count()
    
    def reset(self) -> None:
        """Clear all documents from collection."""
        try:
            self.client.delete_collection(settings.chroma_collection_name)
            self._initialize()
            logger.warning("⚠️ Vector store reset - all documents deleted")
        except Exception as e:
            logger.error(f"Failed to reset vector store: {e}")
            raise


def get_vector_store() -> VectorStore:
    """Get or create vector store instance."""
    return VectorStore()


if __name__ == "__main__":
    from src.utils import setup_logging
    
    setup_logging(verbose=True)
    
    print("🧪 Testing Vector Store")
    print("=" * 60)
    
    # Initialize
    store = get_vector_store()
    print(f"Documents in store: {store.count()}")
    
    # Test add
    if store.count() == 0:
        print("\n📝 Adding test documents...")
        store.add_documents(
            documents=[
                "ImagePullBackOff occurs when Kubernetes cannot pull a container image. Common causes: wrong image name, missing pull secrets, network issues.",
                "CrashLoopBackOff means a pod is crashing repeatedly. Check logs with kubectl logs. Common causes: application errors, missing dependencies.",
                "Pending pods are waiting for resources. Check with kubectl describe pod. Common causes: insufficient CPU/memory, node selectors not matching."
            ],
            metadatas=[
                {"topic": "ImagePullBackOff", "source": "test"},
                {"topic": "CrashLoopBackOff", "source": "test"},
                {"topic": "Pending", "source": "test"}
            ],
            ids=["doc1", "doc2", "doc3"]
        )
        print(f"✅ Documents added. Total: {store.count()}")
    
    # Test query
    print("\n🔍 Testing query...")
    results = store.query("Why can't my pod pull an image?", n_results=2)
    
    print("\nResults:")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n{i+1}. Topic: {metadata.get('topic', 'Unknown')}")
        print(f"   Text: {doc[:100]}...")
    
    print("\n✅ Vector store working!")
