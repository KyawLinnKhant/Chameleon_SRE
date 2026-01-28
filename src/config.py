"""
Configuration management for Chameleon-SRE.
Handles environment detection, settings, and hardware optimization.
"""

import os
import platform
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Ollama Configuration
    ollama_host: str = Field(
        default="http://localhost:11434", 
        validation_alias="OLLAMA_HOST"
    )
    ollama_model: str = Field(
        default="llama3.2:3b", 
        validation_alias="OLLAMA_MODEL"
    )

    # LangSmith Tracing
    langchain_tracing: bool = Field(
        default=False, 
        validation_alias="LANGCHAIN_TRACING_V2"
    )
    langchain_api_key: str | None = Field(
        default=None, 
        validation_alias="LANGCHAIN_API_KEY"
    )
    langchain_project: str = Field(
        default="chameleon-sre", 
        validation_alias="LANGCHAIN_PROJECT"
    )
    langchain_endpoint: str = "https://api.smith.langchain.com"

    # Hardware Configuration
    device: Literal["auto", "mps", "cuda", "cpu"] = Field(
        default="auto", 
        validation_alias="DEVICE"
    )
    use_gpu: bool = Field(
        default=True, 
        validation_alias="USE_GPU"
    )

    # ChromaDB
    chroma_db_path: str = Field(
        default="./data/chroma_db", 
        validation_alias="CHROMA_DB_PATH"
    )
    chroma_collection_name: str = Field(
        default="k8s_docs", 
        validation_alias="CHROMA_COLLECTION_NAME"
    )

    # Agent Configuration
    max_iterations: int = Field(
        default=10, 
        validation_alias="MAX_ITERATIONS"
    )
    timeout_seconds: int = Field(
        default=300, 
        validation_alias="TIMEOUT_SECONDS"
    )
    verbose: bool = Field(
        default=True, 
        validation_alias="VERBOSE"
    )

    # Kubernetes
    kubeconfig: str = Field(
        default="~/.kube/config", 
        validation_alias="KUBECONFIG"
    )
    k8s_namespace: str = Field(
        default="default", 
        validation_alias="K8S_NAMESPACE"
    )

    # Safety
    allow_destructive_commands: bool = Field(
        default=False, 
        validation_alias="ALLOW_DESTRUCTIVE_COMMANDS"
    )
    dry_run_mode: bool = Field(
        default=False, 
        validation_alias="DRY_RUN_MODE"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_device() -> str:
    """
    Auto-detect the best available hardware device.
    
    Returns:
        str: Device identifier ("mps", "cuda", or "cpu")
    """
    settings = Settings()

    if settings.device != "auto":
        return settings.device

    if not settings.use_gpu:
        return "cpu"

    # Check for Apple Silicon (M1/M2/M3)
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        try:
            import torch
            if torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass

    # Check for NVIDIA CUDA
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass

    return "cpu"


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def ensure_directories() -> None:
    """Create necessary directories if they don't exist."""
    root = get_project_root()
    directories = [
        root / "data" / "chroma_db",
        root / "data" / "processed",
        root / "data" / "raw",
        root / "data" / "runbooks",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
ensure_directories()


if __name__ == "__main__":
    print("🔧 Chameleon-SRE Configuration")
    print("=" * 50)
    print(f"Ollama Host: {settings.ollama_host}")
    print(f"Ollama Model: {settings.ollama_model}")
    print(f"Device: {get_device()}")
    print(f"ChromaDB Path: {settings.chroma_db_path}")
    print(f"Max Iterations: {settings.max_iterations}")
    print(f"Verbose: {settings.verbose}")
    print(f"Dry Run Mode: {settings.dry_run_mode}")
    print("=" * 50)
