"""
Main entry point for Chameleon-SRE
Interactive CLI for the autonomous SRE agent
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_device_info, OLLAMA_BASE_URL, MODEL_NAME, CHROMA_PERSIST_DIR
from src.agent import run_agent


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )


def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 60)
    print("🦎 Chameleon-SRE v1.0 | Autonomous Site Reliability Engineer")
    print("=" * 60)
    
    device_info = get_device_info()
    print(f"Device: {device_info['device']} ({device_info.get('gpu_name', 'CPU')})")
    print(f"Model: {MODEL_NAME} @ {OLLAMA_BASE_URL}")
    print(f"Knowledge Base: {CHROMA_PERSIST_DIR}")
    print("=" * 60 + "\n")


def check_prerequisites():
    """Check if required services are running"""
    checks = []
    
    # Check Ollama
    import requests
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            checks.append(("✅ Ollama Server", "Running"))
        else:
            checks.append(("❌ Ollama Server", "Not responding"))
    except:
        checks.append(("❌ Ollama Server", "Not running - Start with 'ollama serve'"))
    
    # Check kubectl
    import subprocess
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            timeout=3
        )
        if result.returncode == 0:
            checks.append(("✅ Kubernetes", "Connected"))
        else:
            checks.append(("⚠️ Kubernetes", "Not accessible"))
    except:
        checks.append(("❌ kubectl", "Not installed"))
    
    # Check ChromaDB
    if os.path.exists(CHROMA_PERSIST_DIR):
        checks.append(("✅ ChromaDB", "Initialized"))
    else:
        checks.append(("⚠️ ChromaDB", "Run 'python scripts/ingest_docs.py' to setup"))
    
    print("System Status:")
    for status, message in checks:
        print(f"  {status}: {message}")
    print()
    
    # Critical check
    if any("❌ Ollama" in c[0] for c in checks):
        print("⚠️  WARNING: Ollama is required. Start with: ollama serve")
        return False
    
    return True


def interactive_mode():
    """Run agent in interactive mode"""
    print("Type 'exit' or 'quit' to stop, 'help' for examples\n")
    
    while True:
        try:
            user_input = input("🧑 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == "help":
                print_help()
                continue
            
            # Run agent
            print()
            result = run_agent(user_input, verbose=True)
            
            # Print final response
            if result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    print(f"\n🦎 Agent: {last_message.content}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            logging.exception("Error in interactive mode")


def print_help():
    """Print example commands"""
    examples = [
        "Check the status of all pods in default namespace",
        "Find pods in CrashLoopBackOff and diagnose the issue",
        "Show me logs for the nginx deployment",
        "Restart the redis-master deployment",
        "Search the knowledge base for ImagePullBackOff solutions",
        "Alert me if any critical pods are down"
    ]
    
    print("\n📋 Example Commands:")
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example}")
    print()


def batch_mode(query: str):
    """Run a single query and exit"""
    print()
    result = run_agent(query, verbose=True)
    
    if result["messages"]:
        last_message = result["messages"][-1]
        if hasattr(last_message, "content"):
            print(f"\n🦎 Agent: {last_message.content}\n")


def main():
    """Main entry point"""
    setup_logging()
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n⚠️  Some prerequisites are missing. Continue anyway? (y/n): ", end="")
        if input().lower() != 'y':
            sys.exit(1)
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Chameleon-SRE Autonomous Agent")
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Run a single query and exit (batch mode)"
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive mode"
    )
    
    args = parser.parse_args()
    
    if args.query:
        batch_mode(args.query)
    elif not args.no_interactive:
        interactive_mode()
    else:
        print("No query provided. Use --query or run without --no-interactive")
        sys.exit(1)


if __name__ == "__main__":
    main()
