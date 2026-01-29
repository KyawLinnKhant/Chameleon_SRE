# 🦎 Chameleon-SRE: Autonomous Site Reliability Engineer

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-M2%20Optimized-black.svg)](https://www.apple.com/mac/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Executive Summary

Chameleon-SRE is a **Compound AI System** designed to autonomously monitor, diagnose, and repair Kubernetes clusters. Unlike simple chatbots, it operates as a **Stateful Agent** using LangGraph, enabling it to reason in loops (Think → Act → Observe → Correct) rather than linear chains.

**Key Features:**
- 🔒 **100% Local**: Runs entirely on Apple Silicon using Ollama (zero cloud costs)
- 🧠 **Self-Healing**: Autonomous error detection and correction loops
- 📚 **RAG-Powered**: ChromaDB knowledge base for technical documentation
- 🎛️ **Kubernetes Native**: Direct cluster access via kubectl
- 🔍 **Observable**: Full LangSmith tracing for debugging

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chameleon-SRE Agent                      │
├─────────────────────────────────────────────────────────────┤
│  Cognitive Engine: Llama 3.2 (3B) on Ollama                │
│  Orchestrator: LangGraph State Machine                      │
│  Tools: kubectl | RAG Search | Voice Alerts                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Knowledge Base (ChromaDB)                       │
│  - Kubernetes Documentation                                  │
│  - Error Resolution Playbooks                                │
│  - Historical Incident Logs                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           Kubernetes Cluster (Minikube)                      │
│  - Pods, Services, Deployments                               │
│  - ConfigMaps, Secrets, PVCs                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Hardware**: Apple Silicon (M1/M2/M3) or x86 with GPU
- **Software**:
  - Python 3.10+
  - Conda/Miniconda
  - Docker Desktop
  - Ollama
  - kubectl & minikube

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/chameleon-sre.git
cd chameleon-sre

# 2. Create Conda environment
conda create -n chameleon-sre python=3.10 -y
conda activate chameleon-sre

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Ollama server
ollama serve &

# 5. Pull the LLM model
ollama pull llama3.2

# 6. Start Minikube
minikube start --driver=docker

# 7. Ingest documentation into RAG
python scripts/ingest_docs.py

# 8. Run the agent
python src/main.py
```

---

## 📦 Project Structure

```
chameleon-sre/
├── src/
│   ├── __init__.py
│   ├── config.py          # Hardware detection & settings
│   ├── state.py           # LangGraph state definition
│   ├── tools.py           # kubectl, RAG, voice tools
│   ├── agent.py           # Core agent logic
│   └── main.py            # Entry point
├── scripts/
│   ├── ingest_docs.py     # RAG data ingestion
│   └── test_k8s.py        # Infrastructure tests
├── k8s/
│   ├── deployment.yaml    # Agent deployment
│   ├── rbac.yaml          # Permissions
│   └── configmap.yaml     # Configuration
├── docs/
│   └── k8s-troubleshooting.md  # Sample documentation
├── tests/
│   ├── test_agent.py
│   └── test_tools.py
├── Dockerfile             # Multi-stage build
├── docker-compose.yaml    # Local development
├── requirements.txt
└── README.md
```

---

## 🛠️ Usage

### Interactive Mode

```bash
python src/main.py
```

```
🦎 Chameleon-SRE v1.0 | Apple Silicon Optimized
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Device: mps (Apple Metal Performance Shaders)
Model: llama3.2 @ localhost:11434
Knowledge Base: 127 documents loaded

You: Check the status of all pods in the default namespace
Agent: Executing kubectl get pods -n default...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found 3 pods:
• nginx-deployment-abc123 (Running)
• redis-master-xyz789 (CrashLoopBackOff) ⚠️
• postgres-db-def456 (Running)

Investigating redis-master-xyz789...
[RAG Search] Querying knowledge base for "CrashLoopBackOff"...
Found resolution: Missing ConfigMap 'redis-config'

Attempting auto-repair...
✅ Created ConfigMap 'redis-config'
✅ Pod redis-master-xyz789 restarted successfully
```

### Kubernetes Deployment

```bash
# Build Docker image
docker build -t chameleon-sre:v1 .

# Load into Minikube
minikube image load chameleon-sre:v1

# Deploy to cluster
kubectl apply -f k8s/

# View logs
kubectl logs -f deployment/chameleon-sre
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test specific component
pytest tests/test_agent.py::test_self_healing_loop

# Test Kubernetes connectivity
python scripts/test_k8s.py
```

---

## 📊 Monitoring

The agent uses **LangSmith** for observability:

1. Sign up at [smith.langchain.com](https://smith.langchain.com)
2. Get your API key
3. Set environment variables:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_key_here
```

View traces in the LangSmith dashboard to debug agent decisions.

---

## 🔧 Configuration

Edit `src/config.py`:

```python
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2"  # or llama3.2:70b for better reasoning
MAX_RETRIES = 3
TEMPERATURE = 0.0  # Deterministic for production
```

---

## 🐛 Troubleshooting

### Issue: "Ollama connection refused"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
pkill ollama && ollama serve &
```

### Issue: "kubectl: command not found"
```bash
# Install kubectl
brew install kubectl

# Verify Minikube context
kubectl config current-context  # Should show "minikube"
```

### Issue: "ChromaDB persistence error"
```bash
# Clear and rebuild vector database
rm -rf chroma_db/
python scripts/ingest_docs.py
```

---

## 🗺️ Roadmap

- [x] **Phase 1**: Core agent with LangGraph
- [x] **Phase 2**: RAG knowledge base
- [x] **Phase 3**: Kubernetes deployment
- [ ] **Phase 4**: Prometheus metrics integration
- [ ] **Phase 5**: Slack/PagerDuty notifications
- [ ] **Phase 6**: Multi-cluster support
- [ ] **Phase 7**: Predictive failure detection

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **LangChain Team**: For the incredible LangGraph framework
- **Ollama**: For making local LLMs accessible
- **Anthropic**: For Claude (used to design this architecture 😉)

---

## 📧 Contact

- **Author**: Kyaw Linn Khant
- **Issues**: [GitHub Issues](https://github.com/yourusername/chameleon-sre/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/chameleon-sre/discussions)

---
