# 🦎 Chameleon-SRE

**Autonomous Site Reliability Engineer powered by LangGraph, Ollama & ChromaDB**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)](https://langchain-ai.github.io/langgraph/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange.svg)](https://ollama.ai/)

Chameleon-SRE is an **autonomous AI agent** that monitors, diagnoses, and helps resolve Kubernetes cluster issues. Unlike traditional chatbots that simply respond to queries, Chameleon-SRE uses **LangGraph state machines** to reason in cycles (Think → Act → Observe → Correct), making it capable of true autonomous operations.

**🎯 Built for SREs who want:**
- **Zero cloud costs** - Runs entirely locally on your machine
- **Real autonomy** - Not just a chatbot, but a reasoning agent
- **Production safety** - Built-in guards against destructive commands
- **Instant answers** - Local LLM with no API latency
- **Expert knowledge** - RAG system with K8s troubleshooting docs

---

## 🎬 Demo

```bash
🦎 Chameleon-SRE (Fast Mode)
============================================================

🔧 You: show me all pods

🦎 Chameleon-SRE:
[Executing: kubectl get pods -n default]

NAME              READY   STATUS             RESTARTS   AGE
nginx             1/1     Running            0          5m
srv-api-gateway   0/1     ImagePullBackOff   0          2m

The srv-api-gateway pod is failing with ImagePullBackOff. 
This occurs when Kubernetes cannot pull the container image. 
Common causes: wrong image tag, missing pull secrets, or 
network issues.

🔧 You: why is srv-api-gateway failing?

🦎 Chameleon-SRE:
[Executing: kubectl describe pod srv-api-gateway]
[Searching documentation: ImagePullBackOff troubleshooting]

📚 Relevant Documentation:

ImagePullBackOff occurs when Kubernetes cannot pull a container 
image from the registry.

Common causes:
1. Wrong image name or tag (e.g., 'nginx:wrongtag')
2. Image doesn't exist in the registry
3. Authentication required for private registry
4. Network connectivity issues
5. Registry rate limits or downtime

Diagnosis found: The pod is using "nginx:nonexistent-tag-123" 
which doesn't exist in Docker Hub.

Solution: Update your deployment to use a valid image tag like 
"nginx:latest" or "nginx:1.25"
```

---

## ✨ Key Features

### 🧠 True Autonomy with LangGraph
- **Cyclic Reasoning**: Think → Act → Observe → Correct loops
- **Self-Healing**: Automatically retries on errors with adjusted approach
- **Multi-Step Planning**: Can execute complex troubleshooting workflows

### 💻 100% Local & Private
- **No Cloud Dependencies**: Runs on Apple Silicon (M1/M2/M3) or x86
- **Zero API Costs**: Uses Ollama for local LLM inference
- **Data Sovereignty**: All data stays on your machine

### 🛡️ Production-Safe
- **Command Validation**: Blocks dangerous operations (`delete`, `drain`, `cordon`)
- **Dry-Run Mode**: Test commands without executing
- **Timeout Protection**: Prevents hanging operations
- **RBAC Compatible**: Works with Kubernetes security policies

### 📚 Knowledge-Enhanced (RAG)
- **Vector Database**: ChromaDB with 10+ troubleshooting guides
- **Semantic Search**: Finds relevant docs by meaning, not keywords
- **Always Current**: Easy to add your own documentation

### ⚡ Optimized Performance
- **Fast Responses**: ~10-20 seconds for most queries
- **Lightweight Models**: Works with 1B-3B parameter LLMs
- **Low Resource Usage**: Runs on laptops with 8GB+ RAM

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              LangGraph State Machine                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Think → Decide Action                           │  │
│  │    ↓                                              │  │
│  │  Act → Execute Tool (kubectl/RAG)                │  │
│  │    ↓                                              │  │
│  │  Observe → Capture Results                       │  │
│  │    ↓                                              │  │
│  │  Decide → Continue/Retry/Finish                  │  │
│  │    ↓                                              │  │
│  │  (Loop back if needed)                           │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │kubectl │  │ RAG    │  │ Voice  │
    │ tools  │  │ChromaDB│  │ Alert  │
    └────────┘  └────────┘  └────────┘
         │           │           │
         └───────────┴───────────┘
                     │
                     ▼
         ┌──────────────────────┐
         │   Ollama (M2 GPU)    │
         │  Llama 3.2 (1B-3B)   │
         └──────────────────────┘
```

### Component Breakdown

**🧠 Agent (LangGraph)**
- State machine with cyclic reasoning
- Decides when to use tools vs. answer directly
- Self-corrects on errors

**🔧 Tools Layer**
- `execute_k8s_command`: Safe kubectl wrapper
- `get_pod_status`: Pod health checks
- `read_pod_logs`: Log retrieval
- `describe_resource`: Resource inspection
- `read_rag_docs`: Knowledge base search

**📚 RAG System (ChromaDB)**
- Vector database for documentation
- Semantic search (all-MiniLM-L6-v2 embeddings)
- 10 built-in troubleshooting guides

**🤖 LLM (Ollama)**
- Local inference on GPU (MPS/CUDA) or CPU
- Models: Llama 3.2 (1B/3B), Mistral 7B
- No internet required after setup

---

## 🚀 Quick Start

### Prerequisites

- **macOS** (Apple Silicon M1/M2/M3) or **Linux** (x86_64)
- **Python 3.11+**
- **8GB+ RAM** (16GB recommended)
- **Docker Desktop** (for Minikube)
- **10GB disk space** (for models)

### 1. Install Dependencies

```bash
# Install Ollama
brew install ollama  # macOS
# or visit https://ollama.ai for other platforms

# Start Ollama server
ollama serve

# Download LLM model
ollama pull llama3.2:3b  # 3B model (2GB)
# or llama3.2:1b for lighter systems (1GB)

# Install Kubernetes tools
brew install kubectl minikube docker
```

### 2. Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/chameleon-sre.git
cd chameleon-sre

# Create virtual environment
conda create -n chameleon-sre python=3.11 -y
conda activate chameleon-sre

# Install Python dependencies
pip install -r requirements.txt

# Install ChromaDB for RAG
pip install chromadb --break-system-packages
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env (optional - defaults work for most cases)
nano .env
```

Key settings:
```bash
OLLAMA_MODEL=llama3.2:3b  # or llama3.2:1b
KUBECONFIG=/Users/your-username/.kube/config
MAX_ITERATIONS=10
ALLOW_DESTRUCTIVE_COMMANDS=false  # Keep false for safety!
```

### 4. Setup Kubernetes (Optional)

```bash
# Start local cluster
minikube start --driver=docker --memory=4096 --cpus=2

# Verify connection
kubectl get nodes

# Create test pods
kubectl run nginx --image=nginx
kubectl run broken --image=nginx:wrongtag  # Intentionally broken for testing
```

### 5. Load Knowledge Base

```bash
# Ingest 10 troubleshooting guides into ChromaDB
python scripts/ingest_docs.py

# Verify
python scripts/ingest_docs.py --test
```

### 6. Run the Agent

```bash
# Start interactive mode
python -m src.agent

# Or using make
make run
```

---

## 📖 Usage Examples

### Example 1: Pod Troubleshooting

```bash
🔧 You: show me all pods

🦎 Chameleon-SRE:
[Executes: kubectl get pods]

NAME              READY   STATUS             RESTARTS   AGE
nginx             1/1     Running            0          5m
broken            0/1     ImagePullBackOff   0          2m

Analysis: The 'broken' pod is in ImagePullBackOff state.

🔧 You: why is the broken pod failing?

🦎 Chameleon-SRE:
[Executes: kubectl describe pod broken]
[Searches docs: ImagePullBackOff]

Diagnosis: The pod is trying to pull 'nginx:wrongtag' which 
doesn't exist. 

Solution: Update the image tag to a valid one like 'nginx:latest'
```

### Example 2: Knowledge Query

```bash
🔧 You: What causes CrashLoopBackOff?

🦎 Chameleon-SRE:
[Searches documentation]

📚 CrashLoopBackOff indicates a pod is crashing repeatedly.

Common causes:
1. Application bugs causing crashes
2. Missing dependencies (database not ready)
3. Configuration errors (wrong env vars)
4. Resource limits too low (OOMKilled)
5. Health check failures
6. Port conflicts

Diagnosis steps:
- kubectl logs <pod-name>
- kubectl logs <pod-name> --previous
- kubectl describe pod <pod-name>
- Check for OOMKilled in status

[Full detailed guide with solutions...]
```

### Example 3: Resource Investigation

```bash
🔧 You: check resource usage in monitoring namespace

🦎 Chameleon-SRE:
[Executes: kubectl top pods -n monitoring]

NAME              CPU(cores)   MEMORY
prometheus-0      120m         8.2Gi
grafana-abc       25m          512Mi

Analysis: Prometheus is using 8.2GB memory.
Let me check if limits are set...

[Executes: kubectl describe pod prometheus-0]

Finding: No memory limits configured.

Recommendation:
1. Set memory limit: 10Gi
2. Reduce retention period (currently 90d → 30d)
3. Enable chunk compression
```

---

## 🎓 How It Works

### LangGraph State Machine

Chameleon-SRE uses **LangGraph** to implement a stateful reasoning loop:

```python
def agent_node(state):
    """Main reasoning loop"""
    
    # 1. THINK: Analyze current situation
    messages = [system_prompt] + state["messages"]
    response = llm.invoke(messages)
    
    # 2. ACT: Decide if action needed
    if action_detected(response):
        # 3. OBSERVE: Execute and capture results
        observation = execute_tool(action)
        
        # 4. DECIDE: Continue or finish
        if should_continue(observation):
            return loop_back_to_think()
        else:
            return finish()
```

### ReAct Pattern

The agent uses **ReAct (Reasoning + Acting)**:

```
User: "Why is my pod failing?"
  ↓
Think: "I need to check pod status first"
  ↓
Act: execute_k8s_command("kubectl get pods")
  ↓
Observe: "Pod is in ImagePullBackOff"
  ↓
Think: "Now I need details about this error"
  ↓
Act: describe_resource("pod", "myapp-xyz")
  ↓
Observe: "Error: image 'myapp:latset' not found"
  ↓
Think: "That's a typo - should be 'latest'"
  ↓
Answer: "Fix the image tag from 'latset' to 'latest'"
```

### RAG (Retrieval Augmented Generation)

When the agent needs expert knowledge:

```
User asks question
  ↓
Agent queries ChromaDB (semantic search)
  ↓
Retrieves top 3 relevant docs
  ↓
Combines with live kubectl data
  ↓
Generates informed answer
```

---

## 🛠️ Development

### Project Structure

```
chameleon-sre/
├── src/                    # Core application
│   ├── agent.py           # LangGraph state machine
│   ├── tools.py           # Kubernetes tools
│   ├── state.py           # Agent state definitions
│   ├── prompts.py         # System prompts
│   ├── config.py          # Configuration
│   └── utils.py           # Helper functions
│
├── models/                 # LLM clients
│   ├── ollama_client.py   # Ollama integration
│   └── model_config.yaml  # Model parameters
│
├── rag/                    # RAG system
│   ├── vectorstore.py     # ChromaDB integration
│   ├── embeddings.py      # Embedding management
│   └── retriever.py       # Document retrieval
│
├── scripts/                # Automation
│   ├── ingest_docs.py     # Load documentation
│   ├── setup_minikube.sh  # Local cluster setup
│   └── deploy.sh          # Deployment automation
│
├── k8s/                    # Kubernetes manifests
│   ├── namespace.yaml
│   ├── rbac.yaml
│   └── deployment.yaml
│
├── docker/                 # Container config
│   └── Dockerfile
│
├── data/                   # Persistent data
│   └── chroma_db/         # Vector database
│
└── tests/                  # Test suite
    ├── test_agent.py
    ├── test_tools.py
    └── test_rag.py
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test
pytest tests/test_agent.py -v

# With coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code
black src/ models/ rag/

# Lint
ruff check src/

# Type checking
mypy src/
```

---

## 🔒 Security & Safety

### Built-in Safeguards

1. **Command Validation**
   - Blocks `delete`, `drain`, `cordon` by default
   - Requires explicit flag to enable destructive commands

2. **Dry-Run Mode**
   ```bash
   DRY_RUN_MODE=true python -m src.agent
   ```

3. **Timeout Protection**
   - Commands timeout after 5 minutes
   - Prevents hanging operations

4. **Namespace Isolation**
   - Agent operates in specified namespace only
   - Cannot affect other namespaces without permission

5. **RBAC Compatible**
   - Works with Kubernetes ServiceAccounts
   - Respects cluster security policies

### Enabling Destructive Commands

⚠️ **Use with caution in development only**

```bash
# In .env
ALLOW_DESTRUCTIVE_COMMANDS=true
```

Or use dry-run mode for testing:

```bash
DRY_RUN_MODE=true python -m src.agent
```

---

## 📊 Performance

### Benchmarks

| Metric | Value |
|--------|-------|
| Query response time | 10-20 seconds |
| kubectl execution | 0.5-1 second |
| RAG search | 0.1-0.5 seconds |
| Memory usage | ~500MB (with 3B model) |
| Disk usage | ~3GB (models + data) |

### Model Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| llama3.2:1b | 1GB | ⚡⚡⚡ Fast | ⭐⭐ Good | Laptops, quick queries |
| llama3.2:3b | 2GB | ⚡⚡ Medium | ⭐⭐⭐ Great | Balanced performance |
| mistral:7b | 4GB | ⚡ Slow | ⭐⭐⭐⭐ Excellent | Desktop, complex tasks |

**Recommendation**: Start with `llama3.2:3b` for best balance.

---

## 📚 Knowledge Base

### Built-in Troubleshooting Guides

The RAG system includes comprehensive guides for:

1. **ImagePullBackOff** - Image pull failures
2. **CrashLoopBackOff** - Repeated pod crashes
3. **Pending Pods** - Scheduling and resource issues
4. **OOMKilled** - Out of memory errors
5. **Service Not Accessible** - Networking problems
6. **Readiness Probe Failures** - Health check issues
7. **ConfigMap/Secret Issues** - Configuration problems
8. **Persistent Volume Issues** - Storage problems
9. **Resource Limits Best Practices** - CPU/memory tuning
10. **Node Issues** - Node-level problems

Each guide includes:
- ✅ Common causes (5-6 scenarios)
- ✅ Diagnosis steps with kubectl commands
- ✅ Step-by-step solutions
- ✅ Best practices

### Adding Your Own Documentation

```python
# Edit scripts/ingest_docs.py

K8S_DOCS.append({
    "topic": "Your Custom Topic",
    "content": """
    Your detailed troubleshooting guide here.
    
    Common causes:
    1. Cause one
    2. Cause two
    
    Diagnosis:
    - kubectl commands to run
    
    Solutions:
    - Step-by-step fixes
    """,
    "source": "your-team-docs"
})

# Re-run ingestion
python scripts/ingest_docs.py --reset
```

---

## 🎛️ Configuration

### Environment Variables

```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Hardware
DEVICE=auto  # auto, mps, cuda, cpu
USE_GPU=true

# Agent
MAX_ITERATIONS=10
TIMEOUT_SECONDS=300
VERBOSE=true

# Kubernetes
KUBECONFIG=~/.kube/config
K8S_NAMESPACE=default

# Safety
ALLOW_DESTRUCTIVE_COMMANDS=false
DRY_RUN_MODE=false

# ChromaDB
CHROMA_DB_PATH=./data/chroma_db
CHROMA_COLLECTION_NAME=k8s_docs
```

### Model Configuration

```yaml
# models/model_config.yaml

model:
  name: "llama3.2:3b"
  temperature: 0.1  # Low for deterministic SRE tasks

generation:
  max_tokens: 2048
  context_window: 8192

tools:
  enabled: true
  max_retries: 3

safety:
  timeout_seconds: 300
  require_confirmation_for:
    - delete
    - drain
    - cordon
```

---

## 🐳 Docker Deployment

### Build Image

```bash
docker build -f docker/Dockerfile -t chameleon-sre:latest .
```

### Run Container

```bash
docker run -it \
  -v ~/.kube/config:/root/.kube/config \
  -v ./data:/app/data \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  chameleon-sre:latest
```

---

## ☸️ Kubernetes Deployment

### Deploy to Cluster

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n chameleon-sre

# View logs
kubectl logs -f deployment/chameleon-sre -n chameleon-sre
```

### RBAC Configuration

The agent requires these permissions:

```yaml
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "describe"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list"]
```

---

## 🔧 Troubleshooting

### Common Issues

**1. "Connection refused" to Ollama**

```bash
# Start Ollama server
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

**2. "Connection refused" to Kubernetes**

```bash
# Set kubectl context
kubectl config use-context minikube

# Verify connection
kubectl get nodes
```

**3. "No documents found" in RAG**

```bash
# Run ingestion script
python scripts/ingest_docs.py

# Verify documents loaded
python scripts/ingest_docs.py --test
```

**4. Agent too slow**

```bash
# Use lighter model
ollama pull llama3.2:1b

# Update .env
OLLAMA_MODEL=llama3.2:1b
```

**5. Out of memory**

```bash
# Reduce model size or close other applications
# Monitor with:
top  # macOS/Linux
```

---

## 🗺️ Roadmap

### ✅ Phase 1: Core Agent (Complete)
- [x] LangGraph state machine
- [x] Kubernetes tool integration
- [x] Safety guards and validation
- [x] Ollama local LLM
- [x] Interactive CLI

### ✅ Phase 2: RAG System (Complete)
- [x] ChromaDB vector store
- [x] Documentation ingestion
- [x] Semantic search
- [x] 10 troubleshooting guides

### 🚧 Phase 3: Production Features (In Progress)
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests
- [ ] Prometheus metrics
- [ ] Unit test coverage
- [ ] CI/CD pipeline

### 📋 Phase 4: Advanced Capabilities (Planned)
- [ ] Multi-cluster support
- [ ] Automated remediation (with approval)
- [ ] Slack/Teams integration
- [ ] Incident report generation
- [ ] Custom runbook execution
- [ ] Web UI dashboard

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with tests
4. **Run tests**: `make test`
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=src tests/

# Format code
make format

# Lint
make lint
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain Team** - For the incredible LangGraph framework
- **Ollama Team** - For making local LLMs accessible and easy
- **ChromaDB** - For the excellent vector database
- **Kubernetes Community** - For comprehensive documentation
- **Open Source Community** - For the amazing tools and libraries

---

## 📧 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/chameleon-sre/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/yourusername/chameleon-sre/discussions)
- **Email**: your.email@example.com
- **Twitter**: [@yourusername](https://twitter.com/yourusername)

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! It helps others discover the project.

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/chameleon-sre&type=Date)](https://star-history.com/#yourusername/chameleon-sre&Date)

---

## 🎓 Learn More

### Resources
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Ollama Documentation](https://ollama.ai/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

### Related Projects
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [Ollama](https://github.com/ollama/ollama) - Local LLM runner
- [kubectl-ai](https://github.com/sozercan/kubectl-ai) - AI assistant for kubectl

---

**Built with ❤️ for Site Reliability Engineers**

*Making Kubernetes troubleshooting autonomous, one pod at a time.* 🦎

---

