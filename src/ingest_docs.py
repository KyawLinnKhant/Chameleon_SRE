#!/usr/bin/env python3
"""
Documentation ingestion script for Chameleon-SRE.
Loads Kubernetes troubleshooting knowledge into ChromaDB.
"""

import argparse
from pathlib import Path
from loguru import logger

from src.utils import setup_logging
from rag.vectorstore import get_vector_store


# Kubernetes troubleshooting knowledge base
K8S_DOCS = [
    {
        "topic": "ImagePullBackOff",
        "content": """ImagePullBackOff occurs when Kubernetes cannot pull a container image from the registry.

Common causes:
1. **Wrong image name or tag**: Typo in deployment YAML (e.g., 'nginx:latset' instead of 'nginx:latest')
2. **Image doesn't exist**: The specified image/tag is not in the registry
3. **Authentication required**: Private registry needs imagePullSecrets
4. **Network issues**: Cannot reach the registry (firewall, DNS problems)
5. **Registry unavailable**: Docker Hub rate limits or registry downtime
6. **Pull timeout**: Image too large or slow network

How to diagnose:
- kubectl describe pod <pod-name>: Check Events section for error details
- Look for "ErrImagePull" or "ImagePullBackOff" in status
- Verify image exists: docker pull <image:tag>
- Check imagePullSecrets if using private registry

Solutions:
- Fix image name/tag in deployment
- Add imagePullSecrets for private registries
- Verify network connectivity to registry
- Use local/cached images for development
- Check registry status and rate limits""",
        "source": "kubernetes-troubleshooting"
    },
    {
        "topic": "CrashLoopBackOff",
        "content": """CrashLoopBackOff indicates a pod is crashing repeatedly and Kubernetes is backing off restart attempts.

Common causes:
1. **Application errors**: Bugs causing crashes (null pointer, unhandled exceptions)
2. **Missing dependencies**: Required services or databases not available
3. **Configuration errors**: Wrong environment variables, missing config files
4. **Resource limits**: OOMKilled - container exceeds memory limits
5. **Health check failures**: Liveness probe failing repeatedly
6. **Port already in use**: Another process using the same port

How to diagnose:
- kubectl logs <pod-name>: Check application logs for errors
- kubectl logs <pod-name> --previous: Logs from crashed container
- kubectl describe pod <pod-name>: Check restart count and reason
- Look for "OOMKilled" in status (memory issue)
- Check events for clues

Solutions:
- Fix application bugs causing crashes
- Ensure dependencies are ready (init containers, readiness checks)
- Verify configuration (env vars, secrets, configmaps)
- Increase memory limits if OOMKilled
- Adjust or remove failing liveness probes during debugging
- Check for port conflicts""",
        "source": "kubernetes-troubleshooting"
    },
    {
        "topic": "Pending Pods",
        "content": """Pods stuck in Pending state are waiting for cluster resources or conditions to be met.

Common causes:
1. **Insufficient resources**: Not enough CPU or memory available on nodes
2. **Node selector mismatch**: Pod requires node labels that don't exist
3. **Taints and tolerations**: Pod doesn't tolerate node taints
4. **PersistentVolume not available**: Waiting for storage to be provisioned
5. **Affinity/anti-affinity rules**: Cannot satisfy placement constraints
6. **Resource quotas exceeded**: Namespace has hit resource limits

How to diagnose:
- kubectl describe pod <pod-name>: Check Events section
- Look for "FailedScheduling" events
- kubectl get nodes: Check node status and available resources
- kubectl top nodes: See current resource usage
- kubectl describe nodes: Check taints and allocatable resources

Solutions:
- Add more nodes to cluster (scale up)
- Reduce resource requests in pod spec
- Fix node selectors or remove if not needed
- Add tolerations for tainted nodes
- Provision PersistentVolumes or use dynamic provisioning
- Adjust resource quotas
- Review affinity rules""",
        "source": "kubernetes-troubleshooting"
    },
    {
        "topic": "OOMKilled",
        "content": """OOMKilled (Out Of Memory Killed) means the container was terminated for exceeding memory limits.

Common causes:
1. **Memory leak**: Application not releasing memory
2. **Insufficient limits**: Memory limit too low for workload
3. **Traffic spike**: Sudden increase in requests/load
4. **Large dataset processing**: Working with big files or data
5. **No resource limits**: Container using all node memory

How to diagnose:
- kubectl describe pod <pod-name>: Look for "OOMKilled" in container status
- kubectl top pod <pod-name>: Check current memory usage
- Application logs: May show memory allocation errors
- Monitoring tools: Check memory usage trends over time

Solutions:
- Increase memory limits in pod spec
- Set memory requests equal to limits for guaranteed QoS
- Fix memory leaks in application
- Implement memory-efficient algorithms
- Use horizontal pod autoscaling for traffic spikes
- Add resource limits if missing
- Consider using larger node instance types""",
        "source": "kubernetes-troubleshooting"
    },
    {
        "topic": "Service Not Accessible",
        "content": """Service cannot be reached from inside or outside the cluster.

Common causes:
1. **No endpoints**: Service selector doesn't match any pods
2. **Pods not ready**: Pods exist but failing readiness checks
3. **Wrong service type**: Using ClusterIP when LoadBalancer needed
4. **Port mismatch**: Service port doesn't match container port
5. **Network policy**: Blocking traffic to pods
6. **Ingress misconfigured**: External access not properly configured

How to diagnose:
- kubectl get endpoints <service-name>: Check if service has endpoints
- kubectl get pods -l <service-selector>: Verify pods match selector
- kubectl describe service <service-name>: Check ports and selectors
- Test from within cluster: kubectl run test --image=curlimages/curl -- curl <service-name>
- Check network policies: kubectl get networkpolicies

Solutions:
- Fix service selector to match pod labels
- Ensure pods are ready (check readiness probes)
- Use correct service type (ClusterIP/NodePort/LoadBalancer)
- Match service port with container port
- Update or remove blocking network policies
- Configure ingress correctly for external access
- Check firewall rules for NodePort/LoadBalancer""",
        "source": "kubernetes-troubleshooting"
    },
    {
        "topic": "Readiness Probe Failures",
        "content": """Readiness probe failures prevent traffic from reaching pods.

Common causes:
1. **Application not ready**: Still starting up or initializing
2. **Wrong probe configuration**: Incorrect path, port, or timing
3. **Dependencies not available**: Database or API not accessible
4. **Timeout too short**: Probe timing out before app responds
5. **Health endpoint error**: /health or /ready endpoint returning errors

How to diagnose:
- kubectl describe pod <pod-name>: Check readiness probe failures
- kubectl logs <pod-name>: Check if application is actually ready
- Test health endpoint: kubectl exec <pod-name> -- curl localhost:<port>/health
- Check probe configuration in deployment

Solutions:
- Increase initialDelaySeconds to allow longer startup
- Increase timeoutSeconds if requests are slow
- Fix health endpoint to return correct status
- Ensure dependencies are available before marking ready
- Use separate liveness and readiness probes
- Temporarily remove probe to test if app works
- Check that probe port matches application port""",
        "source": "kubernetes-troubleshooting"
    },
    {
        "topic": "ConfigMap and Secret Issues",
        "content": """Problems with ConfigMaps and Secrets preventing pods from starting.

Common causes:
1. **ConfigMap/Secret not found**: Referenced resource doesn't exist
2. **Wrong namespace**: Resource in different namespace than pod
3. **Incorrect keys**: Referencing non-existent keys in ConfigMap/Secret
4. **Volume mount issues**: Path conflicts or permission problems
5. **Immutable ConfigMaps**: Cannot update existing immutable ConfigMap

How to diagnose:
- kubectl get configmap <name>: Verify ConfigMap exists
- kubectl get secret <name>: Verify Secret exists
- kubectl describe pod <pod-name>: Check mount failures in events
- Check pod spec for correct names and keys

Solutions:
- Create missing ConfigMap/Secret
- Ensure resource is in same namespace as pod
- Fix key names in pod spec
- Verify volume mount paths don't conflict
- Delete and recreate if using immutable ConfigMaps
- Use kubectl create configmap --from-file or --from-literal
- Check RBAC permissions if ServiceAccount cannot read""",
        "source": "kubernetes-troubleshooting"
    },
    {
        "topic": "Persistent Volume Issues",
        "content": """PersistentVolume and PersistentVolumeClaim problems.

Common causes:
1. **No PV available**: No PV matches PVC requirements
2. **StorageClass not found**: Requested StorageClass doesn't exist
3. **Access mode mismatch**: PV and PVC have incompatible access modes
4. **Size mismatch**: PV smaller than PVC requests
5. **Binding issues**: PVC stuck in Pending state
6. **Node affinity**: PV cannot be attached to pod's node

How to diagnose:
- kubectl get pvc: Check PVC status (Bound/Pending)
- kubectl describe pvc <name>: Check events for binding failures
- kubectl get pv: See available PersistentVolumes
- Check StorageClass: kubectl get storageclass

Solutions:
- Create PV that matches PVC requirements
- Use dynamic provisioning with StorageClass
- Fix access mode (ReadWriteOnce/ReadWriteMany/ReadOnlyMany)
- Increase PV size to match PVC
- Ensure StorageClass has provisioner configured
- Check node labels match PV node affinity
- Verify volume plugin is installed on nodes""",
        "source": "kubernetes-troubleshooting"
    },
    {
        "topic": "Resource Limits and Requests",
        "content": """Best practices for setting CPU and memory resources.

Key concepts:
1. **Requests**: Guaranteed minimum resources
2. **Limits**: Maximum resources allowed
3. **QoS Classes**: Guaranteed, Burstable, BestEffort
4. **Resource quotas**: Namespace-level constraints
5. **LimitRanges**: Default limits for pods

Best practices:
- Always set requests and limits
- Set requests = limits for critical workloads (Guaranteed QoS)
- Use monitoring to determine appropriate values
- Start conservative, adjust based on actual usage
- Memory limits should be ~1.5x typical usage
- CPU limits can be higher than typical usage
- Set namespace quotas to prevent resource hogging

Common mistakes:
- No limits: Pods can consume all node resources
- Limits too low: Causes throttling (CPU) or OOMKilled (memory)
- Requests too high: Wastes resources, pods won't schedule
- Requests without limits: Allows bursting but unpredictable

How to find right values:
- kubectl top pod <name>: Current usage
- Monitoring dashboard: Historical trends
- Start with: CPU request 100m, limit 500m; Memory request 128Mi, limit 256Mi
- Adjust based on metrics over days/weeks""",
        "source": "kubernetes-best-practices"
    },
    {
        "topic": "Node Issues",
        "content": """Common node-level problems affecting pods.

Common issues:
1. **Node NotReady**: Node lost connection to control plane
2. **Disk pressure**: Node running out of disk space
3. **Memory pressure**: Node low on memory
4. **PID pressure**: Too many processes running
5. **Network issues**: Node cannot reach other nodes or control plane

How to diagnose:
- kubectl get nodes: Check node status and conditions
- kubectl describe node <name>: See detailed conditions and events
- kubectl top node <name>: Check resource usage
- Check node logs: journalctl -u kubelet

Solutions:
- NotReady: Check kubelet service, network connectivity
- Disk pressure: Clean up old images (docker system prune), increase disk
- Memory pressure: Kill non-essential processes, add more nodes
- PID pressure: Increase pid limits, reduce pod density
- Cordon node to prevent new pods: kubectl cordon <node-name>
- Drain node to evict pods: kubectl drain <node-name> --ignore-daemonsets
- Restart kubelet: systemctl restart kubelet
- Check cloud provider for node health""",
        "source": "kubernetes-troubleshooting"
    }
]


