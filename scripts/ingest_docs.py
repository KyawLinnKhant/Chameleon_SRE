"""
Document Ingestion Script for ChromaDB
Crawls documentation and creates vector embeddings for RAG
"""

import os
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample Kubernetes troubleshooting documentation
SAMPLE_DOCS = [
    {
        "content": """
        # CrashLoopBackOff Troubleshooting
        
        CrashLoopBackOff indicates that a pod is crashing repeatedly. Common causes:
        
        1. **Missing Configuration**: Pod expects ConfigMap or Secret that doesn't exist
           - Solution: Check pod spec for volume mounts, create missing resources
           - Command: kubectl describe pod <pod-name> | grep -A 5 "Mounts"
        
        2. **Application Error**: Code is crashing on startup
           - Solution: Check pod logs for stack traces
           - Command: kubectl logs <pod-name> --previous
        
        3. **Resource Limits**: Container exceeds memory/CPU limits
           - Solution: Check resource usage, increase limits if needed
           - Command: kubectl top pod <pod-name>
        
        4. **Health Check Failure**: Liveness/readiness probes failing
           - Solution: Review probe configuration, adjust timeout/threshold
        
        Auto-remediation steps:
        1. Inspect logs: kubectl logs <pod-name> --tail=50
        2. Check events: kubectl get events --field-selector involvedObject.name=<pod-name>
        3. Verify ConfigMaps/Secrets exist
        4. If missing config: Create from template or ask engineer
        5. If resource issue: Suggest increasing limits
        6. Restart deployment: kubectl rollout restart deployment/<deployment-name>
        """,
        "metadata": {"source": "k8s-troubleshooting.md", "topic": "CrashLoopBackOff"}
    },
    {
        "content": """
        # ImagePullBackOff Troubleshooting
        
        ImagePullBackOff means Kubernetes cannot pull the container image. Causes:
        
        1. **Image Does Not Exist**
           - Typo in image name or tag
           - Image deleted from registry
           - Solution: Verify image exists in registry
        
        2. **Authentication Required**
           - Private registry without credentials
           - Solution: Create imagePullSecret
           - Command: kubectl create secret docker-registry <secret-name> \\
             --docker-server=<registry> --docker-username=<user> --docker-password=<pass>
        
        3. **Network Issues**
           - Registry unreachable from cluster
           - Solution: Check network policies, firewall rules
        
        4. **Rate Limiting**
           - Docker Hub rate limits exceeded
           - Solution: Use authenticated pulls or mirror registry
        
        Auto-remediation steps:
        1. Check image name: kubectl get pod <pod-name> -o jsonpath='{.spec.containers[*].image}'
        2. Test image pull manually: docker pull <image-name>
        3. Verify imagePullSecrets: kubectl get pod <pod-name> -o yaml | grep imagePullSecrets
        4. If private registry: Ensure secret exists and is referenced
        5. Alert engineer if registry is unreachable
        """,
        "metadata": {"source": "k8s-troubleshooting.md", "topic": "ImagePullBackOff"}
    },
    {
        "content": """
        # Pod Pending Troubleshooting
        
        Pending state means scheduler cannot place the pod. Common reasons:
        
        1. **Insufficient Resources**
           - No nodes have enough CPU/memory
           - Solution: Check node capacity, consider scaling cluster
           - Command: kubectl describe nodes | grep -A 5 "Allocated resources"
        
        2. **Node Selector Mismatch**
           - Pod requires specific node labels that don't exist
           - Solution: Check nodeSelector/affinity rules
           - Command: kubectl get pod <pod-name> -o yaml | grep -A 3 nodeSelector
        
        3. **Taints and Tolerations**
           - Nodes are tainted and pod has no tolerations
           - Solution: Add tolerations or remove taints
        
        4. **PersistentVolume Issues**
           - PVC cannot bind to PV
           - Solution: Check PV availability, storage class
        
        Auto-remediation steps:
        1. Describe pod: kubectl describe pod <pod-name>
        2. Check scheduler events: kubectl get events --sort-by='.lastTimestamp'
        3. If resource issue: Alert engineer (cannot auto-scale production)
        4. If node selector: Suggest removing constraint or labeling nodes
        5. If PVC: Check PV status and storage class
        """,
        "metadata": {"source": "k8s-troubleshooting.md", "topic": "Pending"}
    },
    {
        "content": """
        # Redis Configuration Best Practices
        
        When deploying Redis on Kubernetes:
        
        1. **ConfigMap Setup**
           - Store redis.conf in ConfigMap
           - Mount as volume: /usr/local/etc/redis/redis.conf
           - Example:
             apiVersion: v1
             kind: ConfigMap
             metadata:
               name: redis-config
             data:
               redis.conf: |
                 maxmemory 256mb
                 maxmemory-policy allkeys-lru
        
        2. **Persistence**
           - Use PersistentVolumeClaim for data directory
           - Mount to: /data
           - Enable AOF or RDB snapshots in config
        
        3. **Resource Limits**
           - Memory: Set to 2x maxmemory config
           - CPU: 0.5-1 core typical
        
        4. **Health Checks**
           - Liveness: redis-cli ping
           - Readiness: redis-cli ping
           - Initial delay: 30s
        
        Common issues:
        - Missing ConfigMap: Create with defaults
        - OOM kills: Increase memory limit or reduce maxmemory
        - Connection refused: Check service and port (default 6379)
        """,
        "metadata": {"source": "redis-best-practices.md", "topic": "Redis"}
    },
    {
        "content": """
        # Safe Kubectl Operations for Autonomous Agents
        
        **Allowed Operations (Read-Only):**
        - kubectl get <resource>
        - kubectl describe <resource>
        - kubectl logs <pod>
        - kubectl top <resource>
        - kubectl get events
        
        **Allowed Operations (Safe Modifications):**
        - kubectl rollout restart deployment/<name>
        - kubectl scale deployment/<name> --replicas=<N>
        - kubectl create configmap (with review)
        - kubectl annotate/label (non-critical resources)
        
        **FORBIDDEN Operations:**
        - kubectl delete namespace
        - kubectl delete --all
        - Any operation with && or | (command chaining)
        - kubectl delete pv/pvc (data loss)
        - kubectl delete deployment (without confirmation)
        - kubectl apply -f (without reviewing YAML)
        
        **Security Guidelines:**
        - Always validate commands before execution
        - Require human confirmation for destructive operations
        - Log all kubectl commands executed
        - Implement command whitelisting
        - Use --dry-run=client for testing
        - Never expose credentials in logs
        
        **Error Recovery:**
        If a kubectl command fails:
        1. Check cluster connectivity: kubectl cluster-info
        2. Verify permissions: kubectl auth can-i <verb> <resource>
        3. Inspect error message for root cause
        4. Do not retry destructive commands
        5. Alert engineer if permission denied
        """,
        "metadata": {"source": "kubectl-safety.md", "topic": "Security"}
    }
]


