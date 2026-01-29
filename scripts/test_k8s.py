"""
Kubernetes Infrastructure Test Suite
Verifies cluster connectivity and creates test workloads
"""

import subprocess
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools import execute_k8s_command


def run_command(cmd: str, shell: bool = True) -> tuple:
    """Run shell command and return (success, output)"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def test_kubectl_installed():
    """Test if kubectl is installed"""
    print("1️⃣ Testing kubectl installation...", end=" ")
    success, output = run_command("kubectl version --client")
    
    if success:
        print("✅ PASSED")
        return True
    else:
        print("❌ FAILED")
        print(f"   {output}")
        return False


def test_cluster_connection():
    """Test cluster connectivity"""
    print("2️⃣ Testing cluster connection...", end=" ")
    success, output = run_command("kubectl cluster-info")
    
    if success and "Kubernetes control plane" in output:
        print("✅ PASSED")
        return True
    else:
        print("❌ FAILED")
        print(f"   {output}")
        print("   Hint: Run 'minikube start' to create a cluster")
        return False


def test_namespace_access():
    """Test namespace access"""
    print("3️⃣ Testing namespace access...", end=" ")
    success, output = run_command("kubectl get namespaces")
    
    if success:
        print("✅ PASSED")
        return True
    else:
        print("❌ FAILED")
        print(f"   {output}")
        return False


def deploy_test_pod():
    """Deploy a test nginx pod"""
    print("4️⃣ Deploying test pod...", end=" ")
    
    # Create deployment
    cmd = """kubectl create deployment test-nginx --image=nginx:alpine --dry-run=client -o yaml | kubectl apply -f -"""
    success, output = run_command(cmd)
    
    if not success:
        print("❌ FAILED")
        print(f"   {output}")
        return False
    
    # Wait for pod to be ready
    for _ in range(30):
        success, output = run_command("kubectl get pods -l app=test-nginx -o jsonpath='{.items[0].status.phase}'")
        if success and "Running" in output:
            print("✅ PASSED")
            return True
        time.sleep(1)
    
    print("⚠️ TIMEOUT (pod not ready)")
    return False


def test_tool_integration():
    """Test our custom tool integration"""
    print("5️⃣ Testing tool integration...", end=" ")
    
    try:
        result = execute_k8s_command.invoke({"command": "get pods"})
        
        if "ERROR" not in result:
            print("✅ PASSED")
            return True
        else:
            print("❌ FAILED")
            print(f"   {result}")
            return False
    except Exception as e:
        print("❌ FAILED")
        print(f"   {str(e)}")
        return False


def cleanup_test_resources():
    """Clean up test resources"""
    print("6️⃣ Cleaning up test resources...", end=" ")
    
    success, output = run_command("kubectl delete deployment test-nginx --ignore-not-found=true")
    
    if success:
        print("✅ PASSED")
        return True
    else:
        print("⚠️ WARNING")
        print(f"   {output}")
        return True  # Non-critical


def create_broken_pod():
    """Create a pod that will enter CrashLoopBackOff for testing"""
    print("7️⃣ Creating broken pod for testing...", end=" ")
    
    broken_pod_yaml = """
apiVersion: v1
kind: Pod
metadata:
  name: broken-pod
  labels:
    app: test-broken
spec:
  containers:
  - name: crash
    image: busybox
    command: ["sh", "-c", "echo 'I will crash now' && exit 1"]
"""
    
    # Save to temp file
    with open("/tmp/broken-pod.yaml", "w") as f:
        f.write(broken_pod_yaml)
    
    success, output = run_command("kubectl apply -f /tmp/broken-pod.yaml")
    
    if success:
        print("✅ CREATED")
        print("   💡 Agent can now practice fixing this pod!")
        return True
    else:
        print("❌ FAILED")
        print(f"   {output}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🦎 Chameleon-SRE Infrastructure Test Suite")
    print("=" * 60 + "\n")
    
    tests = [
        test_kubectl_installed,
        test_cluster_connection,
        test_namespace_access,
        deploy_test_pod,
        test_tool_integration,
        cleanup_test_resources,
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    # Optional: Create broken pod for agent testing
    print("Optional Test (for agent practice):")
    create_broken_pod()
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Infrastructure is ready.")
        print("\nNext steps:")
        print("  1. Run: python scripts/ingest_docs.py")
        print("  2. Run: python src/main.py")
    else:
        print("⚠️  Some tests failed. Please fix issues above.")
        print("\nCommon fixes:")
        print("  - Install kubectl: brew install kubectl")
        print("  - Start minikube: minikube start")
        print("  - Check Docker: docker ps")
    
    print("=" * 60 + "\n")
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
