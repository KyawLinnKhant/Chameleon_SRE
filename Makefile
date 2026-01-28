.PHONY: help install dev-install clean test lint format docker-build k8s-deploy

help:
	@echo "Chameleon-SRE - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install production dependencies"
	@echo "  make dev-install      Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test            Run test suite"
	@echo "  make lint            Run linters (ruff)"
	@echo "  make format          Format code (black)"
	@echo "  make clean           Remove build artifacts"
	@echo ""
	@echo "RAG:"
	@echo "  make ingest-docs     Load documentation into ChromaDB"
	@echo ""
	@echo "Deployment:"
	@echo "  make docker-build    Build Docker image"
	@echo "  make k8s-setup       Setup Minikube cluster"
	@echo "  make k8s-deploy      Deploy to Kubernetes"
	@echo ""
	@echo "Running:"
	@echo "  make run             Run agent locally"
	@echo "  make run-debug       Run with verbose logging"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

test:
	pytest tests/ -v

lint:
	ruff check src/ models/ rag/ tests/

format:
	black src/ models/ rag/ tests/

ingest-docs:
	python scripts/ingest_docs.py --source ./data/raw/

docker-build:
	docker build -f docker/Dockerfile -t chameleon-sre:latest .

k8s-setup:
	bash scripts/setup_minikube.sh

k8s-deploy:
	bash scripts/deploy.sh

run:
	python -m src.agent

run-debug:
	VERBOSE=true python -m src.agent