def create_collection():
    """Create or get ChromaDB collection"""
    client = PersistentClient(path=CHROMA_PERSIST_DIR)
    
    # Create embedding function
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name="k8s_docs",
        embedding_function=embedding_fn,
        metadata={"description": "Kubernetes troubleshooting documentation"}
    )
    
    return collection


def ingest_documents(collection, documents: list):
    """
    Ingest documents into ChromaDB with chunking
    
    Args:
        collection: ChromaDB collection
        documents: List of {content, metadata} dicts
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    all_chunks = []
    all_metadatas = []
    all_ids = []
    
    for doc_idx, doc in enumerate(documents):
        # Split document into chunks
        chunks = text_splitter.split_text(doc["content"])
        
        for chunk_idx, chunk in enumerate(chunks):
            chunk_id = f"doc_{doc_idx}_chunk_{chunk_idx}"
            all_chunks.append(chunk)
            all_metadatas.append(doc["metadata"])
            all_ids.append(chunk_id)
    
    # Add to collection
    logger.info(f"Adding {len(all_chunks)} chunks to collection...")
    collection.add(
        documents=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids
    )
    
    logger.info(f"✅ Ingested {len(documents)} documents ({len(all_chunks)} chunks)")


def load_markdown_files(docs_dir: Path):
    """
    Load markdown files from docs directory
    
    Args:
        docs_dir: Path to docs directory
    
    Returns:
        List of documents
    """
    documents = []
    
    if not docs_dir.exists():
        logger.warning(f"Docs directory not found: {docs_dir}")
        return documents
    
    for md_file in docs_dir.glob("**/*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            documents.append({
                "content": content,
                "metadata": {
                    "source": md_file.name,
                    "path": str(md_file),
                    "type": "markdown"
                }
            })
            logger.info(f"Loaded: {md_file.name}")
        
        except Exception as e:
            logger.error(f"Failed to load {md_file}: {e}")
    
    return documents


def main():
    """Main ingestion workflow"""
    print("=" * 60)
    print("🦎 Chameleon-SRE Knowledge Base Ingestion")
    print("=" * 60)
    
    # Create collection
    logger.info("Creating ChromaDB collection...")
    collection = create_collection()
    
    # Load documents from docs/ directory
    docs_dir = Path(__file__).parent.parent / "docs"
    user_docs = load_markdown_files(docs_dir)
    
    # Combine with sample docs
    all_docs = SAMPLE_DOCS + user_docs
    
    logger.info(f"Total documents to ingest: {len(all_docs)}")
    
    # Ingest
    ingest_documents(collection, all_docs)
    
    # Test query
    logger.info("\nTesting knowledge base...")
    results = collection.query(
        query_texts=["How to fix CrashLoopBackOff?"],
        n_results=1
    )
    
    if results["documents"] and results["documents"][0]:
        print("\n✅ Knowledge base is working!")
        print(f"Sample result: {results['documents'][0][0][:200]}...")
    else:
        print("\n⚠️  Warning: No results from test query")
    
    print("\n" + "=" * 60)
    print(f"✅ Knowledge base ready at: {CHROMA_PERSIST_DIR}")
    print(f"   Total chunks: {collection.count()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
