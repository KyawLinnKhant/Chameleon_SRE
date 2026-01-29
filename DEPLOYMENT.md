# 🚀 Deployment Guide

## Quick Start (Local Development)

### 1. Prerequisites Check
```bash
# Check Python version
python --version  # Should be 3.10+

# Check Ollama
ollama --version

# Check Docker
docker --version

# Check Kubernetes tools
kubectl version --client
minikube version
```

### 2. Environment Setup
```bash
# Clone repository
git clone https://github.com/yourusername/chameleon-sre.git
cd chameleon-sre

# Create Conda environment
conda create -n chameleon-sre python=3.10 -y
conda activate chameleon-sre

# Install dependencies
pip install -r requirements.txt
```

### 3. Start Services
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull model (first time only)
ollama pull llama3.2

# Terminal 3: Start Minikube
minikube start --driver=docker
```

### 4. Initialize Knowledge Base
```bash
python scripts/ingest_docs.py
```

### 5. Run the Agent
```bash
# Interactive mode
python src/main.py

# Batch mode
python src/main.py --query "Check pod status"
```

---

## Docker Deployment

### Build Image
```bash
docker build -t chameleon-sre:v1 .
```

### Run with Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f chameleon-sre

# Stop services
docker-compose down
```

### Run Standalone Container
```bash
docker run -it --rm \
  --network host \
  -v ~/.kube:/root/.kube:ro \
  -v $(pwd)/chroma_db:/app/chroma_db \
  chameleon-sre:v1
```

---

## Kubernetes Deployment

### 1. Build and Load Image
```bash
# Build
docker build -t chameleon-sre:v1 .

# Load into Minikube
minikube image load chameleon-sre:v1

# Verify
minikube image ls | grep chameleon
```

### 2. Deploy to Cluster
```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply individually
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
```

### 3. Verify Deployment
```bash
# Check deployment status
kubectl get deployments
kubectl get pods -l app=chameleon-sre

# Check logs
kubectl logs -f deployment/chameleon-sre

# Check events
kubectl get events --field-selector involvedObject.name=chameleon-sre
```

### 4. Access Agent
```bash
# If running in interactive mode, exec into pod
kubectl exec -it deployment/chameleon-sre -- python src/main.py

# If running as daemon, check logs
kubectl logs -f deployment/chameleon-sre
```

---

## Production Deployment

### 1. External Ollama Server

For production, run Ollama on a dedicated GPU server:

```yaml
# k8s/configmap.yaml
data:
  OLLAMA_BASE_URL: "http://ollama-server.production.svc.cluster.local:11434"
```

Deploy Ollama:
```bash
# Option 1: External server
ssh gpu-server
ollama serve --host 0.0.0.0

# Option 2: Kubernetes deployment
kubectl apply -f k8s/ollama-deployment.yaml
```

### 2. Persistent Storage

Use a proper storage class:

```yaml
# k8s/deployment.yaml
spec:
  storageClassName: ssd  # or your preferred storage class
  resources:
    requests:
      storage: 10Gi
```

### 3. Secrets Management

For LangSmith API key:

```bash
kubectl create secret generic chameleon-secrets \
  --from-literal=LANGCHAIN_API_KEY=your_key_here

# Reference in deployment
envFrom:
  - secretRef:
      name: chameleon-secrets
```

### 4. Resource Limits

Adjust based on your cluster:

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### 5. Monitoring

Enable LangSmith tracing:

```yaml
# k8s/configmap.yaml
data:
  LANGCHAIN_TRACING_V2: "true"
  LANGCHAIN_PROJECT: "chameleon-sre-production"
```

---

## Troubleshooting

### Agent Can't Connect to Ollama

**Symptom**: "Connection refused" errors

**Solution**:
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# For Docker: Use host.docker.internal
# For Minikube: Use host.minikube.internal

# Test connection from container
docker run --rm --network host curlimages/curl \
  http://localhost:11434/api/tags
```

### Agent Can't Access Kubernetes

**Symptom**: "Unauthorized" or permission errors

**Solution**:
```bash
# Verify RBAC
kubectl get serviceaccount chameleon-sre
kubectl get clusterrolebinding chameleon-sre-binding

# Test permissions
kubectl auth can-i get pods --as=system:serviceaccount:default:chameleon-sre
```

### ChromaDB Not Initialized

**Symptom**: "Collection not found" errors

**Solution**:
```bash
# Re-run ingestion
python scripts/ingest_docs.py

# In Kubernetes, check init container logs
kubectl logs deployment/chameleon-sre -c setup-rag
```

### High Memory Usage

**Symptom**: OOMKilled pods

**Solution**:
1. Increase memory limits in deployment
2. Use a smaller model: `ollama pull llama3.2:1b`
3. Reduce embedding model size in config

---

## Scaling Considerations

### Horizontal Scaling (Multiple Agents)

```yaml
# k8s/deployment.yaml
spec:
  replicas: 3  # Run 3 agent instances
```

**Note**: Agents work independently. Use a message queue (Redis, RabbitMQ) for task distribution.

### Vertical Scaling (Bigger Agents)

```yaml
# Use larger model
data:
  OLLAMA_MODEL: "llama3.2:70b"

# Increase resources
resources:
  requests:
    memory: "8Gi"
    cpu: "4000m"
```

---

## Health Checks

### Liveness Probe
Ensures agent process is running.

### Readiness Probe
Ensures agent can connect to Ollama and Kubernetes.

### Custom Health Check
```bash
# Add to deployment.yaml
livenessProbe:
  exec:
    command:
      - python
      - -c
      - |
        import requests
        r = requests.get('http://localhost:11434/api/tags')
        exit(0 if r.status_code == 200 else 1)
```

---

## Backup and Recovery

### Backup ChromaDB
```bash
# Copy from pod
kubectl cp chameleon-sre-pod:/app/chroma_db ./backup/

# Or use PVC snapshot
kubectl get pvc chameleon-sre-pvc
kubectl snapshot create chameleon-sre-snapshot --pvc chameleon-sre-pvc
```

### Restore ChromaDB
```bash
# Copy to pod
kubectl cp ./backup/ chameleon-sre-pod:/app/chroma_db

# Or restore from snapshot
kubectl apply -f k8s/pvc-from-snapshot.yaml
```

---

## Upgrading

### Rolling Update
```bash
# Build new image
docker build -t chameleon-sre:v2 .

# Update deployment
kubectl set image deployment/chameleon-sre agent=chameleon-sre:v2

# Monitor rollout
kubectl rollout status deployment/chameleon-sre

# Rollback if needed
kubectl rollout undo deployment/chameleon-sre
```

---

## Security Hardening

1. **Least Privilege RBAC**: Review and minimize permissions in `k8s/rbac.yaml`
2. **Network Policies**: Restrict agent network access
3. **Pod Security Standards**: Enable pod security admission
4. **Secrets Encryption**: Enable encryption at rest for secrets
5. **Audit Logging**: Enable Kubernetes audit logs for agent actions

---

## Performance Tuning

### Optimize Ollama
```bash
# Use GPU acceleration
ollama run llama3.2 --gpu

# Adjust context window
export OLLAMA_NUM_CTX=4096
```

### Optimize ChromaDB
```python
# In config.py
CHUNK_SIZE = 500  # Smaller chunks for faster retrieval
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight model
```

### Optimize Agent
```python
# In config.py
MAX_ITERATIONS = 5  # Limit reasoning loops
TEMPERATURE = 0.0  # Deterministic (faster)
```

---

**Last Updated**: 2026-01-29  
**Version**: 1.0
