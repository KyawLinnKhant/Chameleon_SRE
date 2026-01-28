# 🦎 Chameleon-SRE

**Autonomous Site Reliability Engineer powered by LangGraph & Ollama**

Chameleon-SRE is an AI agent that autonomously monitors, diagnoses, and resolves Kubernetes cluster issues. Unlike traditional chatbots, it operates as a stateful agent using LangGraph, enabling true reasoning loops and self-correction.

---

## 🎯 Key Features

- **🧠 Autonomous Reasoning**: LangGraph state machine with cyclic Think → Act → Observe → Correct loops
- **💻 Local-First**: Runs entirely on Apple Silicon (M1/M2/M3) using Ollama—zero cloud costs
- **🔒 Safe by Design**: Built-in command validation and dry-run mode prevent destructive operations
- **📚 RAG-Enabled**: ChromaDB integration for context-aware troubleshooting
- **🎯 Production-Ready**: Designed for real Kubernetes clusters with RBAC and observability

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Human Query   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  LangGraph State Machine    │
│  (Think → Act → Observe)    │
└─────────┬───────────────────┘
          │
          ├──► 🔧 Kubectl Tools (Safe Wrappers)
          ├──► 📚 ChromaDB (RAG Knowledge)
          └──► 🔊 System Alerts (TTS)
          │
          ▼
┌─────────────────────────────┐
│   Ollama (Llama 3.2:3b)     │
│   Running on M2 GPU         │
└─────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# 1. Install Ollama
brew install ollama

# 2. Start Ollama server
ollama serve

# 3. Download the model
ollama pull llama3.2:3b

# 4. Install Kubernetes tools
brew install kubectl minikube docker
```

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd chameleon-sre

# Create virtual environment
conda create -n chameleon-sre python=3.11 -y
conda activate chameleon-sre

# Install dependencies
make install

# Or manually:
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Start Minikube (local K8s cluster)
make k8s-setup
```

### Run the Agent

```bash
# Interactive mode
python -m src.agent

# Or use make
make run

# With debug logging
make run-debug
```

---

## 📖 Usage Examples

### Example 1: Pod Troubleshooting

```
🔧 You: Why is my frontend pod crashing?

🦎 Chameleon-SRE:
Analysis: I need to check the pod status and recent logs.

[Executing: kubectl get pods -n default]
NAME                        READY   STATUS             RESTARTS
frontend-7d4b8c9f6d-xyz     0/1     ImagePullBackOff   3

[Executing: kubectl describe pod frontend-7d4b8c9f6d-xyz]
Events:
  Failed to pull image "frontend:latset": ErrImagePull

Diagnosis: The pod is failing due to a typo in the image tag.
The deployment is trying to pull "latset" instead of "latest".

Recommendation: Fix the image tag in your deployment YAML:
  image: frontend:latest  # Fixed typo
```

### Example 2: Resource Investigation

```
🔧 You: Check the resource usage of pods in the monitoring namespace

🦎 Chameleon-SRE:
[Executing: kubectl top pods -n monitoring]

NAME              CPU(cores)   MEMORY(bytes)
prometheus-0      120m         8.2Gi
grafana-xyz       25m          512Mi

Analysis: Prometheus is consuming 8.2GB of memory. 
Let me check the configuration...

[Executing: kubectl describe pod prometheus-0 -n monitoring]

Finding: No memory limits are set on the Prometheus pod.

Recommendation:
1. Set memory limit: 10Gi
2. Reduce retention period from 90d to 30d
3. Enable chunk compression
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
│   └── config.py          # Configuration
├── models/                 # LLM clients
│   └── ollama_client.py
├── rag/                    # RAG system (Phase 2)
├── k8s/                    # Kubernetes manifests
├── docker/                 # Container config
└── scripts/                # Automation scripts
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_agent.py -v

# With coverage
make test-coverage
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format

# Type checking
mypy src/
```

---

## 🧪 Testing Without Kubernetes

You can test the agent without a real Kubernetes cluster:

```python
from src.agent import run_agent

# The agent will work with dry-run mode
response = run_agent("What would happen if I deleted pod xyz?")
print(response)
```

---

## 🔒 Safety Features

### Built-in Safeguards

1. **Command Validation**: Dangerous commands (`delete`, `drain`, `cordon`) are blocked by default
2. **Dry-Run Mode**: Test commands without executing them
3. **Timeout Protection**: Commands timeout after 5 minutes
4. **Namespace Isolation**: Agent operates in specified namespace only
5. **Human Confirmation**: Critical actions require explicit approval

### Enable Destructive Commands

Only enable this in development environments:

```bash
# In .env
ALLOW_DESTRUCTIVE_COMMANDS=true
```

---

## 📊 Observability

### LangSmith Integration

Track agent reasoning and tool calls:

```bash
# In .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key_here
```

View traces at: https://smith.langchain.com

### Logs

```bash
# Logs are stored in logs/
tail -f logs/chameleon-sre_*.log

# Real-time monitoring
watch -n 1 'kubectl get pods -A'
```

---

## 🚢 Deployment

### Docker

```bash
# Build image
make docker-build

# Run container
docker run -it \
  -v ~/.kube/config:/root/.kube/config \
  chameleon-sre:latest
```

### Kubernetes

```bash
# Deploy to cluster
make k8s-deploy

# Check agent logs
kubectl logs -f deployment/chameleon-sre -n chameleon-sre

# Delete deployment
kubectl delete -f k8s/
```

---

## 🎓 Learning Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug/)

---

## 🗺️ Roadmap

### Phase 1: Core Agent ✅
- [x] LangGraph state machine
- [x] Kubernetes tool wrappers
- [x] Safety guards and validation
- [x] Ollama integration

### Phase 2: RAG System ⏳
- [ ] ChromaDB setup
- [ ] Documentation ingestion
- [ ] Semantic search
- [ ] Context-aware responses

### Phase 3: Production Features ⏳
- [ ] Containerization (Docker)
- [ ] Kubernetes deployment
- [ ] Prometheus metrics
- [ ] Alerting integration

### Phase 4: Advanced Capabilities 📋
- [ ] Multi-cluster support
- [ ] Automated remediation
- [ ] Incident reports
- [ ] Slack integration

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **LangChain Team**: For the incredible LangGraph framework
- **Ollama Team**: For making local LLMs accessible
- **Kubernetes Community**: For comprehensive documentation

---

## 📧 Contact

For questions or feedback:
- Open an issue on GitHub
- Email: mlops@example.com
- Twitter: @chameleon_sre

---

**Built with ❤️ for Site Reliability Engineers**
