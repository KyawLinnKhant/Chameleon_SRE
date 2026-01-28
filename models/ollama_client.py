"""
Ollama client for local LLM inference.
Manages connection to Ollama server and model loading.
"""

from langchain_ollama import ChatOllama
from loguru import logger

from src.config import settings


def get_llm() -> ChatOllama:
    """
    Get a configured Ollama LLM instance.
    
    Returns:
        ChatOllama: Configured LLM client
    """
    logger.info(f"Initializing Ollama client: {settings.ollama_model}")
    
    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_host,
        temperature=0.1,  # Low temperature for deterministic SRE tasks
        num_predict=2048,  # Max tokens to generate
        num_ctx=8192,  # Context window size
    )
    
    logger.success("Ollama client initialized")
    return llm


def check_ollama_connection() -> bool:
    """
    Check if Ollama server is accessible.
    
    Returns:
        bool: True if connection successful
    """
    try:
        llm = get_llm()
        # Try a simple invocation
        response = llm.invoke("Hello")
        logger.info("✅ Ollama connection verified")
        return True
    except Exception as e:
        logger.error(f"❌ Ollama connection failed: {e}")
        return False


if __name__ == "__main__":
    from src.utils import setup_logging
    
    setup_logging(verbose=True)
    
    print("\n=== Testing Ollama Connection ===\n")
    
    if check_ollama_connection():
        print("✅ Ollama is ready")
        
        # Test inference
        llm = get_llm()
        response = llm.invoke("What is Kubernetes?")
        print(f"\n🤖 Test Response:\n{response.content}\n")
    else:
        print("❌ Ollama is not available")
        print("\nTroubleshooting:")
        print("1. Check if Ollama is installed: ollama --version")
        print("2. Start Ollama server: ollama serve")
        print(f"3. Verify model is downloaded: ollama pull {settings.ollama_model}")
