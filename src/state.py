"""
State definitions for LangGraph agent.
Defines the AgentState that tracks conversation history and execution context.
"""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    State schema for the Chameleon-SRE agent.
    
    This state is maintained across all nodes in the LangGraph state machine.
    The 'add_messages' reducer ensures messages are appended rather than replaced.
    """
    
    # Conversation history (automatic message accumulation)
    messages: Annotated[list, add_messages]
    
    # Execution context
    iteration_count: int
    error_log: list[str]
    last_tool_output: str | None
    
    # Task tracking
    task_completed: bool
    requires_human_intervention: bool
    
    # Kubernetes context
    current_namespace: str
    affected_resources: list[str]


def create_initial_state(namespace: str = "default") -> AgentState:
    """
    Create a fresh agent state for a new conversation.
    
    Args:
        namespace: Kubernetes namespace to operate in
        
    Returns:
        AgentState: Initial state with empty values
    """
    return AgentState(
        messages=[],
        iteration_count=0,
        error_log=[],
        last_tool_output=None,
        task_completed=False,
        requires_human_intervention=False,
        current_namespace=namespace,
        affected_resources=[],
    )


def should_continue(state: AgentState, max_iterations: int = 10) -> bool:
    """
    Determine if the agent should continue executing.
    
    Args:
        state: Current agent state
        max_iterations: Maximum allowed iterations
        
    Returns:
        bool: True if agent should continue, False otherwise
    """
    # Stop if task is complete
    if state["task_completed"]:
        return False
    
    # Stop if human intervention is needed
    if state["requires_human_intervention"]:
        return False
    
    # Stop if max iterations reached
    if state["iteration_count"] >= max_iterations:
        return False
    
    return True


if __name__ == "__main__":
    # Test state creation
    state = create_initial_state("production")
    print("Initial State:")
    print(f"  Namespace: {state['current_namespace']}")
    print(f"  Iteration Count: {state['iteration_count']}")
    print(f"  Task Completed: {state['task_completed']}")
    print(f"  Should Continue: {should_continue(state)}")
