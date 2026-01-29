.PHONY: help install test run docker k8s clean

help:
	@echo "🦎 Chameleon-SRE Makefile"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "Available targets:"
	@echo "  make install       - Install dependencies"
	@echo "  make ingest        - Setup ChromaDB knowledge base"
	@echo "  make test          - Run all tests"
	@echo "  make test-k8s      - Test Kubernetes connectivity"
	@echo "  make run           - Run agent interactively"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run with docker-compose"
	@echo "  make k8s-deploy    - Deploy to Kubernetes"
	@echo "  make k8s-logs      - View Kubernetes logs"
	@echo "  make k8s-delete    - Delete Kubernetes deployment"
	@echo "  make clean         - Clean temporary files"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

install:
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

ingest:
	python scripts/ingest_docs.py
	@echo "✅ Knowledge base initialized"

test:
	pytest tests/ -v
	@echo "✅ All tests passed"

test-k8s:
	python scripts/test_k8s.py
	@echo "✅ Infrastructure tests complete"

run:
	python src/main.py

docker-build:
	docker build -t chameleon-sre:v1 .
	@echo "✅ Docker image built"

docker-run:
	docker-compose up -d
	@echo "✅ Docker services started"
	@echo "View logs: docker-compose logs -f"

docker-stop:
	docker-compose down
	@echo "✅ Docker services stopped"

k8s-deploy:
	@echo "Building and loading image..."
	docker build -t chameleon-sre:v1 .
	minikube image load chameleon-sre:v1
	@echo "Deploying to Kubernetes..."
	kubectl apply -f k8s/
	@echo "✅ Deployed to Kubernetes"
	@echo "Check status: kubectl get pods -l app=chameleon-sre"

k8s-logs:
	kubectl logs -f deployment/chameleon-sre

k8s-status:
	kubectl get all -l app=chameleon-sre

k8s-delete:
	kubectl delete -f k8s/
	@echo "✅ Kubernetes resources deleted"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf dist build
	@echo "✅ Cleaned temporary files"

dev-setup: install ingest
	@echo "✅ Development environment ready!"
	@echo "Next steps:"
	@echo "  1. Start Ollama: ollama serve"
	@echo "  2. Start Minikube: minikube start"
	@echo "  3. Run agent: make run"
