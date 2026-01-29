"""
Test suite for Chameleon-SRE agent logic
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state import AgentState, create_initial_state, should_continue


class TestAgentState:
    """Test agent state management"""
    
    def test_create_initial_state(self):
        """Test initial state creation"""
        user_input = "Check pod status"
        state = create_initial_state(user_input)
        
        assert state["current_task"] == user_input
        assert len(state["messages"]) == 1
        assert state["messages"][0]["role"] == "user"
        assert state["iteration_count"] == 0
        assert state["task_complete"] is False
        assert len(state["error_log"]) == 0
    
    def test_should_continue_with_low_iterations(self):
        """Test should_continue returns True when iterations are low"""
        state = create_initial_state("Test task")
        state["iteration_count"] = 3
        
        assert should_continue(state, max_iterations=10) is True
    
    def test_should_continue_with_max_iterations(self):
        """Test should_continue returns False at max iterations"""
        state = create_initial_state("Test task")
        state["iteration_count"] = 10
        
        assert should_continue(state, max_iterations=10) is False
    
    def test_should_continue_with_task_complete(self):
        """Test should_continue returns False when task is complete"""
        state = create_initial_state("Test task")
        state["task_complete"] = True
        
        assert should_continue(state, max_iterations=10) is False
    
    def test_should_continue_with_many_errors(self):
        """Test should_continue returns False with too many errors"""
        state = create_initial_state("Test task")
        state["error_log"] = ["error1", "error2", "error3", "error4", "error5"]
        
        assert should_continue(state, max_iterations=10) is False


class TestStateAnnotations:
    """Test state type annotations"""
    
    def test_messages_list_append(self):
        """Test messages list can be appended"""
        state = create_initial_state("Test")
        initial_count = len(state["messages"])
        
        state["messages"].append({"role": "assistant", "content": "Response"})
        
        assert len(state["messages"]) == initial_count + 1
    
    def test_error_log_accumulation(self):
        """Test error log can accumulate errors"""
        state = create_initial_state("Test")
        
        state["error_log"].append("Error 1")
        state["error_log"].append("Error 2")
        
        assert len(state["error_log"]) == 2
        assert "Error 1" in state["error_log"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
