"""
Configuration module for Chameleon-SRE
Handles hardware detection, model settings, and environment configuration
"""

import os
import platform
from typing import Literal

import torch


def get_device() -> Literal["mps", "cuda", "cpu"]:
    """
    Auto-detect optimal compute device for inference
    
    Returns:
        "mps" for Apple Silicon
        "cuda" for NVIDIA GPUs
        "cpu" as fallback
    """
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_device_info() -> dict:
    """Get detailed device information"""
    device = get_device()
    info = {
        "device": device,
        "platform": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    }
    
    if device == "cuda":
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_memory"] = f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB"
    elif device == "mps":
        info["gpu_name"] = "Apple Metal Performance Shaders"
    
    return info


# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2")

# Agent Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))  # Deterministic for SRE tasks
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))

# Kubernetes Configuration
KUBECTL_PATH = os.getenv("KUBECTL_PATH", "kubectl")
DEFAULT_NAMESPACE = os.getenv("K8S_NAMESPACE", "default")

# ChromaDB Configuration
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# LangSmith Configuration (Observability)
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "chameleon-sre")

# Voice Alert Configuration
ENABLE_VOICE_ALERTS = os.getenv("ENABLE_VOICE_ALERTS", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# System Prompt for SRE Agent
SYSTEM_PROMPT = """You are Chameleon-SRE, an autonomous Site Reliability Engineer.

**Core Responsibilities:**
1. Monitor Kubernetes cluster health
2. Diagnose infrastructure issues
3. Execute safe remediation actions
4. Learn from historical incidents

**Operational Guidelines:**
- ALWAYS verify cluster state before actions
- NEVER delete resources without explicit confirmation
- Use RAG knowledge base for troubleshooting
- Retry failed operations with exponential backoff
- Alert engineers for critical issues
- Document all actions in conversation history

**Available Tools:**
- execute_k8s_command: Run kubectl commands (READ-ONLY by default)
- read_rag_docs: Search knowledge base for solutions
- system_voice_alert: Notify engineer via voice

**Decision Framework:**
1. OBSERVE: Gather current cluster state
2. ANALYZE: Compare against expected state
3. SEARCH: Query knowledge base for similar issues
4. ACT: Execute minimal corrective action
5. VERIFY: Confirm resolution
6. DOCUMENT: Update incident log

You reason in loops, not chains. If an action fails, you see the error and adapt.
Be precise, cautious, and always prioritize cluster stability over speed.
"""


if __name__ == "__main__":
    print("🦎 Chameleon-SRE Configuration")
    print("=" * 60)
    
    device_info = get_device_info()
    for key, value in device_info.items():
        print(f"{key:20s}: {value}")
    
    print(f"\n{'Model':20s}: {MODEL_NAME}")
    print(f"{'Ollama URL':20s}: {OLLAMA_BASE_URL}")
    print(f"{'Chroma DB':20s}: {CHROMA_PERSIST_DIR}")
    print(f"{'LangSmith':20s}: {'Enabled' if LANGCHAIN_TRACING_V2 else 'Disabled'}")
