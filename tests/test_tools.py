"""
Test suite for Chameleon-SRE tools
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools import validate_kubectl_command


class TestKubectlValidation:
    """Test kubectl command validation"""
    
    def test_valid_get_command(self):
        """Test that simple get commands are allowed"""
        assert validate_kubectl_command("kubectl get pods") is True
        assert validate_kubectl_command("kubectl get deployments") is True
    
    def test_valid_describe_command(self):
        """Test that describe commands are allowed"""
        assert validate_kubectl_command("kubectl describe pod nginx-123") is True
    
    def test_valid_logs_command(self):
        """Test that logs commands are allowed"""
        assert validate_kubectl_command("kubectl logs nginx-123") is True
        assert validate_kubectl_command("kubectl logs nginx-123 --tail=50") is True
    
    def test_invalid_delete_namespace(self):
        """Test that namespace deletion is blocked"""
        assert validate_kubectl_command("kubectl delete namespace production") is False
    
    def test_invalid_delete_all(self):
        """Test that bulk deletion is blocked"""
        assert validate_kubectl_command("kubectl delete pods --all") is False
        assert validate_kubectl_command("kubectl delete deployment --all") is False
    
    def test_invalid_command_chaining(self):
        """Test that command chaining is blocked"""
        assert validate_kubectl_command("kubectl get pods && kubectl delete pod test") is False
        assert validate_kubectl_command("kubectl get pods; rm -rf /") is False
    
    def test_invalid_piping(self):
        """Test that piping is blocked"""
        assert validate_kubectl_command("kubectl get pods | grep nginx") is False
    
    def test_invalid_command_substitution(self):
        """Test that command substitution is blocked"""
        assert validate_kubectl_command("kubectl get pods `whoami`") is False
        assert validate_kubectl_command("kubectl get pods $(whoami)") is False
    
    def test_case_insensitive_blocking(self):
        """Test that validation is case-insensitive"""
        assert validate_kubectl_command("kubectl DELETE namespace prod") is False
        assert validate_kubectl_command("kubectl Delete NAMESPACE prod") is False


class TestToolSafety:
    """Test overall tool safety mechanisms"""
    
    def test_read_only_operations_allowed(self):
        """Test that read-only operations pass validation"""
        read_only_commands = [
            "kubectl get pods",
            "kubectl describe deployment nginx",
            "kubectl logs pod-123",
            "kubectl top nodes",
            "kubectl get events"
        ]
        
        for cmd in read_only_commands:
            assert validate_kubectl_command(cmd) is True, f"Failed on: {cmd}"
    
    def test_safe_modifications_allowed(self):
        """Test that safe modification operations pass"""
        safe_commands = [
            "kubectl rollout restart deployment/nginx",
            "kubectl scale deployment/nginx --replicas=3",
            "kubectl annotate pod nginx-123 description=test"
        ]
        
        for cmd in safe_commands:
            assert validate_kubectl_command(cmd) is True, f"Failed on: {cmd}"
    
    def test_dangerous_operations_blocked(self):
        """Test that dangerous operations are blocked"""
        dangerous_commands = [
            "kubectl delete namespace kube-system",
            "kubectl delete pods --all",
            "kubectl get pods && rm -rf /",
            "kubectl get pods | xargs kubectl delete pod",
            "kubectl delete pv data-volume"
        ]
        
        for cmd in dangerous_commands:
            assert validate_kubectl_command(cmd) is False, f"Should block: {cmd}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
