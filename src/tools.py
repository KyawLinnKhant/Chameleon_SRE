"""
Tool definitions for the Chameleon-SRE agent
Each tool is a function the agent can call to interact with the world
"""

import os
import re
import subprocess
from typing import List, Dict, Any
import logging

from langchain_core.tools import tool
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

from .config import (
    KUBECTL_PATH,
    DEFAULT_NAMESPACE,
    CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL,
    ENABLE_VOICE_ALERTS
)

logger = logging.getLogger(__name__)


# ============================================================================
# Kubernetes Tools
# ============================================================================

def validate_kubectl_command(cmd: str) -> bool:
    """
    Validate kubectl command to prevent dangerous operations
    
    Args:
        cmd: The kubectl command to validate
    
    Returns:
        True if safe, False if potentially dangerous
    """
    dangerous_patterns = [
        r"delete\s+namespace",  # Don't allow namespace deletion
        r"delete\s+.*\s+--all",  # Don't allow bulk deletion
        r"&&",  # No command chaining
        r"\|",  # No piping
        r";",   # No command separation
        r"`",   # No command substitution
        r"\$\(",  # No command substitution
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, cmd, re.IGNORECASE):
            logger.warning(f"Blocked dangerous command: {cmd}")
            return False
    
    return True


@tool
def execute_k8s_command(command: str, namespace: str = DEFAULT_NAMESPACE) -> str:
    """
    Execute a kubectl command safely
    
    Args:
        command: kubectl command (without 'kubectl' prefix)
        namespace: Kubernetes namespace (default from config)
    
    Returns:
        Command output or error message
    
    Examples:
        execute_k8s_command("get pods")
        execute_k8s_command("describe pod nginx-abc123", namespace="production")
    """
    # Construct full command
    full_command = f"{KUBECTL_PATH} {command}"
    
    # Add namespace if not already specified and command needs it
    if "-n " not in command and "--namespace" not in command:
        if any(x in command for x in ["get", "describe", "logs", "exec"]):
            full_command += f" -n {namespace}"
    
    # Security validation
    if not validate_kubectl_command(full_command):
        return "ERROR: Command blocked for security reasons. Avoid delete, piping, or command chaining."
    
    try:
        logger.info(f"Executing: {full_command}")
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"ERROR (exit {result.returncode}): {result.stderr}"
    
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 30 seconds"
    except Exception as e:
        return f"ERROR: {str(e)}"


@tool
def get_pod_logs(pod_name: str, namespace: str = DEFAULT_NAMESPACE, tail: int = 100) -> str:
    """
    Get logs from a Kubernetes pod
    
    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace
        tail: Number of recent lines to retrieve
    
    Returns:
        Pod logs or error message
    """
    return execute_k8s_command(
        f"logs {pod_name} --tail={tail}",
        namespace=namespace
    )


@tool
def restart_deployment(deployment_name: str, namespace: str = DEFAULT_NAMESPACE) -> str:
    """
    Restart a Kubernetes deployment (creates new pods)
    
    Args:
        deployment_name: Name of the deployment
        namespace: Kubernetes namespace
    
    Returns:
        Status message
    """
    return execute_k8s_command(
        f"rollout restart deployment/{deployment_name}",
        namespace=namespace
    )


# ============================================================================
# RAG (Retrieval-Augmented Generation) Tools
# ============================================================================

def get_chroma_client():
    """Get or create ChromaDB client"""
    try:
        client = PersistentClient(path=CHROMA_PERSIST_DIR)
        return client
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        return None


@tool
def read_rag_docs(query: str, top_k: int = 3) -> str:
    """
    Search the knowledge base for relevant documentation
    
    Args:
        query: Search query (e.g., "CrashLoopBackOff troubleshooting")
        top_k: Number of top results to return
    
    Returns:
        Formatted search results with relevant documentation
    
    Examples:
        read_rag_docs("how to fix ImagePullBackOff")
        read_rag_docs("redis configuration best practices")
    """
    client = get_chroma_client()
    
    if client is None:
        return "ERROR: Knowledge base not available. Run 'python scripts/ingest_docs.py' first."
    
    try:
        # Get the collection
        collection = client.get_collection(
            name="k8s_docs",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )
        )
        
        # Query the collection
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        if not results["documents"] or not results["documents"][0]:
            return f"No relevant documentation found for: {query}"
        
        # Format results
        output = [f"📚 Knowledge Base Results for: {query}\n"]
        
        for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
            source = metadata.get("source", "Unknown")
            output.append(f"\n--- Result {i} (Source: {source}) ---")
            output.append(doc[:500])  # First 500 chars
            if len(doc) > 500:
                output.append("... [truncated]")
        
        return "\n".join(output)
    
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return f"ERROR: Failed to search knowledge base: {str(e)}"


# ============================================================================
# Alert & Notification Tools
# ============================================================================

@tool
def system_voice_alert(message: str, severity: str = "warning") -> str:
    """
    Send voice alert to engineer (macOS 'say' command or system notification)
    
    Args:
        message: Alert message to speak
        severity: "info", "warning", or "critical"
    
    Returns:
        Confirmation message
    
    Examples:
        system_voice_alert("Pod nginx is in CrashLoopBackOff", severity="critical")
    """
    if not ENABLE_VOICE_ALERTS:
        return f"Voice alerts disabled. Would have said: {message}"
    
    try:
        # Try macOS 'say' command
        if os.system("which say > /dev/null 2>&1") == 0:
            voice = {
                "info": "Samantha",
                "warning": "Alex",
                "critical": "Victoria"
            }.get(severity, "Alex")
            
            subprocess.run(
                ["say", "-v", voice, message],
                check=True,
                timeout=10
            )
            return f"✅ Voice alert sent: {message}"
        else:
            # Fallback: print to console
            severity_emoji = {
                "info": "ℹ️",
                "warning": "⚠️",
                "critical": "🚨"
            }.get(severity, "⚠️")
            
            print(f"\n{severity_emoji} ALERT: {message}\n")
            return f"✅ Console alert sent: {message}"
    
    except Exception as e:
        logger.error(f"Voice alert failed: {e}")
        return f"ERROR: Failed to send alert: {str(e)}"


# ============================================================================
# Tool Registry (for LangGraph)
# ============================================================================

ALL_TOOLS = [
    execute_k8s_command,
    get_pod_logs,
    restart_deployment,
    read_rag_docs,
    system_voice_alert,
]


def get_tools() -> List:
    """Get all available tools for the agent"""
    return ALL_TOOLS