def ingest_kubernetes_docs(vector_store, reset: bool = False):
    """
    Ingest Kubernetes documentation into vector store.
    
    Args:
        vector_store: VectorStore instance
        reset: If True, clear existing documents first
    """
    if reset:
        logger.warning("Resetting vector store...")
        vector_store.reset()
    
    # Check if already populated
    current_count = vector_store.count()
    if current_count > 0 and not reset:
        logger.info(f"Vector store already has {current_count} documents")
        response = input("Add more documents anyway? (y/n): ")
        if response.lower() != 'y':
            logger.info("Skipping ingestion")
            return
    
    # Prepare data
    documents = []
    metadatas = []
    ids = []
    
    for i, doc in enumerate(K8S_DOCS):
        documents.append(doc['content'])
        metadatas.append({
            'topic': doc['topic'],
            'source': doc['source'],
            'doc_type': 'troubleshooting'
        })
        ids.append(f"k8s_doc_{i}")
    
    # Add to vector store
    logger.info(f"Ingesting {len(documents)} documents...")
    vector_store.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    logger.success(f"✅ Ingestion complete! Total documents: {vector_store.count()}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest Kubernetes documentation into ChromaDB"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset vector store before ingestion"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test retrieval after ingestion"
    )
    
    args = parser.parse_args()
    
    setup_logging(verbose=True)
    
    print("📚 Chameleon-SRE Documentation Ingestion")
    print("=" * 60)
    
    # Initialize vector store
    vector_store = get_vector_store()
    
    # Ingest docs
    ingest_kubernetes_docs(vector_store, reset=args.reset)
    
    # Test if requested
    if args.test:
        print("\n🧪 Testing retrieval...")
        from rag.retriever import get_retriever
        
        retriever = get_retriever()
        test_query = "Why is my pod stuck in ImagePullBackOff?"
        
        print(f"\nQuery: {test_query}\n")
        docs = retriever.retrieve(test_query, top_k=2)
        
        if docs:
            print("Top results:")
            for i, doc in enumerate(docs, 1):
                print(f"\n{i}. {doc['metadata']['topic']}")
                print(f"   Relevance: {doc['relevance']:.3f}")
                print(f"   Preview: {doc['content'][:150]}...")
        else:
            print("❌ No results found")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
