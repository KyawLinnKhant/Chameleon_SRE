"""
Embedding generation for RAG system.
Uses ChromaDB's built-in embeddings (default: all-MiniLM-L6-v2).
"""

from loguru import logger


class EmbeddingManager:
    """
    Manages embeddings for RAG.
    ChromaDB handles embeddings automatically, so this is a simple wrapper.
    """
    
    def __init__(self):
        """Initialize embedding manager."""
        logger.info("Using ChromaDB default embeddings (all-MiniLM-L6-v2)")
    
    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text.
        
        Note: ChromaDB handles this automatically during add/query.
        This method is here for potential future custom embeddings.
        
        Args:
            text: Text to embed
            
        Returns:
            list[float]: Embedding vector (handled by ChromaDB)
        """
        # ChromaDB handles this automatically
        # This is just a placeholder for potential future custom embeddings
        return []
    
    def batch_generate(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            list[list[float]]: List of embedding vectors
        """
        # ChromaDB handles batch processing automatically
        return []


def get_embedding_manager() -> EmbeddingManager:
    """Get embedding manager instance."""
    return EmbeddingManager()


if __name__ == "__main__":
    print("✅ ChromaDB handles embeddings automatically")
    print("Default model: all-MiniLM-L6-v2 (384 dimensions)")
    print("No additional setup required!")
