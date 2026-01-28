"""
Document retriever for RAG system.
Handles semantic search and context preparation.
"""

from loguru import logger

from rag.vectorstore import get_vector_store


class DocumentRetriever:
    """Retrieves relevant documents for RAG queries."""
    
    def __init__(self):
        """Initialize retriever with vector store."""
        self.vector_store = get_vector_store()
        logger.info(f"Retriever initialized with {self.vector_store.count()} documents")
    
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_relevance: float = 0.0
    ) -> list[dict]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            min_relevance: Minimum relevance score (0-1, lower is more similar)
            
        Returns:
            list[dict]: List of relevant documents with metadata
        """
        try:
            # Query vector store
            results = self.vector_store.query(query, n_results=top_k)
            
            # Format results
            documents = []
            for doc, metadata, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                # ChromaDB uses L2 distance, lower is better
                relevance_score = 1.0 / (1.0 + distance)  # Convert to 0-1 score
                
                if relevance_score >= (1 - min_relevance):  # Filter by threshold
                    documents.append({
                        'content': doc,
                        'metadata': metadata,
                        'relevance': relevance_score,
                        'distance': distance
                    })
            
            logger.info(f"Retrieved {len(documents)} relevant documents")
            return documents
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def format_context(self, documents: list[dict], max_length: int = 2000) -> str:
        """
        Format retrieved documents into context string.
        
        Args:
            documents: List of retrieved documents
            max_length: Maximum context length in characters
            
        Returns:
            str: Formatted context
        """
        if not documents:
            return "No relevant documentation found."
        
        context_parts = ["📚 Relevant Documentation:\n"]
        current_length = len(context_parts[0])
        
        for i, doc in enumerate(documents, 1):
            # Format document
            topic = doc['metadata'].get('topic', 'General')
            source = doc['metadata'].get('source', 'Unknown')
            content = doc['content']
            
            doc_text = f"\n{i}. {topic} (Source: {source})\n{content}\n"
            
            # Check length limit
            if current_length + len(doc_text) > max_length:
                context_parts.append(f"\n... (truncated, {len(documents) - i + 1} more results)")
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "".join(context_parts)


def get_retriever() -> DocumentRetriever:
    """Get retriever instance."""
    return DocumentRetriever()


if __name__ == "__main__":
    from src.utils import setup_logging
    
    setup_logging(verbose=True)
    
    print("🧪 Testing Retriever")
    print("=" * 60)
    
    retriever = get_retriever()
    
    # Test query
    query = "Why is my pod stuck in ImagePullBackOff?"
    print(f"\nQuery: {query}\n")
    
    docs = retriever.retrieve(query, top_k=2)
    
    if docs:
        print("Retrieved documents:")
        for doc in docs:
            print(f"\n- Topic: {doc['metadata'].get('topic', 'Unknown')}")
            print(f"  Relevance: {doc['relevance']:.3f}")
            print(f"  Content: {doc['content'][:100]}...")
        
        print("\n" + "=" * 60)
        print("Formatted context:")
        print(retriever.format_context(docs))
    else:
        print("⚠️ No documents found. Run the ingestion script first!")
