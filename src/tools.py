"""
Tool definitions for the Chameleon-SRE agent.
Updated with real RAG integration.
"""

import subprocess
from typing import Annotated

from langchain_core.tools import tool
from loguru import logger

from src.config import settings
from src.utils import sanitize_command, format_kubectl_output, extract_error_message


@tool
def execute_k8s_command(
    command: Annotated[str, "The kubectl command to execute (e.g., 'kubectl get pods')"]
) -> str:
    """
    Execute a kubectl command and return the output.
    
    This tool provides safe access to Kubernetes operations with built-in
    validation and safety checks. Destructive commands require explicit permission.
    
    Args:
        command: The kubectl command to run
        
    Returns:
        str: Command output or error message
        
    Examples:
        >>> execute_k8s_command("kubectl get pods -n default")
        >>> execute_k8s_command("kubectl describe pod myapp-xyz")
        >>> execute_k8s_command("kubectl logs myapp-xyz --tail=50")
    """
    logger.info(f"Executing K8s command: {command}")
    
    try:
        # Sanitize command
        safe_command = sanitize_command(command)
        
        # Add dry-run flag if enabled
        if settings.dry_run_mode and "get" not in command.lower():
            safe_command += " --dry-run=client"
            logger.warning("DRY RUN MODE: Command will not be executed")
        
        # Execute command
        result = subprocess.run(
            safe_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=settings.timeout_seconds,
        )
        
        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            logger.error(f"Command failed: {error_msg}")
            return f"❌ Error: {error_msg}"
        
        # Format and return output
        output = result.stdout or "Command executed successfully (no output)"
        formatted_output = format_kubectl_output(output)
        
        logger.success(f"Command succeeded (output: {len(output)} chars)")
        return formatted_output
    
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {settings.timeout_seconds} seconds"
        logger.error(error_msg)
        return f"❌ {error_msg}"
    
    except ValueError as e:
        # Dangerous command blocked
        logger.warning(f"Command blocked: {e}")
        return f"❌ {str(e)}"
    
    except Exception as e:
        error_msg = extract_error_message(e)
        logger.error(f"Unexpected error: {error_msg}")
        return f"❌ Unexpected error: {error_msg}"


@tool
def get_pod_status(
    namespace: Annotated[str, "Kubernetes namespace"] = "default",
    label_selector: Annotated[str | None, "Label selector (e.g., 'app=nginx')"] = None,
) -> str:
    """
    Get the status of pods in a namespace with optional label filtering.
    
    This is a convenience wrapper around kubectl that provides structured output.
    
    Args:
        namespace: Kubernetes namespace to query
        label_selector: Optional label selector to filter pods
        
    Returns:
        str: Pod status information
        
    Examples:
        >>> get_pod_status("production")
        >>> get_pod_status("default", "app=nginx")
    """
    command = f"kubectl get pods -n {namespace}"
    
    if label_selector:
        command += f" -l {label_selector}"
    
    command += " -o wide"
    
    return execute_k8s_command(command)


@tool
def read_pod_logs(
    pod_name: Annotated[str, "Name of the pod"],
    namespace: Annotated[str, "Kubernetes namespace"] = "default",
    tail: Annotated[int, "Number of lines to show from end"] = 50,
    container: Annotated[str | None, "Container name (for multi-container pods)"] = None,
) -> str:
    """
    Read logs from a Kubernetes pod.
    
    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace
        tail: Number of lines to retrieve from the end
        container: Optional container name for multi-container pods
        
    Returns:
        str: Pod logs
        
    Examples:
        >>> read_pod_logs("myapp-xyz", "production", tail=100)
        >>> read_pod_logs("myapp-xyz", "production", container="sidecar")
    """
    command = f"kubectl logs {pod_name} -n {namespace} --tail={tail}"
    
    if container:
        command += f" -c {container}"
    
    return execute_k8s_command(command)


@tool
def describe_resource(
    resource_type: Annotated[str, "Resource type (e.g., 'pod', 'service', 'deployment')"],
    resource_name: Annotated[str, "Name of the resource"],
    namespace: Annotated[str, "Kubernetes namespace"] = "default",
) -> str:
    """
    Get detailed information about a Kubernetes resource.
    
    Args:
        resource_type: Type of resource (pod, service, deployment, etc.)
        resource_name: Name of the resource
        namespace: Kubernetes namespace
        
    Returns:
        str: Detailed resource information
        
    Examples:
        >>> describe_resource("pod", "myapp-xyz", "production")
        >>> describe_resource("service", "api-service", "default")
    """
    command = f"kubectl describe {resource_type} {resource_name} -n {namespace}"
    return execute_k8s_command(command)


@tool
def read_rag_docs(
    query: Annotated[str, "Search query for documentation"]
) -> str:
    """
    Search the RAG knowledge base for relevant Kubernetes documentation.
    
    This tool retrieves relevant documentation snippets based on semantic similarity
    to help the agent make informed decisions.
    
    Args:
        query: Natural language query describing what you need to know
        
    Returns:
        str: Relevant documentation excerpts
        
    Examples:
        >>> read_rag_docs("How do I troubleshoot ImagePullBackOff errors?")
        >>> read_rag_docs("What are best practices for resource limits?")
    """
    logger.info(f"RAG query: {query}")
    
    try:
        # Import here to avoid circular dependency
        from rag.retriever import get_retriever
        
        # Get retriever and search
        retriever = get_retriever()
        documents = retriever.retrieve(query, top_k=3)
        
        if not documents:
            return "📚 No relevant documentation found. Try rephrasing your query."
        
        # Format results
        context = retriever.format_context(documents, max_length=1500)
        
        logger.success(f"Retrieved {len(documents)} relevant documents")
        return context
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        # Fallback to helpful message
        return f"""📚 Documentation search unavailable: {str(e)}

💡 Tip: Run the ingestion script first:
   python scripts/ingest_docs.py

For now, here are general troubleshooting steps:
1. Check pod status: kubectl get pods
2. Describe the pod: kubectl describe pod <pod-name>
3. Check logs: kubectl logs <pod-name>
4. Look for common issues: ImagePullBackOff, CrashLoopBackOff, Pending
"""


@tool
def system_voice_alert(
    message: Annotated[str, "Critical message to announce to the engineer"]
) -> str:
    """
    Send a voice alert to notify the engineer of critical findings.
    
    Use this sparingly - only for truly critical issues that require immediate attention.
    
    Args:
        message: The message to announce
        
    Returns:
        str: Confirmation of alert sent
        
    Examples:
        >>> system_voice_alert("Critical: All pods in production namespace are failing!")
    """
    logger.critical(f"🔊 VOICE ALERT: {message}")
    
    # On macOS, use 'say' command for TTS
    try:
        subprocess.run(
            ["say", message],
            timeout=10,
            capture_output=True,
        )
        return f"✅ Voice alert sent: {message}"
    except Exception as e:
        logger.warning(f"Voice alert failed: {e}")
        return f"⚠️ Voice alert unavailable (logged instead): {message}"


# Export all tools as a list
AGENT_TOOLS = [
    execute_k8s_command,
    get_pod_status,
    read_pod_logs,
    describe_resource,
    read_rag_docs,
    system_voice_alert,
]


if __name__ == "__main__":
    from src.utils import setup_logging
    
    setup_logging(verbose=True)
    
    # Test tools
    print("\n=== Testing Tools ===\n")
    
    # Test RAG
    print("Testing RAG...")
    result = read_rag_docs.invoke({"query": "ImagePullBackOff troubleshooting"})
    print(f"RAG result: {result[:200]}...")
